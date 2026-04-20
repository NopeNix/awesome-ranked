@echo off
setlocal

REM Downloads the published images from Docker Hub.

set TAG=%1
if "%TAG%"=="" set TAG=latest

docker pull nopenix/awesome-ranked-backend:%TAG% 
docker pull nopenix/awesome-ranked-frontend:%TAG%

endlocal
