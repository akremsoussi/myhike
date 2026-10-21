# Campagnes JMeter Docker sous Windows

Le point d'entree est `charge/campagne.ps1`. Il execute les paliers
**1, 5, 10, 25, 50, 100** en CLI, deux fois par defaut. Les valeurs imposees
par le sujet sont distinctes : **10 s de montee puis 60 s mesurees**.
La duree du groupe vaut 72 s : 10 s de montee, 60 s de plateau, 2 s de marge.
Un marqueur execute avant la montee fixe l'origine de la mesure. La fenetre
retenue commence 1 s apres la fin de montee et dure exactement 60 s.
Les lignes de montee et le marqueur restent dans le brut, mais sont exclus de
la synthese et des rapports HTML. Les requetes sont selectionnees par leur
instant de depart ; leur temps de reponse complet est conserve.

## Avant de mesurer

- Arreter toutes les VMs du projet et les autres injecteurs JMeter.
- Utiliser le meme PC, les memes donnees et comptes, les memes ressources,
  le meme plan execute et les memes durees pour les deux deploiements.
- Fermer les applications inutiles ; noter tout ecart de configuration.
- Docker doit etre lance et `http://localhost:8080/api/health` doit repondre.
- Python 3 standard suffit. Le runtime fourni avec Codex est trouve
  automatiquement sur ce PC ; ailleurs passer `-Python chemin/python.exe`.

Verification sans charge ni effacement :

```powershell
cd D:\Myhike
powershell -NoProfile -ExecutionPolicy Bypass -File .\charge\campagne.ps1 -Mode Check
```

## Etalonnage (etape 16)

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\charge\campagne.ps1 -Mode Calibration -OtherDeploymentStopped
```

L'etalonnage vise `/index.html` sur Nginx, sans calcul metier, sans temporisation.
Il applique 20 puis 100 utilisateurs, deux fois (`-CalibrationUsers 20,100`
est modifiable depuis une session PowerShell). Augmenter ces valeurs si aucun
plafond n'est observe. Les mesures d'injecteur regroupent les
processus `java` du PC : fermer les autres applications Java pour les interpreter.
Verifier que le plafond soutenu depasse nettement le debit applicatif, que
l'injecteur ne sature pas et que les repetitions restent proches (ecart de
debit et p95 idealement inferieur a 10 %). Un fichier produit ne prouve pas
a lui seul que l'etalonnage est concluant. Ne pas presenter les anciens chiffres
du rapport d'etalonnage comme issus de cette nouvelle execution.

## Campagne Docker (etape 17)

**`-ResetDatabase` sauvegarde puis efface la base Docker avant chaque repetition.**
Les comptes/publications crees depuis le peuplement disparaissent de la base
active ; leur sauvegarde reste dans `.charge-backups/`, exclu de Git. Les fichiers
photo ne sont pas supprimes. Ne lancer cette option que sur l'environnement local
de test. Les fichiers SQL contiennent `SET NAMES utf8mb4`.

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\charge\campagne.ps1 -Mode Campaign -ResetDatabase -OtherDeploymentStopped
```

Chaque repetition commence par un controle positif (connexion et consultation)
et negatif (mauvais mot de passe). L'assertion controle aussi le cookie de session.
Un echec de validation interrompt la campagne. Les erreurs des paliers, elles,
sont conservees : elles constituent un resultat, notamment a saturation.
Le script borne chaque processus JMeter ; un depassement interrompt la campagne.
Les connexions TCP sont reutilisees entre iterations pour eviter l'epuisement
des ports Windows. Les cookies restent effaces avant chaque nouvelle connexion
applicative et les comptes CSV continuent de tourner. Cette option doit aussi
etre utilisee pour la campagne VM. Un `java.net.BindException` invalide la mesure.
Les captures GUI de validation demandees a l'etape 15 restent a realiser dans
JMeter, elles ne sont pas remplacees par les controles CLI.

## Fichiers produits et comparaison VM

Tous les bruts sont dans **`charge/resultats/`**, conformement au sujet :

```text
charge/resultats/
  dk-1-r1-<date>.csv
  dk-5-r1-<date>.csv
  ...
  dk-100-r2-<date>.csv
  dk-<date>/
    configuration.json
    plan-execute.jmx
    synthese.csv
    dk-*-plateau.csv
    dk-*-statistiques.csv
    dk-*-serveur.jsonl
    rapport-1-r1/index.html
    ...
```

Les futurs `vm-*.csv` du binome doivent aller dans ce meme dossier, sans ecraser
les `dk-*`. `-ResultsDirectory` permet d'indiquer explicitement un autre dossier
commun si le binome en choisit un. Chaque execution a un identifiant unique.
Les resultats ne sont ni committes ni pousses automatiquement.

`synthese.csv` contient nombre de requetes, erreurs, moyenne, mediane, p90, p95,
p99, debit et maximum d'utilisateurs actifs. Le debit de reference vaut
nombre de requetes dans la fenetre / 60 s. Le dashboard JMeter utilise sa propre
definition de l'intervalle et peut donc afficher un debit legerement different.

`*-serveur.jsonl` conserve les instants UTC, CPU/memoire/BlockIO par conteneur,
connexions MySQL et compteurs InnoDB, ainsi que CPU/memoire des processus Java.
Les compteurs disque sont cumulatifs : comparer leurs deltas sur la fenetre
indiquee dans la synthese. Les relevements MySQL ajoutent une connexion de mesure.
Les releves commencent avant JMeter : filtrer leurs instants sur cette meme
fenetre pour l'analyse du plateau. Un code de collecte non nul signale des
metriques manquantes ; ne pas les presenter comme des zeros.
`*-serveur-synthese.json` calcule automatiquement ces indicateurs sur la meme
fenetre que JMeter et fait echouer la campagne si la collecte est incomplete.

Les gros bruts d'etalonnage sont aussi conserves en `.csv.gz` (compression sans
perte, a versionner). Les CSV d'etalonnage non compresses et les CSV de plateau
derives restent disponibles localement mais sont exclus de Git, pour eviter
la limite de taille des fichiers GitHub. Les bruts applicatifs `dk-*.csv` restent
versionnables. `repetabilite.csv` donne les ecarts de debit et p95 entre repetitions.

La comparaison doit utiliser le meme `plan-execute.jmx`, fichier de comptes et
peuplement (empreintes dans `configuration.json`). Un plan VM different, une
autre temporisation, une montee incluse dans les chiffres ou une autre machine
invalident une comparaison directe. Les deux repetitions Docker ne remplacent
pas une deuxieme serie VM/Docker avec ordre inverse, demandee par le sujet.
Le temps de demarrage et la memoire au repos viennent des etapes 10/14.

Pour verifier specifiquement un palier instable, `-Users 50` execute uniquement
ce niveau, toujours avec deux repetitions et reinitialisation avant chaque serie.
Conserver ce controle sous son nouvel identifiant ; il ne remplace pas les six
paliers de la campagne principale, ni leurs donnees brutes.

## Arret anticipe

Depuis une autre fenetre PowerShell :

```powershell
& "$env:USERPROFILE\Downloads\apache-jmeter-5.6.3\bin\shutdown.cmd"
```

Une fenetre interrompue reste dans les bruts ; verifier la configuration et la
couverture de 60 s avant d'en utiliser les statistiques. Ne pas lancer les deux
deploiements ensemble, y compris pour aller plus vite.
