# Dossier d'Analyse : Application Refuges (3 Tiers)

**Binôme :** Akrem SOUSSI & Rémi CORTIAL  
**Établissement :** Aix-Marseille Université — École d'ingénieurs  
**Année universitaire :** 2025 – 2026  
**Module :** DEV 1 — Application Trois-Tiers  
**Prototype Figma :** [Lien vers la maquette Figma](https://www.figma.com/design/KrPHETSktcZgtTbB9uxVyB/Refuges-%E2%80%93-Web-App?node-id=10-2)

---

## 1. Contexte et Objectif

Le projet **Refuges** est une application web répartie en trois couches étanches (Présentation, Métier, Données) dédiée aux passionnés de montagne et de randonnée. Elle permet la cartographie, la recherche et la consultation des refuges alpins et pyrénéens, la planification et le partage de sorties de randonnée avec profils altimétriques et tracés GPX, ainsi que l'animation de communautés par massif montagneux.

L'objectif de cette analyse est de définir sans ambiguïté les acteurs du système, leurs cas d'utilisation nominaux et d'erreur, ainsi que les règles de gestion garanties par le schéma relationnel de la base de données avant tout choix d'implémentation.

---

## 2. Recensement des Acteurs et Rôles

L'application distingue quatre catégories d'acteurs :

| Acteur / Rôle | Niveau d'accès | Description des prérogatives |
| :--- | :---: | :--- |
| **Visiteur (Non connecté)** | Public | Consultation de la carte interactive, recherche des refuges, consultation des massifs et des sorties publiques. Demande d'inscription. |
| **Randonneur (Utilisateur)** | Authentifié | Consultation personnalisée, planification et publication de sorties de randonnée avec tracé GPX, gestion des amis et de la visibilité de ses activités, signalement de contenus inappropriés. |
| **Modérateur / Administrateur** | Privilégié | Traitement des signalements utilisateurs, masquage ou suppression de contenus illicites, suspension temporaire de comptes randonneurs non conformes. |
| **Super Administrateur** | Absolu | Responsable suprême du site. Attribution et révocation des rôles d'administrateurs, suspension/suppression définitive de tout compte, validation des accès réservés. |

---

## 3. Cas d'Usage Principaux

Chaque cas d'usage est décrit selon son déclencheur, son déroulement nominal et ses cas d'erreur.

### CU1 : Création de compte et authentification
- **Acteur :** Visiteur / Randonneur
- **Déclencheur :** Clic sur « Inscription » ou « Connexion ».
- **Enchaînement nominal :**
  1. Le visiteur fournit son identifiant (email, nom d'utilisateur) et un mot de passe robuste.
  2. Le serveur métier calcule le condensat lent et salé (Argon2id) et crée le compte au statut initial `active` (ou `pending` avec confirmation par email).
  3. L'utilisateur renseigne ses identifiants sur la page de connexion.
  4. Le serveur vérifie le mot de passe, génère un jeton de session sécurisé (cookie HTTP-only / token de session).
  5. L'utilisateur est redirigé vers sa page d'accueil personnalisée.
- **Cas d'erreur :**
  - *Identifiant inconnu ou mot de passe erroné :* Le serveur renvoie un code `401 Unauthorized` avec le message générique « Identifiants incorrects » (pas de fuite d'information sur l'existence du compte).
  - *Compte suspendu :* Si le compte fait l'objet d'une suspension par un administrateur (`suspended_at IS NOT NULL`), l'accès est refusé avec un code `403 Forbidden`.

### CU2 : Consultation cartographique et recherche de refuges
- **Acteur :** Visiteur / Randonneur
- **Déclencheur :** Accès à la carte interactive ou utilisation du filtre de recherche (massif, type d'hébergement, altitude, capacité).
- **Enchaînement nominal :**
  1. Le client requiert les refuges visibles dans l'emprise géographique courante (`GET /api/refuges/?bounds=...`).
  2. Le serveur métier extrait les données du SGBD relationnel et transmet la liste au format GeoJSON/JSON.
  3. La couche présentation affiche les marqueurs dynamiques, les fonds de carte (OSM / OpenTopoMap / Plan IGN) et la fiche synthétique au clic sur un refuge.
- **Cas d'erreur :**
  - *Secteur sans refuge (liste vide) :* Message explicite « Aucun refuge répertorié dans ce secteur ou avec ces filtres ».
  - *Refuge inexistant :* Requête sur un identifiant absent (`GET /api/refuges/99999`) -> code `404 Not Found`.

### CU3 : Publication d'une sortie avec trace GPX et profil altimétrique
- **Acteur :** Randonneur authentifié
- **Déclencheur :** Clic sur « Nouvelle sortie ».
- **Enchaînement nominal :**
  1. L'utilisateur saisit le titre, la date, la description et téléverse un fichier GPX.
  2. Le serveur métier valide l'intégrité du fichier XML/GPX, extrait les coordonnées de la trace, calcule la distance cumulée et le dénivelé positif/négatif.
  3. La sortie est enregistrée en base et rattachée à l'utilisateur de la session courante.
  4. L'application affiche la carte du parcours et le graphique de profil altimétrique.
- **Cas d'erreur :**
  - *Fichier GPX corrompu ou invalide :* Rejet avec code `422 Unprocessable Entity` et message « Le fichier GPX est invalide ou ne contient aucune coordonnée ».
  - *Utilisateur non connecté :* Code `401 Unauthorized`.

### CU4 : Gestion des droits et modération des comptes
- **Acteur :** Administrateur / Super Administrateur
- **Déclencheur :** Consultation du panneau d'administration des comptes.
- **Enchaînement nominal :**
  1. L'administrateur recherche un utilisateur signalé et consulte son historique.
  2. Il clique sur « Suspendre le compte ».
  3. Le serveur métier vérifie la hiérarchie des rôles : un administrateur ne peut suspendre qu'un utilisateur classique (`role = 'user'`). Seul le Super Admin peut intervenir sur un autre administrateur.
  4. Le statut de suspension est consigné dans `moderation_log` et le compte est invalidé.
- **Cas d'erreur :**
  - *Tentative d'un administrateur de suspendre un pair ou le Super Admin :* Refus strict avec code `403 Forbidden` (« Vous ne disposez pas des privilèges nécessaires pour agir sur ce compte »).

---

## 4. Règles de Gestion (RG)

Conformément aux exigences du sujet (page 4), les règles de gestion déterminent les cardinalités et sont **strictement garanties par le schéma relationnel**, et non par le seul code client ou applicatif :

| Règle | Énoncé contractuel | Traduction dans le schéma SQL |
| :--- | :--- | :--- |
| **RG1** | Tout refuge est obligatoirement rattaché à un massif identifié. | Clé étrangère `massif_id` NOT NULL dans la table `refuges`, référençant `massifs(id)`. |
| **RG2** | Une sortie de randonnée appartient à un et un seul randonneur auteur. | Clé étrangère `author_id` NOT NULL dans `outings`, référençant `users(id)`. |
| **RG3** | Un utilisateur peut participer à plusieurs sorties, et une sortie réunit plusieurs participants. | Table d'association `outing_participants` avec clé primaire composite `(outing_id, user_id)`. |
| **RG4** | Un compte correspond à une personne physique unique. | Contraintes d'unicité `UNIQUE` sur les colonnes `email` et `username` de la table `users`. |
| **RG5** | Un compte non validé ou suspendu ne peut pas ouvrir de session. | Colonnes `status` ('active', 'pending') et `suspended_at` contrôlées lors de l'authentification. |
| **RG6** | Les mots de passe ne sont jamais stockés en clair ni avec une fonction rapide. | Condensat lent et salé (Argon2id avec coût mémoire et temps) stocké dans `password_hash VARCHAR(255)`. |
| **RG7** | L'identité de l'utilisateur provient exclusivement de la session serveur. | Aucune clé d'identité transmise en paramètre d'URL. Résolution par jeton cryptographique dans la table `sessions`. |
| **RG8** | L'intégrité référentielle est maintenue en cas de suppression de compte. | Contraintes `ON DELETE CASCADE` ou `ON DELETE SET NULL` définies sur les clés étrangères. |

---

## 5. Synthèse des Écrans et Prototype Figma

Le prototype graphique a été conçu sur Figma : [Accès au Prototype Figma](https://www.figma.com/design/KrPHETSktcZgtTbB9uxVyB/Refuges-%E2%80%93-Web-App?node-id=10-2).

Il matérialise l'ensemble des parcours attendus :
1. **Écran E1 — Accueil et Carte interactive :** Visualisation des massifs et des refuges, recherche multicritères, sélection des couches IGN / OpenTopoMap / OSM.
2. **Écran E2 — Connexion / Inscription :** Formulaire d'authentification avec gestion des erreurs explicites.
3. **Écran E3 — Fiche détaillée d'un refuge :** Caractéristiques complètes, coordonnées, altitude, météo, photos et commentaires.
4. **Écran E4 — Planification et tracé de sortie :** Formulaire de sortie, import GPX, calcul du profil altimétrique.
5. **Écran E5 — Profil et Communautés :** Gestion des amis, de la visibilité des posts et participation aux massifs.
6. **Écran E6 — Panneau de modération et d'administration :** Gestion des comptes, suspension d'utilisateurs et suivi des signalements.
