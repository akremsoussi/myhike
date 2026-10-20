# Refuges — Application Web Trois-Tiers

**Binôme :** Akrem SOUSSI & Rémi CORTIAL  
**Établissement :** Aix-Marseille Université — École d'ingénieurs  
**Année universitaire :** 2025 – 2026  
**Module :** DEV 1 — Application Trois-Tiers (Enseignant : Mohamed Quafafou)  
**Prototype Figma :** [Consulter la maquette Figma en ligne](https://www.figma.com/design/KrPHETSktcZgtTbB9uxVyB/Refuges-%E2%80%93-Web-App?node-id=10-2)

---

## 1. Présentation du Projet

**Refuges** est une application web conçue selon une **architecture 3 tiers stricte**, dédiée à la découverte, la cartographie et le partage de randonnées en montagne :
- **Cartographie dynamique multi-fonds :** Consultation des massifs et de plus de **4 600 refuges réels** avec basculement entre couches OpenStreetMap, OpenTopoMap et Plan IGN officiel.
- **Gestion des sorties et profils altimétriques :** Import et analyse de fichiers GPX, calcul automatique de dénivelé et distance, tracé interactif de randonnées.
- **Réseau et communauté :** Gestion d'amis, publications, interactions et communautés par massif montagnard.
- **Administration hiérarchisée :** Modération de contenu, suspension de comptes et gestion des privilèges (Randonneur, Modérateur, Super Administrateur).

---

## 2. Architecture Logicielle et Organisation du Dépôt

Conformément au cahier des charges (Section 5.2), le dépôt sépare rigoureusement les responsabilités dès la racine :

```text
myhike/
├── client/ (-> frontend)     # Couche Présentation : React 19, TypeScript, Leaflet, Vite
├── metier/ (-> backend)      # Couche Métier : Python 3.12, FastAPI, SQLAlchemy, Argon2id
├── donnees/                  # Couche Données : schema.sql et peuplement.sql (MySQL)
├── deploiement/              # Configuration du déploiement 3 VMs (Netplan, Nginx, Systemd)
│   ├── reseau/               # Configurations statiques Netplan des 3 machines
│   ├── donnees/              # mysqld.cnf, privileges.sql, schema et données
│   ├── metier/               # Service systemd et .env externalisé
│   ├── proxy/                # Configuration Nginx (reverse proxy /api/ et SPA)
│   └── PROCEDURE.md          # Procédure complète chronologique pas à pas
├── docs/                     # Documentation et livrables d'évaluation
│   ├── analyse.md            # Dossier d'analyse (Étape 1 : acteurs, cas d'usage, règles)
│   ├── requetes.md           # Exemples de requêtes cURL de la couche métier (Étape 4)
│   ├── tests.md              # Cahier de recette et tableau de tests (Étape 6)
│   ├── mesures.md            # Mesures de référence de l'étape 10 et matrice
│   └── captures/             # Captures d'écran des tests réseau et des snapshots
├── ova/                      # Archives des trois machines virtuelles (.ova)
└── LISEZMOI.md               # Le présent fichier de présentation et démarrage rapide
```

---

## 3. Comptes de Démonstration

Tous les comptes ci-dessous sont préconfigurés dans la base avec le mot de passe commun **`refuges123`** :

| Rôle | Identifiant / Email | Mot de passe | Prérogatives |
| :--- | :--- | :---: | :--- |
| **Randonneur** | `randonneur@refuges.local` | `refuges123` | Utilisateur classique : consultation, sorties GPX, amis |
| **Modérateur** | `moderateur@refuges.local` | `refuges123` | Modération des contenus et signalements, suspension |
| **Administrateur** | `admin@refuges.local` | `refuges123` | Administration standard |
| **Super Admin** | `remi@gmail.com` | `refuges123` | Droits absolus : gestion des administrateurs et du site |

---

## 4. Démarrage Rapide en Local (Développement)

### Prérequis
- Python 3.12+
- Node.js 22+ (ou 24 LTS)
- Serveur MySQL 8.0

### A. Base de données
```bash
mysql -u root -p -e "CREATE DATABASE refuges CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
mysql -u root -p -e "CREATE USER 'refuges'@'localhost' IDENTIFIED BY 'refuges';"
mysql -u root -p -e "GRANT ALL PRIVILEGES ON refuges.* TO 'refuges'@'localhost'; FLUSH PRIVILEGES;"

# Injection du schéma et des données
mysql -u refuges -prefuges refuges < donnees/schema.sql
mysql -u refuges -prefuges refuges < donnees/peuplement.sql
```

### B. Couche Métier (API FastAPI)
```bash
cd metier
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # Renseigner les identifiants si besoin
uvicorn app.main:app --host 127.0.0.1 --port 8000
```
L'API répond sur : `http://127.0.0.1:8000/api/health`

### C. Couche Présentation (Client React)
```bash
cd client
npm install
npm run dev
```
L'interface s'ouvre sur : `http://localhost:5173/`

---

## 5. Déploiement Réparti sur 3 Machines Virtuelles (Partie 1)

Pour le déploiement sur trois machines virtuelles isolées avec réseau interne (`intnet-app`, `10.10.10.0/24`), consultez le guide complet :
👉 **[`deploiement/PROCEDURE.md`](deploiement/PROCEDURE.md)**

Les mesures de référence et la matrice de joignabilité validée sont consignées dans :
👉 **[`docs/mesures.md`](docs/mesures.md)**
