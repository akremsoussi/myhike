# Résultats Docker — 21 octobre 2026

**Projet :** MyHike / Refuges  
**Binôme :** Akrem SOUSSI et Rémi CORTIAL

> Mise à jour de présentation du 26 octobre : les bruts VM sont désormais réunis dans le [rapport consolidé](../../docs/rapport-charge.md). Le présent document conserve le bilan Docker de la session d’origine ; les mentions de comparaison VM à compléter décrivent son état à cette date.

La campagne principale couvre **1, 5, 10, 25, 50 et 100 utilisateurs**, avec
**deux séries complètes**. Deux contrôles isolés supplémentaires ont été faits à 50.
Chaque série commence par une sauvegarde et une réinitialisation SQL, puis par
un contrôle positif et un contrôle négatif du scénario. Les photos sur disque
ont été conservées. Les VMs étaient arrêtées.

Chaque palier dure 72 secondes : 10 secondes de montée, 60 secondes de mesure
et deux secondes de marge. La mesure exclut la montée et une seconde supplémentaire
de stabilisation. Les rapports sont calculés sur cette fenêtre de 60 secondes.

## Campagne principale

| Utilisateurs | Débit série 1 (req/s) | Débit série 2 (req/s) | p95 série 1 (ms) | p95 série 2 (ms) | Erreurs série 1 / 2 |
|---:|---:|---:|---:|---:|---:|
| 1 | 1,27 | 1,25 | 117,5 | 123,4 | 0 % / 0 % |
| 5 | 6,12 | 6,08 | 125,7 | 125,0 | 0 % / 0 % |
| 10 | 12,28 | 12,12 | 142,0 | 132,0 | 0 % / 0 % |
| 25 | 29,12 | 29,08 | 266,7 | 272,0 | 0 % / 0 % |
| 50 | 36,75 | 42,47 | 1 290,4 | 919,95 | 0 % / 0 % |
| 100 | 2,45 | 2,42 | 30 015,7 | 30 013,8 | 98,64 % / 100 % |

Le débit total inclut les erreurs. À 100 utilisateurs, il ne représente donc
pas un débit de requêtes réussies. Le p95 autour de 30 secondes correspond
essentiellement au délai d'attente client, et non à des réponses réussies.

Les paliers de 1 à 25 sont reproductibles à moins de 10 % sur le débit et le p95.
À 50, la campagne principale montre 14,43 % d'écart de débit et 33,52 % de p95.
À 100, le décrochage et les délais d'attente sont reproduits.

## Contrôles supplémentaires à 50

| Contrôle | Débit (req/s) | p95 (ms) | Erreurs |
|---:|---:|---:|---:|
| 1 | 41,80 | 944,3 | 0 % |
| 2 | 34,00 | 1 673,2 | 0 % |

Ils ne satisfont pas non plus le critère de répétabilité : écart de débit de
20,58 %, de p95 de 55,69 %. Conserver les quatre mesures ; ne pas sélectionner
uniquement la meilleure. Une stabilisation des conditions de mesure est nécessaire
avant d'utiliser un chiffre précis à 50 pour départager VM et Docker.
Les contrôles isolés ne remplacent pas la campagne progressive complète.

## Cause observée du décrochage

Les journaux du backend montrent :

```text
sqlalchemy.exc.TimeoutError: QueuePool limit of size 5 overflow 10 reached,
connection timed out, timeout 30.00
```

Le pool applicatif de **15 connexions** est épuisé. Ce constat ne signifie pas
que le moteur MySQL a atteint sa capacité maximale. À 50, le backend consomme
déjà beaucoup de CPU ; à 100, l'attente de connexions devient visible dans les
journaux. L'influence exacte des threads, du pool et d'Argon2 nécessiterait une
expérience distincte. Aucun réglage applicatif n'a été modifié pendant la campagne.

## Étalonnage

Sur `/index.html`, sans traitement métier ni temporisation :

| Utilisateurs | Série | Débit (req/s) | p95 (ms) | Erreurs |
|---:|---:|---:|---:|---:|
| 20 | 1 | 10 874,17 | 3 | 0 % |
| 20 | 2 | 7 588,92 | 5 | 0 % |
| 100 | 1 | 17 115,22 | 11 | 0 % |
| 100 | 2 | 12 023,33 | 16 | 0 % |

La borne basse reste très supérieure au débit applicatif observé et les mesures
CPU Java sont conservées. La variation statique dépasse cependant 10 % : ces
essais ne prouvent ni un plafond précis, ni une répétabilité statique à 10 %.
Le premier essai avec épuisement des ports TCP est marqué invalide. La réutilisation
des connexions TCP a corrigé ce problème ; cette même option devra être conservée
pour les tests VM.

## Où sont les fichiers ?

Tous les chemins ci-dessous sont relatifs à `charge/resultats/` :

- **12 bruts principaux** : `dk-<utilisateurs>-r<1 ou 2>-20261021-113529-649.csv`.
- **2 bruts de contrôle** : `dk-50-r<1 ou 2>-20261021-115723-513.csv`.
- [Rapport principal](dk-20261021-113529-649/RAPPORT-DOCKER.md).
- [Synthèse principale](dk-20261021-113529-649/synthese.csv).
- [Répétabilité principale](dk-20261021-113529-649/repetabilite.csv).
- [Rapport des contrôles](dk-20261021-115723-513/RAPPORT-DOCKER.md).
- [Répétabilité des contrôles](dk-20261021-115723-513/repetabilite.csv).
- Étalonnage : `etalonnage-dk-20261021-112624-419/`, avec les bruts `.csv.gz` au niveau parent.

Dans chaque dossier de campagne : configuration et empreintes SHA-256, plan
exécuté, CSV de plateau, statistiques, métriques serveur JSONL et synthèses JSON,
rapports HTML régénérables depuis les CSV JMeter (non inclus dans le rendu).
Les copies de plateau volumineuses sont dérivées et exclues de Git ; les bruts
d'étalonnage sont conservés sans perte en `.csv.gz`.

Les sauvegardes privées sont dans `.charge-backups/` à la racine du projet,
exclues de Git, ainsi que `.env.docker`. Les sauvegardes privées ne sont pas publiées sur GitHub.

## Relancer

Depuis PowerShell, à la racine du projet :

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\charge\campagne.ps1 -Mode Campaign -ResetDatabase -OtherDeploymentStopped
```

Cette commande sauvegarde puis efface la base locale avant chaque série.
Pour un contrôle isolé, ajouter `-Users 50`. Les noms de sortie sont uniques.
Voir [le guide](../AUTOMATISATION.md).

## Comparaison VM encore à compléter

Les bruts `vm-*.csv` du collègue pourront être déposés dans le **même dossier**.
Comparer le même plan exécuté, les mêmes comptes et données, la même fenêtre hors
montée et la même machine hôte, avec les mêmes budgets de ressources.
La seconde série VM/Docker doit aussi inverser l'ordre des déploiements.
Les données VM, captures GUI de validation, courbes comparatives et mesures
de démarrage/mémoire au repos restent des livrables distincts à réunir.

À la fin des tests, les trois conteneurs sont sains et `/api/health` répond
`api=ok, database=ok`. La réinitialisation UTF-8 a été vérifiée sur Écrins et Pyrénées.
