#!/usr/bin/env bash
set -euo pipefail

export SCRAPE_SOURCE_URL="${SCRAPE_SOURCE_URL:-https://raw.githubusercontent.com/awesome-selfhosted/awesome-selfhosted/refs/heads/master/README.md}"
export SCRAPE_INTERVAL_HOURS="${SCRAPE_INTERVAL_HOURS:-24}"
export SCRAPE_CONCURRENCY="${SCRAPE_CONCURRENCY:-2}"

docker compose -f /config/workspace/awesome-ranked/docker-compose.yml up -d --build
