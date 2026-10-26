# Validation graphique JMeter

**Projet :** Refuges  
**Binôme :** Akrem SOUSSI et Rémi CORTIAL

La validation est réalisée : connexion et consultation en HTTP 200, puis refus HTTP 401 avec un mot de passe incorrect. Voir les [captures et résultats](captures/README.md).

## Reproduire la validation

Démarrer un seul déploiement, hors campagne de charge.

1. Depuis PowerShell, lancer le script `validation-gui.ps1 -Cas positif` du dossier `charge/comparaison/`.
2. Dans JMeter, sélectionner `Validation GUI positif`, puis cliquer sur le triangle vert. Le plan fait une seule itération avec un utilisateur.
3. Vérifier les deux requêtes en vert (connexion et consultation), puis enregistrer une capture lisible dans `captures/validation-positive.png`.
4. Fermer JMeter, relancer le script avec `-Cas negatif`, sélectionner le résultat de connexion et afficher l'échec de l'assertion. Le mot de passe est volontairement incorrect.
5. Enregistrer la capture dans `captures/validation-negative.png`. Cet échec attendu démontre que le plan détecte une authentification refusée.

Ne pas lancer les captures pendant une campagne de charge. Ne pas présenter le contrôle négatif comme une panne de l'application.
