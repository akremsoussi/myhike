# Cahier de Recette et Tableau de Tests (Étape 6)

**Binôme :** Akrem SOUSSI & Rémi CORTIAL  
**Module :** DEV 1 — Application Trois-Tiers  

Ce document consigne les scénarios de test d'intégration de l'application **Refuges**, couvrant les parcours nominaux, les cas d'erreur aux limites, la vérification des quatre niveaux d'acteurs et la suite de tests automatisés.

---

## 1. Tableau de Recette Fonctionnelle et d'Intégration

| ID | Acteur / Rôle | Cas testé | Action réalisée | Résultat attendu | Résultat obtenu | Statut |
| :---: | :--- | :--- | :--- | :--- | :--- | :---: |
| **T01** | Visiteur | Accès non authentifié à une page protégée | Navigation directe vers `/carte` ou `/profil` sans session | Redirection automatique vers `/connexion` ; `GET /api/auth/me` renvoie `401 Unauthorized` | Redirection vers `/connexion` et code `401` | **VALIDÉ** |
| **T02** | Visiteur | Inscription et confirmation par email | Inscription sur `/inscription`, lecture du lien dans la console, ouverture de `/confirmation-email?token=...` | Compte créé en `pending_email` (confiné sur `/inscription/confirmation`), puis passage à `active` après validation du jeton | Compte activé et redirection vers `/carte` | **VALIDÉ** |
| **T03** | Visiteur | Mot de passe oublié | Saisie de l'email sur `/mot-de-passe-oublie`, ouverture du lien `/mot-de-passe/nouveau?token=...`, saisie du nouveau mot de passe | Anciennes sessions révoquées, nouveau condensat Argon2id enregistré, connexion réussie avec le nouveau mot de passe | Mot de passe modifié et anciennes sessions invalidées | **VALIDÉ** |
| **T04** | Visiteur | Mot de passe erroné ou email inconnu | Saisie d'un mauvais mot de passe ou d'un email inexistant sur `/connexion` | Refus `HTTP 401` avec le même message générique « Adresse email ou mot de passe incorrect. » | Message d'erreur affiché sans fuite sur l'existence du compte | **VALIDÉ** |
| **T05** | Utilisateur (`user`) | Connexion nominale (`randonneur` & `alpiniste`) | Connexion avec `randonneur@refuges.local` ou `alpiniste@refuges.local` (`refuges123`) | Ouverture de session, barre de navigation à 3 onglets (*Carte*, *Communautés*, *Sorties*), aucun onglet *Modération* | Session active, interface utilisateur conforme | **VALIDÉ** |
| **T06** | Utilisateur (`user`) | Exploration de la carte et fiche refuge | Recherche et filtrage sur `/carte` (*Gardés*, *Non gardés*, *Avec sortie*), ouverture d'une fiche `/refuges/:id` | Marqueurs affichés par emprise `bbox`, fiche détaillée avec altitude, capacité, photos et sorties associées | 4 652 refuges interrogeables, fiche complète affichée | **VALIDÉ** |
| **T07** | Utilisateur (`user`) | Refuge inexistant | Navigation vers `/refuges/999999` | Réponse `HTTP 404 Not Found`, message « Ce refuge n'existe pas. » | Bandeau d'erreur explicite affiché | **VALIDÉ** |
| **T08** | Utilisateur (`user`) | Publication d'un post avec photo et trace GPX | Création d'un post sur `/posts/nouveau` avec image et fichier `.gpx` | Image convertie en WebP sans EXIF, distance et dénivelé positif calculés (`HTTP 201`) | Post affiché dans le fil de la communauté avec aperçu du tracé | **VALIDÉ** |
| **T09** | Utilisateur (`user`) | Création et participation à une sortie | Création d'une sortie sur `/sorties/nouvelle` par `randonneur`, puis inscription par `alpiniste` sur `/sorties/:id` | Sortie créée (`HTTP 201`), compteur de participants incrémenté, étapes et carte affichées | Sortie visible et participation enregistrée | **VALIDÉ** |
| **T10** | Utilisateur (`user`) | Demandes d'amis et confidentialité | Réglage de la confidentialité sur `/parametres/confidentialite` (ex. *Moi uniquement*) et consultation du profil par un tiers | Le profil tiers bascule sur l'écran `06b · Profil privé` lorsque les listes sont masquées | Respect strict des audiences (`everyone`, `friends`, `me`) | **VALIDÉ** |
| **T11** | Utilisateur (`user`) | Tentative d'accès à la modération | Saisie manuelle de `/moderation` ou appel `GET /api/moderation/users` par `randonneur` | Redirection vers `/carte` côté client et rejet `HTTP 403 Forbidden` côté API | Accès bloqué (client et serveur) | **VALIDÉ** |
| **T12** | Admin classique (`moderator`) | Accès à la modération et gestion des communautés | Connexion avec `moderateur@refuges.local` (`refuges123`), clic sur l'onglet *Modération*, création d'une communauté | Onglet *Modération* visible dans la Navbar, tableau de bord et gestion des communautés accessibles | Communauté créée et journalisée dans `moderation_logs` | **VALIDÉ** |
| **T13** | Admin classique (`moderator`) | Suspension d'un utilisateur et blocage de connexion | `moderateur` suspend le compte `alpiniste` depuis `/moderation/comptes` | Sessions actives d'`alpiniste` révoquées ; toute tentative de connexion d'`alpiniste` renvoie `403 Forbidden` (« Ce compte a été suspendu par la modération. ») | Déconnexion immédiate et reconnexion bloquée jusqu'à réactivation | **VALIDÉ** |
| **T14** | Admin classique (`moderator`) | Protection hiérarchique entre administrateurs | `moderateur` tente de promouvoir un utilisateur, ou de suspendre/supprimer un autre `moderator` ou le `super_admin` | Boutons désactivés dans l'interface et rejet `HTTP 403 Forbidden` par l'API métier | Action refusée avec message explicite | **VALIDÉ** |
| **T15** | Super Admin (`super_admin`) | Promotion et révocation de modérateurs | Connexion avec `remi@gmail.com` (`refuges123`), promotion d'un utilisateur en `moderator` puis rétrogradation en `user` | Seul `super_admin` dispose des boutons de changement de rôle actifs ; l'API applique le changement (`HTTP 200`) et trace l'action | Rôle mis à jour en temps réel et consigné dans le journal | **VALIDÉ** |

---

## 2. Suite de Tests Automatisés et Qualité du Code

En complément de la recette manuelle, le projet embarque une suite complète de tests d'intégration automatisés exécutée sur une base MySQL dédiée (`refuges_test`) :

- **Tests Backend (`pytest`) :** **Suite complète de tests automatisés passés à 100 %** (`tests/test_accounts.py`, `tests/test_communities.py`, `tests/test_discovery.py`, `tests/test_friends.py`, `tests/test_health.py`, `tests/test_media.py`, `tests/test_moderation.py`, `tests/test_outings.py`, `tests/test_password_reset.py`, `tests/test_refuge_photos.py`, `tests/test_refuges.py`).
- **Qualité Backend (`ruff check .`) :** **0 erreur, 0 avertissement**.
- **Compilation & Qualité Frontend (`npm run build && npm run lint`) :** Compilation TypeScript stricte (`tsc -b`), bundle de production Vite et linter `oxlint` (**0 erreur, 0 avertissement** sur 103 fichiers).

Pour relancer toute la suite de tests localement :
```bash
cd metier && .venv/bin/pytest && .venv/bin/ruff check .
cd ../client && npm run build && npm run lint
```
