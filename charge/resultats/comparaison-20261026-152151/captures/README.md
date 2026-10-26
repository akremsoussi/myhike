# Validation graphique JMeter

Captures originales fournies par l’utilisateur le 26 octobre 2026, après exécution manuelle dans JMeter 5.6.3. Elles ne sont ni retouchées ni reconstituées.

| Cas | Connexion | Consultation | Preuve |
|---|---|---|---|
| Mot de passe correct | HTTP 200, succès | HTTP 200, succès | [Capture positive](validation-positive.png) |
| Mot de passe incorrect | HTTP 401, échec attendu | HTTP 401, accès refusé | [Capture négative](validation-negative.png) |

Compléments : [connexion nominale](validation-positive-connexion.png), [consultation refusée](validation-negative-consultation.png).

Les fichiers `gui-positif.xml` et `gui-negatif.xml` sont en réalité des **CSV**, malgré leur extension choisie par le listener JMeter. Leur contenu confirme les codes et états affichés. Le marqueur `__measurement_origin` est exclu de la validation des requêtes applicatives. Ces essais à un utilisateur ne sont pas ajoutés aux statistiques des campagnes de charge.
