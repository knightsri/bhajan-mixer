# Bhajan Mixer - Implementation Specification for Claude Code

## Project Overview

**Goal:** Build a Python-based CLI tool that intelligently combines audio/video content from multiple sources (YouTube URLs, playlists, local directories) using circular rotation algorithm.

**Primary Use Case:** Creating varied devotional music mixes from multiple sources to avoid listening repetition.

---

## Core Requirements

### 1. Command-Line Interface

**Entry Point:** `bhajan-mixer.py` (or installed as `bhajan-mixer` command)

**Syntax:**
```bash
bhajan-mixer [OPTIONS] <source1> <source2> ... <sourceN>
```

**Required Arguments:**
- `sources` (positional, variadic): One or more YouTube URLs, playlist URLs, or directory paths

**Optional Flags:**
```
--album <name>      Album/folder name for outputs (default: "run-1", auto-increment if exists)
--mp4out            Enable video output (MP4) in addition to audio (MP3)
--dry-run           Show what would be created without actually downloading/processing
--recurse           Scan directories recursively (default: false, only top-level)
```

**Examples:**
```bash
# Audio only from YouTube playlists
bhajan-mixer --album "Morning" https://youtube.com/playlist?list=PLxxx https://youtube.com/watch?v=yyyy

# Audio + video from mixed sources
bhajan-mixer --album "Visual" --mp4out https://youtube.com/playlist?list=PLxxx /local/music

# Dry run to preview
bhajan-mixer --dry-run --album "Test" <sources...>

# Recursive directory scan
bhajan-mixer --album "Deep" --recurse /music/root
```

---

## 2. Source Processing

### Source Types to Support

1. **YouTube Direct Video URL**
   - Pattern: `https://youtube.com/watch?v=VIDEO_ID` or `https://youtu.be/VIDEO_ID`
   - Treat as single-item playlist (repeats infinitely in rotation)

2. **YouTube Playlist URL**
   - Pattern: `https://youtube.com/playlist?list=PLAYLIST_ID`
   - Extract all video IDs from playlist
   - Handle private/deleted videos gracefully

3. **Local Directory**
   - Absolute or relative path to directory
   - Scan for `.mp3` and `.mp4` files
   - Ignore all other file types
   - Respect `--recurse` flag for subdirectories
   - Maintain alphabetical sort order

### Source Validation Rules

**For YouTube sources:**
- Use `yt-dlp` to extract metadata/download
- Skip videos that fail to download (private, deleted, geo-blocked)
- Report skipped videos to console
- If ALL videos in a playlist fail → remove entire source from rotation
- If direct video URL fails → remove that source from rotation

**For directory sources:**
- Verify path exists and is readable
- Count valid MP3/MP4 files
- If directory contains 0 valid files → remove source from rotation

**Critical Rule:** Only sources with ≥1 successfully retrieved file participate in rotation.

---

## 3. Circular Rotation Algorithm

### Core Logic

```python
# Pseudocode for rotation algorithm

sources = []  # List of Source objects, each with list of media files

# Get max length
max_length = max(len(source.files) for source in sources)

# Generate combined tracks
for track_num in range(1, max_length + 1):
    combined_audio = []
    combined_video = []
    
    for source_idx, source in enumerate(sources):
        # Circular index: wrap around when source exhausted
        file_idx = (track_num - 1) % len(source.files)
        media_file = source.files[file_idx]
        
        # Add to appropriate pipeline
        if media_file.has_audio:
            combined_audio.append(media_file.audio_path)
        if media_file.has_video and mp4out_enabled:
            combined_video.append(media_file.video_path)
    
    # Create combined track
    create_mp3(combined_audio, f"track-{track_num:02d}.mp3")
    if mp4out_enabled and combined_video:
        create_mp4(combined_video, f"track-{track_num:02d}.mp4")
```

### Key Points

- **Circular indexing:** Use modulo operator: `index = (iteration - 1) % source_length`
- **Independent pipelines:** MP3 and MP4 processing are separate
  - A source may contribute to MP3 but not MP4 (if no video)
  - Final MP3 count may differ from MP4 count
- **Track numbering:** Zero-padded to 2 digits minimum (`track-01.mp3`, `track-02.mp3`, etc.)

---

## 4. Audio Processing (MP3 Pipeline)

### Download/Extraction

**YouTube sources:**
```python
# Using yt-dlp
ydl_opts = {
    'format': 'bestaudio/best',
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'mp3',
        'preferredquality': '320',  # Best quality
    }],
    'outtmpl': 'downloads/%(id)s.%(ext)s',
}
```

**Directory sources:**
- Copy MP3 files to temp location for processing
- If only MP4 exists: extract audio using ffmpeg
  ```bash
  ffmpeg -i input.mp4 -vn -acodec libmp3lame -q:a 0 output.mp3
  ```

### Combination/Concatenation

Use `ffmpeg` concat demuxer or `pydub` for combining:

```python
# Using pydub (simpler)
from pydub import AudioSegment

combined = AudioSegment.empty()
for audio_file in audio_files:
    segment = AudioSegment.from_mp3(audio_file)
    combined += segment

combined.export(output_path, format="mp3", bitrate="320k")
```

### Metadata (ID3 Tags)

Use `mutagen` library for ID3v2 tags:

```python
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, TIT2, TALB, TPE1, TRCK

audio = MP3(output_file, ID3=ID3)

# Extract titles from source files
titles = []
for source_file in source_files:
    title = extract_title(source_file)  # From YouTube metadata or existing ID3
    if title:
        titles.append(title)

# Combine titles with bullet separator
combined_title = " • ".join(titles)

# If too long, use fallback
if len(combined_title) > 80:
    combined_title = f"Track {track_num:02d} (from {len(source_files)} sources)"

audio.tags.add(TIT2(encoding=3, text=combined_title))
audio.tags.add(TALB(encoding=3, text=album_name))
audio.tags.add(TPE1(encoding=3, text=combined_artists or "Various Artists"))
audio.tags.add(TRCK(encoding=3, text=f"{track_num}/{total_tracks}"))

audio.save()
```

**Artist handling:** Same as title - concatenate with " • ", skip if missing from source

---

## 5. Video Processing (MP4 Pipeline)

### Only When `--mp4out` Flag Present

**Download YouTube videos:**
```python
ydl_opts = {
    'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
    'outtmpl': 'downloads/%(id)s.%(ext)s',
}
```

### Normalization Required

All videos must be normalized before concatenation:
- **Resolution:** 1080p (1920x1080)
- **Framerate:** 30fps
- **Aspect ratio:** 16:9 (pad/crop if needed)

```bash
# Using ffmpeg for normalization
ffmpeg -i input.mp4 \
  -vf "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2,fps=30" \
  -c:v libx264 -preset medium -crf 23 \
  -c:a aac -b:a 192k \
  normalized.mp4
```

### Video Concatenation

```bash
# Create concat file
echo "file 'video1.mp4'" > concat.txt
echo "file 'video2.mp4'" >> concat.txt
echo "file 'video3.mp4'" >> concat.txt

# Concatenate
ffmpeg -f concat -safe 0 -i concat.txt -c copy output.mp4
```

### Video Pipeline Rules

- **Sources without video:** Skipped entirely in MP4 pipeline
- **Directory MP3 without matching MP4:** Not included in video output
- **MP4 without MP3 in directory:** Extract audio, include in both pipelines
- Final MP4 count may differ from MP3 count

---

## 6. Output Management

### Directory Structure

```
output/
├── {album-name}/
│   ├── track-01.mp3
│   ├── track-01.mp4  (if --mp4out)
│   ├── track-02.mp3
│   └── ...
├── {album-name}.1/   (if album-name exists)
└── {album-name}.2/   (if album-name.1 exists)
```

**Auto-incrementing:** If target folder exists, append `.1`, `.2`, etc.

### Cleanup Strategy

**Intermediate files to delete:**
- All downloaded YouTube videos/audio in temp directory
- Normalized video files (pre-concatenation)
- Extracted audio from MP4 sources
- Any temp files created during processing

**Keep only:**
- Final combined `track-NN.mp3` files
- Final combined `track-NN.mp4` files (if --mp4out)

**Implementation:** Use Python's `tempfile` module or explicit cleanup at end:
```python
import shutil
shutil.rmtree('downloads/')  # Remove entire temp directory
```

---

## 7. User Feedback (Console Output)

### Standard Run Output

```
🎵 Bhajan Mixer v1.0

📥 Processing 4 sources:
  ✓ YouTube Playlist (arg 1): 15/18 videos downloaded (3 failed, skipped)
  ✗ Direct URL (arg 2): Download failed - SKIPPING entire source
  ✓ Directory /music (arg 3): 8 MP3 files, 5 MP4 files found
  ✓ YouTube Playlist (arg 4): 22/22 videos downloaded

📊 Valid sources: 3 (1 source removed)
📊 MP3 pipeline: 3 sources (max length: 22) → Will create 22 audio tracks
📊 MP4 pipeline: 2 sources (max length: 22) → Will create 22 video tracks

🎼 Creating combined tracks:
  ✓ track-01.mp3 (A1 • B1 • C1)
  ✓ track-01.mp4 (combining 2 videos)
  ✓ track-02.mp3 (A2 • B2 • C2)
  ✓ track-02.mp4 (combining 2 videos)
  ...
  [████████████████████████] 22/22 complete

✅ Success!
   Output: output/Morning-Bhajans/
   Created: 22 MP3 files, 22 MP4 files
   
🗑️  Cleaned up 67 intermediate files
⏱️  Total time: 3m 42s
```

### Progress Indicators

- Show which source is being processed
- Progress during YouTube downloads (yt-dlp provides this)
- Progress bar for track creation
- Final summary with counts and timing

### Dry Run Output

```
🔍 DRY RUN MODE - No files will be created

📥 Would process 3 sources:
  ≈ YouTube Playlist (arg 1): ~18 videos (estimate)
  ≈ Directory /music (arg 2): Would scan for MP3/MP4 files
  ≈ YouTube Direct (arg 3): 1 video

📊 Estimated outputs:
   MP3 tracks: ~18 (depends on longest source)
   MP4 tracks: ~18 (if --mp4out enabled)

⚠️  NOTE: Actual counts may differ due to:
   • Failed downloads (private/deleted videos)
   • Invalid files in directories
   • Network issues

Output would be created in: output/Morning-Bhajans/

💡 Remove --dry-run flag to execute
```

---

## 8. Error Handling

### Graceful Degradation

**Principle:** Never crash - always provide best-effort results

**Handle these scenarios:**

1. **Individual video download fails:**
   - Log warning to console
   - Skip that video
   - Continue with remaining videos in playlist

2. **Entire source fails (0 valid files):**
   - Remove from rotation
   - Inform user
   - Continue with remaining sources

3. **All sources fail:**
   - Display error message
   - Exit gracefully with code 1

4. **FFmpeg errors during concatenation:**
   - Log error with details
   - Continue to next track (partial output acceptable)

5. **Disk space issues:**
   - Catch `OSError` during file writes
   - Display helpful error message
   - Clean up partial files

### Logging Strategy

Use Python's `logging` module:
```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(message)s'  # Clean output for users
)

# For debugging (optional --verbose flag)
if args.verbose:
    logging.basicConfig(level=logging.DEBUG)
```

---

## 9. Dependencies & Requirements

### Required Python Packages

```
# requirements.txt
yt-dlp>=2024.0.0
pydub>=0.25.1
mutagen>=1.47.0
ffmpeg-python>=0.2.0
```

### System Dependencies

- **ffmpeg:** Must be installed and in PATH
  - Ubuntu: `apt-get install ffmpeg`
  - macOS: `brew install ffmpeg`
  - Windows: Download from ffmpeg.org

### Python Version

- Minimum: Python 3.8
- Recommended: Python 3.10+

---

## 10. Docker Support

### Dockerfile Structure

```dockerfile
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY bhajan-mixer.py .

# Create volume mount point
VOLUME ["/app/output"]

# Set entrypoint
ENTRYPOINT ["python", "bhajan-mixer.py"]
```

### Docker Usage

```bash
# Build
docker build -t bhajan-mixer .

# Run with output volume
docker run -v $(pwd)/output:/app/output bhajan-mixer \
  --album "Test" \
  https://youtube.com/playlist?list=PLxxx

# Run with local music directory
docker run \
  -v $(pwd)/output:/app/output \
  -v $(pwd)/music:/app/music:ro \
  bhajan-mixer --album "Local" /app/music
```

---

## 11. Project Structure

```
bhajan-mixer/
├── bhajan-mixer.py          # Main entry point
├── requirements.txt         # Python dependencies
├── Dockerfile              # Docker configuration
├── README.md               # User documentation
├── LICENSE                 # MIT License
├── .gitignore             # Git ignore patterns
└── tests/                 # Unit tests (optional but recommended)
    ├── __init__.py
    ├── test_rotation.py
    ├── test_sources.py
    └── test_metadata.py
```

---

## 12. Implementation Priorities

**CRITICAL: Dockerfile and Wrapper Scripts Are Already Done!**

The following files are **already complete and provided**:
- ✅ `bhajan-mixer.bat` (Windows wrapper script)
- ✅ `bhajan-mixer.sh` (Linux/Mac wrapper script)
- ✅ `Dockerfile` (Docker configuration)

**You only need to create:**
- `bhajan-mixer.py` (main application)
- `requirements.txt` (Python dependencies)

**Development & Testing Approach:**

Every single test, from first hello-world to final production, must be done using the wrapper scripts:

```bash
# ALWAYS test this way (Windows)
bhajan-mixer.bat --album "Test" <sources>

# ALWAYS test this way (Linux/Mac)
./bhajan-mixer.sh --album "Test" <sources>

# NEVER run these commands directly:
# docker build ...   ❌ (wrapper does this)
# docker run ...     ❌ (wrapper does this)
# python script.py   ❌ (not how users will run it)
```

**Why this matters:**
- ✅ You test exactly what users will run
- ✅ No environment differences between dev and prod
- ✅ Wrapper handles all Docker complexity
- ✅ Instant feedback on real-world usage
- ✅ No surprises in deployment

---

### Phase 1: Core Audio Pipeline (MVP)

**Goal:** Get basic audio mixing working through wrapper scripts

**Create these files:**

1. **requirements.txt**
```
yt-dlp>=2024.0.0
pydub>=0.25.1
mutagen>=1.47.0
```

2. **bhajan-mixer.py** - Implement:
   - CLI argument parsing (`--album` flag and sources)
   - YouTube video/playlist download using yt-dlp (MP3, best quality)
   - Local directory scanning for MP3 files (top-level only)
   - Circular rotation algorithm (see section 3)
   - Audio concatenation using pydub
   - Basic console output showing progress
   - Automatic cleanup of intermediate files
   - Output to: `output/{album-name}/track-01.mp3`, etc.

**Testing Phase 1:**

```bash
# Test 1: Single YouTube video
./bhajan-mixer.sh --album "Test1" https://youtube.com/watch?v=VIDEO_ID

# Expected: output/Test1/track-01.mp3 exists and plays

# Test 2: Small playlist
./bhajan-mixer.sh --album "Test2" https://youtube.com/playlist?list=SMALL_LIST

# Expected: output/Test2/track-01.mp3 through track-NN.mp3

# Test 3: Rotation with multiple sources
./bhajan-mixer.sh --album "Test3" \
  https://youtube.com/watch?v=VIDEO1 \
  https://youtube.com/watch?v=VIDEO2 \
  https://youtube.com/watch?v=VIDEO3

# Expected: track-01.mp3 contains VIDEO1+VIDEO2+VIDEO3 combined

# Test 4: Local directory
./bhajan-mixer.sh --album "Test4" ~/Music/test-folder

# Expected: Combined MP3s from directory contents
```

**Phase 1 Complete When:** All 4 test scenarios work correctly through wrapper scripts.

---

### Phase 2: Metadata & Polish

**Goal:** Production-quality audio pipeline with rich metadata

**Add to bhajan-mixer.py:**
- ID3 tag generation using mutagen
  - Album: from `--album` flag
  - Track: "N/Total" format
  - Title: Concatenate source titles with " • " separator
  - Title fallback: "Track NN (from X sources)" if > 80 chars
  - Artist: Concatenate or "Various Artists"
- Album folder auto-increment (`Morning-Bhajans.1`, `.2`, etc.)
- `--dry-run` flag implementation
- `--recurse` flag for recursive directory scanning
- Enhanced console output with progress indicators
- Improved error handling with actionable messages

**Testing Phase 2:**

```bash
# Test metadata
./bhajan-mixer.sh --album "Metadata-Test" <sources>
# Check: MP3 files have correct ID3 tags

# Test dry-run
./bhajan-mixer.sh --dry-run --album "Preview" <sources>
# Check: Shows preview without downloading

# Test recurse
./bhajan-mixer.sh --album "Deep" --recurse ~/Music
# Check: Scans subdirectories

# Test auto-increment
./bhajan-mixer.sh --album "Same-Name" <sources>
./bhajan-mixer.sh --album "Same-Name" <sources>
# Check: Creates Same-Name/ and Same-Name.1/
```

**Phase 2 Complete When:** Metadata is correct, all flags work through wrapper scripts.

---

### Phase 3: Video Support

**Goal:** Add optional video mixing capability

**Add to bhajan-mixer.py:**
- `--mp4out` flag
- Video download from YouTube (best quality)
- Video normalization using ffmpeg
  - Resolution: 1080p (1920x1080)
  - Framerate: 30fps
  - Aspect ratio: 16:9 (pad if needed)
- Video concatenation
- Handle MP4-only sources (extract audio for MP3 pipeline)
- Independent MP3 and MP4 pipelines
- Report both audio and video track counts

**Testing Phase 3:**

```bash
# Test video output
./bhajan-mixer.sh --album "Video-Test" --mp4out <playlist-url>
# Check: Creates both track-NN.mp3 and track-NN.mp4

# Test mixed sources
./bhajan-mixer.sh --album "Mixed" --mp4out \
  <video-playlist> \
  ~/Music/audio-only \
  <single-video>
# Check: MP3 count may differ from MP4 count

# Test MP4 extraction
mkdir test-mp4 && cp some-video.mp4 test-mp4/
./bhajan-mixer.sh --album "Extract" test-mp4
# Check: Extracts audio from MP4, includes in rotation
```

**Phase 3 Complete When:** Video mixing works correctly through wrapper scripts.

---

### Phase 4: Final Polish

**Goal:** Production-ready with comprehensive error handling

**Improve bhajan-mixer.py:**
- All error messages are helpful and actionable
- Handle all edge cases gracefully
- Performance optimizations if needed
- Final testing with various combinations
- Code cleanup and documentation

**Testing Phase 4:**

```bash
# Test error scenarios
./bhajan-mixer.sh --album "Errors" https://invalid-url
./bhajan-mixer.sh --album "Empty" /nonexistent/path
./bhajan-mixer.sh --album "Private" <private-video-url>
# Check: Helpful error messages, no crashes

# Test large playlists
./bhajan-mixer.sh --album "Large" <100-video-playlist>
# Check: Progress shown, handles correctly

# Test mixed valid/invalid
./bhajan-mixer.sh --album "Mixed-Valid" \
  <valid-url> \
  <invalid-url> \
  <valid-dir>
# Check: Skips invalid, continues with valid sources
```

**Phase 4 Complete When:** All edge cases handled, production-ready.

---

## Critical Development Rules

### Rule 1: Always Test Through Wrapper Scripts

**RIGHT WAY:**
```bash
# Make code change to bhajan-mixer.py
# Test immediately
./bhajan-mixer.sh --album "Quick-Test" <source>
```

**WRONG WAY:**
```bash
# Make code change
docker build -t bhajan-mixer .     ❌ Don't do this manually
docker run ...                     ❌ Don't do this manually
python bhajan-mixer.py ...         ❌ Don't run Python directly
```

The wrapper script rebuilds the image automatically if Dockerfile or requirements changed. Just run the wrapper!

### Rule 2: Start Simple, Build Up

Phase 1 test progression:
1. Single YouTube video (simplest)
2. Small playlist (3-5 videos)
3. Multiple sources for rotation
4. Local directory
5. Mixed sources

Don't jump to complex scenarios until basics work.

### Rule 3: Verify Each Feature

After adding any feature:
1. Make the code change
2. Run wrapper script with test case
3. Check output exists and is correct
4. Check console messages are clear
5. Only then move to next feature

### Rule 4: Clean Rebuilds

If something seems wrong:

```bash
# Clean rebuild
docker rmi bhajan-mixer
./bhajan-mixer.sh --album "Fresh-Test" <source>
# Wrapper will rebuild from scratch
```

---

## Development Workflow Example

**Real example of building Phase 1:**

```bash
# 1. Create requirements.txt with dependencies
# 2. Create minimal bhajan-mixer.py with just argparse
# 3. Test argument parsing
./bhajan-mixer.sh --album "Args-Test" --help
# Should show help message

# 4. Add YouTube download capability
# 5. Test single video download
./bhajan-mixer.sh --album "Download-Test" https://youtube.com/watch?v=SHORT_VIDEO
# Should download and create track-01.mp3

# 6. Add playlist support
# 7. Test with small playlist
./bhajan-mixer.sh --album "Playlist-Test" https://youtube.com/playlist?list=SMALL_LIST
# Should download all videos

# 8. Add rotation algorithm
# 9. Test with 2 sources
./bhajan-mixer.sh --album "Rotation-Test" \
  https://youtube.com/watch?v=VIDEO1 \
  https://youtube.com/watch?v=VIDEO2
# track-01.mp3 should contain VIDEO1+VIDEO2

# 10. Add local directory support
# 11. Test with directory
./bhajan-mixer.sh --album "Dir-Test" ~/Music/test
# Should scan and combine MP3s

# Phase 1 done!
```

Notice: **Every single test** uses the wrapper script, never raw Docker or Python commands.

---

## Why This Approach Works

**Traditional approach (wrong):**
```
Local dev → Docker → Wrapper scripts → Production
         ↑ Environment   ↑ Complexity    ↑ Surprises!
         differences     added late      here
```

**Our approach (right):**
```
Wrapper scripts (Day 1) → More features → Production
                       ↑ No surprises    ↑ Just works!
                       Same environment throughout
```

By building and testing in Docker from the very beginning, using the wrapper scripts that users will actually run, you eliminate an entire class of problems before they can happen.

---

## 13. Testing Strategy

### Unit Tests (Recommended)

```python
# test_rotation.py
def test_circular_rotation_basic():
    sources = [
        ['A1', 'A2', 'A3'],  # 3 items
        ['B1'],              # 1 item
        ['C1', 'C2']         # 2 items
    ]
    expected = [
        ['A1', 'B1', 'C1'],  # Iteration 1
        ['A2', 'B1', 'C2'],  # Iteration 2
        ['A3', 'B1', 'C1'],  # Iteration 3 (C wraps)
    ]
    result = generate_rotation(sources)
    assert result == expected

def test_single_source_repeats():
    sources = [
        ['A1', 'A2', 'A3'],
        ['B1']
    ]
    # B1 should appear in all 3 outputs
    result = generate_rotation(sources)
    assert len(result) == 3
    assert all('B1' in iteration for iteration in result)
```

### Integration Tests

1. Test with real YouTube playlists (use small test playlists)
2. Test with sample MP3/MP4 files
3. Test dry-run mode
4. Test error scenarios (invalid URLs, empty directories)

---

## 14. Edge Cases to Handle

1. **Empty playlist:** Remove from rotation, inform user
2. **All sources fail:** Exit with error message
3. **Single source provided:** Still works (no rotation, just copies)
4. **Very large playlists (500+ videos):** Should work but may be slow
5. **Unicode in filenames/titles:** Handle properly in all paths
6. **Duplicate filenames in different directories:** Use unique temp names
7. **Disk space exhaustion:** Catch and report
8. **Network interruption during download:** Retry or skip gracefully
9. **Album name with special characters:** Sanitize for filesystem
10. **Source with only MP4 (no audio):** Extract audio, include in MP3 pipeline

---

## 15. Performance Considerations

### Optimization Opportunities

1. **Parallel downloads:** Use `concurrent.futures` for multiple YouTube downloads
2. **Streaming concatenation:** Don't load entire files into memory
3. **Incremental cleanup:** Delete intermediate files as soon as processed
4. **Progress caching:** Cache YouTube playlist metadata for --dry-run

### Resource Management

- **Disk space:** Monitor and warn if running low
- **Memory:** Use streaming for large file processing
- **Network:** Implement retry logic with exponential backoff

---

## 16. Future Enhancements (Not Required for v1.0)

- [ ] Resume interrupted downloads
- [ ] Playlist shuffle option
- [ ] Custom output formats (FLAC, WAV, etc.)
- [ ] Crossfade between tracks
- [ ] Volume normalization
- [ ] Silence trimming
- [ ] Batch mode (config file with multiple jobs)
- [ ] Web UI for easier operation
- [ ] Cloud storage integration (S3, Google Drive)

---

## Implementation Notes for Claude Code

### Key Architectural Decisions

1. **Modular design:** Separate concerns (download, process, combine, metadata)
2. **Configuration object:** Pass settings throughout rather than global variables
3. **Error recovery:** Use try/except liberally but intelligently
4. **User experience:** Console output is critical - make it informative and pretty

### Code Quality Guidelines

- Type hints where helpful
- Docstrings for non-obvious functions
- Keep functions focused and testable
- Use context managers (`with` statements) for file operations
- Validate inputs early (fail fast principle)

### Critical Success Factors

✅ **Must work correctly:** Rotation algorithm is core - test thoroughly  
✅ **Must be reliable:** Graceful error handling for all edge cases  
✅ **Must be clear:** User should always know what's happening  
✅ **Must be clean:** Automatic cleanup of intermediate files  

---

## Questions? Implementation Blockers?

This spec should provide everything needed to build Bhajan Mixer. If you encounter ambiguities or edge cases not covered here, make reasonable decisions that align with:

1. **User experience first:** Make it easy and predictable
2. **Fail gracefully:** Never crash, always inform
3. **Keep it simple:** Don't over-engineer
4. **Production quality:** Handle real-world messiness

**Ready to build!** 🚀
