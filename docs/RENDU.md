# Dossier de rendu — Refuges

**Projet :** Refuges  
**Binôme :** Akrem SOUSSI et Rémi CORTIAL

**Rapport final :** [ouvrir le PDF de synthèse (22 pages)](rapport-final.pdf).

## Parcours de lecture

| Partie | Documents et preuves |
|---|---|
| 1 — Analyse et application | [Analyse](analyse.md), [annexe détaillée](analyse-detaillee.md), [démarche Figma](demarche-maquette-figma.md), [diagrammes](diagrams/README.md), [requêtes API](requetes.md), [tests](tests.md), [parcours illustrés](captures/parcours-application/README.md) |
| 2 — Machines virtuelles | [Procédure VM](../deploiement/PROCEDURE.md), [mesures et réseau](mesures.md), [archives OVA](../deploiement/OVA.md) |
| 3 — Docker | [Procédure Docker](../docker/PROCEDURE.md), [comparaison VM / Docker](comparaison.md), [preuves](preuves-docker/2026-10-26/README.md), [mesures de référence](synthese-mesures-remi.md) |
| 4 — JMeter | [Rapport de charge](rapport-charge.md), [24 essais et preuves](../charge/resultats/comparaison-20261026-152151/README.md), [étalonnage](../charge/etalonnage.md), [automatisation](../charge/comparaison/README.md) |

Le [guide principal](../LISEZMOI.md) présente le démarrage du projet. Le schéma et le peuplement SQL sont dans [donnees/](../donnees/). Le rapport final rassemble la démarche et les résultats ; les documents Markdown conservent les détails et les procédures.

## Organisation

- `docs/` : analyses, comparaisons, diagrammes et captures.
- `deploiement/` : configuration et procédure des machines virtuelles.
- `docker/` : configuration et procédure des conteneurs.
- `charge/` : plans JMeter, scripts, protocoles et résultats bruts.
- `client/`, `metier/`, `donnees/` : code des trois couches de l’application.
- `ova/` : archives VM et médias de démonstration conservés localement, hors historique Git.

Les trois OVA et leurs empreintes sont téléchargeables dans la [release GitHub du rendu](https://github.com/akremsoussi/myhike/releases/tag/rendu-2026-10-26). L’archive locale des médias de démonstration n’est pas jointe à cette release ; son utilisation est décrite dans la [procédure Docker](../docker/PROCEDURE.md).

## Résultats et limites

Le fonctionnement du prototype Figma a été confirmé par Rémi. Les 24 essais de charge, les six mesures de démarrage/repos et la [validation graphique JMeter](../charge/resultats/comparaison-20261026-152151/captures/README.md) sont réalisés. Les mesures de référence de Rémi comprennent également 60 consultations réussies.

Cinq paliers dépassent le seuil de répétabilité de 10 % : VM 5, 10 et 50 utilisateurs ; Docker 1 et 5 utilisateurs. Les différences de versions et de périmètre sont explicitées dans les rapports.

Les [résultats historiques](rapport-charge-historique-remi.md) restent disponibles pour la traçabilité. Les CSV, journaux techniques, configurations et empreintes sont conservés dans leur format d’origine ; les documents explicatifs sont en Markdown.
