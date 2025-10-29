@echo off
REM Docker Network Conflict Resolution Script for Horme POV
REM This script safely cleans up conflicting Docker resources

echo ==========================================
echo Docker Network Conflict Cleanup
echo ==========================================
echo.

echo [1/6] Stopping conflicting containers...
docker stop legalcopilot-frontend legalcopilot-backend legalcopilot-postgres legalcopilot-redis 2>nul
docker stop pickleball-app 2>nul
docker stop horme-redis horme-postgres 2>nul
echo     Containers stopped successfully

echo.
echo [2/6] Removing conflicting containers...
docker rm legalcopilot-frontend legalcopilot-backend legalcopilot-postgres legalcopilot-redis 2>nul
docker rm pickleball-app 2>nul
docker rm horme-redis horme-postgres 2>nul
echo     Containers removed successfully

echo.
echo [3/6] Removing conflicting networks...
docker network rm legalcopilot-network 2>nul
docker network rm horme_network 2>nul
echo     Networks removed successfully

echo.
echo [4/6] Pruning unused Docker resources...
docker system prune -f
docker network prune -f
echo     Cleanup completed

echo.
echo [5/6] Creating isolated networks with unique IP ranges...

REM Create network for Horme POV (172.30.0.0/16)
docker network create ^
  --driver bridge ^
  --subnet=172.30.0.0/16 ^
  --gateway=172.30.0.1 ^
  --opt com.docker.network.bridge.name=horme-br0 ^
  horme-isolated-network

REM Create network for LegalCopilot (172.31.0.0/16) 
docker network create ^
  --driver bridge ^
  --subnet=172.31.0.0/16 ^
  --gateway=172.31.0.1 ^
  --opt com.docker.network.bridge.name=legal-br0 ^
  legalcopilot-isolated-network

REM Create network for Pickleball (172.32.0.0/16)
docker network create ^
  --driver bridge ^
  --subnet=172.32.0.0/16 ^
  --gateway=172.32.0.1 ^
  --opt com.docker.network.bridge.name=pickleball-br0 ^
  pickleball-isolated-network

echo     Isolated networks created successfully

echo.
echo [6/6] Network configuration complete!
echo.
echo Networks created:
docker network ls | findstr "horme\|legal\|pickleball"
echo.
echo ==========================================
echo Cleanup completed successfully!
echo ==========================================
echo.
echo Next steps:
echo 1. Update your Docker Compose files to use the new networks
echo 2. Update port mappings to avoid conflicts
echo 3. Restart your services with: deploy-docker.bat start
echo.
pause