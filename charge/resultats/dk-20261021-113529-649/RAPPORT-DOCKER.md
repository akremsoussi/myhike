# Campagne Docker : résultats mesurés

Début UTC : 2026-10-21T09:35:29.7417920Z. Commit de référence : `07a0baa812be57c05519d5924cb5835699ed467b`.
Les empreintes des plans, comptes et fichiers SQL sont conservées dans `configuration.json`.

## Protocole

Injecteur JMeter 5.6.3 en CLI sur Windows, hors des conteneurs. VMs arrêtées.
Paliers : 1, 5, 10, 25, 50, 100. Répétitions : 2.
Montée : 10 s ; fenêtre mesurée : 60 s, hors montée.
Une seconde de stabilisation supplémentaire est exclue. Les requêtes sont sélectionnées
par leur instant de départ ; leur durée entière est conservée, même en cas de timeout.
Base sauvegardée puis réinitialisée avant chaque série. Fichiers photo conservés.
Scénario : connexion avec compte CSV, cookie de session, consultation des refuges.
Temporisation : 500 à 1 000 ms avant chaque requête. Connexions TCP réutilisées.
Contrôles positifs et négatifs exécutés avant chaque série.

## Mesures applicatives (plateau uniquement)

| Utilisateurs | Série | Requêtes | Erreurs (%) | Débit total (req/s) | Débit réussi (req/s) | Médiane (ms) | p90 (ms) | p95 (ms) | p99 (ms) |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 1 | 76 | 0.00 | 1.27 | 1.27 | 63.0 | 115.5 | 117.5 | 152.75 |
| 1 | 2 | 75 | 0.00 | 1.25 | 1.25 | 80.0 | 115.0 | 123.4 | 151.6 |
| 5 | 1 | 367 | 0.00 | 6.12 | 6.12 | 46.0 | 115.0 | 125.7 | 154.72 |
| 5 | 2 | 365 | 0.00 | 6.08 | 6.08 | 77.0 | 114.8 | 125.0 | 151.8 |
| 10 | 1 | 737 | 0.00 | 12.28 | 12.28 | 78.0 | 123.4 | 142.0 | 212.12 |
| 10 | 2 | 727 | 0.00 | 12.12 | 12.12 | 79.0 | 118.0 | 132.0 | 165.96 |
| 25 | 1 | 1747 | 0.00 | 29.12 | 29.12 | 85.0 | 203.4 | 266.7 | 430.62 |
| 25 | 2 | 1745 | 0.00 | 29.08 | 29.08 | 86.0 | 211.6 | 272.0 | 428.0 |
| 50 | 1 | 2205 | 0.00 | 36.75 | 36.75 | 531.0 | 1124.0 | 1290.4 | 1573.0 |
| 50 | 2 | 2548 | 0.00 | 42.47 | 42.47 | 396.0 | 798.0 | 919.95 | 1209.3 |
| 100 | 1 | 147 | 98.64 | 2.45 | 0.03 | 30008.0 | 30015.0 | 30015.7 | 30017.0 |
| 100 | 2 | 145 | 100.00 | 2.42 | 0.00 | 30004.0 | 30007.0 | 30013.8 | 30018.8 |

Le débit total inclut les échecs. Un p95 proche de 30 000 ms avec un fort taux
d'erreur indique surtout le timeout client de 30 s, et non la latence des réponses réussies.

## Répétabilité

| Utilisateurs | Écart de débit (%) | Écart de p95 (%) |
|---:|---:|---:|
| 1 | 1.33 | 4.90 |
| 5 | 0.55 | 0.56 |
| 10 | 1.37 | 7.30 |
| 25 | 0.11 | 1.97 |
| 50 | 14.43 | 33.52 |
| 100 | 1.37 | 0.01 |

Écart = (maximum - minimum) / moyenne des répétitions. Les écarts supérieurs à
10 % doivent être explicités ou contrôlés par une nouvelle campagne dans des conditions stables.

## Ressources et goulot observé

| Utilisateurs | Série | CPU backend moyen (% Docker) | Mémoire backend max (MiB) | Connexions MySQL max | CPU injecteur moyen (% hôte) |
|---:|---:|---:|---:|---:|---:|
| 1 | 1 | 32.2 | 157.3 | 3 | 0.04 |
| 1 | 2 | 14.6 | 91.2 | 3 | 0.04 |
| 5 | 1 | 105.3 | 210.5 | 4 | 0.18 |
| 5 | 2 | 84.5 | 134.2 | 4 | 0.22 |
| 10 | 1 | 166.7 | 173.6 | 7 | 0.35 |
| 10 | 2 | 158.5 | 179.1 | 6 | 0.40 |
| 25 | 1 | 518.4 | 408.4 | 7 | 0.60 |
| 25 | 2 | 505.4 | 540.6 | 9 | 0.61 |
| 50 | 1 | 948.7 | 928.6 | 16 | 0.65 |
| 50 | 2 | 919.0 | 908.1 | 16 | 0.81 |
| 100 | 1 | 46.3 | 212.0 | 16 | 0.14 |
| 100 | 2 | 16.4 | 159.9 | 16 | 0.17 |

Dans Docker, 100 % CPU correspond à un cœur logique ; plusieurs centaines de
pour cent ne sont donc pas une erreur. Les connexions MySQL incluent celle du relevé.
Le détail des entrées-sorties et les relevés horodatés sont conservés dans les fichiers serveur.

Les journaux conservés montrent une saturation du pool SQLAlchemy :
`QueuePool limit of size 5 overflow 10 reached`, soit 15 connexions, avec un délai de 30 s.
Cette observation explique les erreurs de pool. Elle ne prouve pas une saturation du moteur MySQL.
L'influence du pool, des threads de traitement et du coût Argon2 devra être isolée dans une expérience séparée.

Aucun réglage applicatif n'a été changé entre les paliers pour améliorer artificiellement les résultats.

## Étalonnage de l’injecteur

Cible statique `/index.html` de Nginx, sans temporisation et sans traitement métier.

| Utilisateurs | Série | Débit (req/s) | Erreurs (%) | p95 (ms) |
|---:|---:|---:|---:|---:|
| 100 | 1 | 17115.22 | 0.0 | 11.0 |
| 100 | 2 | 12023.33 | 0.0 | 16.0 |
| 20 | 1 | 10874.17 | 0.0 | 3.0 |
| 20 | 2 | 7588.92 | 0.0 | 5.0 |

Le débit statique varie entre les répétitions : ne pas en déduire un plafond précis
ou une répétabilité statique inférieure à 10 %. Même la borne basse est très supérieure
au débit applicatif mesuré. Comparer aussi la charge CPU de Java pour écarter une saturation
de l'injecteur. Les résultats bruts volumineux sont archivés sans perte en `.csv.gz`.
Le premier essai avec épuisement des ports TCP est marqué invalide et exclu de cette campagne.

## Comparaison VM à compléter

Les résultats VM ne sont pas encore disponibles. Aucun écart VM/Docker ne peut être calculé.
Déposer leurs bruts `vm-*.csv` dans le même dossier `charge/resultats/`.
Utiliser le même plan exécuté, comptes, données, durées, machine hôte et budgets de ressources.
Réaliser aussi la seconde série VM/Docker avec ordre inversé dans une même session, comme demandé par le sujet.
Les captures GUI de validation, les mesures de démarrage/mémoire au repos des étapes 10/14
et les courbes comparatives finales restent des livrables distincts.

## Traçabilité

- Bruts : `../dk-*-r*-*.csv` ; toutes les requêtes, montée comprise.
- Statistiques : `synthese.csv` ; plateau uniquement.
- Relevés serveur : `*-serveur.jsonl` et `*-serveur-synthese.json`.
- Rapports JMeter : `rapport-<utilisateurs>-r<répétition>/index.html`.
- Sauvegardes privées : `.charge-backups/` à la racine du projet, exclues de Git.
