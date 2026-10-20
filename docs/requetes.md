# Exemples de Requêtes API (Couche Métier)

Ce document fournit des exemples concrets de requêtes exécutables au format `curl` illustrant les fonctionnalités de la couche métier, les codes retours HTTP attendus, et la gestion stricte de l'authentification et des autorisations.

**URL de base de l'API :** `http://localhost:8000/api` (ou via le proxy `http://localhost:8080/api`).

---

## 1. Authentification et Session

### A. Connexion nominale (Randonneur)
```bash
curl -X POST http://localhost:8080/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"login": "randonneur@refuges.local", "password": "refuges123"}' \
  -c cookies.txt -i
```
**Réponse attendue :** `HTTP/1.1 200 OK`
- Le cookie de session `session` est positionné dans l'en-tête `Set-Cookie`.
- Le corps renvoie le profil utilisateur avec son rôle : `{"id": 3, "username": "randonneur", "role": "user", ...}`.

### B. Échec d'authentification (Mot de passe erroné)
```bash
curl -X POST http://localhost:8080/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"login": "randonneur@refuges.local", "password": "mauvais-password"}' \
  -i
```
**Réponse attendue :** `HTTP/1.1 401 Unauthorized`
```json
{
  "detail": {
    "code": "invalid_credentials",
    "message": "Identifiant ou mot de passe incorrect."
  }
}
```

---

## 2. Déduction de l'identité depuis la session

L'API ne requiert jamais l'identifiant utilisateur dans l'URL (`/api/users/3`) pour les actions personnelles : l'identité est systématiquement résolue à partir du cookie de session.

```bash
curl -X GET http://localhost:8080/api/users/me \
  -b cookies.txt -i
```
**Réponse attendue :** `HTTP/1.1 200 OK`
Renvoie les données du compte connecté (`randonneur`).

---

## 3. Consultation de la base de données (Refuges)

### A. Liste filtrée des refuges dans une zone géographique
```bash
curl -X GET "http://localhost:8080/api/refuges/?north=45.5&south=45.0&east=6.5&west=6.0" \
  -i
```
**Réponse attendue :** `HTTP/1.1 200 OK`
Renvoie un tableau JSON des refuges situés dans le secteur.

### B. Détail d'un refuge existant
```bash
curl -X GET http://localhost:8080/api/refuges/1 \
  -i
```
**Réponse attendue :** `HTTP/1.1 200 OK`

### C. Refuge introuvable
```bash
curl -X GET http://localhost:8080/api/refuges/999999 \
  -i
```
**Réponse attendue :** `HTTP/1.1 404 Not Found`
```json
{
  "detail": {
    "code": "not_found",
    "message": "Refuge introuvable."
  }
}
```

---

## 4. Création d'une sortie avec tracé GPX

```bash
curl -X POST http://localhost:8080/api/outings/ \
  -b cookies.txt \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Tour des Aiguilles Rouges",
    "description": "Superbe boucle avec étape au refuge.",
    "date": "2026-10-25T08:00:00Z",
    "visibility": "public"
  }' \
  -i
```
**Réponse attendue :** `HTTP/1.1 201 Created`

---

## 5. Contrôle des autorisations et Modération (403 Forbidden)

### A. Connexion en Administrateur
```bash
curl -X POST http://localhost:8080/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"login": "admin@refuges.local", "password": "refuges123"}' \
  -c admin_cookies.txt -i
```

### B. Suspension autorisée d'un utilisateur classique
```bash
curl -X POST http://localhost:8080/api/moderation/users/3/suspend \
  -b admin_cookies.txt \
  -H "Content-Type: application/json" \
  -d '{"reason": "Non respect des règles de la communauté."}' \
  -i
```
**Réponse attendue :** `HTTP/1.1 200 OK`

### C. Refus d'autorisation : un utilisateur classique tente une action modérateur
```bash
curl -X POST http://localhost:8080/api/moderation/users/2/suspend \
  -b cookies.txt \
  -H "Content-Type: application/json" \
  -d '{"reason": "Tentative frauduleuse"}' \
  -i
```
**Réponse attendue :** `HTTP/1.1 403 Forbidden`
```json
{
  "detail": {
    "code": "forbidden",
    "message": "Privilèges insuffisants pour effectuer cette action."
  }
}
```
