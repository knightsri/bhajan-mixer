#!/bin/bash
# Quick start script for Google Drive MP3 Player

set -e

echo "🎵 Google Drive MP3 Player - Docker Quick Start"
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker and try again."
    exit 1
fi

# Build the image
echo "📦 Building Docker image..."
docker build -t gdrive-mp3-player:latest .

# Stop existing container if running
if docker ps -a | grep -q gdrive-mp3-player; then
    echo "🛑 Stopping existing container..."
    docker stop gdrive-mp3-player 2>/dev/null || true
    docker rm gdrive-mp3-player 2>/dev/null || true
fi

# Run the container
echo "🚀 Starting container..."
docker run -d \
    --name gdrive-mp3-player \
    -p 3099:3099 \
    -v "$(pwd)/cache:/app/cache" \
    --restart unless-stopped \
    gdrive-mp3-player:latest

echo ""
echo "✅ Server is running!"
echo ""
echo "🌐 Open in browser: http://localhost:3099"
echo ""
echo "📋 Useful commands:"
echo "   docker logs -f gdrive-mp3-player    # View logs"
echo "   docker stop gdrive-mp3-player       # Stop server"
echo "   docker start gdrive-mp3-player      # Start server"
echo "   docker restart gdrive-mp3-player    # Restart server"
echo ""
