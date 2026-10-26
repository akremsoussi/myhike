# Comparaison locale VirtualBox / Docker

**Projet :** MyHike / Refuges  
**Binôme :** Akrem SOUSSI et Rémi CORTIAL

Cette automatisation est configurée pour ce PC : projet `D:\Myhike`, VM `D:\Myhike-VM`, VirtualBox `D:\virtualBox`, JMeter 5.6.3 dans les téléchargements. Les chemins sont déclarés au début de `campaign.py` et `control.py`.

## Campagne complète

Depuis PowerShell :

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File D:\Myhike\charge\comparaison\lancer-comparaison.ps1
```

Le script crée un nouveau dossier daté, conserve les anciens CSV, sauvegarde puis réinitialise la base **avant chacune des quatre séries**, applique un plafond de 1 CPU / 2 Gio par couche Docker et alterne les déploiements. Il arrête Docker Desktop pendant les essais VM. Il mesure les six paliers, deux fois chacun, puis trois démarrages et la mémoire au repos. Les fichiers SQL et le plan exécuté sont figés. Ne pas lancer une autre charge en parallèle.

Les sauvegardes SQL privées restent dans `D:\Myhike\.charge-backups`. La clé SSH reste dans `D:\Myhike-VM\installation\id_rsa` ; elle n'est pas copiée dans le dépôt. Les bibliothèques Python utilisées sont `paramiko`, `psutil`, `matplotlib` et `reportlab`.

Les CSV sont dans `charge/resultats/comparaison-<date>/bruts/charge/`, avec les noms `vm-<charge>-r<répétition>-<date>.csv` et `dk-...csv`. Les statistiques, journaux, métriques serveur, courbes, bilan de répétabilité et rapport sont dans `charge/resultats/comparaison-<date>/`.

## Arrêt sur erreur et reprise

Un échec d'installation, de collecte ou de contrôle stoppe l'automatisation. Un taux d'erreur applicatif élevé est un résultat de mesure, pas une raison de supprimer l'essai. Une récupération du backend après saturation a lieu uniquement entre campagnes et est consignée.

Ne pas relancer aveuglément une étape déjà produite : les CSV et sauvegardes existants sont protégés contre l'écrasement. Pour reprendre une campagne partielle, examiner les fichiers de `etapes/` et exécuter seulement les étapes manquantes avec `campaign.py vm|dk --rep 1|2`. Le chemin actif est indiqué dans `D:\Myhike-VM\installation\campagne-active.txt`.

Les captures de validation GUI restent manuelles si l'accès à Java est refusé par le contrôle Windows. Voir `VALIDATION-GUI.md` dans le dossier de la campagne du 26 octobre. Les contrôles CLI ne doivent pas être présentés comme ces captures.

## Portée des résultats

Les versions logicielles des deux déploiements sont différentes et archivées. Les répétitions qui dépassent 10 % de variation sont signalées, sans sélection du meilleur résultat. La mémoire au repos est relevée après les campagnes et redémarrages ; il s'agit de la somme des RSS des processus hôtes identifiés, avec le moteur Linux Docker lorsqu'il est accessible. Aucun envoi GitHub n'est effectué.
