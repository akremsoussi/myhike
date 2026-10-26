# Dossier de rendu - MyHike / Refuges

**Akrem SOUSSI et Rémi CORTIAL - 26 octobre 2026**

## Parcours de lecture

| Partie | Livrables et preuves |
|---|---|
| 1 - Analyse et application trois tiers | [Analyse PDF - 4 pages](analyse.pdf), [source Markdown](analyse.md), [annexe détaillée](analyse-detaillee.md), [démarche Figma](demarche-maquette-figma.md), [diagrammes](diagrams/README.md), [requêtes API](requetes.md), [recette](tests.md), [deux parcours illustrés](captures/parcours-application/README.md), [code et démarrage](../LISEZMOI.md) |
| 2 - Machines virtuelles | [Procédure VM](../deploiement/PROCEDURE.md), [références et réseau](mesures.md), [captures](captures/) |
| 3 - Conteneurs et comparaison | [Procédure Docker](../docker/PROCEDURE.md), [comparaison PDF - 2 pages](comparaison.pdf), [source Markdown](comparaison.md), [preuves Docker](preuves-docker/2026-10-26/README.md), [analyse des mesures intégrées](synthese-mesures-remi.md) |
| 4 - Charge JMeter | [Rapport PDF de 4 pages](rapport-charge.pdf), [rapport texte](rapport-charge.md), [dossier complet des 24 essais](../charge/resultats/comparaison-20261026-152151/README.md), [étalonnage](../charge/etalonnage.md), [automatisation](../charge/comparaison/README.md) |

Le schéma et le peuplement SQL sont dans [donnees/](../donnees/). Le lien Figma est dans [LISEZMOI.md](../LISEZMOI.md). Les diagrammes comprennent la base, les cas d'utilisation, les classes, la séquence de requêtes et l'architecture.

## Statut honnête du rendu

- **Figma :** accès au fichier en lecture sans connexion vérifié ; fonctionnement du prototype confirmé par Rémi le 26 octobre 2026. [Ouvrir la maquette](https://www.figma.com/design/KrPHETSktcZgtTbB9uxVyB/Refuges-%E2%80%93-Web-App?node-id=10-6). Depuis la session anonyme utilisée pour le contrôle, les commandes de présentation demandaient une connexion Figma.
- Les 24 essais de charge et les six mesures de démarrage/repos sont réalisés. Les CSV, statistiques, métriques serveur et courbes sont conservés.
- Les six relevés de référence fournis par Rémi ont été recalculés depuis leurs données brutes ; 60 consultations réussies sont vérifiées.
- Cinq paliers de charge dépassent le seuil de répétabilité de 10 % : VM 5, 10, 50 ; Docker 1, 5. Le rapport les signale ; le critère n'est pas déclaré satisfait partout.
- **Validation GUI JMeter réalisée :** connexion et consultation en HTTP 200, puis refus HTTP 401 avec mot de passe incorrect. [Captures et relevés](../charge/resultats/comparaison-20261026-152151/captures/README.md).
- Les trois archives OVA sont obligatoires et prêtes localement dans `ova/` (environ 2,88 Go). Elles sont exclues de Git et doivent être jointes séparément au rendu. Voir les [tailles, empreintes et instructions d’import](../deploiement/OVA.md). Le dépôt Git seul ne contient pas ces archives.

## Historique et reproductibilité

Les nouvelles mesures ne remplacent aucun ancien CSV de Rémi ou Docker. Le [rapport historique](rapport-charge-historique-remi.md) et les [synthèses historiques](../charge/resultats/synthese/) restent disponibles. Les différences de poste, versions, budgets et périmètres sont explicites.

Les sauvegardes privées, clés SSH et fichiers d'environnement locaux ne sont pas publiés. Les gros bruts d'étalonnage sont disponibles en `.csv.gz` sans perte ; les CSV de plateau sont dérivables et ne sont pas versionnés.
