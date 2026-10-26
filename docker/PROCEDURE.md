# Partie 3 - Déploiement Docker de Refuges

Cette procédure part d'un clone du dépôt contenant `client/`, `metier/`, `donnees/` et `docker/`. Trois services sont construits : Nginx (frontend), FastAPI (backend) et MySQL (db). Les résultats de validation du 26 octobre 2026 et le tableau comparatif sont dans [docs/comparaison.md](../docs/comparaison.md).

## 1. Prérequis et installation du moteur

Les vérifications jointes ont été exécutées avec Docker Engine et Compose dans Ubuntu 24.04 sous WSL2, depuis un poste Windows. VirtualBox héberge les trois VM de comparaison. Docker Desktop n'est pas nécessaire pour cette configuration.

Installation sur l'Ubuntu WSL de ce poste :

```bash
sudo apt-get update
sudo apt-get install -y docker.io docker-compose-v2 docker-buildx
sudo systemctl start docker
sudo docker version
sudo docker compose version
```

Cette installation nécessite systemd actif dans WSL. Les versions du moteur réellement utilisées sont archivées dans `docs/preuves-docker/2026-10-26/versions.txt`. Sur un poste déjà équipé de Docker, conserver son installation et vérifier sa compatibilité avec Compose V2.

## 2. Configuration privée

Depuis la racine du dépôt :

```bash
cp .env.docker.example .env.docker
nano .env.docker
chmod 600 .env.docker
```

Renseigner `DB_NAME`, `DB_USER`, `DB_PASSWORD` et `MYSQL_ROOT_PASSWORD`. Ne pas écraser un fichier `.env.docker` existant. Il est ignoré par Git. Les mots de passe MySQL et le mot de passe des comptes applicatifs sont distincts.

Pour une base déjà initialisée, conserver les identifiants utilisés à sa création : modifier `.env.docker` ne change pas le mot de passe des utilisateurs SQL existants.

## 3. Construction et démarrage

```bash
sudo docker compose --env-file .env.docker -f docker/compose.yaml config --quiet
sudo bash docker/demarrer.sh refuges
curl --fail http://127.0.0.1:8080/api/health
```

`demarrer.sh` construit les images, attend les trois services sains, puis applique l'isolation complémentaire depuis l'hôte Linux natif. L'application est accessible sur `http://localhost:8080`. La santé attendue est `{"api":"ok","database":"ok"}`.

Le backend installe `metier/requirements.lock`, relevé sur l'image construite puis vérifié par `pip check`. Les dépendances de développement restent dans `requirements-dev.txt`. Mettre à jour explicitement ce verrou lors d'un changement de dépendances ; ne pas régénérer les versions pendant une campagne de mesure.

Le proxy utilise `npm ci` avec `client/package-lock.json`, compile React, puis ne conserve que le client compilé et Nginx. Les bases d'image sont fixées par digests. Les fichiers `*.Dockerfile.dockerignore` sont les exclusions spécifiques à chaque Dockerfile.

## 4. Réseaux et isolation

| Service | Réseaux | Port interne | Port publié |
|---|---|---:|---|
| frontend | web | 80 | 127.0.0.1:8080 vers 80 |
| backend | web + data | 8000 | Aucun |
| db | data, interne | 3306 (33060 également interne à MySQL) | Aucun |

Les services utilisent leurs noms DNS : Nginx appelle `backend`, FastAPI appelle `db`. Le navigateur passe uniquement par le proxy. Le proxy et la base n'ont aucun réseau commun.

**Moteur Linux natif :** ne pas confondre absence de publication et absence d'accès depuis le noyau hôte. Les tests initiaux ont montré un accès direct WSL aux IP des conteneurs. `isoler_hote.py` ajoute une chaîne iptables OUTPUT propre au projet, limitée à ses deux sous-réseaux et aux ports privés 8000, 3306, 33060. Le proxy publié reste accessible, ainsi que les communications entre conteneurs. Il ne modifie pas les autres chaînes applicatives.

Après une recréation des réseaux ou un redémarrage de l'hôte, utiliser `demarrer.sh`, qui réapplique les règles. Si les services sont déjà démarrés :

```bash
sudo python3 docker/isoler_hote.py --project refuges
```

Pour retirer uniquement les règles de ce projet après l'arrêt définitif de ce déploiement :

```bash
sudo python3 docker/isoler_hote.py --project refuges --remove
```

Les règles natives du moteur ne sont pas nécessaires sur tous les systèmes Docker Desktop ; les tests doivent être faits depuis le poste hôte et, si pertinent, depuis l'environnement Linux du moteur. L'administrateur du moteur peut toujours modifier ses propres règles : ce n'est pas une barrière contre root.

## 5. Données et persistance

Sur un volume vide, MySQL exécute `donnees/schema.sql` puis `donnees/peuplement.sql`, montés en lecture seule. La validation a relevé 4 652 refuges, 156 massifs, 6 communautés et 30 utilisateurs dont 25 comptes de charge. Les identifiants de démonstration sont dans `LISEZMOI.md`.

Le volume nommé `mysql_data` conserve la base ; `uploads` conserve les fichiers envoyés. Les noms réels sont préfixés par le nom du projet Compose. Ne pas importer `schema.sql` sur une base que l'on souhaite conserver : il contient des suppressions de tables.

Un arrêt ordinaire conserve les conteneurs et les volumes :

```bash
sudo docker compose --env-file .env.docker -f docker/compose.yaml stop
sudo bash docker/demarrer.sh refuges
```

Une suppression des conteneurs et réseaux conserve les volumes nommés :

```bash
sudo docker compose --env-file .env.docker -f docker/compose.yaml down
```

La variante `down -v` **supprime les volumes et leurs données**. Elle sert uniquement à une réinitialisation voulue, après sauvegarde ; elle n'est pas nécessaire pour un redémarrage. Aucune commande de ce type n'a été utilisée pour les preuves jointes.

Les photos externes ne font pas partie du jeu SQL initial. Pour les importer dans le volume uploads, exécuter, si souhaité :

```bash
sudo docker compose --env-file .env.docker -f docker/compose.yaml exec backend python -u -m app.scripts.import_refuge_photos
```

Les emails sont écrits dans les logs en mode console. Les photos et l'envoi SMTP réel ne sont pas des conditions du scénario mesuré ici.

## 6. Rejouer les vérifications sans toucher à une base de travail

La validation du rendu a utilisé le projet séparé `refuges-validation` et ses propres volumes :

```bash
sudo bash docker/demarrer.sh refuges-validation
sudo python3 docker/valider.py --project refuges-validation --output docs/preuves-docker/nouvelle-validation --persistence
```

Le validateur vérifie les connexions aux adresses IP réelles depuis les trois conteneurs et depuis WSL, la connexion d'un compte applicatif, le cookie et une consultation HTTP 200. Le mode `--persistence`, réservé à un nom de projet contenant `validation`, écrit un marqueur dans une table de test dédiée, recrée les conteneurs sans supprimer les volumes, vérifie le marqueur et les compteurs métier, puis retire la table de test. Il n'importe ni ne réinitialise les données existantes.

Avant une nouvelle capture, vérifier les trois services :

```bash
sudo docker compose -p refuges-validation --env-file .env.docker -f docker/compose.yaml ps
```

## 7. Mesures de référence et traçabilité

Le script PowerShell `docker/mesurer_reference.ps1` exécute trois séries Docker puis trois séries VM, sans simultanéité. Il démarre uniquement les VM nommées dans le script, refuse une session VM déjà ouverte et les éteint par ACPI. Il exige un terminal Windows ayant accès à VirtualBox, à WSL et aux informations mémoire des processus.

Il mesure la disponibilité réelle de `/api/health`, le coût mémoire hôte et dix consultations authentifiées HTTP 200 par série. Les volumes et données sont conservés. Consulter les paramètres du script pour le chemin WSL du dépôt et le dossier de sortie. Ce script ne mesure pas la charge JMeter ; les campagnes de la partie 4 ne sont pas modifiées.

Voir [les preuves](../docs/preuves-docker/2026-10-26/README.md), la [comparaison au format Markdown](../docs/comparaison.md). Les limites de périmètre mémoire, de disque et de versions applicatives y sont indiquées.
