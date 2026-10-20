#!/usr/bin/env bash
# ==============================================================================
# Refuges — Script de lancement complet en une seule commande (Développement)
# Lance automatiquement :
#   1. Le serveur MySQL local (service systemd utilisateur ou système)
#   2. Les migrations Alembic (schéma SQL à jour)
#   3. Le serveur métier FastAPI sur http://127.0.0.1:8000 (EMAIL_BACKEND=console)
#   4. Le client React / Vite sur http://localhost:5173
# ==============================================================================
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$ROOT_DIR/metier"
[ -d "$BACKEND_DIR" ] || BACKEND_DIR="$ROOT_DIR/backend"
FRONTEND_DIR="$ROOT_DIR/client"
[ -d "$FRONTEND_DIR" ] || FRONTEND_DIR="$ROOT_DIR/frontend"

# Chargement automatique de NVM si disponible (Node 24 LTS)
if [ -s "${HOME}/.nvm/nvm.sh" ]; then
  # shellcheck disable=SC1091
  source "${HOME}/.nvm/nvm.sh"
  nvm use 24 >/dev/null 2>&1 || true
fi

echo "=================================================================="
echo "  Refuges — Démarrage de l'application 3-tiers en local"
echo "=================================================================="

# 1. Vérification / démarrage de MySQL (port 3306)
if ! ss -tln 2>/dev/null | grep -q ':3306 '; then
  echo "[1/4] Démarrage du service MySQL local..."
  if systemctl --user list-unit-files 2>/dev/null | grep -q 'mysql-user.service'; then
    systemctl --user start mysql-user.service
  elif command -v sudo >/dev/null 2>&1; then
    sudo systemctl start mysql 2>/dev/null || sudo systemctl start mariadb 2>/dev/null || true
  fi
  sleep 2
else
  echo "[1/4] Serveur MySQL déjà actif sur le port 3306."
fi

# 2. Migrations Alembic
echo "[2/4] Vérification des migrations SQL (Alembic)..."
(
  cd "$BACKEND_DIR"
  .venv/bin/alembic upgrade head
)

# Nettoyage propre des processus enfants à l'arrêt (Ctrl+C)
BACKEND_PID=""
FRONTEND_PID=""
cleanup() {
  echo ""
  echo "Arrêt des serveurs Refuges..."
  [ -n "$FRONTEND_PID" ] && kill "$FRONTEND_PID" 2>/dev/null || true
  [ -n "$BACKEND_PID" ] && kill "$BACKEND_PID" 2>/dev/null || true
  wait 2>/dev/null || true
  echo "Application arrêtée proprement."
}
trap cleanup EXIT INT TERM

# 3. Démarrage du backend FastAPI
echo "[3/4] Démarrage de l'API FastAPI sur http://127.0.0.1:8000 ..."
(
  cd "$BACKEND_DIR"
  export EMAIL_BACKEND="${EMAIL_BACKEND:-console}"
  exec .venv/bin/uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
) &
BACKEND_PID=$!

# 4. Démarrage du frontend React / Vite
echo "[4/4] Démarrage du client React (Vite) sur http://localhost:5173 ..."
(
  cd "$FRONTEND_DIR"
  exec npm run dev -- --host 127.0.0.1 --port 5173
) &
FRONTEND_PID=$!

sleep 2
echo ""
echo "=================================================================="
echo "  Application Refuges prête !"
echo "  -> Interface Web (Client) : http://localhost:5173"
echo "  -> API REST & Swagger     : http://127.0.0.1:8000/docs"
echo "------------------------------------------------------------------"
echo "  Comptes de démonstration (mot de passe commun : refuges123) :"
echo "  - Utilisateur 1   : randonneur@refuges.local  (@randonneur)"
echo "  - Utilisateur 2   : alpiniste@refuges.local   (@alpiniste)"
echo "  - Admin classique : moderateur@refuges.local  (@moderateur)"
echo "  - Admin supérieur : remi@gmail.com            (@remi)"
echo "------------------------------------------------------------------"
echo "  Note : EMAIL_BACKEND=console est actif. Les liens de confirmation"
echo "  d'email et de réinitialisation de mot de passe s'affichent"
echo "  directement dans ce terminal."
echo "  Appuyez sur Ctrl+C pour tout arrêter."
echo "=================================================================="

wait

