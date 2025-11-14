# Bhajan Mixer - Claude Code Project Context

## Project Overview

**What:** CLI tool that creates varied audio/video mixes by rotating through multiple YouTube playlists/videos and local music folders.

**Why:** For devotional music listeners who want variety without repetitive listening - combines sources in round-robin fashion.

**How:** Docker-based Python application with wrapper scripts for zero-friction user experience.

---

## Current Project State

### ✅ Complete (Provided)
- Dockerfile
- bhajan-mixer.bat (Windows wrapper script)
- bhajan-mixer.sh (Linux/Mac wrapper script)
- README.md (user documentation)
- SETUP.md (installation guide)
- IMPLEMENTATION_SPEC.md (full technical specification)

### 📝 To Build (Your Task)
- **bhajan-mixer.py** (main Python application)
- **requirements.txt** (Python dependencies)

---

## Architecture Summary

### User Experience Flow
```
User runs: ./bhajan-mixer.sh --album "Morning" <sources>
                    ↓
Wrapper script checks Docker and builds image (first time)
                    ↓
Runs Docker container with volume mounts
                    ↓
Container runs: python bhajan-mixer.py --album "Morning" <sources>
                    ↓
Downloads/processes media, creates combined tracks
                    ↓
Outputs to: output/Morning/track-01.mp3, track-02.mp3, ...
```

### Core Algorithm: Circular Rotation

**Example:**
- Source 1 (playlist): [A1, A2, A3, A4, A5] (5 videos)
- Source 2 (direct): [B1] (1 video, repeats)
- Source 3 (playlist): [C1, C2, C3] (3 videos, cycles)

**Output:**
- track-01.mp3: A1 + B1 + C1 (combined)
- track-02.mp3: A2 + B1 + C2 (combined)
- track-03.mp3: A3 + B1 + C3 (combined)
- track-04.mp3: A4 + B1 + C1 ← C cycles back
- track-05.mp3: A5 + B1 + C2 ← Done (longest source exhausted)

**Key points:**
- Shorter sources wrap around (circular indexing)
- Total tracks = length of longest source
- Each track is independent (not a continuous mix)

---

## Technical Stack

**Language:** Python 3.11+

**Key Dependencies:**
- `yt-dlp` - YouTube download (video/audio extraction)
- `pydub` - Audio manipulation and concatenation
- `mutagen` - ID3 tag metadata
- `ffmpeg` (system) - Video normalization and processing

**Deployment:** Docker container (provided)

**User Interface:** CLI via wrapper scripts (provided)

---

## Critical Development Rules

### Rule 1: Test Only Through Wrapper Scripts

**ALWAYS test this way:**
```bash
./bhajan-mixer.sh --album "Test" <sources>
```

**NEVER run these:**
```bash
docker build ...           ❌ Wrapper does this
docker run ...             ❌ Wrapper does this  
python bhajan-mixer.py ... ❌ Not how users run it
```

Why: The wrapper script IS the product. Testing any other way creates false confidence.

### Rule 2: Docker Configuration Is Fixed

The Dockerfile is already provided and complete:
- Python 3.11-slim base
- ffmpeg installed
- Requirements installed
- Entry point configured

**Don't modify the Dockerfile.** Just create the Python code it will run.

### Rule 3: Build in Phases

See IMPLEMENTATION_SPEC.md section 12 for detailed phases:
- Phase 1: Core audio mixing (YouTube + directories, rotation, basic output)
- Phase 2: Metadata & polish (ID3 tags, --dry-run, --recurse, better UX)
- Phase 3: Video support (--mp4out, normalization, MP4 concatenation)
- Phase 4: Final polish (error handling, edge cases)

---

## Phase 1 Requirements (Current Focus)

### Files to Create

**1. requirements.txt**
```
yt-dlp>=2024.0.0
pydub>=0.25.1
mutagen>=1.47.0
```

**2. bhajan-mixer.py** - Must implement:

**CLI:**
- Argument parsing: `--album <name>` and variadic sources
- Validate Docker environment variables if needed

**Source Processing:**
- YouTube video URL → download as MP3 (best quality)
- YouTube playlist URL → extract all video IDs, download each as MP3
- Local directory → scan for .mp3 files (top-level only in Phase 1)
- Skip and report any failed downloads

**Rotation Algorithm:**
```python
sources = [list of media files from each source]
max_length = max(len(source) for source in sources)

for track_num in range(1, max_length + 1):
    combined_audio = []
    for source in sources:
        file_index = (track_num - 1) % len(source)  # Circular!
        combined_audio.append(source[file_index])
    
    # Concatenate combined_audio into track-{track_num:02d}.mp3
    # Save to /app/output/{album_name}/track-{track_num:02d}.mp3
```

**Audio Concatenation:**
```python
from pydub import AudioSegment

combined = AudioSegment.empty()
for audio_file in audio_files:
    segment = AudioSegment.from_mp3(audio_file)
    combined += segment

combined.export(output_path, format="mp3", bitrate="320k")
```

**Output Management:**
- Create output directory: `/app/output/{album_name}/`
- If exists, auto-increment: `.1`, `.2`, etc.
- Delete all intermediate files (downloads, temp files)

**Console Output:**
```
🎵 Bhajan Mixer

📥 Processing 3 sources:
  ✓ YouTube Playlist (arg 1): 15/18 videos (3 failed)
  ✗ Direct URL (arg 2): Failed - SKIPPING
  ✓ Directory (arg 3): 8 MP3 files found

📊 Valid sources: 2
📊 Will create 15 tracks

🎼 Creating tracks: [progress indicator]

✅ Complete! Created 15 files in: output/Morning/
🗑️  Cleaned up 32 intermediate files
```

---

## Testing Phase 1

After creating the files, run these tests through wrapper scripts:

### Test 1: Single Video
```bash
./bhajan-mixer.sh --album "Test1" https://youtube.com/watch?v=dQw4w9WgXcQ
```
**Expected:** `output/Test1/track-01.mp3` exists and plays

### Test 2: Small Playlist
```bash
./bhajan-mixer.sh --album "Test2" https://youtube.com/playlist?list=PLrAXtmErZgOeiKm4sgNOknGvNjby9efdf
```
**Expected:** Multiple `track-NN.mp3` files, one per video

### Test 3: Rotation (2 sources)
```bash
./bhajan-mixer.sh --album "Test3" \
  https://youtube.com/watch?v=VIDEO1 \
  https://youtube.com/watch?v=VIDEO2
```
**Expected:** `track-01.mp3` contains VIDEO1+VIDEO2 combined

### Test 4: Local Directory
```bash
mkdir test-music
cp ~/Music/some-song.mp3 test-music/
./bhajan-mixer.sh --album "Test4" test-music
```
**Expected:** Scans directory and creates tracks

---

## Common Pitfalls to Avoid

### 1. Not Using Circular Indexing
```python
# WRONG - will crash when source exhausted
file = source[track_num]

# RIGHT - wraps around
file_index = (track_num - 1) % len(source)
file = source[file_index]
```

### 2. Not Cleaning Up Intermediate Files
Users will run this repeatedly. If you don't delete downloads, disk fills up fast.

### 3. Not Handling Failed Downloads Gracefully
YouTube videos fail for many reasons (private, deleted, geo-blocked). Skip them and continue.

### 4. Hardcoding Paths
```python
# WRONG - won't work in Docker
output = "/Users/me/output"

# RIGHT - use environment or defaults
output = os.getenv("OUTPUT_DIR", "/app/output")
```

### 5. Not Testing Through Wrapper Scripts
If you test with `python bhajan-mixer.py` directly, you're not testing the real deployment path.

---

## Docker Environment

**Working directory:** `/app`

**Volume mounts (handled by wrapper):**
- Host `./output` → Container `/app/output` (where tracks are saved)
- Host local directories → Container `/app/mountN` (read-only)

**Entry point:** `python bhajan-mixer.py` with args passed through

---

## Code Structure Suggestions

```python
# bhajan-mixer.py structure suggestion

import argparse
import os
from pathlib import Path
from typing import List
import yt_dlp
from pydub import AudioSegment

class Source:
    """Represents a media source (YouTube or directory)"""
    def __init__(self, location: str):
        self.location = location
        self.files: List[Path] = []
    
    def download_or_scan(self):
        """Download from YouTube or scan directory"""
        pass

def parse_args():
    """Parse command-line arguments"""
    pass

def create_output_dir(base_dir: str, album_name: str) -> Path:
    """Create output directory with auto-increment"""
    pass

def rotate_and_combine(sources: List[Source], output_dir: Path):
    """Main rotation algorithm"""
    max_length = max(len(s.files) for s in sources)
    
    for track_num in range(1, max_length + 1):
        audio_files = []
        for source in sources:
            idx = (track_num - 1) % len(source.files)
            audio_files.append(source.files[idx])
        
        output_file = output_dir / f"track-{track_num:02d}.mp3"
        combine_audio(audio_files, output_file)

def combine_audio(files: List[Path], output: Path):
    """Concatenate audio files"""
    pass

def cleanup_temp_files():
    """Remove all intermediate downloads"""
    pass

def main():
    args = parse_args()
    sources = [Source(loc) for loc in args.sources]
    
    # Download/scan all sources
    for source in sources:
        source.download_or_scan()
    
    # Filter out empty sources
    sources = [s for s in sources if len(s.files) > 0]
    
    # Create output directory
    output_dir = create_output_dir("/app/output", args.album)
    
    # Rotate and combine
    rotate_and_combine(sources, output_dir)
    
    # Cleanup
    cleanup_temp_files()

if __name__ == "__main__":
    main()
```

This is just a suggestion - implement however works best!

---

## Success Criteria for Phase 1

**Phase 1 is complete when:**

1. ✅ Both files created (requirements.txt, bhajan-mixer.py)
2. ✅ Wrapper script builds Docker image successfully
3. ✅ All 4 test scenarios pass:
   - Single video downloads and plays
   - Playlist creates multiple tracks
   - Rotation combines sources correctly
   - Local directory scanning works
4. ✅ Console output is clear and informative
5. ✅ Intermediate files are cleaned up
6. ✅ Handles failed downloads gracefully

**Then we move to Phase 2** (metadata, --dry-run, --recurse, better UX)

---

## Reference Documents

**For detailed specs:** Read IMPLEMENTATION_SPEC.md sections:
- Section 2: Source Processing
- Section 3: Circular Rotation Algorithm  
- Section 4: Audio Processing
- Section 6: Output Management
- Section 7: User Feedback
- Section 12: Implementation Priorities (detailed phase breakdown)

**For user requirements:** Read README.md to understand:
- What users expect
- How they'll use it
- What output should look like

---

## Getting Started

1. Read this file completely
2. Skim IMPLEMENTATION_SPEC.md (especially sections 2, 3, 4, 6, 7, 12)
3. **Open CHECKLIST.md** - this is your task-by-task guide
4. Start with Phase 1, item 1.1
5. Work through each checklist item sequentially
6. Mark items complete as you finish them
7. Test each item before moving to next

**The checklist approach:**
- 📋 CHECKLIST.md has every task broken down
- ✅ Check off items as you complete them
- 🔄 Work systematically through phases
- ⚠️ Don't skip ahead - each builds on previous

**Automated workflow:**
You can work through the entire checklist autonomously:
- Read each item
- Implement the requirement
- Test it (through wrapper script!)
- Mark it complete
- Move to next item
- Announce when each phase is complete

This means you can build all 4 phases without waiting for prompts between phases!

**Remember:** Every test must use the wrapper script. That's the product.

---

## Questions?

If anything is unclear:
1. Check IMPLEMENTATION_SPEC.md first (very detailed)
2. Check README.md for user perspective
3. Ask specific questions about ambiguous areas

You have complete specs - everything needed to build this is documented.

**Let's build something great! 🚀**
