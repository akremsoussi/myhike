# Étalonnage du protocole - étape 16

**Projet :** Refuges  
**Binôme :** Akrem SOUSSI et Rémi CORTIAL

## 1. Instrument et paramètres

JMeter 5.6.3 s’exécute en CLI sur l’hôte Windows. La cible statique est `/index.html` servie par Nginx, sans temporisation ni traitement métier. La campagne applicative utilise 25 comptes, une montée de 10 s puis une fenêtre de 60 s à partir de l’origine + 11 s (1 s de stabilisation). La durée programmée est de 72 s. Paliers : 1, 5, 10, 25, 50, 100.

La réutilisation TCP est activée dans le plan préparé ; les cookies sont remis à zéro entre itérations. Les paramètres effectivement utilisés et leurs empreintes sont archivés dans chaque dossier de session.

## 2. Débit statique observé

| Utilisateurs | Débit observé (req/s) | p95 (ms) | Erreurs |
|---:|---:|---:|---:|
| 100 | 17 115,22 | 11,0 | 0,00 % |
| 100 | 12 023,33 | 16,0 | 0,00 % |
| 20 | 10 874,17 | 3,0 | 0,00 % |
| 20 | 7 588,92 | 5,0 | 0,00 % |

Source : [synthèse statique](resultats/etalonnage-dk-20261021-112624-419/synthese.csv). Les deux répétitions sont détaillées dans les statistiques du même dossier. Le minimum est 7 588,92 req/s, largement au-dessus du maximum applicatif observé de 42,47 req/s (environ 179 fois). Cela donne une marge observée ; le plafond exact n’est pas établi. La variabilité statique dépasse 10 % et ne valide pas la répétabilité. Le premier essai invalidé par épuisement des ports TCP reste exclu.

## 3. Répétabilité applicative

Écart retenu dans les scripts Docker : (maximum − minimum) / moyenne × 100. Le seuil de 10 % est évalué séparément sur débit et p95.

| Utilisateurs | Écart de débit (%) | Écart de p95 (%) | Lecture |
|---:|---:|---:|---|
| 1 | 1,33 | 4,90 | Sous 10 % |
| 5 | 0,55 | 0,56 | Sous 10 % |
| 10 | 1,37 | 7,30 | Sous 10 % |
| 25 | 0,11 | 1,97 | Sous 10 % |
| 50 | 14,43 | 33,52 | Au-dessus de 10 % |
| 100 | 1,37 | 0,01 | Sous 10 % |

À 100, des chiffres proches ne valident pas un service nominal : les erreurs atteignent 98,64 à 100 %. À 50, les contrôles supplémentaires donnent 41,80 et 34,00 req/s ; leurs écarts de débit (20,58 %) et p95 (55,69 %) confirment l’instabilité. Conserver toutes les mesures sans sélectionner la meilleure.

## 4. Charge de l’injecteur et réserves

Pendant la campagne applicative, la moyenne CPU Java relevée reste inférieure à 1 % de l’hôte (12 processeurs logiques déclarés). Les JSON de synthèse et les JSONL horodatés sont archivés avec la campagne. Ce constat et la marge statique ne suggèrent pas un injecteur limitant sur ces essais ; ils ne remplacent pas un étalonnage répété dans les conditions de la future campagne VM.

L’ancien document mentionnait > 205 req/s et deux essais à 14,8 / 14,3 req/s sans bruts dédiés identifiés. Ces valeurs historiques ne servent pas à certifier l’étalonnage actuel. La série VM n’a qu’une répétition conservée et sa fenêtre de plateau n’est pas tracée.

## 5. Reproduction et preuves

- [Guide d’automatisation](AUTOMATISATION.md) : préparation du plan, étalonnage et campagne.
- [Configuration principale](resultats/dk-20261021-113529-649/configuration.json) : versions, durées et empreintes.
- [Répétabilité principale](resultats/dk-20261021-113529-649/repetabilite.csv).
- [Index des résultats et validations 200/401](resultats/README.md).

Avant une comparaison définitive, utiliser le même plan préparé et les mêmes timeouts pour VM et Docker, le même poste et les mêmes budgets de ressources, puis deux séries dans un ordre inversé.
