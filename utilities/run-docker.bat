@echo off
REM Quick start script for Google Drive MP3 Player - Windows

echo 🎵 Google Drive MP3 Player - Docker Quick Start
echo.

REM Check if Docker is running
docker info >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ❌ Docker is not running. Please start Docker Desktop and try again.
    exit /b 1
)

REM Build the image
echo 📦 Building Docker image...
docker build -t gdrive-bhajan-player:latest .

REM Stop existing container if running
docker ps -a | findstr gdrive-bhajan-player >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo 🛑 Stopping existing container...
    docker stop gdrive-bhajan-player 2>nul
    docker rm gdrive-bhajan-player 2>nul
)

REM Run the container
echo 🚀 Starting container...
docker run -d ^
    --name gdrive-bhajan-player ^
    -p 3099:3099 ^
    -v "%cd%\cache:/app/cache" ^
    --restart unless-stopped ^
    gdrive-bhajan-player:latest

echo.
echo ✅ Server is running!
echo.
echo 🌐 Open in browser: http://localhost:3099
echo.
echo 📋 Useful commands:
echo    docker logs -f gdrive-bhajan-player    # View logs
echo    docker stop gdrive-bhajan-player       # Stop server
echo    docker start gdrive-bhajan-player      # Start server
echo    docker restart gdrive-bhajan-player    # Restart server
echo.
