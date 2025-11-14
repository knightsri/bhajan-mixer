# Bhajan Mixer - Complete Project Package

Complete specifications and scripts for building the Bhajan Mixer application.

## 📦 What's Included

### Core Documentation
- **CLAUDE.md** - Start here! Context file for Claude Code
- **IMPLEMENTATION_SPEC.md** - Complete technical specification  
- **README.md** - User documentation (what users will see)
- **SETUP.md** - Installation guide (for end users)

### Ready-to-Use Scripts
- **bhajan-mixer.bat** - Windows wrapper script ✅ Complete
- **bhajan-mixer.sh** - Linux/Mac wrapper script ✅ Complete

## 🚀 Quick Start with Claude Code

### Step 1: Read CLAUDE.md
This file contains everything Claude Code needs to know:
- Project overview and architecture
- Current state (what's done, what to build)
- Phase 1 requirements in detail
- Testing approach
- Common pitfalls to avoid

### Step 2: Give Claude Code This Instruction

```
Build Phase 1 of Bhajan Mixer.

Context: Read CLAUDE.md for full project overview.

Create these files:
1. requirements.txt - Python dependencies (yt-dlp, pydub, mutagen)
2. bhajan-mixer.py - Main application implementing Phase 1 features

Phase 1 Requirements (from CLAUDE.md):
- CLI argument parsing (--album flag and sources)
- YouTube video/playlist download (MP3, best quality)
- Local directory scanning for MP3 files
- Circular rotation algorithm
- Audio concatenation using pydub
- Basic console output
- Cleanup of intermediate files

Testing:
Every test must use the wrapper scripts:
  ./bhajan-mixer.sh --album "Test" <sources>

Never run docker or python commands directly - the wrapper script
is the product.

Dockerfile and wrapper scripts are already complete.
Focus on getting the core rotation algorithm working correctly.
```

### Step 3: Test Phase 1

```bash
# Single video
./bhajan-mixer.sh --album "Test1" https://youtube.com/watch?v=VIDEO_ID

# Rotation with 2 sources  
./bhajan-mixer.sh --album "Test2" \
  https://youtube.com/watch?v=VIDEO1 \
  https://youtube.com/watch?v=VIDEO2

# Local directory
./bhajan-mixer.sh --album "Test3" ~/Music/test-folder
```

### Step 4: Continue to Phase 2-4

See CLAUDE.md for Phase 2-4 details (metadata, video support, polish)

## 📖 File Guide

**For Claude Code:**
- Start with: **CLAUDE.md**
- Reference: **IMPLEMENTATION_SPEC.md** (sections 2,3,4,6,7,12)

**For Understanding the Product:**
- User perspective: **README.md**
- Setup flow: **SETUP.md**

**Already Complete:**
- **bhajan-mixer.bat** - Windows wrapper
- **bhajan-mixer.sh** - Linux/Mac wrapper
- **Dockerfile** - Mentioned in spec, will be created

## 🎯 Key Points

1. **Dockerfile and wrapper scripts are already done**
   - You only need to create: bhajan-mixer.py and requirements.txt

2. **Always test through wrapper scripts**
   - `./bhajan-mixer.sh --album "Test" <sources>`
   - Never run `docker build/run` or `python script.py` directly

3. **Build in phases**
   - Phase 1: Core audio (YouTube + directories + rotation)
   - Phase 2: Metadata (ID3 tags, --dry-run, --recurse)
   - Phase 3: Video (--mp4out, normalization, MP4 concatenation)
   - Phase 4: Polish (error handling, edge cases)

4. **Circular rotation is key**
   - Shorter sources wrap around infinitely
   - Total tracks = length of longest source
   - See CLAUDE.md for algorithm example

## ✅ Success Criteria

**Phase 1 complete when:**
- Wrapper script builds and runs successfully
- Single YouTube video downloads and creates track-01.mp3
- Playlist creates multiple tracks
- Rotation combines 2+ sources correctly
- Local directories scan and work
- Intermediate files are cleaned up
- Console output is clear

## 📁 Project Structure (After Build)

```
bhajan-mixer/
├── CLAUDE.md                  ✅ Provided
├── IMPLEMENTATION_SPEC.md     ✅ Provided
├── README.md                  ✅ Provided
├── SETUP.md                   ✅ Provided
├── bhajan-mixer.bat           ✅ Provided
├── bhajan-mixer.sh            ✅ Provided
├── Dockerfile                 📝 To create
├── requirements.txt           📝 To create
├── bhajan-mixer.py            📝 To create
└── output/                    (created at runtime)
    └── {album-name}/
        ├── track-01.mp3
        ├── track-02.mp3
        └── ...
```

## 🎵 What This Builds

**Smart audio/video mixer for devotional music**

Rotates through multiple YouTube playlists and local folders to create varied listening experiences without repetition.

Example:
```bash
./bhajan-mixer.sh --album "Morning" \
  https://youtube.com/playlist?list=HANUMAN \
  https://youtube.com/playlist?list=SHIVA \
  ~/Music/krishna-bhajans
```

Creates tracks that cycle through all three sources, ensuring variety!

---

**Ready to build? Start with CLAUDE.md! 🚀**
