@echo off
setlocal enabledelayedexpansion

REM Builds backend and frontend images locally.

set ROOT=%~dp0..
set ROOT=%ROOT:/=\%

docker build -f "%ROOT%backend\Dockerfile" -t nopenix/awesome-ranked-backend:local "%ROOT%backend"
docker build -f "%ROOT%frontend\Dockerfile" -t nopenix/awesome-ranked-frontend:local "%ROOT%frontend"

echo Built images:
docker images | findstr awesome-ranked-

endlocal
