# Refuges — Application Web Trois-Tiers

**Projet :** Refuges  
**Binôme :** Akrem SOUSSI et Rémi CORTIAL

**Rendu :** [index de toutes les parties](docs/RENDU.md), [rapport de charge principal](docs/rapport-charge.md) et [mesures de Rémi intégrées](docs/synthese-mesures-remi.md).

**Établissement :** Aix-Marseille Université — École d'ingénieurs (Polytech Marseille)
**Année universitaire :** 2025 – 2026
**Module :** DEV 1 — Application Trois-Tiers (Enseignant : Mohamed Quafafou)
**Prototype Figma :** [Consulter la maquette Figma en ligne](https://www.figma.com/design/KrPHETSktcZgtTbB9uxVyB/Refuges-%E2%80%93-Web-App?node-id=10-2&t=JR58gAGYpNzeFWH1-1)

---

## 1. Présentation du Projet

**Refuges** est une application web communautaire conçue selon une **architecture 3 tiers stricte** (Présentation, Métier, Données), dédiée aux randonneurs et alpinistes :
- **Cartographie interactive des refuges :** Exploration de **4 652 refuges et cabanes réels** (importés depuis `refuges.info`) par emprise géographique, filtres (*Gardés*, *Non gardés*, *Avec sortie*) et photographies importées par les scripts du projet.
- **Communautés par massif et publications :** Partage de récits, de photos (converties en WebP et purgées de leurs métadonnées EXIF/GPS) et de traces GPX avec calcul automatique de la distance et du dénivelé positif.
- **Organisation de sorties en montagne :** Planification de sorties publiques ou sur invitation jalonnées d'étapes (refuges ou points libres) avec tracé sur la carte.
- **Réseau social et confidentialité :** Demandes d'amis, suggestions par communautés communes, contrôle fin de l'audience du profil et recherche transversale.
- **Modération et administration hiérarchisée :** Quatre niveaux d'acteurs clairement distingués (*Visiteur non connecté*, *Utilisateur connecté*, *Administrateur classique*, *Administrateur supérieur*).

---

## 2. Organisation du Dépôt

```text
myhike/
├── start.sh                  # Script de lancement complet en local en UNE SEULE commande
├── client/                   # Couche Présentation : React 19, TypeScript, Leaflet, Vite
├── metier/                   # Couche Métier : Python 3.12, FastAPI, SQLAlchemy 2, Argon2id
├── donnees/                  # Couche Données : schema.sql et peuplement.sql (MySQL 8)
├── deploiement/              # Configuration du déploiement 3 VMs (Netplan, Nginx, Systemd)
│   ├── reseau/               # Configurations statiques Netplan des 3 machines
│   ├── donnees/              # mysqld.cnf, privileges.sql, schema.sql et data.sql
│   ├── metier/               # Service systemd et .env externalisé
│   ├── proxy/                # Configuration Nginx (reverse proxy /api/ et SPA)
│   └── PROCEDURE.md          # Procédure complète chronologique pas à pas
├── docker/                   # Configuration Compose et procédure Docker
├── charge/                   # Plans JMeter, scripts et mesures
├── docs/                     # Documentation et livrables d'évaluation
│   ├── analyse.md            # Dossier d'analyse (Étape 1 : acteurs, cas d'usage, RG, Figma)
│   ├── requetes.md           # Exemples de requêtes cURL de la couche métier (Étape 4)
│   ├── tests.md              # Cahier de recette et tableau de tests (Étape 6)
│   ├── mesures.md            # Mesures de référence de l'étape 10 et matrice réseau
│   └── captures/             # Captures d'écran des tests réseau et des snapshots
├── ova/                      # Emplacement des archives des 3 machines virtuelles (.ova)
└── LISEZMOI.md               # Le présent fichier de présentation et démarrage rapide
```

---

## 3. Types d'Utilisateurs et Comptes de Démonstration

Tous les comptes ci-dessous sont préconfigurés et vérifiés dans la base de données avec le mot de passe commun **`refuges123`** :

| Type d'utilisateur | Rôle (`users.role`) | Pseudo | Adresse email de connexion | Mot de passe | Interfaces et droits associés |
| :--- | :---: | :---: | :--- | :---: | :--- |
| **Visiteur sans connexion** | — | — | *(Non connecté)* | — | Accès uniquement aux écrans publics (`/connexion`, `/inscription`, `/mot-de-passe-oublie`, `/conditions`, `/statut`). Redirigé vers `/connexion` pour toute autre page. |
| **Utilisateur classique 1** | `user` | `@randonneur` | `randonneur@refuges.local` | `refuges123` | Accès complet aux écrans utilisateur `03` à `12` (Carte, Refuges, Communautés, Posts, Sorties, Amis, Profil). Aucun accès à `/moderation`. |
| **Utilisateur classique 2** | `user` | `@alpiniste` | `alpiniste@refuges.local` | `refuges123` | Deuxième compte utilisateur classique permettant de tester les interactions croisées (demandes d'amis, invitations à une sortie, signalements, visibilité *Amis uniquement*). |
| **Administrateur classique** | `moderator` | `@moderateur` | `moderateur@refuges.local` | `refuges123` | Accès à toutes les fonctionnalités utilisateur + onglet **« Modération »** (`/moderation` : Tableau de bord, Signalements, Communautés, Comptes). Peut suspendre/réactiver/supprimer un compte `user`, mais **ne peut ni modifier les rôles ni sanctionner un autre administrateur**. |
| **Administrateur supérieur** | `super_admin` | `@remi` | `remi@gmail.com` | `refuges123` | **Droits absolus :** toutes les fonctionnalités de modération + **seul compte habilité à promouvoir/rétrograder des modérateurs** et à suspendre ou supprimer un compte `moderator`. |

---

## 4. Lancement en Local en Une Seule Commande

Depuis la racine du dépôt, exécutez simplement :

```bash
./start.sh
```

Ce script unique :
1. Démarre automatiquement le serveur **MySQL** local s'il n'est pas déjà actif.
2. Vérifie et applique les migrations **Alembic** (`alembic upgrade head`).
3. Lance l'API **FastAPI** sur `http://127.0.0.1:8000` (avec `EMAIL_BACKEND=console`).
4. Lance le client **React / Vite** sur **`http://localhost:5173`**.
5. Arrête proprement tous les processus enfants lorsque vous appuyez sur `Ctrl+C`.

> **Confirmation d'email et mot de passe oublié en local :**
> Par défaut en développement (`EMAIL_BACKEND=console`), lors d'une nouvelle inscription (`/inscription`) ou d'une demande de réinitialisation de mot de passe (`/mot-de-passe-oublie`), l'email contenant le lien cliquable (`/confirmation-email?token=...` ou `/mot-de-passe/nouveau?token=...`) est affiché directement dans le terminal où tourne `./start.sh`. Pour utiliser un serveur SMTP réel, renseignez `EMAIL_BACKEND=smtp` et `SMTP_HOST` dans `metier/.env`.

### Installation initiale (si l'environnement n'est pas encore initialisé)
```bash
# 1. Base de données MySQL
mysql -u root -p -e "CREATE DATABASE IF NOT EXISTS refuges CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
mysql -u root -p -e "CREATE USER IF NOT EXISTS 'refuges'@'127.0.0.1' IDENTIFIED BY 'refuges';"
mysql -u root -p -e "GRANT ALL PRIVILEGES ON refuges.* TO 'refuges'@'127.0.0.1'; FLUSH PRIVILEGES;"
mysql -u refuges -prefuges -h 127.0.0.1 refuges < donnees/schema.sql
mysql -u refuges -prefuges -h 127.0.0.1 refuges < donnees/peuplement.sql

# 2. Dépendances Backend & Frontend
cd metier && python3 -m venv .venv && .venv/bin/pip install -r requirements.txt && cd ..
cd client && npm install && cd ..

# 3. Démarrage en une commande
./start.sh
```

---

## 5. Déploiement Réparti sur 3 Machines Virtuelles (Partie 2)

Pour le déploiement sur trois machines virtuelles isolées avec réseau interne (`intnet-app`, `10.10.10.0/24`), consultez la procédure détaillée :
- **[`deploiement/PROCEDURE.md`](deploiement/PROCEDURE.md)** — Guide chronologique d'installation des 3 VMs
- **[`docs/mesures.md`](docs/mesures.md)** — Mesures de référence (Étape 10) et matrice de joignabilité
- **[`docs/analyse.md`](docs/analyse.md)** — Dossier d'analyse complet et correspondance Figma
- **[`docs/requetes.md`](docs/requetes.md)** — Exemples de requêtes HTTP (`curl`)
- **[`docs/tests.md`](docs/tests.md)** — Cahier de recette et résultats des tests

---

## 6. Déploiement Docker (Partie 3)

- [Procédure complète et démarrage en une commande](docker/PROCEDURE.md).
- [Comparaison VM / Docker au format Markdown](docs/comparaison.md).
- [Preuves de validation, d'isolation, de persistance et mesures brutes](docs/preuves-docker/2026-10-26/README.md).

Dans Ubuntu WSL, une fois `.env.docker` configuré :

```bash
sudo bash docker/demarrer.sh refuges-validation
```

Ce projet possède ses propres volumes. Les preuves du 26 octobre 2026 n'ont pas réinitialisé les bases de travail ni modifié les anciens résultats JMeter.

## 7. Mesure et Injection de charge JMeter (Partie 4)

Consulter [l’index des livrables](charge/README.md), le [rapport comparatif Markdown](docs/rapport-charge.md) et les [preuves de la campagne](charge/resultats/comparaison-20261026-152151/README.md). Les courbes et tableaux réunissent les campagnes VM et Docker disponibles ; les conditions de mesure et les limites de répétabilité y sont explicitées.

L'injection de charge et la comparaison de performances entre VMs et conteneurs sont configurées dans le dossier **[`charge/`](charge/)** :
- **[`charge/plan.jmx`](charge/plan.jmx)** — Plan de test JMeter paramétrable (`-Jutilisateurs`, `-Jmontee`, `-Jduree`, `-Jhost`, `-Jport`)
- **[`charge/comptes.csv`](charge/comptes.csv)** — Jeu de données de 25 comptes utilisateurs de test
- **[`charge/etalonnage.md`](charge/etalonnage.md)** — Rapport d'étalonnage de l'injecteur et vérification de reproductibilité
- **[`docs/rapport-charge.md`](docs/rapport-charge.md)** — Rapport d'analyse comparative, tableau de synthèse et analyse technique des goulots d'étranglement

### Reproduction des campagnes

Voir [charge/AUTOMATISATION.md](charge/AUTOMATISATION.md) pour la préparation du plan et les commandes CLI. Une nouvelle campagne doit utiliser des noms uniques, le même plan exécuté sur les deux déploiements et une fenêtre de 60 s hors montée. Les options de réinitialisation de base sont décrites dans ce guide.
