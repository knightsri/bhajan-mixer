#!/bin/bash
# Bhajan Mixer - Linux/Mac Wrapper Script
# Handles Docker build, run, and cleanup automatically

set -e  # Exit on error

# ==========================================
# Configuration
# ==========================================
IMAGE_NAME="bhajan-mixer"
OUTPUT_DIR="$(pwd)/output"
CONTAINER_NAME="bhajan-mixer-run"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ==========================================
# Helper Functions
# ==========================================
error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# ==========================================
# Check if Docker is installed
# ==========================================
if ! command -v docker &> /dev/null; then
    error "Docker is not installed or not in PATH"
    echo ""
    echo "Please install Docker from:"
    echo "  Linux: https://docs.docker.com/engine/install/"
    echo "  Mac: https://www.docker.com/products/docker-desktop"
    echo ""
    exit 1
fi

# ==========================================
# Check if Docker daemon is running
# ==========================================
if ! docker ps &> /dev/null; then
    error "Docker daemon is not running"
    echo ""
    echo "Please start Docker and try again"
    echo ""
    exit 1
fi

# ==========================================
# Build Docker image if it doesn't exist
# ==========================================
if ! docker image inspect "$IMAGE_NAME" &> /dev/null; then
    echo ""
    info "Building Bhajan Mixer Docker image..."
    echo "This only happens once and may take a few minutes."
    echo ""
    
    if ! docker build -t "$IMAGE_NAME" .; then
        error "Failed to build Docker image"
        exit 1
    fi
    
    echo ""
    success "Image built successfully!"
    echo ""
fi

# ==========================================
# Create output directory if it doesn't exist
# ==========================================
mkdir -p "$OUTPUT_DIR"

# ==========================================
# Create and mount YouTube cache directory
# ==========================================
CACHE_DIR="$(pwd)/.YTCACHE"
mkdir -p "$CACHE_DIR"

# ==========================================
# Parse arguments to detect local directories and files
# ==========================================
VOLUME_MOUNTS="-v $OUTPUT_DIR:/app/output -v $CACHE_DIR:/app/.YTCACHE"
MOUNT_COUNT=0
ARGS=()

for arg in "$@"; do
    # Check if argument is a local directory path
    if [[ -d "$arg" ]]; then
        # It's a local directory - mount it
        MOUNT_COUNT=$((MOUNT_COUNT + 1))
        ABS_PATH="$(cd "$arg" && pwd)"
        VOLUME_MOUNTS="$VOLUME_MOUNTS -v $ABS_PATH:/app/mount$MOUNT_COUNT:ro"
        # Replace the argument with the container path
        ARGS+=("/app/mount$MOUNT_COUNT")
    elif [[ -f "$arg" ]]; then
        # It's a local file - mount it
        MOUNT_COUNT=$((MOUNT_COUNT + 1))
        ABS_PATH="$(cd "$(dirname "$arg")" && pwd)/$(basename "$arg")"
        VOLUME_MOUNTS="$VOLUME_MOUNTS -v $ABS_PATH:/app/mount$MOUNT_COUNT:ro"
        # Replace the argument with the container path
        ARGS+=("/app/mount$MOUNT_COUNT")
    else
        # Not a local path - pass as-is (URL or flag)
        ARGS+=("$arg")
    fi
done

# ==========================================
# Run the container
# ==========================================
echo ""
echo "========================================"
echo "  Bhajan Mixer"
echo "========================================"
echo ""

# Run docker with proper argument handling
docker run --rm --name "$CONTAINER_NAME" $VOLUME_MOUNTS "$IMAGE_NAME" "${ARGS[@]}"

EXITCODE=$?

echo ""
if [ $EXITCODE -eq 0 ]; then
    echo "========================================"
    echo "  Complete! Check output/ directory"
    echo "========================================"
else
    echo "========================================"
    echo "  Error occurred (exit code: $EXITCODE)"
    echo "========================================"
fi
echo ""

exit $EXITCODE
