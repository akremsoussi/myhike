# Nouvelles mesures VM / Docker - 26 octobre 2026

Les 24 essais de charge ont été exécutés et vérifiés : 1, 5, 10, 25, 50 et 100 utilisateurs, deux répétitions pour chaque déploiement. Les résultats historiques restent hors de ce dossier et ne sont pas modifiés. Dossier préparé pour publication GitHub avec les preuves de Rémi, qui restent dans leur dossier d’origine.

## À ouvrir d’abord

- [Rapport PDF de 4 pages](rapports/rapport-comparaison.pdf)
- [Rapport en Markdown](rapports/rapport-comparaison.md)
- [Synthèse des 24 essais](rapports/synthese.csv)
- [Répétabilité](rapports/repetabilite.csv)
- [Vérification des données brutes](rapports/verification-donnees.json)

## Classement

| Dossier ou fichier | Contenu |
|---|---|
| `bruts/charge/` | 24 CSV JMeter originaux, noms `vm-*` et `dk-*` |
| `bruts/etalonnage/` | 8 CSV d’étalonnage et leurs copies gzip sans perte |
| `etapes/` | Fenêtres de mesure, statistiques par requête, CPU/RAM/E/S/connexions, contrôles et journaux |
| `calibration/` | Statistiques et métriques des étalonnages |
| `graphiques/` | Courbes du débit, du p95 et des erreurs |
| `rapports/` | PDF, Markdown, tableaux CSV et vérification |
| `baseline-vm.json`, `baseline-dk.json` | Trois démarrages et mesures au repos par déploiement |
| `configuration.json`, `PROTOCOLE.md` | Paramètres figés, empreintes et limites |
| `automatisation/` | Copie des scripts de mesure et d’analyse, sans clé ni sauvegarde privée |
| `interrompu-sur-demande/` | Étalonnage interrompu lors de la pause demandée, exclu de l’analyse |
| `archives-documents/` | Anciennes versions des documents de synthèse |

## Points à ne pas masquer

Cinq paliers dépassent 10 % de variation sur le débit ou le p95 : VM 5, 10 et 50 utilisateurs ; Docker 1 et 5 utilisateurs. Les deux résultats restent publiés. Les versions logicielles diffèrent entre les déploiements.

Les captures GUI de validation restent à faire : le contrôle Windows a refusé l’accès à Java. Voir [les instructions](VALIDATION-GUI.md). Les contrôles CLI sont réalisés, mais ne remplacent pas ces captures.

Les sauvegardes SQL restent dans `D:\Myhike\.charge-backups`, hors du dossier de résultats. Les trois VM sont remises en service à la fin ; Docker Desktop est arrêté.

## Publication

Les huit bruts d’étalonnage sont versionnés en `.csv.gz` (décompression sans perte). Les CSV décompressés et les fenêtres de plateau restent locaux et sont dérivables. Les diagnostics interrompus et anciennes copies de documents restent locaux. Voir [le rendu](../../../docs/RENDU.md) et [les apports de Rémi](../../../docs/synthese-mesures-remi.md).
