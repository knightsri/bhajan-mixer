# Bhajan Mixer - Setup Guide

## Overview

Bhajan Mixer uses Docker for consistent deployment. **Wrapper scripts are included** that handle everything automatically - you just run them!

## Prerequisites

**Only requirement: Docker Desktop**
- **Windows:** [Docker Desktop for Windows](https://www.docker.com/products/docker-desktop)
- **Mac:** [Docker Desktop for Mac](https://www.docker.com/products/docker-desktop)
- **Linux:** [Docker Engine](https://docs.docker.com/engine/install/)

That's it! The wrapper scripts handle all Docker operations.

---

## Setup Steps

### 1. Get the Project

```bash
# Clone from GitHub
git clone https://github.com/yourusername/bhajan-mixer.git
cd bhajan-mixer

# Or download and extract ZIP
```

**You should see these files:**
```
bhajan-mixer/
├── bhajan-mixer.bat          ✅ Windows wrapper (included)
├── bhajan-mixer.sh           ✅ Linux/Mac wrapper (included)
├── Dockerfile                ✅ Docker config (included)
├── bhajan-mixer.py           📝 Main app (you'll build this)
├── requirements.txt          📝 Dependencies (you'll build this)
└── README.md
```

### 2. Make Script Executable (Linux/Mac Only)

```bash
chmod +x bhajan-mixer.sh
```

### 3. First Run

The wrapper script will automatically build the Docker image on first run.

**Windows:**
```bash
bhajan-mixer.bat --album "Test" https://youtube.com/watch?v=dQw4w9WgXcQ
```

**Linux/Mac:**
```bash
./bhajan-mixer.sh --album "Test" https://youtube.com/watch?v=dQw4w9WgXcQ
```

**What happens:**
1. ✅ Script checks Docker is installed and running
2. ✅ Script builds Docker image (takes 2-5 minutes first time only)
3. ✅ Downloads the video and converts to MP3
4. ✅ Creates `output/Test/track-01.mp3`

**All future runs are instant** - image is already built!

---

## Verify Installation

After first run:

```
output/
└── Test/
    └── track-01.mp3  ← Should exist and play
```

Play the MP3 to verify it worked!

---

## Common Setup Issues

### "Docker is not installed"

**Solution:** Install Docker Desktop:
- Windows/Mac: Download from docker.com
- Linux: Follow official Docker install guide

### "Docker daemon is not running"

**Solution:** 
- Windows/Mac: Open Docker Desktop application
- Linux: `sudo systemctl start docker`

### "Permission denied" (Linux)

**Solution:** Add your user to docker group:
```bash
sudo usermod -aG docker $USER
# Log out and back in for changes to take effect
```

### Script won't run (Linux/Mac)

**Solution:** Make it executable:
```bash
chmod +x bhajan-mixer.sh
```

---

## Usage Examples After Setup

### Simple Playlist Mix
```bash
# Windows
bhajan-mixer.bat --album "Morning" ^
  https://youtube.com/playlist?list=PLAYLIST1 ^
  https://youtube.com/playlist?list=PLAYLIST2

# Linux/Mac
./bhajan-mixer.sh --album "Morning" \
  https://youtube.com/playlist?list=PLAYLIST1 \
  https://youtube.com/playlist?list=PLAYLIST2
```

### Local Music + YouTube
```bash
# Windows
bhajan-mixer.bat --album "Combined" C:\Music https://youtube.com/playlist?list=PLxxx

# Linux/Mac
./bhajan-mixer.sh --album "Combined" ~/Music https://youtube.com/playlist?list=PLxxx
```

### With Video Output
```bash
# Windows
bhajan-mixer.bat --album "Visual" --mp4out ^
  https://youtube.com/playlist?list=PLxxx

# Linux/Mac
./bhajan-mixer.sh --album "Visual" --mp4out \
  https://youtube.com/playlist?list=PLxxx
```

---

## What Gets Created

### Project Structure
```
bhajan-mixer/
├── bhajan-mixer.bat          # Windows wrapper script
├── bhajan-mixer.sh           # Linux/Mac wrapper script
├── bhajan-mixer.py           # Main Python application
├── Dockerfile                # Docker configuration
├── requirements.txt          # Python dependencies
├── README.md                 # Documentation
├── SETUP.md                  # This file
└── output/                   # Created on first run
    ├── Album-Name-1/
    │   ├── track-01.mp3
    │   ├── track-02.mp3
    │   └── ...
    └── Album-Name-2/
        └── ...
```

### Docker Image (Automatic)
- Built automatically on first run
- Named: `bhajan-mixer`
- Size: ~500MB (includes Python, ffmpeg, dependencies)
- Only built once - reused for all future runs

---

## Updating Bhajan Mixer

When a new version is released:

```bash
# Pull latest code
git pull origin main

# Rebuild Docker image
docker build -t bhajan-mixer .

# Or just run - wrapper will rebuild if needed
```

---

## Troubleshooting

### Check Docker Status
```bash
docker ps
# Should show running containers (or empty if none running)
```

### Check Docker Images
```bash
docker images
# Should show 'bhajan-mixer' in the list
```

### Rebuild Image
```bash
docker rmi bhajan-mixer
# Then run wrapper script again - it will rebuild
```

### View Container Logs
```bash
docker logs bhajan-mixer-run
# Shows output from last run
```

### Clean Up Old Images
```bash
# Remove all unused images
docker image prune -a
```

---

## Getting Help

- **Issues:** [GitHub Issues](https://github.com/yourusername/bhajan-mixer/issues)
- **Discussions:** [GitHub Discussions](https://github.com/yourusername/bhajan-mixer/discussions)
- **Documentation:** See [README.md](README.md)

---

## Next Steps

✅ Setup complete! Now:

1. Read [README.md](README.md) for full usage guide
2. Try the example commands
3. Create your first real mix!

**Happy mixing! 🎵**
