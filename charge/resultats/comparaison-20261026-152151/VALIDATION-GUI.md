> Validation réalisée le 26 octobre 2026. Voir les [captures et résultats](captures/README.md). Les instructions ci-dessous permettent de la reproduire.

# Reproduire la validation graphique JMeter

Les contrôles positifs et négatifs en ligne de commande sont enregistrés dans `etapes/`. Ils ne remplacent pas les deux captures de l'interface demandées dans le sujet. L'accès de l'outil de contrôle Windows à Java a été refusé ; aucune capture artificielle n'a été produite.

À effectuer après les campagnes, avec un seul déploiement démarré :

1. Depuis PowerShell, lancer le script `validation-gui.ps1 -Cas positif` de ce dossier.
2. Dans JMeter, sélectionner `Validation GUI positif`, puis cliquer sur le triangle vert. Le plan fait une seule itération avec un utilisateur.
3. Vérifier les deux requêtes en vert (connexion et consultation), puis enregistrer une capture lisible dans `captures/validation-positive.png`.
4. Fermer JMeter, relancer le script avec `-Cas negatif`, sélectionner le résultat de connexion et afficher l'échec de l'assertion. Le mot de passe est volontairement incorrect.
5. Enregistrer la capture dans `captures/validation-negative.png`. Cet échec attendu démontre que le plan détecte une authentification refusée.

Ne pas lancer les captures pendant une campagne de charge. Ne pas présenter le contrôle négatif comme une panne de l'application.
