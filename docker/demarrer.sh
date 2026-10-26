#!/usr/bin/env bash
set -euo pipefail
repo_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
project_name="${1:-refuges}"
cd "$repo_dir"
if [[ ! -f .env.docker ]]; then
  echo 'Créer .env.docker à partir de .env.docker.example et renseigner les mots de passe.' >&2
  exit 1
fi
if [[ "$(uname -s)" == Linux && "$EUID" -ne 0 ]]; then
  echo 'Sur Linux / WSL natif : utiliser sudo pour appliquer également le filtrage hôte.' >&2
  exit 1
fi
docker compose -p "$project_name" --env-file .env.docker -f docker/compose.yaml up -d --build --wait
if [[ "$(uname -s)" == Linux ]]; then
  python3 docker/isoler_hote.py --project "$project_name"
fi
echo 'Refuges disponible : http://localhost:8080'
