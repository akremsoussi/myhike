# Dossier d'Analyse : Application Refuges (Architecture 3-Tiers)

**Projet :** Refuges  
**Binôme :** Akrem SOUSSI et Rémi CORTIAL

**Établissement :** Aix-Marseille Université — École d'ingénieurs (Polytech Marseille)  
**Année universitaire :** 2025 – 2026  
**Module :** DEV 1 — Application Trois-Tiers (Enseignant : Mohamed Quafafou)  
**Prototype Figma :** [Refuges – Web App (Figma)](https://www.figma.com/design/KrPHETSktcZgtTbB9uxVyB/Refuges-%E2%80%93-Web-App?node-id=10-2&t=JR58gAGYpNzeFWH1-1)

---

## 1. Contexte et Objectif

Le projet **Refuges** est une application web communautaire répartie en trois couches strictement isolées (**Présentation**, **Métier**, **Données**) dédiée aux randonneurs et alpinistes. Elle permet :
- La consultation cartographique interactive et la recherche de **4 652 refuges et cabanes réels** (issus de `refuges.info`) répartis par massifs montagneux, avec synchronisation automatique des photos.
- L'animation de **communautés par massif** (Alpes, Pyrénées, Préalpes, Corse…) où les membres partagent des publications (récits, photos redimensionnées et nettoyées de leurs métadonnées EXIF, traces GPX avec calcul de distance et dénivelé).
- La planification et l'organisation de **sorties de randonnée** (publiques ou sur invitation) jalonnées d'étapes (refuges ou points libres) et accompagnées d'un tracé cartographique ou GPX.
- Un **réseau social de montagne** complet : demandes d'amis, suggestions d'amis par communautés communes, paramètres fins de confidentialité et recherche transversale.
- Un **espace de modération et d'administration hiérarchisé** permettant le traitement des signalements, l'administration des communautés et la gestion des comptes utilisateurs.

Conformément à l'**Étape 1** du sujet, ce dossier d'analyse définit sans ambiguïté les acteurs, les cas d'utilisation (déclencheur, scénario nominal, cas d'erreur), les règles de gestion traduites dans le schéma relationnel SQL, ainsi que la correspondance complète avec les écrans de la maquette Figma.

---

## 2. Recensement des Acteurs et Matrice des Droits

L'application distingue **quatre profils d'acteurs** aux prérogatives strictement cloisonnées côté client (gardes de routes React) et côté serveur métier (dépendances FastAPI `CurrentUser`, `ActiveUser`, `ModeratorUser` et contrôle hiérarchique) :

| Type d'acteur | Rôle en base (`users.role`) | État de session | Interfaces et fonctionnalités accessibles | Restrictions appliquées |
| :--- | :---: | :---: | :--- | :--- |
| **1. Visiteur sans connexion** | — | Non authentifié (ou compte `pending_email`) | Écrans publics : Connexion (`/connexion`), Inscription (`/inscription`), Mot de passe oublié (`/mot-de-passe-oublie`), Confirmation d'email (`/confirmation-email`), Conditions d'utilisation (`/conditions`), Statut du service (`/statut`). | Toute route applicative (`/carte`, `/communautes`, `/sorties`, `/profil`, `/moderation`) redirige vers `/connexion` (et l'API renvoie `401 Unauthorized`). Un inscrit dont l'email n'est pas encore confirmé est confiné sur l'écran `02b · Compte en attente` (`/inscription/confirmation`). |
| **2. Utilisateur connecté** | `user` | Authentifié (`status = 'active'`) | Accès complet aux écrans utilisateur `03` à `12` : Carte des refuges, Fiche refuge, Mon profil, Mes amis, Confidentialité, Profil d'un tiers, Communautés, Publication de posts (texte/photos/GPX), Sorties (création, participation, invitation), Recherche globale, Signalement de posts ou de comptes. | Aucun accès à l'onglet ni aux routes `/moderation/*` (redirection vers `/carte` côté client, rejet `403 Forbidden` côté API). Ne peut modifier/supprimer que ses propres posts et sorties. |
| **3. Administrateur classique** | `moderator` | Authentifié (`status = 'active'`) | Tous les droits d'un utilisateur connecté + onglet **« Modération »** dans la barre de navigation donnant accès aux écrans `13` à `16` : Tableau de bord, Signalements, création/modification/suppression de Communautés, export CSV des comptes, et **suspension / réactivation / suppression des comptes utilisateurs classiques (`user`)**. Peut modérer (supprimer) tout post ou sortie signalée. | **Protection hiérarchique stricte :** ne peut **ni promouvoir ni rétrograder** le rôle d'un compte (`403 Forbidden`), et ne peut **ni suspendre, ni réactiver, ni supprimer** un autre administrateur classique (`moderator`) ou un Super Administrateur (`super_admin`). |
| **4. Administrateur supérieur** | `super_admin` | Authentifié (`status = 'active'`) | **Droits absolus sur la plateforme :** toutes les prérogatives de modération + **seul rôle habilité à promouvoir un utilisateur en administrateur classique (`moderator`) ou à lui retirer son rôle**, ainsi qu'à suspendre, réactiver ou supprimer le compte d'un administrateur classique (`moderator`). | Ne peut pas s'auto-suspendre, s'auto-rétrograder ou supprimer son propre compte (`409 Conflict`). |

---

## 3. Cas d'Usage Principaux

Chaque cas d'usage précise son déclencheur, son déroulement nominal et le traitement explicite de ses cas d'erreur.

### CU1 — Inscription, confirmation par email et authentification
- **Acteur :** Visiteur sans connexion
- **Déclencheur :** Soumission du formulaire d'inscription (`/inscription`) ou de connexion (`/connexion`).
- **Enchaînement nominal :**
  1. Lors de l'inscription, le visiteur saisit un pseudo (`^[a-z0-9_]{3,30}$`), une adresse email valide, un mot de passe d'au moins 8 caractères et accepte les conditions d'utilisation.
  2. Le serveur métier calcule le condensat **Argon2id** du mot de passe, crée l'utilisateur avec `status = 'pending_email'`, génère un jeton de vérification à usage unique (dont seule l'empreinte SHA-256 est stockée dans `email_tokens`) et envoie le lien de confirmation (`/confirmation-email?token=...`).
  3. Tant que l'adresse n'est pas confirmée, l'utilisateur est dirigé vers l'écran **02b · Compte en attente** (`/inscription/confirmation`), où il peut renvoyer l'email (après délai anti-abus de 60 s) ou corriger son adresse email.
  4. Au clic sur le lien de confirmation (`POST /api/auth/verify-email`), le compte passe à `status = 'active'` et `email_verified_at` est horodaté.
  5. Lors de la connexion (`POST /api/auth/login`), le serveur vérifie le condensat Argon2id, crée une session en base (`sessions`) et dépose le cookie `refuges_session` (`HttpOnly`, `SameSite=Lax`).
- **Cas d'erreur :**
  - *Email ou mot de passe erroné :* Réponse `401 Unauthorized` (`invalid_credentials` : « Adresse email ou mot de passe incorrect. ») — message identique dans les deux cas et vérification à temps constant contre un condensat factice pour empêcher l'énumération des comptes.
  - *Compte suspendu par la modération :* Réponse `403 Forbidden` (`account_suspended` : « Ce compte a été suspendu par la modération. »).
  - *Pseudo ou email déjà pris :* Réponse `409 Conflict` avec indication précise du champ en doublon.
  - *Lien de confirmation expiré ou déjà utilisé :* Réponse `400 Bad Request` (`invalid_or_expired_token`).

### CU2 — Réinitialisation de mot de passe oublié
- **Acteur :** Visiteur sans connexion
- **Déclencheur :** Clic sur « Mot de passe oublié ? » depuis l'écran de connexion (`/mot-de-passe-oublie`).
- **Enchaînement nominal :**
  1. Le visiteur saisit son adresse email (`POST /api/auth/password-reset`).
  2. Si un compte non suspendu existe, le serveur invalide les anciens jetons de réinitialisation, génère un nouveau jeton `purpose = 'reset'` valable 1 heure et envoie le lien `/mot-de-passe/nouveau?token=...`.
  3. L'utilisateur choisit son nouveau mot de passe (`POST /api/auth/password-reset/confirm`) : le condensat Argon2id est mis à jour et **toutes les sessions actives du compte sont immédiatement révoquées**.
- **Cas d'erreur :**
  - *Adresse email inconnue ou compte suspendu :* Le serveur renvoie exactement la même réponse `204 No Content` sans révéler si l'adresse est inscrite.
  - *Jeton invalide ou expiré :* Réponse `400 Bad Request` (`invalid_or_expired_token`).

### CU3 — Exploration cartographique et consultation des refuges
- **Acteur :** Utilisateur connecté (`user`, `moderator`, `super_admin`)
- **Déclencheur :** Ouverture de l'écran `03 · Carte` (`/carte`) ou déplacement de la carte Leaflet.
- **Enchaînement nominal :**
  1. À chaque déplacement (`moveend`), le client interroge `GET /api/refuges?bbox=west,south,east,north` avec les filtres actifs (*Tous*, *Gardés*, *Non gardés*, *Avec sortie*) ou un terme de recherche.
  2. Le serveur retourne les refuges de l'emprise (jusqu'à 2 000 marqueurs regroupés par clusters et les 100 refuges les plus proches du centre dans la liste latérale).
  3. L'ouverture de la fiche complète (`04 · Fiche refuge`, `/refuges/:id`) affiche les informations techniques (altitude, places, gardiennage, équipements), télécharge à la demande les photographies depuis `refuges.info`, et liste les sorties à venir passant par ce refuge ainsi que les posts qui le mentionnent.
- **Cas d'erreur :**
  - *Aucun refuge dans la zone ou selon les filtres :* Affichage d'un état vide explicite (« Aucun refuge dans cette zone. »).
  - *Identifiant de refuge inexistant :* Réponse `404 Not Found` (« Ce refuge n'existe pas. »).

### CU4 — Publication dans une communauté (texte, photos WebP, trace GPX)
- **Acteur :** Utilisateur connecté membre d'une communauté
- **Déclencheur :** Clic sur « Nouveau post » (`09 · Nouveau post`, `/posts/nouveau`).
- **Enchaînement nominal :**
  1. L'utilisateur sélectionne optionnellement une communauté dont il est membre et un refuge associé, saisit son récit, choisit la visibilité (`public` ou `friends`), téléverse jusqu'à 4 photos (`POST /api/uploads`) et/ou importe un fichier `.gpx` (ou trace son itinéraire sur la carte).
  2. Chaque photo téléversée est décodée par Pillow, purgée de ses métadonnées EXIF (notamment GPS), orientée et réencodée en WebP.
  3. Lors de la publication (`POST /api/posts`), le serveur calcule la distance en mètres (formule de Haversine) et le dénivelé positif cumulé si la trace comporte des altitudes.
- **Cas d'erreur :**
  - *Publication vide (ni texte, ni photo, ni trace) :* Rejet `422 Unprocessable Entity`.
  - *Publication dans une communauté dont l'utilisateur n'est pas membre :* Rejet `403 Forbidden` (`not_member` : « Rejoignez la communauté pour y publier. »).
  - *Fichier image corrompu ou hors format JPEG/PNG/WebP :* Rejet `422 Unprocessable Entity` (`invalid_image`).

### CU5 — Organisation et participation à une sortie de randonnée
- **Acteur :** Utilisateur connecté
- **Déclencheur :** Création d'une sortie (`12 · Créer/modifier une sortie`, `/sorties/nouvelle`) ou clic sur « Rejoindre la sortie » (`11 · Détail d'une sortie`, `/sorties/:id`).
- **Enchaînement nominal :**
  1. L'organisateur définit le titre, la date/heure de départ, le nombre maximal de participants (2 à 50), la visibilité (`public` ou `invitation`), au moins un point de stop (refuge ou point libre sur la carte) et optionnellement un tracé GPX/carte.
  2. L'organisateur est automatiquement inscrit comme premier participant.
  3. Les autres randonneurs (ou uniquement les amis invités si `visibility = 'invitation'`) peuvent rejoindre ou quitter la sortie tant qu'elle n'est pas complète ni passée.
- **Cas d'erreur :**
  - *Sortie complète :* Rejet `409 Conflict` (`outing_full` : « Cette sortie est complète. »).
  - *Sortie sur invitation sans être invité :* Masquée de la liste et rejet `404` / `403` (`invitation_required`).
  - *Sortie déjà passée :* Rejet `409 Conflict` (`outing_past`).

### CU6 — Modération, hiérarchie des administrateurs et bannissement
- **Acteur :** Administrateur classique (`moderator`) ou Administrateur supérieur (`super_admin`)
- **Déclencheur :** Action dans l'espace de modération (`/moderation`, `/moderation/signalements`, `/moderation/communautes`, `/moderation/comptes`).
- **Enchaînement nominal :**
  1. L'administrateur consulte le tableau de bord (`13`), traite les signalements ouverts (suppression du post signalé ou classement sans suite) et gère les communautés (`14`, `15`).
  2. Sur l'écran `16 · Gestion des comptes`, la suspension d'un utilisateur (`POST /api/moderation/users/{username}/suspend`) passe immédiatement son statut à `suspended`, **révoque toutes ses sessions ouvertes en base** (le déconnectant instantanément) et bloque toute reconnexion future (`403 Forbidden`).
  3. Seul le **Super Administrateur (`super_admin`)** peut promouvoir un utilisateur au rôle `moderator` ou lui retirer ce rôle (`PUT /api/moderation/users/{username}/role`), et seul lui peut suspendre ou supprimer un compte `moderator`.
  4. Toute action de modération est horodatée dans le journal d'audit `moderation_logs`.
- **Cas d'erreur :**
  - *Un administrateur classique (`moderator`) tente de modifier un rôle ou de suspendre/supprimer un autre administrateur :* Rejet `403 Forbidden`.
  - *Un administrateur tente de modifier ou suspendre son propre compte :* Rejet `409 Conflict` (`self_action`).

---

## 4. Règles de Gestion et Traduction dans le Schéma Relationnel

Conformément aux exigences du sujet, les règles de gestion structurelles sont **garanties par le schéma MySQL InnoDB** (clés primaires, clés étrangères, contraintes d'unicité et d'énumération) et complétées par la logique métier :

| Code | Énoncé de la règle de gestion | Garantie dans le schéma SQL (`donnees/schema.sql`) |
| :---: | :--- | :--- |
| **RG1** | Un compte utilisateur possède un pseudo et une adresse email uniques, un rôle parmi `('user', 'moderator', 'super_admin')` et un statut parmi `('pending_email', 'active', 'suspended')`. | Contraintes `UNIQUE (username)`, `UNIQUE (email)` et colonnes `ENUM('user','moderator','super_admin') NOT NULL`, `ENUM('pending_email','active','suspended') NOT NULL` sur `users`. |
| **RG2** | Les mots de passe et les jetons (session, email) ne sont jamais stockés en clair en base de données. | Colonne `users.password_hash VARCHAR(255)` (condensat Argon2id) et colonnes `token_hash VARCHAR(64) UNIQUE` (empreinte SHA-256) dans `sessions` et `email_tokens`. |
| **RG3** | Chaque refuge importé est identifié de manière unique et peut être rattaché à un massif et illustré par plusieurs photos ordonnées. | Contrainte `UNIQUE (external_id)` sur `refuges`, clé étrangère `massif_id -> massifs(id) ON DELETE SET NULL`, et table `refuge_photos` (`refuge_id -> refuges(id) ON DELETE CASCADE`). |
| **RG4** | Une communauté possède un identifiant d'URL (`slug`) unique et peut regrouper zéro, un ou plusieurs refuges (et inversement). | Contrainte `UNIQUE (slug)` sur `communities` et table associative `community_refuges` à clé primaire composite `(community_id, refuge_id)`. |
| **RG5** | Un utilisateur ne peut adhérer qu'une seule fois à une même communauté et n'aimer qu'une seule fois un même post. | Clés primaires composites `(community_id, user_id)` sur `community_members` et `(post_id, user_id)` sur `post_likes`. |
| **RG6** | Il ne peut exister qu'une seule demande d'amitié dans un sens donné entre deux utilisateurs. | Contrainte `UNIQUE (requester_id, addressee_id)` sur la table `friendships` et vérification bidirectionnelle avant insertion. |
| **RG7** | Une sortie de randonnée est organisée par un unique utilisateur, comporte des étapes ordonnées (`outing_stops`) et une liste de participants uniques. | Clé étrangère `organizer_id NOT NULL -> users(id) ON DELETE CASCADE`, clé primaire `(outing_id, position)` sur `outing_stops`, et clé primaire `(outing_id, user_id)` sur `outing_participants`. |
| **RG8** | La suppression d'un compte utilisateur entraîne la suppression automatique de ses sessions, jetons, publications, participations et signalements, tout en conservant le journal de modération. | Clauses `ON DELETE CASCADE` sur `sessions`, `email_tokens`, `posts`, `outings`, `community_members`, `friendships`, et `ON DELETE SET NULL` sur `moderation_logs.actor_id`. |
| **RG9** | L'identité de l'auteur d'une action provient exclusivement de la session serveur résolue via le cookie `refuges_session`. | Aucune route de modification n'accepte `user_id` ou `author_id` dans le corps de la requête ; résolution systématique via `sessions.token_hash`. |

---

## 5. Correspondance Complète avec la Maquette Figma (Écrans 01 à 16)

La maquette Figma ([Refuges – Web App](https://www.figma.com/design/KrPHETSktcZgtTbB9uxVyB/Refuges-%E2%80%93-Web-App?node-id=10-2&t=JR58gAGYpNzeFWH1-1)) définit une charte graphique cohérente (police `Inter`, palette forêt `#1A4D2E` / `#2E6B34`, ambre `#D97706`, surface `#FAF8F5`) intégralement implémentée dans `client/src/styles/tokens.css` et les 20 écrans ci-dessous :

| N° Figma | Nom de l'écran dans Figma | Node ID Figma | Route React (`client`) | Accès requis |
| :---: | :--- | :---: | :--- | :--- |
| **01** | Connexion | `10:6` | `/connexion` (+ `/mot-de-passe-oublie`, `/mot-de-passe/nouveau`) | Visiteur non connecté (`GuestOnly`) |
| **02** | Inscription | `10:34` | `/inscription` (+ `/conditions`) | Visiteur non connecté (`GuestOnly`) |
| **02b** | Compte en attente (confirmation email) | `49:2` | `/inscription/confirmation` & `/confirmation-email` | Inscrit en attente (`RequirePending`) / Public |
| **03** | Carte des refuges | `11:2` | `/carte` | Utilisateur actif (`RequireActive`) |
| **04** | Fiche refuge | `11:117` | `/refuges/:id` | Utilisateur actif (`RequireActive`) |
| **05** | Mon profil | `13:2` | `/profil` | Utilisateur actif (`RequireActive`) |
| **05b** | Mes amis (demandes, amis, suggestions) | `49:40` | `/parametres/amis` | Utilisateur actif (`RequireActive`) |
| **05c** | Confidentialité | `49:148` | `/parametres/confidentialite` | Utilisateur actif (`RequireActive`) |
| **06** | Profil d'un autre utilisateur | `13:110` | `/u/:username` | Utilisateur actif (`RequireActive`) |
| **06b** | Profil d'un autre utilisateur (privé) | `49:256` | `/u/:username` (selon audience) | Utilisateur actif (`RequireActive`) |
| **07** | Communautés | `14:2` | `/communautes` | Utilisateur actif (`RequireActive`) |
| **08** | Page d'une communauté | `14:98` | `/communautes/:slug` | Utilisateur actif (`RequireActive`) |
| **09** | Nouveau post | `14:212` | `/posts/nouveau` | Utilisateur actif (`RequireActive`) |
| **10** | Sorties | `15:2` | `/sorties` | Utilisateur actif (`RequireActive`) |
| **11** | Détail d'une sortie | `15:166` | `/sorties/:id` | Utilisateur actif (`RequireActive`) |
| **12** | Créer / modifier une sortie | `15:266` | `/sorties/nouvelle` & `/sorties/:id/modifier` | Utilisateur actif (`RequireActive`) |
| **13** | Admin · Tableau de bord | `16:2` | `/moderation` & `/moderation/signalements` | Admin classique (`moderator`) ou `super_admin` |
| **14** | Admin · Communautés | `16:118` | `/moderation/communautes` | Admin classique (`moderator`) ou `super_admin` |
| **15** | Admin · Créer / modifier une communauté | `17:2` | `/moderation/communautes/nouvelle` & `/:slug` | Admin classique (`moderator`) ou `super_admin` |
| **16** | Admin · Gestion des comptes | `17:92` | `/moderation/comptes` | Admin classique (`moderator`) ou `super_admin` |
