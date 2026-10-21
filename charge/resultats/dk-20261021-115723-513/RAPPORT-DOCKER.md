# Campagne Docker : résultats mesurés

Début UTC : 2026-10-21T09:57:23.6121918Z. Commit de référence : `07a0baa812be57c05519d5924cb5835699ed467b`.
Les empreintes des plans, comptes et fichiers SQL sont conservées dans `configuration.json`.

## Protocole

Injecteur JMeter 5.6.3 en CLI sur Windows, hors des conteneurs. VMs arrêtées.
Paliers : 50. Répétitions : 2.
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
| 50 | 1 | 2508 | 0.00 | 41.80 | 41.80 | 428.0 | 847.0 | 944.3 | 1278.65 |
| 50 | 2 | 2040 | 0.00 | 34.00 | 34.00 | 622.0 | 1423.4 | 1673.2 | 2231.88 |

Le débit total inclut les échecs. Un p95 proche de 30 000 ms avec un fort taux
d'erreur indique surtout le timeout client de 30 s, et non la latence des réponses réussies.

## Répétabilité

| Utilisateurs | Écart de débit (%) | Écart de p95 (%) |
|---:|---:|---:|
| 50 | 20.58 | 55.69 |

Écart = (maximum - minimum) / moyenne des répétitions. Les écarts supérieurs à
10 % doivent être explicités ou contrôlés par une nouvelle campagne dans des conditions stables.

## Ressources et goulot observé

| Utilisateurs | Série | CPU backend moyen (% Docker) | Mémoire backend max (MiB) | Connexions MySQL max | CPU injecteur moyen (% hôte) |
|---:|---:|---:|---:|---:|---:|
| 50 | 1 | 950.2 | 825.7 | 16 | 0.84 |
| 50 | 2 | 885.9 | 1003.0 | 17 | 0.67 |

Dans Docker, 100 % CPU correspond à un cœur logique ; plusieurs centaines de
pour cent ne sont donc pas une erreur. Les connexions MySQL incluent celle du relevé.
Le détail des entrées-sorties et les relevés horodatés sont conservés dans les fichiers serveur.

Consulter les journaux du backend avant de conclure sur l'origine d'une saturation.

Aucun réglage applicatif n'a été changé entre les paliers pour améliorer artificiellement les résultats.

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
