# Étalonnage

**Projet :** Refuges  
**Binôme :** Akrem SOUSSI et Rémi CORTIAL

Deux répétitions sur `/index.html`, 20 puis 100 utilisateurs, sans temporisation. Même poste et mêmes plafonds par couche que les campagnes applicatives.

| Déploiement | Utilisateurs | Série | Débit (req/s) | p95 (ms) | Erreurs (%) |
|---|---:|---:|---:|---:|---:|
| vm | 20 | 1 | 723.6667 | 33.0 | 0.0 |
| vm | 20 | 2 | 735.6 | 32.0 | 0.0 |
| vm | 100 | 1 | 473.6667 | 299.0 | 0.0 |
| vm | 100 | 2 | 470.0333 | 306.0 | 0.0 |
| dk | 20 | 1 | 5887.4333 | 6.0 | 0.0 |
| dk | 20 | 2 | 5970.7333 | 6.0 | 0.0 |
| dk | 100 | 1 | 6199.9167 | 73.0 | 0.0 |
| dk | 100 | 2 | 6318.4167 | 72.0 | 0.0 |

Les deux répétitions sont sans erreur et sous 10 % de variation sur le débit et le p95 à chaque charge. La capacité constatée dépasse largement le débit applicatif. Il s’agit d’une borne basse de capacité du couple injecteur/proxy, pas d’un plafond isolé de Java. Le proxy VM peut limiter cette mesure.

Les calibrations VM utilisent le premier collecteur par interrogation, plus coûteux que le collecteur persistant utilisé pendant les campagnes applicatives. Les calibrations Docker utilisent Docker stats. Les métriques de l’injecteur sont conservées.

[Données et preuves](resultats/comparaison-20261026-152151/README.md). Les anciens essais restent disponibles et ne sont pas mélangés à cette campagne.

[Étalonnages historiques documentés par Rémi](etalonnage-historique.md).
