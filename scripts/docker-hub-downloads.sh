#!/usr/bin/env bash
set -euo pipefail

TAG="${1:-latest}"

docker pull "nopenix/awesome-ranked-backend:${TAG}" || true
docker pull "nopenix/awesome-ranked-frontend:${TAG}" || true
