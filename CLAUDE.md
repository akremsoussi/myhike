# Refuges — contexte projet

Site web (desktop, maquettes en 1440 × 900) pour les randonneurs : carte des refuges de montagne, communautés par massif, sorties organisées entre utilisateurs, amis et confidentialité des posts. Une app mobile est envisagée plus tard, mais ce dépôt concerne le site.

Projet scolaire : **uniquement des outils, bibliothèques et services gratuits.**

Ce fichier distingue deux choses :
- **Maquette** : ce qui est visible dans Figma (vérifié écran par écran).
- **Proposition** : décisions de conception non tranchées, à valider avant de coder.

## Stack

- Environnement de développement : **Ubuntu**, Node LTS (via nvm), Python 3 appelé avec la commande **`python3`** (jamais `python`).
- Frontend : **React + Vite + TypeScript** (dossier `frontend/`).
- Backend : **API FastAPI** (Python 3, dossier `backend/`).
- Base de données : **MySQL** (installé en local ; base `refuges`, utilisateur `refuges`). Les identifiants sont lus depuis un fichier `.env` non versionné, rempli à la main : jamais en dur dans le code, jamais dans ce fichier.
- Langue de l'interface : **français** (dates « Sam. 4 oct. · 7h30 », nombres « 1 240 », « 2 542 m »).
- Police : **Inter** uniquement (400, 500, 600, 700). La charger via un paquet gratuit (par exemple `@fontsource/inter`).
- Design tokens : `frontend/src/styles/tokens.css` (variables CSS) et `frontend/src/styles/tokens.ts` (mêmes valeurs pour le JS). Ne jamais coder une couleur, un rayon ou une taille de police en dur.

## Commandes

Première installation :

```bash
cd backend
cp .env.example .env          # puis remplir DB_PASSWORD (et les autres valeurs si besoin)
python3 -m venv .venv
.venv/bin/pip install -r requirements-dev.txt
.venv/bin/alembic upgrade head   # crée ou met à jour les tables de la base refuges
.venv/bin/python -m app.scripts.import_refuges   # importe les refuges depuis refuges.info (~3 min)
.venv/bin/python -m app.scripts.seed_communities # crée les communautés de départ (en attendant l'écran 15)
cd ../frontend
npm install
```

Base de test (une seule fois ; l'utilisateur `refuges` ne peut pas créer de base) :

```bash
sudo mysql -e "CREATE DATABASE refuges_test CHARACTER SET utf8mb4; GRANT ALL PRIVILEGES ON refuges_test.* TO 'refuges'@'localhost';"
```

Après une modification des modèles : `.venv/bin/alembic revision --autogenerate -m "…"`, relire le fichier généré dans `alembic/versions/`, puis `.venv/bin/alembic upgrade head`.

Lancement (deux terminaux) :

```bash
cd backend && .venv/bin/uvicorn app.main:app --reload     # API sur http://127.0.0.1:8000 (docs : /api/docs)
cd frontend && npm run dev                                 # site sur http://localhost:5173, /api relayé vers l'API
```

Vérifications : `cd backend && .venv/bin/pytest && .venv/bin/ruff check .` ; `cd frontend && npm run build && npm run lint`.
`GET /api/health` renvoie `{"api": "ok", "database": "ok"}`, ou une erreur 503 si MySQL est injoignable (page `/statut`).

Emails en développement : avec `EMAIL_BACKEND=console` (par défaut), le lien de confirmation est écrit dans les logs de l'API (ligne `…/inscription/confirmer?token=…`). Pour une vraie boîte de réception locale, lancer Mailpit et mettre `EMAIL_BACKEND=smtp` dans `.env`.
Les tests backend utilisent la base `refuges_test` (vidée à chaque test) et ne touchent jamais `refuges`.

## Maquettes Figma

Fichier : https://www.figma.com/design/KrPHETSktcZgtTbB9uxVyB — une seule page, « Web (desktop) », en trois sections.
Avec le serveur MCP Figma : `get_design_context` ou `get_screenshot` avec le `fileKey` `KrPHETSktcZgtTbB9uxVyB` et le node ID ci-dessous. Le fichier n'a **ni composants ni variables** Figma : les composants React sont à créer à partir des écrans.

Les routes sont des **propositions** (rien dans la maquette ne les fixe).

| Écran | Node ID | Route proposée | Accès |
|---|---|---|---|
| 01 · Connexion | 10:6 | `/connexion` | public |
| 02 · Inscription | 10:34 | `/inscription` | public |
| 02b · Compte en attente de validation | 49:2 | `/inscription/confirmation` | compte non confirmé |
| (pas d'écran) Lien reçu par email | — | `/inscription/confirmer?token=…` | public |
| 03 · Carte des refuges | 11:2 | `/carte` | connecté |
| 04 · Fiche refuge | 11:117 | `/refuges/:id` | connecté |
| 05 · Mon profil | 13:2 | `/profil` | connecté |
| 05b · Mes amis | 49:40 | `/profil/amis` | connecté |
| 05c · Paramètres de confidentialité | 49:148 | `/parametres/confidentialite` | connecté |
| 06 · Profil d'un utilisateur (non ami) | 13:110 | `/u/:username` | connecté |
| 06b · Profil d'un utilisateur (ami) | 49:256 | `/u/:username` (même page, état ami) | connecté |
| 07 · Communautés | 14:2 | `/communautes` | connecté |
| 08 · Page communauté | 14:98 | `/communautes/:slug` | connecté |
| 09 · Nouveau post | 14:212 | `/posts/nouveau` | connecté |
| 10 · Sorties | 15:2 | `/sorties` | connecté |
| 11 · Détail sortie | 15:166 | `/sorties/:id` | connecté |
| 12 · Créer / modifier une sortie | 15:266 | `/sorties/nouvelle`, `/sorties/:id/modifier` | connecté |
| 13 · Admin – Tableau de bord | 16:2 | `/moderation` | modérateur |
| 14 · Admin – Gestion des communautés | 16:118 | `/moderation/communautes` | modérateur |
| 15 · Admin – Créer / modifier une communauté | 17:2 | `/moderation/communautes/:slug` | modérateur |
| 16 · Admin – Gestion des comptes | 17:92 | `/moderation/comptes` | modérateur |

06 et 06b sont **un seul composant** dont l'affichage dépend de la relation d'amitié.

### Contenu de chaque écran (maquette)

- **01 Connexion** : panneau vert à gauche (800 px) avec logo, accroche et chiffres ; formulaire à droite (420 px) : email, mot de passe, « Mot de passe oublié ? », « Se connecter », lien vers l'inscription.
- **02 Inscription** : même mise en page ; nom d'utilisateur, email, mot de passe (« 8 caractères min. ») et confirmation, case « J'accepte les conditions d'utilisation », « S'inscrire ».
- **02b Compte en attente** : même mise en page ; statut « En attente de confirmation », adresse email en gras, trois étapes (compte créé, email à confirmer, accès), « Renvoyer l'email » avec délai (0:45), lien expirant au bout de 24 h, « Modifier l'email », « Retour à la connexion ».
- **03 Carte** : liste de refuges à gauche (420 px) avec recherche et filtres Tous / Gardés / Non gardés / Avec sortie ; carte à droite avec étiquettes de refuges, popup (« Voir la fiche », « Créer une sortie ») et zoom.
- **04 Fiche refuge** : fil d'Ariane, photo, description, accès, colonne latérale (380 px) : altitude, places, massif, gardiennage, téléphone, « Créer une sortie ici », « Voir les posts liés », sorties prévues.
- **05 Mon profil** : en-tête (avatar, nom, @pseudo, bio, statistiques Sorties / Posts / Communautés / Amis, « Modifier le profil », « Confidentialité », « Se déconnecter ») ; à gauche : mes sorties à venir, carte « Mes amis » (demandes en attente, lien vers 05b) ; à droite (440 px) : mes communautés, mes publications avec badge Public / Amis, « + Publier ».
- **05b Mes amis** : recherche, onglets Mes amis / Demandes reçues / Demandes envoyées, demandes reçues (Accepter / Refuser), grille des amis ; à droite (440 px) : demandes envoyées (Annuler), suggestions (« + Ajouter »).
- **05c Confidentialité** : menu des paramètres (260 px : Profil, Confidentialité, Compte & sécurité, Notifications) et panneau des réglages (voir « Règles métier »), « Annuler » / « Enregistrer ».
- **06 / 06b Profil d'un autre** : même en-tête que 05 ; non ami : « + Ajouter en ami » et « Inviter à une sortie », publications publiques et bloc « 9 publications réservées aux amis » ; ami : « Amis ✓ », « Ami depuis mars 2026 », tous les posts avec badge « Amis » sur les posts privés. À droite (440 px) : communautés en commun, publications.
- **07 Communautés** : recherche, filtres Toutes / Mes communautés / Alpes / Pyrénées / Préalpes, grille de cartes (membres, posts, « Rejoindre » ou « Inscrit ✓ »).
- **08 Page communauté** : bannière verte (nom, membres, posts, région, « Inscrit ✓ ») ; fil de posts (816 px) avec zone « Partager une photo ou un chemin… », auteur, date, visibilité (Public / Amis), texte, photo ou chemin (distance, dénivelé), j'aime, « Commenter (5) », « Voir le profil », menu « ⋯ » ; à droite (360 px) : à propos, membres, refuges de la communauté, « Quitter la communauté ».
- **09 Nouveau post** (formulaire de 1040 px) : « Publier sur » Mon profil / Une communauté (+ choix de la communauté), description, photos, chemin optionnel (tracer sur la carte ou importer un GPX), visibilité Public / Amis uniquement, « Annuler » / « Publier ».
- **10 Sorties** : « + Créer une sortie », onglets À venir / Mes sorties / Où je participe / Passées, grille de cartes (statut Ouverte / Complète, date, organisateur, nombre de points de stop, participants).
- **11 Détail sortie** : carte avec points de stop numérotés ; à droite (400 px) : date, organisateur, distance et dénivelé, visibilité, points de stop, participants (5 / 8), « Rejoindre la sortie », « Partager ».
- **12 Créer / modifier une sortie** : titre, date, heure, places max, visibilité Publique / Sur invitation, points de stop réordonnables (refuge ou point libre), carte avec outils de tracé.
- **13 Tableau de bord** : statistiques (utilisateurs, communautés, sorties actives, comptes signalés), activité récente, signalements à traiter (« Examiner »).
- **14 Gestion des communautés** : tableau (communauté, région, membres, posts, date de création, Modifier / Supprimer), filtres par région.
- **15 Créer / modifier une communauté** : nom, description, massif / région, mode d'inscription (« Ouverte à tous »), refuges rattachés, bannière, icône, zone de danger (suppression).
- **16 Gestion des comptes** : filtres Tous / Admins / Signalés / Suspendus, tableau (utilisateur, rôle, date d'inscription), panneau de détail (voir le profil public, promouvoir, suspendre, supprimer), « Exporter (CSV) ».

### Écrans référencés mais non dessinés

À concevoir avant de coder ces parcours : mot de passe oublié (lien de 01), conditions d'utilisation (02), modifier le profil (05), sections Profil / Compte & sécurité / Notifications des paramètres (05c), contenu des onglets « Demandes reçues » et « Demandes envoyées » (05b), états « demande envoyée » et « demande reçue » du profil d'un autre (06), commentaires d'un post (08), liste complète des membres (« Tout voir », 08), posts liés à un refuge (04), résultats de la recherche globale (barre de navigation), page Signalements (menu de modération).

## Rôles

Deux rôles : **utilisateur** et **modérateur**.

La maquette mélange encore les termes : « Admin », « ADMIN », « Administratrice », « Promouvoir administrateur », filtre « Admins », mais aussi « Lucas Durand promu modérateur ». **Dans le code et l'interface, utiliser « modérateur » / « Modération ».**

- **Utilisateur** : carte et fiches refuges, rejoindre et quitter des communautés, publier (photo et/ou chemin) sur son profil ou dans une communauté, consulter les profils, gérer ses amis et sa confidentialité, créer et rejoindre des sorties.
- **Modérateur** : en plus, créer / modifier / supprimer des communautés, gérer les comptes (promouvoir, suspendre, supprimer), traiter les signalements.

### Modération et signalements (implémenté)

- Signaler : menu « ⋯ » d'un post des autres, ou « Signaler ce profil » (fenêtre `ReportDialog`, pas dessinée dans la maquette). Motifs : Propos insultants, Spam, Faux profil, Autre. On ne signale que ce qu'on peut lire ; un doublon encore ouvert n'est pas recréé.
- Page `/moderation/signalements` (pas dessinée) : liste des signalements ouverts, « Classer », « Supprimer le post », « Examiner le compte » (écran 16 avec `?compte=pseudo`).
- Journal `moderation_log` : alimente l'« Activité récente » (création / modification / suppression de communauté, post supprimé par un modérateur, rôle, suspension, suppression, signalements classés, export CSV).
- Un modérateur ne peut ni se suspendre, ni changer son propre rôle, ni supprimer son compte (409 `self_action`). Suspendre révoque aussi les sessions.
- L'identifiant (slug) d'une communauté est tiré du nom à la création et ne change plus. « Inscription » n'a qu'une valeur, « Ouverte à tous » ; bannière et icône ne sont pas encore enregistrables (pas de stockage d'images).

## Règles métier

### Comptes et validation

- **Maquette** : après l'inscription, l'écran 02b demande de cliquer sur un lien reçu par email ; lien valable 24 h ; renvoi limité dans le temps ; adresse modifiable.
- **Implémenté** : statuts de compte `pending_email` → `active`, et `suspended` (le filtre « Suspendus » existe dans 16).
  - L'inscription connecte l'utilisateur en `pending_email`. Il n'a accès qu'à 02b : l'API répond 403 `account_pending` via la dépendance `ActiveUser`, et le front redirige avec `RequireActive`.
  - Lien de confirmation : jeton aléatoire dont seule l'empreinte SHA-256 est en base ; valable 24 h ; un nouvel envoi ou un changement d'adresse invalide les liens précédents ; cliquer deux fois sur le même lien n'est pas une erreur.
  - Renvoi limité à un toutes les 60 s (429 `resend_too_soon` avec `retry_after`).
  - Un compte `suspended` ne peut plus se connecter, et ses sessions en cours sont refusées (403). Il reste suspendu même s'il confirme son adresse.
  - Sessions : cookie httpOnly `refuges_session` (SameSite=Lax), jeton en base (table `sessions`), révocable.
- **À trancher** : si la validation doit aussi passer par un modérateur, ajouter un statut `pending_review` et un filtre « En attente » dans 16.

### Amitié

- **Maquette** : demandes reçues (Accepter / Refuser), demandes envoyées (Annuler), liste d'amis, suggestions issues des communautés avec amis en commun, bouton « + Ajouter en ami » / « Amis ✓ » sur un profil.
- **Implémenté** (`backend/app/services/friends.py`) : relation symétrique ; demande `pending` → `accepted` ou `declined` ; retrait possible par l'un ou l'autre. Deux demandes croisées deviennent une amitié. Un refus est silencieux : le demandeur voit toujours « Demande envoyée » et ne peut pas renvoyer. Suggestions : membres de mes communautés sans lien avec moi, classés par amis en commun.

### Posts et visibilité

- **Maquette** : un post est publié soit sur le profil seul, soit dans une communauté, et dans ce cas il apparaît **aussi** sur le profil de l'auteur. Visibilité `Public` (tous les membres) ou `Amis uniquement` (vos amis seulement, y compris dans la communauté).
- Règle de lecture : un utilisateur voit un post si sa visibilité est publique, **ou** s'il en est l'auteur, **ou** s'il est ami avec l'auteur. Elle s'applique partout : profil, fil de communauté, posts liés à un refuge.
- **Le filtrage se fait dans l'API FastAPI, jamais seulement dans le front.** Le front ne reçoit jamais le contenu d'un post qu'il n'a pas le droit de voir.
- Sur le profil d'un non-ami, l'API renvoie les posts publics et un **compteur** des posts réservés aux amis (bloc « 9 publications réservées aux amis »).
- **Implémenté** : `post_visible_to(viewer)` (`backend/app/services/visibility.py`) est ajouté à toute requête qui renvoie des posts ; seule une amitié `accepted` compte, dans les deux sens. Un post invisible répond 404 (j'aime, suppression). Publier dans une communauté exige d'en être membre (403 `not_member`). L'auteur ou un modérateur peut supprimer un post.
- **Pas encore implémenté** : photos, chemins et commentaires des posts (zones « Bientôt » dans 09).
- **Implémenté** (proposition retenue) : un modérateur voit un post « Amis uniquement » **seulement depuis la modération**, quand il est signalé ; les fils et profils lui appliquent la règle normale.

### Paramètres de confidentialité (écran 05c, maquette)

- Visibilité par défaut des nouveaux posts : Public | Amis uniquement. Modifiable au moment de publier ; ne change pas les anciens posts.
- Qui peut voir ma liste d'amis (valeur affichée : « Mes amis »).
- Qui peut voir mes sorties à venir (valeur affichée : « Tout le monde »).
- Qui peut m'envoyer une demande d'ami (valeur affichée : « Tout le monde » ; l'aide propose de limiter aux membres de mes communautés).
- Apparaître dans les suggestions d'amis : oui | non.
- **Implémenté** : options Tout le monde / Mes amis / Moi uniquement, et pour les demandes Tout le monde / Membres de mes communautés (colonnes de `users`, `GET/PUT /api/me/privacy`). L'API applique la liste d'amis (compteur `null`), les demandes (403 `requests_restricted`), les suggestions et la visibilité par défaut (écran 09). « Qui peut voir mes sorties » est enregistré mais ne s'appliquera qu'avec les sorties.

### Données des refuges (implémenté)

- Source : **API publique refuges.info**, licence **CC BY-SA 2.0** : l'attribution est obligatoire (elle figure dans l'attribution de la carte, et devra figurer sur la fiche refuge).
- Import dans MySQL par `app.scripts.import_refuges` (relançable : mise à jour par `external_id`), jamais d'appel à refuges.info depuis le navigateur ni à chaque requête. Types importés : cabane non gardée (7), gîte d'étape (9), refuge gardé (10) ; les bâtiments « détruits » sont ignorés. Tables `massifs` et `refuges`.
- « Gardé » = refuge gardé ou gîte d'étape ; « Fermé » quand l'état refuges.info commence par « Ferm ».
- Pas encore de photos (zone réservée en `--color-map-bg`). Le téléphone (`phone`) est le premier numéro trouvé dans le texte brut « Propriétaires » (`owner_info`).

### Sorties

- **Maquette** : titre, date, heure, places max, chemin, points de stop ordonnés (refuge ou point libre), participants, organisateur. Visibilité : Publique ou Sur invitation. Statut : Ouverte ou Complète.
- **Implémenté** (`backend/app/services/outings.py`) :
  - L'organisateur participe d'office et ne peut pas quitter sa sortie ; lui seul la modifie, invite et la supprime (un modérateur peut aussi supprimer).
  - « Complète » = participants ≥ places. On ne rejoint ni une sortie complète ni une sortie passée ; les places ne peuvent pas descendre sous le nombre de participants.
  - « Sur invitation » : visible (liste, détail, filtre « Avec sortie » de la carte) seulement par l'organisateur, les participants et les invités ; seuls les invités la rejoignent. Une sortie invisible répond 404.
  - Heure envoyée par le navigateur avec son fuseau, stockée en UTC.
  - Distance : longueur du chemin tracé, sinon à vol d'oiseau entre les points. Dénivelé : **approximation**, somme des montées entre refuges d'altitude connue (pas de modèle de terrain gratuit intégré).
  - « Qui peut voir mes sorties à venir » (05c) s'applique à la section du profil et au compteur « Sorties », pas à l'onglet Sorties.

## Conventions UI (maquette)

- **Barre de navigation** des pages utilisateur (69 px) : logo « Refuges » à gauche, onglets Carte / Communautés / Sorties au centre (onglet actif sur fond `--color-primary-soft`), à droite recherche (260 px, sans bordure, fond `--color-bg`) et pastille avatar + « Prénom N. » vers `/profil`. La pastille passe sur fond `--color-primary-soft` (texte vert) dans le profil et les paramètres (05, 05b, 05c). Sur 03 et 04, la pastille n'a que l'avatar (barre de 67 px) : à harmoniser, prendre la version avec nom.
- **Contours intérieurs** : Figma trace les contours à l'intérieur. Pour les éléments dimensionnés par leur padding (chips, champs, listes, choix segmentés, bouton secondaire), le contour est un `box-shadow: inset` pour garder la hauteur de la maquette (un champ fait 42 px, comme un bouton). Les cartes gardent une vraie `border`.
- **Pages utilisateur** : contenu de 1200 px centré (marges 28 × 120 px) ; deux colonnes séparées de 24 px. La colonne latérale varie selon l'écran : 440 px (05, 05b, 06), 400 px (11), 380 px (04), 360 px (08). Le formulaire de 09 est plus étroit (1040 px).
- **Pages d'authentification** (01, 02, 02b) : panneau vert de 800 px + formulaire de 420 px centré dans les 640 px restants.
- **Modération** (13 à 16) : barre latérale de 260 px sur `--color-sidebar-bg` (logo sur carré blanc, badge « ADMIN » renommé « Modération », élément actif sur `--color-primary`, compteur de signalements rouge, en bas « Voir le site public » et le compte connecté) ; contenu avec marges 32 × 40 px. Les pastilles d'icône carrées de la maquette sont remplacées par des icônes lucide.
- **Boutons** : primaire (fond vert, texte blanc) ; secondaire (fond blanc, contour vert 1,5 px) ; danger (fond `--color-danger-soft`, texte `--color-danger`). Taille normale 12 × 20 px en 15 px, petite 8 × 14 px en 13 px.
- **Statuts** : « Ouverte » (vert clair), « Complète » et « Chemin » (orange `--color-accent`), « Signalé » (danger), « Non gardé » / « Suspendu » (neutre), « En attente » (`--color-pending`).
- **Ombres** : uniquement sur les éléments posés sur la carte ; les cartes de contenu ont une bordure de 1 px, sans ombre.
- **Composants à factoriser** : `Navbar`, `ModerationSidebar`, `Button`, `Chip`, `StatusBadge`, `VisibilityBadge` (globe = Public, cadenas = Amis), `Avatar` (initiales), `Card`, `Input`, `Select`, `SegmentedControl`, `Toggle`, `Tabs`, `PostCard`, `OutingCard`, `CommunityCard`, `UserRow`, `StatBlock`.
- **Composants de base** : dans `frontend/src/components/` (un fichier `.tsx` et un `.module.css` par composant, exportés par `index.ts`). Catalogue visuel sur la route `/demo` : y ajouter chaque nouveau composant.
- **Icônes** : la maquette utilise des caractères (⌕, ▾, ›, ✓, ♡, ⋯) et quelques SVG (cadenas, globe, enveloppe). Dans le code, utiliser une bibliothèque gratuite (proposition : lucide-react).
- Les zones « Photo », « Chemin » et la carte sont des **placeholders** (couleurs `--color-map-*` et `--color-placeholder-path`). Carte réelle : **Leaflet + react-leaflet**, tuiles **OpenStreetMap** (attribution obligatoire), étiquettes regroupées avec **leaflet.markercluster** ; la page carte est chargée à la demande (`lazy`) pour ne pas alourdir le reste du site.
