# Preuves - Partie 3 Docker

**Projet :** Refuges  
**Binôme :** Akrem SOUSSI et Rémi CORTIAL

Les fichiers de ce dossier attestent les opérations réellement exécutées ; ils ne sont pas des exemples. Le projet Compose de validation est séparé des données de travail et des campagnes JMeter.

| Preuve | Fichiers |
|---|---|
| Trois services en marche et sains | `services.txt`, `services.json`, `releve-services.png` (rendu CLI, pas capture Docker Desktop) |
| Réseaux et adresses | `reseaux.json` |
| Isolation avant et après correction | `matrice-avant-filtrage.json`, `matrice.json`, `matrice-windows.json`, `filtrage-hote.txt` |
| Peuplement réel et parcours authentifié | `peuplement.txt`, `parcours.json` |
| Données conservées après recréation | `persistance.json`, `services-apres-recreation.txt` |
| Images et volumes | `images.json`, `disque-docker.txt`, `volumes-octets.txt`, `disques-docker.json` |
| Versions et empreintes des sources | `versions.txt`, `configuration.json`, `dependances-check.txt` |
| Trois répétitions Docker et VM | `mesures-reference/mesures.json`, `mesures-reference/disques-vm.json`, `mesures-reference/hote.json`, `mesures-reference/docker-stats-r*.jsonl` |
| Synthèse calculée | `synthese-reference.csv` |
| Installation depuis sources et volume vide | `installation-sources.json`, `installation-sources.log` |

## Méthode et limites

Les six essais de référence ont été exécutés sur le même Windows, sans faire tourner simultanément les VM et les conteneurs. Les mesures de latence comprennent dix consultations authentifiées HTTP 200 par essai. Les relevés mémoire hôte ne sont pas remplacés par la somme docker stats : le processus vmmemWSL complet est conservé, avec la limite de l'environnement WSL partagé indiquée dans le rapport.

Les essais de première installation et de validation ont leurs propres volumes, conservés. La suppression des conteneurs du projet d'installation n'a pas supprimé ces volumes. Les fichiers privés .env.docker ne sont pas inclus.

Les valeurs de référence historiques restent dans docs/mesures.md. Les nouveaux relevés n'affirment pas que les versions applicatives déployées dans les anciens invités VM sont identiques au code Docker actuel. Aucun gain global de mémoire ou de disque physique n'est déduit de périmètres différents.

Voir [le compte rendu](../../comparaison.md) et [la procédure](../../../docker/PROCEDURE.md).
