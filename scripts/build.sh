#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

docker build -f "$ROOT/backend/Dockerfile" -t nopenix/awesome-ranked-backend:local "$ROOT/backend"
docker build -f "$ROOT/frontend/Dockerfile" -t nopenix/awesome-ranked-frontend:local "$ROOT/frontend"

echo "Built images:"
docker images | grep "awesome-ranked-" || true
