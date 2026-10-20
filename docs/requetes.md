# Exemples de Requêtes HTTP — Couche Métier (Étape 4)

**Binôme :** Akrem SOUSSI & Rémi CORTIAL  
**Module :** DEV 1 — Application Trois-Tiers  

Ce document présente les requêtes `curl` exécutables directement contre la couche métier FastAPI (`http://127.0.0.1:8000/api`) ou à travers le reverse proxy Nginx (`http://localhost:8080/api`). Elles démontrent le fonctionnement nominal et le traitement des erreurs pour chaque exigence de l'étape 4 du cahier des charges.

---

## 1. Vérification de l'état du service et de la base de données

```bash
curl -s http://127.0.0.1:8000/api/health | jq
```
**Réponse (`HTTP/1.1 200 OK`) :**
```json
{
  "status": "ok",
  "database": "ok"
}
```

---

## 2. Authentification, Confirmation d'Email et Mot de Passe Oublié

### A. Connexion nominale d'un utilisateur classique (`200 OK`)
```bash
curl -i -X POST http://127.0.0.1:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "randonneur@refuges.local", "password": "refuges123"}' \
  -c user_cookies.txt
```
**Réponse (`HTTP/1.1 200 OK`) :**
- En-tête `Set-Cookie: refuges_session=...; HttpOnly; Path=/; SameSite=lax`
- Corps JSON :
```json
{
  "user": {
    "id": 3,
    "username": "randonneur",
    "display_name": "Lucas Randonneur",
    "email": "randonneur@refuges.local",
    "role": "user",
    "status": "active",
    "created_at": "2026-10-16T08:00:00+00:00"
  },
  "verification": null
}
```

### B. Échec d'authentification — Mot de passe erroné ou email inconnu (`401 Unauthorized`)
```bash
curl -i -X POST http://127.0.0.1:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "randonneur@refuges.local", "password": "mauvais-password"}'
```
**Réponse (`HTTP/1.1 401 Unauthorized`) :**
```json
{
  "detail": {
    "code": "invalid_credentials",
    "message": "Adresse email ou mot de passe incorrect."
  }
}
```

### C. Inscription et confirmation d'adresse email (`201 Created` puis `200 OK`)
```bash
# 1. Création d'un compte (statut initial : pending_email)
curl -i -X POST http://127.0.0.1:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "nouveau_rando",
    "email": "nouveau@refuges.local",
    "password": "refuges123",
    "accept_terms": true
  }'

# 2. Validation du jeton affiché dans la console du serveur (EMAIL_BACKEND=console)
curl -i -X POST http://127.0.0.1:8000/api/auth/verify-email \
  -H "Content-Type: application/json" \
  -d '{"token": "<JETON_AFFICHE_DANS_LA_CONSOLE>"}'
```

### D. Demande et confirmation de réinitialisation de mot de passe (`204 No Content`)
```bash
# 1. Demande d'un lien de réinitialisation (affiche le lien dans la console en dev)
curl -i -X POST http://127.0.0.1:8000/api/auth/password-reset \
  -H "Content-Type: application/json" \
  -d '{"email": "randonneur@refuges.local"}'

# 2. Application du nouveau mot de passe à l'aide du jeton reçu
curl -i -X POST http://127.0.0.1:8000/api/auth/password-reset/confirm \
  -H "Content-Type: application/json" \
  -d '{"token": "<JETON_RESET_CONSOLE>", "password": "refuges123"}'
```

---

## 3. Déduction de l'identité exclusivement depuis la session

Aucune route personnelle n'accepte d'identifiant utilisateur dans l'URL : le serveur résout l'utilisateur courant à partir du cookie `refuges_session`.

```bash
curl -s http://127.0.0.1:8000/api/auth/me -b user_cookies.txt | jq
```
**Sans cookie (Visiteur non connecté) :**
```bash
curl -i http://127.0.0.1:8000/api/auth/me
```
**Réponse (`HTTP/1.1 401 Unauthorized`) :**
```json
{
  "detail": {
    "code": "not_authenticated",
    "message": "Connectez-vous pour continuer."
  }
}
```

---

## 4. Consultation Cartographique et Fiches Refuges

### A. Recherche des refuges dans une emprise géographique (`bbox`)
```bash
curl -s "http://127.0.0.1:8000/api/refuges?bbox=6.0,44.7,6.6,45.1&guarded=true&limit=5" \
  -b user_cookies.txt | jq
```
**Réponse (`HTTP/1.1 200 OK`) :** renvoie `{"total": ..., "items": [...]}`.

### B. Fiche détaillée d'un refuge existant (`200 OK`) et inexistant (`404 Not Found`)
```bash
# Refuge existant
curl -i http://127.0.0.1:8000/api/refuges/1 -b user_cookies.txt

# Refuge inexistant -> 404 Not Found
curl -i http://127.0.0.1:8000/api/refuges/999999 -b user_cookies.txt
```
**Réponse pour un refuge inexistant (`HTTP/1.1 404 Not Found`) :**
```json
{
  "detail": {
    "code": "not_found",
    "message": "Ce refuge n'existe pas."
  }
}
```

---

## 5. Création d'une Sortie et Publication d'un Post

### A. Création d'une sortie de randonnée avec étapes et tracé (`201 Created`)
```bash
curl -i -X POST http://127.0.0.1:8000/api/outings \
  -b user_cookies.txt \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Ascension du Refuge du Glacier Blanc",
    "starts_at": "2026-11-15T07:30:00Z",
    "max_participants": 6,
    "visibility": "public",
    "stops": [
      {"name": "Pré de Madame Carle", "latitude": 44.918, "longitude": 6.415},
      {"name": "Point panoramique", "latitude": 44.928, "longitude": 6.405}
    ],
    "path": [[44.918, 6.415, 1874], [44.928, 6.405, 2542]]
  }'
```

### B. Publication d'un post avec trace GPX et calcul automatique de distance/dénivelé (`201 Created`)
```bash
curl -i -X POST http://127.0.0.1:8000/api/posts \
  -b user_cookies.txt \
  -H "Content-Type: application/json" \
  -d '{
    "body": "Magnifique montée matinale sur névé dur, crampons conseillés.",
    "visibility": "public",
    "path": [[44.918, 6.415, 1874], [44.923, 6.410, 2200], [44.928, 6.405, 2542]]
  }'
```

---

## 6. Contrôle d'Accès Hiérarchique : Utilisateur vs Admin Classique vs Super Admin

### A. Un utilisateur classique (`user`) tente d'accéder à la modération (`403 Forbidden`)
```bash
curl -i http://127.0.0.1:8000/api/moderation/dashboard -b user_cookies.txt
```
**Réponse (`HTTP/1.1 403 Forbidden`) :**
```json
{
  "detail": {
    "code": "forbidden",
    "message": "Réservé aux modérateurs."
  }
}
```

### B. Un Administrateur classique (`moderator`) suspend un utilisateur classique (`200 OK`)
```bash
# Connexion en tant qu'Admin classique (moderateur@refuges.local)
curl -s -X POST http://127.0.0.1:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "moderateur@refuges.local", "password": "refuges123"}' \
  -c mod_cookies.txt > /dev/null

# Suspension d'un utilisateur classique (@alpiniste) -> 200 OK
curl -i -X POST http://127.0.0.1:8000/api/moderation/users/alpiniste/suspend \
  -b mod_cookies.txt

# Réactivation immédiate (@alpiniste) -> 200 OK
curl -i -X POST http://127.0.0.1:8000/api/moderation/users/alpiniste/reactivate \
  -b mod_cookies.txt
```

### C. Un Administrateur classique tente de changer un rôle ou de suspendre le Super Admin (`403 Forbidden`)
```bash
# Tentative de promotion par un admin classique -> 403 Forbidden
curl -i -X PUT http://127.0.0.1:8000/api/moderation/users/alpiniste/role \
  -b mod_cookies.txt \
  -H "Content-Type: application/json" \
  -d '{"role": "moderator"}'

# Tentative de suspension du Super Admin (@remi) -> 403 Forbidden
curl -i -X POST http://127.0.0.1:8000/api/moderation/users/remi/suspend \
  -b mod_cookies.txt
```

### D. Le Super Administrateur (`super_admin`) promeut et rétrograde un modérateur (`200 OK`)
```bash
# Connexion en tant que Super Admin (remi@gmail.com)
curl -s -X POST http://127.0.0.1:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "remi@gmail.com", "password": "refuges123"}' \
  -c super_cookies.txt > /dev/null

# Promotion puis retour au rôle utilisateur -> 200 OK
curl -i -X PUT http://127.0.0.1:8000/api/moderation/users/alpiniste/role \
  -b super_cookies.txt \
  -H "Content-Type: application/json" \
  -d '{"role": "moderator"}'

curl -i -X PUT http://127.0.0.1:8000/api/moderation/users/alpiniste/role \
  -b super_cookies.txt \
  -H "Content-Type: application/json" \
  -d '{"role": "user"}'
```
