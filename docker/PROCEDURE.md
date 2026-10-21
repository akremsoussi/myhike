# MyHike — Docker

Fichiers adaptés au dépôt akremsoussi/myhike, commit
1f3f7ecacab8ad129a0b378c4b90b6895e8f46bf.

## Installation des fichiers

Fusionner le contenu de cette archive avec la racine du dépôt, au même niveau
que client/, metier/ et donnees/. Conserver le fichier .env.docker existant.
Le dossier docker/ contient Compose, les deux Dockerfile, leurs exclusions
et la configuration Nginx. Les sources et les fichiers SQL restent dans le dépôt.

Les commandes suivantes sont à exécuter depuis la racine du dépôt.
Sur la machine utilisant Docker Snap, remplacer docker par sudo /snap/bin/docker.

Pour une première installation seulement :

```sh
cp .env.docker.example .env.docker
nano .env.docker
```

Renseigner les deux mots de passe. Avec des volumes existants, conserver
les anciens identifiants : modifier ces variables ne change pas les comptes MySQL.
Ajouter les lignes de docker/gitignore.fragment au .gitignore existant :

```sh
cat docker/gitignore.fragment >> .gitignore
```

## Construction et démarrage

```sh
docker compose --env-file .env.docker -f docker/compose.yaml config --quiet &&
docker compose --env-file .env.docker -f docker/compose.yaml build &&
docker compose --env-file .env.docker -f docker/compose.yaml up -d --wait &&
curl -fsS http://localhost:8080/api/health
```

Ouvrir http://localhost:8080. La réponse de santé attendue est
{"api":"ok","database":"ok"}.

## Base et photos

Sur un volume MySQL vide, donnees/schema.sql est exécuté avant
donnees/peuplement.sql. Ils sont montés en lecture seule sous des noms ordonnés.
Le contenu de ces fichiers appartient au dépôt ; ils ne sont pas dupliqués
dans l'archive. Ne pas importer manuellement schema.sql dans une base existante :
il contient des DROP TABLE.

Le nom de projet refuges et les volumes mysql_data et uploads sont conservés.
Sur le même moteur Docker, les volumes existants refuges_mysql_data et
refuges_uploads sont donc réutilisés. Sur une autre machine, les volumes ne
voyagent pas avec le dépôt : sauvegarder/restaurer la base et les images ensemble.

L'initialisation ne s'exécute pas sur une base existante. Elle ne réalise pas
non plus de migration de l'ancien schéma vers celui du nouveau dépôt.
Avant de réutiliser une ancienne base, sauvegarder les données et vérifier
sa compatibilité avec les modèles actuels, notamment le rôle super_admin.
Un healthcheck réussi vérifie la connexion, pas toutes les fonctionnalités.

Pour importer les photos des refuges depuis le service externe :

```sh
docker compose --env-file .env.docker -f docker/compose.yaml exec backend python -u -m app.scripts.import_refuge_photos
```

L'import nécessite Internet et peut durer longtemps. Le script saute les refuges
déjà vérifiés. Si la base contient des références à des photos dont les fichiers
ont disparu, restaurer le volume uploads correspondant : --again ne garantit pas
le téléchargement des photos déjà référencées.

Les emails utilisent le mode console par défaut. Les liens de confirmation
se lisent dans les logs du backend.

## Architecture et exploitation

- frontend : compilation React depuis client/, puis serveur Nginx.
- backend : FastAPI depuis metier/app, disponible sur le port interne 8000.
- db : MySQL 8.4, disponible sur le réseau data.
- Nginx transmet /api/ au backend et gère les routes React.
- Seul le port 127.0.0.1:8080 est publié.
- frontend et backend partagent web ; backend et db partagent data.
- data est interne. Cela ne bloque pas nécessairement l'accès direct de
  l'hôte Linux aux adresses IP des conteneurs.

```sh
docker compose --env-file .env.docker -f docker/compose.yaml ps
docker compose --env-file .env.docker -f docker/compose.yaml logs --tail=100 backend
docker compose --env-file .env.docker -f docker/compose.yaml stop
docker compose --env-file .env.docker -f docker/compose.yaml up -d --wait
```

Ne pas utiliser down -v pour un simple redémarrage : cette option supprime
les volumes de données et les photos.

## Vérifications de cette adaptation

Les chemins du dépôt, la syntaxe YAML, les références des services, les volumes
et les chemins COPY ont été contrôlés. Les images de base conservent les digests
de l'installation précédente. Les dépendances Python du dépôt ne sont pas toutes
figées : cela ne garantit pas une reconstruction identique dans le temps.

Docker n'était pas disponible dans l'environnement de préparation.
La construction des images, l'initialisation SQL et les tests fonctionnels
doivent donc être confirmés sur la machine cible avec les commandes ci-dessus.
Le connecteur n'a pas renvoyé le contenu du gros fichier peuplement.sql :
sa présence a été vérifiée, mais ses données n'ont pas été auditées.
