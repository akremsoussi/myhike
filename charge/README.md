# Partie 4 - Injection de charge JMeter

**Campagne principale :** [24 essais du 26 octobre](resultats/comparaison-20261026-152151/README.md). [Index du rendu](../docs/RENDU.md). Les campagnes décrites ci-dessous sont conservées comme historique.

Point d'entrée des livrables, organisé selon les étapes 15 à 18 du sujet (pages 54 à 59).

| Étape | Livrable | Emplacement et état |
|---|---|---|
| 15 | Plan, comptes, captures de validation | [plan.jmx](plan.jmx), [comptes.csv](comptes.csv) ; [preuves CSV](resultats/dk-20261021-113529-649/) présentes, captures GUI encore à ajouter |
| 16 | Rapport court d'étalonnage | [etalonnage.md](etalonnage.md) : mesures, répétitions et réserves |
| 17 | Bruts et métriques serveur | [resultats/README.md](resultats/README.md), noms vm-*.csv et dk-*.csv conservés |
| 18 | Courbes, tableau, analyse de 3 à 4 pages | [rapport Markdown](../docs/rapport-charge.md), [rapport PDF de 4 pages](../docs/rapport-charge.pdf), [courbes](../docs/courbes/) |

## Lire les résultats

Les résultats sont organisés par déploiement, palier, répétition et session. La série VM historique et les deux séries Docker ne suivent pas encore un protocole identique : les écarts sont présentés avec leurs limites dans le rapport. Aucun résultat brut n'a été retouché pour rapprocher artificiellement les campagnes.

Les tableaux exploitables sont dans [resultats/synthese/](resultats/synthese/) : client par requête, serveur Docker et inventaire SHA-256. Le PDF est une édition paginée du rapport ; les CSV fournissent le détail.

## Reproduire les tirs

Voir [AUTOMATISATION.md](AUTOMATISATION.md) pour la campagne Docker. Les options de réinitialisation effacent la base après sauvegarde : elles servent à une nouvelle campagne, pas à mettre en forme les données existantes. Vérifier que l'autre déploiement est arrêté.

Le générateur `prepare_plan.py` ajoute notamment le repère temporel, la vérification du cookie et des timeouts. Le `plan-execute.jmx` archivé documente ce qui a réellement tourné ; le plan historique VM ne doit pas être décrit comme identique sans vérification.

## Compléments avant un rendu expérimental définitif

- Captures JMeter GUI : une itération réussie et une itération en échec (mot de passe erroné).
- Deux séries VM avec métriques serveur complètes, fenêtres de 60 s hors montée et configuration archivée.
- Séries VM/Docker sur un même poste, budgets équivalents et ordre inversé dans une même session.
- Contrôle de la variabilité à 50 utilisateurs ; périmètre commun pour démarrage et mémoire au repos.
