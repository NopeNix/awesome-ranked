# awesome-ranked

Awesome-selfhosted GitHub metric snapshots.

## What it does

- Parses `awesome-selfhosted` README to collect GitHub repo URLs
- Scrapes GitHub metrics (stars, forks, watchers, repo created date, last commit, etc.)
- Stores metrics as time-series snapshots in Postgres
- Serves an interactive sortable table UI (light/dark follows system theme)

## Ports (default stack uses collision-safe ports)

- UI: `http://localhost:3001`
- API: `http://localhost:8001`
- Postgres: `localhost:5433`

## Requirements

- Docker + Docker Compose
- Optional: `GITHUB_TOKEN` (recommended; avoids rate limits)

## Run

```bash
export GITHUB_TOKEN="<token>"
docker compose -f /config/workspace/awesome-ranked/docker-compose.yml up -d --build
```

The scheduler runs a backfill and then refreshes based on `SCRAPE_INTERVAL_HOURS`.

## Environment variables

- `GITHUB_TOKEN` (optional)
- `SCRAPE_SOURCE_URL` (optional; default: awesome-selfhosted raw README)
- `SCRAPE_INTERVAL_HOURS` (optional; default: `24`)
- `SCRAPE_CONCURRENCY` (optional; default: `2`)

## API

- `GET /api/repos?sortBy=stars&order=desc&limit=50&offset=0`
- `GET /api/repos/:repo_id/snapshots?limit=200`

Sort keys supported by `/api/repos`:

- `stars`, `forks`, `watchers`, `contributors`, `commits`, `last_commit`, `created`

## Images

GitHub Actions builds and pushes:

- `nopenix/awesome-ranked-backend`
- `nopenix/awesome-ranked-frontend`

## Notes on “dev/commit counts”

- `contributors_count_approx`: best-effort GraphQL approximation (`repository.contributors.totalCount`)
- `commit_count_default_branch`: best-effort GraphQL approximation from default branch history `totalCount`
