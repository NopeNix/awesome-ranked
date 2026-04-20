@echo off
setlocal

REM Starts the local stack (builds images) and triggers scraper.

if "%SCRAPE_SOURCE_URL%"=="" set SCRAPE_SOURCE_URL=https://raw.githubusercontent.com/awesome-selfhosted/awesome-selfhosted/refs/heads/master/README.md
if "%SCRAPE_INTERVAL_HOURS%"=="" set SCRAPE_INTERVAL_HOURS=24
if "%SCRAPE_CONCURRENCY%"=="" set SCRAPE_CONCURRENCY=2

docker compose -f "C:\config\workspace\awesome-ranked\docker-compose.yml" up -d --build

endlocal
