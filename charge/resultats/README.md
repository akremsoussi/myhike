# Résultats JMeter - index et traçabilité

Les fichiers bruts et les dossiers de session d’origine sont conservés. Les tableaux ajoutés sous `synthese/` sont des dérivés de présentation.

| Ensemble | Contenu | Fenêtre / répétitions |
|---|---|---|
| `vm-{1,5,10,25,50,100}.csv` | Bruts VM historiques | Fichier complet ; une série |
| `dk-*-r*-20261021-113529-649.csv` | Bruts Docker principaux | Plateau extrait de 60 s ; deux séries |
| `dk-50-r*-20261021-115723-513.csv` | Contrôles Docker supplémentaires à 50 | Deux contrôles, conservés séparément |
| `etalonnage-*.csv.gz` | Bruts statiques compressés sans perte | Dossiers de session associés |

## Synthèses client

| VM : utilisateurs | Durée totale observée (s) | Requêtes valides | Threads simultanés max |
|---:|---:|---:|---:|
| 1 | 96,94 | 106 | 1 |
| 5 | 101,02 | 425 | 5 |
| 10 | 100,83 | 521 | 10 |
| 25 | 148,49 | 723 | 25 |
| 50 | 64,04 | 309 | 50 |
| 100 | 93,01 | 170 | 100 |

Les durées VM observées ne prouvent pas un plateau de 60 s hors montée. Le script historique exclut les lignes incomplètes ; celles-ci restent présentes dans les sources. Les centiles utilisent une interpolation linéaire au rang (n − 1) × p. Débit VM = N / (dernier achèvement − premier départ). Débit Docker = départs de requêtes dans le plateau / 60 s.

À 100 utilisateurs VM : **37 réponses 500, 17 réponses 504, 4 réponses 401**, et 112 réponses 200. L’ancienne formulation « 58 erreurs 500 » était inexacte.

## Fichiers dérivés

- [Mesures client](synthese/mesures-client.csv) : total et chaque type de requête, p50/p90/p95/p99, erreurs, débit réussi, durée et utilisateurs effectifs.
- [Mesures serveur Docker](synthese/mesures-serveur-docker.csv) : CPU et mémoire par service, I/O disque et connexions DB. CPU Docker : 100 % = un cœur logique.
- [Inventaire des bruts](synthese/inventaire-bruts.csv) : chemin, taille et SHA-256 des CSV racine. Les fichiers compressés et métriques des sessions restent indexés par leurs dossiers.

## Relevés VM manuels

| Utilisateurs | CPU métier moyen (%) | Maximum (%) |
|---:|---:|---:|
| 1 | 2,5 | 3,5 |
| 5 | 8,0 | 11,5 |
| 10 | 10,4 | 16,7 |
| 25 | 13,2 | 19,8 |
| 50 | 11,2 | 19,1 |
| 100 | Non relevé | 26,6 |

Source : relevés manuels communiqués par Rémi dans l’historique projet. Le périmètre exact de normalisation CPU n’est pas archivé. Mémoire par service, I/O et connexions DB VM manquent ; ils ne sont pas reconstruits.

## Validation du scénario

| Preuve | Échantillons | Échecs détectés | Codes |
|---|---:|---:|---|
| [validation-negatif-r1.csv](dk-20261021-113529-649/validation-negatif-r1.csv) | 2 | 2 | 401 |
| [validation-negatif-r2.csv](dk-20261021-113529-649/validation-negatif-r2.csv) | 2 | 2 | 401 |
| [validation-positif-r1.csv](dk-20261021-113529-649/validation-positif-r1.csv) | 2 | 0 | 200 |
| [validation-positif-r2.csv](dk-20261021-113529-649/validation-positif-r2.csv) | 2 | 0 | 200 |

Les contrôles CSV ne remplacent pas les captures GUI demandées à l’étape 15. Les rapports de session restent des comptes rendus historiques ; le [rapport consolidé](../../docs/rapport-charge.md) réunit désormais VM et Docker.
