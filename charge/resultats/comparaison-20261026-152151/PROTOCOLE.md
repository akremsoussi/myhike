# Campagne VM / Docker

**Projet :** Refuges  
**Binôme :** Akrem SOUSSI et Rémi CORTIAL

Scénario : connexion avec cookie de session, puis consultation authentifiée de 20 refuges. Les assertions vérifient HTTP 200, contenu attendu et cookie. Un contrôle avec mot de passe volontairement incorrect doit échouer.

- Un seul déploiement actif ; Docker Desktop lui-même est arrêté pendant les essais VM.
- Même poste Windows, même code applicatif, mêmes SQL et comptes figés dans le dossier de campagne.
- Un CPU et 2 Gio maximum par couche : trois VM à 1 vCPU / 2 Gio et trois conteneurs avec les mêmes plafonds. Le système invité consomme une partie de la RAM des VM.
- Le fichier `plan-execute.jmx` est partagé par les deux déploiements ; aucune différence de scénario.
- JMeter 5.6.3 / Java 8u511, tas 1 Gio, G1GC, réutilisation TCP ; les cookies sont effacés à chaque itération. Temporisation originale conservée : 500 à 1 000 ms avant chaque requête.
- Six paliers : 1, 5, 10, 25, 50, 100 utilisateurs.
- Montée de 10 s. Fenêtre de mesure de 60 s, à partir de la fin du marqueur + 11 s. Durée du groupe 72 s. Les requêtes sont sélectionnées par leur heure de départ, et leur réponse complète reste comptée même après la fin de fenêtre.
- Deux séries en ordre inversé : VM r1, Docker r1, Docker r2, VM r2.
- Avant chaque campagne : sauvegarde SQL privée, recréation de la base à partir des mêmes fichiers, redémarrage MySQL et backend, contrôle nominal et contrôle d'échec.
- Après chaque palier : pause 10 s. Les erreurs et latences de saturation restent dans les données brutes.

## Relevés

Sur les VM, des lecteurs Python persistants lisent les compteurs cgroup du service toutes les 3 s ; cela évite de recréer Python et SSH pour chaque point. Les premières calibrations utilisent un collecteur par interrogation, plus coûteux : elles démontrent une borne conservatrice de débit disponible. La charge applicative utilise exclusivement le collecteur persistant.

CPU : pourcentage d'un cœur, donc 100 % correspond au plafond de chaque couche. Mémoire : mémoire du cgroup moins cache inactif ; la mémoire totale du système invité est relevée séparément. E/S : deltas des octets cgroup et InnoDB. Connexions MySQL : le relevé ajoute une connexion de surveillance. Les mesures Windows enregistrent aussi le CPU/RAM de Java et la mémoire libre du poste.

Les compteurs sont filtrés sur la même fenêtre de 60 s que JMeter. Une collecte manquante ne doit pas être remplacée par zéro. Les horodatages et journaux sont conservés.

## Étalonnage et répétabilité

Deux contrôles de la ressource statique `/index.html`, à 20 puis 100 utilisateurs, sans temporisation. Vérifier l'absence d'erreurs, la marge par rapport au débit applicatif et la faible consommation de l'injecteur. Si le proxy statique sature avant Java, le débit observé est une borne basse de capacité de l'injecteur, pas son plafond isolé.

Comparer les deux répétitions applicatives à chaque charge. Écart relatif = `(max - min) / moyenne × 100`. Les divergences supérieures à 10 % sont signalées ; elles ne sont pas masquées par une sélection du meilleur essai.

## Limites connues avant mesure

Les installations VM et Docker utilisent des versions différentes de Linux, Python, MySQL et Nginx. Les versions exactes sont archivées. La comparaison porte sur ces deux déploiements concrets, et ne permet pas d'attribuer tout écart uniquement à la virtualisation. Les limites CPU et RAM sont égales, mais le mode d'ordonnancement d'un vCPU et d'un quota Docker diffère.

Les résultats anciens de Rémi et les résultats Docker du 21 octobre sont conservés. Les nouvelles campagnes utilisent leur propre identifiant et ne remplacent aucun CSV ancien. Aucun résultat n'est inventé ou corrigé à la main.

Le démarrage complet et la mémoire au repos sont mesurés séparément, trois fois. Sous Windows, le démarrage Docker complet comprend son moteur Linux. Si sa RAM n'est pas accessible, cette limite est indiquée au lieu de présenter la seule somme des conteneurs comme la consommation totale.

Les captures GUI exigées par le sujet nécessitent un accès autorisé de l'outil de contrôle Windows à Java. Les contrôles CLI ne remplacent pas ces captures.
