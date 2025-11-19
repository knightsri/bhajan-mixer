@echo off
REM Bhajan Mixer - Windows Wrapper Script
REM Handles Docker build, run, and cleanup automatically

setlocal enabledelayedexpansion

REM ==========================================
REM Configuration
REM ==========================================
set IMAGE_NAME=bhajan-mixer
set OUTPUT_DIR=%CD%\output
set CONTAINER_NAME=bhajan-mixer-run
set CACHE_DIR=%CD%\.YTCACHE

REM ==========================================
REM Check if Docker is installed
REM ==========================================
docker --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker is not installed or not in PATH
    echo.
    echo Please install Docker Desktop from:
    echo https://www.docker.com/products/docker-desktop
    echo.
    pause
    exit /b 1
)

REM ==========================================
REM Check if Docker daemon is running
REM ==========================================
docker ps >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker daemon is not running
    echo.
    echo Please start Docker Desktop and try again
    echo.
    pause
    exit /b 1
)

REM ==========================================
REM Build Docker image if it doesn't exist
REM ==========================================
docker image inspect %IMAGE_NAME% >nul 2>&1
if errorlevel 1 (
    echo.
    echo [BUILD] Building Bhajan Mixer Docker image...
    echo This only happens once and may take a few minutes.
    echo.
    docker build -t %IMAGE_NAME% .
    if errorlevel 1 (
        echo.
        echo [ERROR] Failed to build Docker image
        pause
        exit /b 1
    )
    echo.
    echo [SUCCESS] Image built successfully!
    echo.
)

REM ==========================================
REM Create output directory if it doesn't exist
REM ==========================================
if not exist "%OUTPUT_DIR%" (
    mkdir "%OUTPUT_DIR%"
)

REM ==========================================
REM Create YouTube cache directory if it doesn't exist
REM ==========================================
if not exist "%CACHE_DIR%" (
    mkdir "%CACHE_DIR%"
)

REM ==========================================
REM Parse arguments to detect local directories and files
REM ==========================================
set VOLUME_MOUNTS=-v "%OUTPUT_DIR%":/app/output -v "%CACHE_DIR%":/app/.YTCACHE
set MOUNT_COUNT=0

REM Check each argument for local directory paths or files
set ARGS=
for %%a in (%*) do (
    set ARG=%%~a

    REM Check if it's a directory
    if exist "!ARG!\*" (
        REM It's a directory - mount it
        set /a MOUNT_COUNT+=1
        set "ABS_PATH=%%~fa"
        set VOLUME_MOUNTS=!VOLUME_MOUNTS! -v "!ABS_PATH!":/app/mount!MOUNT_COUNT!:ro
        REM Replace the argument with the container path
        set ARGS=!ARGS! /app/mount!MOUNT_COUNT!
    ) else if exist "!ARG!" (
        REM It's a file - mount it
        set /a MOUNT_COUNT+=1
        set "ABS_PATH=%%~fa"
        set VOLUME_MOUNTS=!VOLUME_MOUNTS! -v "!ABS_PATH!":/app/mount!MOUNT_COUNT!:ro
        REM Replace the argument with the container path
        set ARGS=!ARGS! /app/mount!MOUNT_COUNT!
    ) else (
        REM Not a local path - pass as-is (URL or flag)
        set ARGS=!ARGS! "!ARG!"
    )
)

REM ==========================================
REM Run the container
REM ==========================================
echo.
echo ========================================
echo   Bhajan Mixer
echo ========================================
echo.

docker run --rm --name %CONTAINER_NAME% %VOLUME_MOUNTS% %IMAGE_NAME% %ARGS%

set EXITCODE=%errorlevel%

echo.
if %EXITCODE% equ 0 (
    echo ========================================
    echo   Complete! Check output\ directory
    echo ========================================
) else (
    echo ========================================
    echo   Error occurred (exit code: %EXITCODE%)
    echo ========================================
)
echo.

exit /b %EXITCODE%
