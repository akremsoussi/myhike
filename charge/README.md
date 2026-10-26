# Tests de charge JMeter

**Projet :** Refuges  
**Binôme :** Akrem SOUSSI et Rémi CORTIAL

## Campagne principale

La comparaison VM / Docker comprend 24 essais : six paliers (1, 5, 10, 25, 50 et 100 utilisateurs), deux répétitions par déploiement. Les conditions, résultats et limites sont décrits dans le [rapport de charge](../docs/rapport-charge.md).

- [Résultats bruts, courbes et tableaux](resultats/comparaison-20261026-152151/README.md).
- [Étalonnage](etalonnage.md).
- [Procédure d’automatisation](comparaison/README.md) et [protocole](comparaison/PROTOCOLE-COMPARE.md).
- [Captures de validation graphique](resultats/comparaison-20261026-152151/captures/README.md) : HTTP 200 en scénario nominal et HTTP 401 avec un mot de passe incorrect.

Cinq paliers dépassent 10 % de variation entre répétitions. Le rapport conserve ces résultats et explique les limites de comparaison.

## Historique

Les [campagnes antérieures](resultats/README.md), leur [automatisation Docker](AUTOMATISATION.md) et le [rapport historique de Rémi](../docs/rapport-charge-historique-remi.md) sont conservés pour la traçabilité. Les anciens tableaux de bord HTML générés ne sont pas inclus ; les données brutes restent disponibles.
