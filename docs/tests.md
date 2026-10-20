# Cahier de Recette et Tableau de Tests (Étape 6)

Ce document consigne les scénarios de test d'intégration de l'application Refuges, couvrant les parcours nominaux, les cas d'erreur aux limites et la vérification des règles de sécurité.

---

## 1. Tableau de Recette d'Intégration

| ID | Cas testé | Action réalisée | Résultat attendu | Résultat obtenu | Statut |
| :---: | :--- | :--- | :--- | :--- | :---: |
| **T01** | Connexion nominale | Saisie de `randonneur@refuges.local` + `refuges123` | Session ouverte, cookie positionné, redirection vers l'accueil | Session ouverte, nom affiché dans la barre | **VALIDÉ** |
| **T02** | Mot de passe erroné | Saisie d'un mot de passe incorrect | Refus HTTP 401, message « Identifiant ou mot de passe incorrect » | Erreur affichée sous le formulaire | **VALIDÉ** |
| **T03** | Compte inexistant | Saisie d'une adresse email inconnue | Refus HTTP 401 sans indication sur l'existence du compte | Même message générique de sécurité | **VALIDÉ** |
| **T04** | Compte suspendu | Connexion sur un compte dont `suspended_at` est renseigné | Refus HTTP 403, compte inaccessible | Message « Compte suspendu par un modérateur » | **VALIDÉ** |
| **T05** | Affichage carte et refuges | Déplacement de la carte sur le massif du Mont-Blanc | Requête géographique `/api/refuges/?bounds=...`, marqueurs affichés | Marqueurs interactifs et fiches refuges visibles | **VALIDÉ** |
| **T06** | Fiche refuge inexistante | Requête directe sur `/api/refuges/999999` | Erreur HTTP 404 Not Found | Message « Refuge introuvable » | **VALIDÉ** |
| **T07** | Création de sortie valide | Remplissage du formulaire + téléversement d'un GPX valide | Sortie créée (HTTP 201), distance et dénivelé calculés | Tracé sur la carte et profil altimétrique rendu | **VALIDÉ** |
| **T08** | Fichier GPX corrompu | Téléversement d'un fichier texte renommé en `.gpx` | Rejet HTTP 422 avec message explicite | Message d'erreur bloquant la soumission | **VALIDÉ** |
| **T09** | Cloisonnement des données utilisateur | Tentative d'accès aux paramètres de confidentialité d'un tiers | Impossible : l'API déduit l'identité uniquement de la session | Données du propriétaire uniquement affichées | **VALIDÉ** |
| **T10** | Modération par un Admin | Admin suspend un compte randonneur | Action autorisée (HTTP 200), utilisateur bloqué | Log de modération consigné et compte suspendu | **VALIDÉ** |
| **T11** | Tentative de suspension abusive | Admin tente de suspendre le Super Admin | Rejet HTTP 403 « Privilèges insuffisants » | Action bloquée par l'API métier | **VALIDÉ** |
| **T12** | Action privilégiée par un utilisateur | Randonneur tente d'appeler l'API de modération directement | Rejet HTTP 403 Forbidden | Accès refusé par le contrôleur de rôle | **VALIDÉ** |
| **T13** | Changement de couche cartographique | Clic sur les boutons de tuiles (OSM / IGN / Topo) | Basculement fluide des tuiles sans erreur JavaScript | Tuiles chargées avec attribution correcte | **VALIDÉ** |
