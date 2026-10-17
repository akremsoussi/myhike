# Procédure de déploiement pas à pas (3 Tiers sur Machines Virtuelles)

Ce document décrit l'ensemble des étapes, dans l'ordre chronologique exact, pour passer de trois machines virtuelles nues à une architecture 3-tiers complètement fonctionnelle et isolée.

---

## 1. Topologie et Plan d'adressage

- **Réseau interne VirtualBox :** `intnet-app`
- **vm-proxy (Ubuntu-Web) :**
  - Carte 1 (`enp0s3`) : Réseau interne `intnet-app` -> `10.10.10.10/24` (Statique)
  - Carte 2 (`enp0s8`) : NAT avec redirection de port hôte `8080` -> invité `80` (et `2210` -> `22` pour maintenance)
- **vm-metier (Ubuntu-API) :**
  - Carte 1 (`enp0s3`) : Réseau interne `intnet-app` -> `10.10.10.20/24` (Statique)
  - Carte 2 : Désactivée (aucun accès NAT)
- **vm-donnees (Ubuntu-DB) :**
  - Carte 1 (`enp0s3`) : Réseau interne `intnet-app` -> `10.10.10.30/24` (Statique)
  - Carte 2 : Désactivée (aucun accès NAT)

---

## 2. Étape 7 — Préparation des machines (Socle commun et clones)

1. **Création de la machine socle (`Ubuntu-base`) :**
   - OS : Ubuntu Server 24.04 LTS (64-bit).
   - Installation minimale avec OpenSSH Server activé.
   - Mise à jour initiale : `sudo apt update && sudo apt upgrade -y`.
2. **Clonage intégral (3 fois) :**
   - Pour chaque clone (`Ubuntu-DB`, `Ubuntu-API`, `Ubuntu-Web`), cocher impérativement : **« Générer de nouvelles adresses MAC pour toutes les cartes réseau »**.
3. **Différenciation de l'identité et réinitialisation de l'ID machine :**
   Sur chaque machine, lancer :
   ```bash
   sudo hostnamectl set-hostname <nom-de-machine>   # db-server, api-server, web-server
   sudo truncate -s 0 /etc/machine-id
   sudo systemd-machine-id-setup && sudo reboot
   ```
4. **Dimensionnement des ressources :**
   - `Ubuntu-Web` : 1 CPU, 1024 Mo RAM.
   - `Ubuntu-API` : 1 CPU, 1024 Mo RAM.
   - `Ubuntu-DB` : 2 CPU, 2048 Mo RAM.
5. **Snapshot initial :** Prendre un instantané nommé `base propre` sur chacune des 3 machines.

---

## 3. Étape 8 — Réseau et adressage Netplan

Sur chaque machine, configurer `/etc/netplan/50-cloud-init.yaml` avec les fichiers correspondants du dossier `reseau/` :
- `Ubuntu-DB` : `addresses: [10.10.10.30/24]`
- `Ubuntu-API` : `addresses: [10.10.10.20/24]`
- `Ubuntu-Web` : `addresses: [10.10.10.10/24]` sur `enp0s3` et `dhcp4: true` sur `enp0s8`.

Appliquer la configuration :
```bash
sudo netplan apply
```
**Validation :**
- `ping -c2 10.10.10.30` depuis `vm-metier` (succès, 0% perte).
- `ping -c2 10.10.10.20` depuis `vm-proxy` (succès, 0% perte).

---

## 4. Étape 9 — Déploiement des trois couches

### Couche 1 : Base de données (`vm-donnees`)
1. Activer ponctuellement l'adaptateur NAT pour installer MySQL :
   ```bash
   sudo apt update && sudo apt install -y mysql-server
   ```
2. Configurer l'écoute réseau dans `/etc/mysql/mysql.conf.d/mysqld.cnf` :
   ```ini
   bind-address = 10.10.10.30
   ```
   Redémarrer MySQL : `sudo systemctl restart mysql`.
3. Créer la base et restreindre l'utilisateur à la machine métier :
   ```sql
   CREATE DATABASE refuges CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
   CREATE USER 'refuges'@'10.10.10.20' IDENTIFIED BY 'refuges';
   GRANT ALL PRIVILEGES ON refuges.* TO 'refuges'@'10.10.10.20';
   FLUSH PRIVILEGES;
   ```
4. Importer les scripts de données :
   ```bash
   sudo mysql refuges < schema.sql
   sudo mysql refuges < data.sql
   ```
5. Mettre en place le filtrage pare-feu (UFW) :
   ```bash
   sudo ufw allow 22/tcp
   sudo ufw allow from 10.10.10.20 to any port 3306 proto tcp
   sudo ufw enable
   ```
6. **Isolation :** Éteindre la VM, désactiver la Carte 2 (NAT) dans VirtualBox, rallumer et prendre le snapshot `db-prete`.

---

### Couche 2 : Application Métier (`vm-metier`)
1. Activer ponctuellement l'adaptateur NAT pour installer l'environnement Python :
   ```bash
   sudo apt update && sudo apt install -y python3 python3-venv python3-pip
   ```
2. Déployer l'archive du backend dans `/home/remi/backend` et installer les dépendances :
   ```bash
   python3 -m venv .venv
   .venv/bin/pip install -r requirements.txt
   ```
3. Définir le fichier d'environnement `/home/remi/backend/.env` :
   ```ini
   DB_HOST=10.10.10.30
   DB_PORT=3306
   DB_NAME=refuges
   DB_USER=refuges
   DB_PASSWORD=refuges
   ```
4. Déclarer le service systemd dans `/etc/systemd/system/refuges-backend.service` (voir `metier/refuges-backend.service`).
5. Activer et démarrer le service :
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable --now refuges-backend
   ```
6. Vérifier la santé : `curl http://10.10.10.20:8000/api/health` -> `{"api":"ok","database":"ok"}`.
7. **Isolation :** Éteindre la VM, désactiver la Carte 2 (NAT), rallumer et prendre le snapshot `metier-prete`.

---

### Couche 3 : Façade Web et Reverse Proxy (`vm-proxy`)
1. Installer Nginx :
   ```bash
   sudo apt update && sudo apt install -y nginx
   ```
2. Déposer les fichiers statiques compilés de l'application React dans `/var/www/html/`.
3. Configurer `/etc/nginx/sites-available/default` (voir `proxy/nginx-refuges.conf`) :
   - Renvoi du préfixe `/api/` vers `http://10.10.10.20:8000/api/`.
   - Redirection de toutes les autres routes vers `/index.html` (SPA).
4. Redémarrer Nginx : `sudo systemctl restart nginx`.
5. Prendre le snapshot `proxy-prete`.

---

## 5. Validation globale
L'application est accessible depuis le navigateur de la machine hôte à l'adresse :
**`http://localhost:8080/`**
