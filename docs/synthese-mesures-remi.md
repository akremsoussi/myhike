# Intégration des mesures de Rémi

**Projet :** MyHike / Refuges  
**Binôme :** Akrem SOUSSI et Rémi CORTIAL

Les apports du commit `311bd31`, intégrés sur `main` par `3ea8466`, sont conservés. Ils complètent les parties déploiement et méthode Figma ; ils n'apportent pas une deuxième série des anciens CSV JMeter VM.

## Vérification des mesures de référence

Les six essais bruts ont été relus : trois par déploiement, dix consultations par essai. Les **60 consultations renvoient HTTP 200 et un total de 4 652 refuges**. Les médianes recalculées correspondent au CSV publié.

| Médiane de trois essais | VM | Docker |
|---|---:|---:|
| Démarrage | 122,80 s | 14,59 s |
| Mémoire hôte | 3073,52 MiB | 4671,84 MiB |
| Latence de consultation | 64,80 ms | 23,70 ms |

Source : [synthèse de Rémi](preuves-docker/2026-10-26/synthese-reference.csv), [données brutes](preuves-docker/2026-10-26/mesures-reference/mesures.json) et [vérification de l'intégration](preuves-docker/2026-10-26/verification-integration.json).

## Pourquoi ces chiffres diffèrent de la nouvelle campagne

- Le poste de Rémi est décrit avec **8 processeurs logiques** ; le poste de la campagne JMeter récente en a **12**. On ne mélange pas leurs résultats.
- Rémi chronomètre Docker avec son moteur WSL déjà disponible ; la nouvelle mesure inclut le démarrage de Docker Desktop et de son moteur Linux.
- Sa mémoire Docker correspond au processus WSL complet, avec d'autres processus et caches. La nouvelle série additionne les RSS des processus hôtes identifiés, dont le moteur Docker. Ces périmètres ne donnent pas une mesure isolée du coût des conteneurs.
- Ses latences sont celles de consultations authentifiées seules, sans la boucle de connexions et la concurrence du scénario JMeter.
- Les mesures disque (25,36 GiB VM avec snapshots ; 559,93 MiB images et volumes Docker) ont des périmètres différents et sont présentées comme tels.

## Ce qui est retenu dans le rendu

1. **Parties 2 et 3 :** [comparaison de déploiement de Rémi](comparaison.md), installation depuis les sources, matrice réseau, persistance, versions et relevés de référence. Les preuves originales restent dans `preuves-docker/2026-10-26/`.
2. **Partie 4 :** [rapport de charge principal](rapport-charge.md), fondé sur les 24 essais de la campagne appariée. La montée, la fenêtre, le plan et les plafonds par couche y sont communs aux deux déploiements.
3. **Historique :** [ancien rapport de Rémi](rapport-charge-historique-remi.md), anciens CSV VM et Docker, anciennes courbes. Ils ne sont pas réécrits pour correspondre aux nouvelles mesures.

Le Dockerfile et les dépendances verrouillées apportés par Rémi sont conservés. La campagne appariée a été exécutée avant leur intégration, sur la base Git `f6e764b` ; elle n'est pas présentée comme un test de charge du nouvel assemblage d'images. Les versions effectivement mesurées sont archivées dans chaque configuration de campagne.
