# Bhajan Mixer - Implementation Checklist

**Instructions for Claude Code:**
Work through this checklist systematically. After completing each item, mark it done and move to the next. Do not skip ahead - each step builds on previous ones.

---

## Phase 1: Core Audio Pipeline

### Setup
- [ ] **1.1** Read CLAUDE.md completely
- [ ] **1.2** Read IMPLEMENTATION_SPEC.md sections 2, 3, 4, 6, 7
- [ ] **1.3** Verify wrapper scripts exist (bhajan-mixer.bat, bhajan-mixer.sh)

### File Creation
- [ ] **1.4** Create requirements.txt with:
  - yt-dlp>=2024.0.0
  - pydub>=0.25.1
  - mutagen>=1.47.0

- [ ] **1.5** Create Dockerfile:
  - Base: python:3.11-slim
  - Install: ffmpeg via apt-get
  - Copy requirements.txt and install
  - Copy bhajan-mixer.py
  - Set working directory: /app
  - Create volume: /app/output
  - Entrypoint: python bhajan-mixer.py

### Core Implementation - bhajan-mixer.py

#### Argument Parsing
- [ ] **1.6** Implement argparse with:
  - `--album` flag (default: "run-1")
  - Positional variadic sources
  - Help text

#### Source Processing
- [ ] **1.7** Implement YouTube video download:
  - Use yt-dlp
  - Extract as MP3, best quality (320kbps)
  - Save to temp directory

- [ ] **1.8** Implement YouTube playlist handling:
  - Extract all video IDs
  - Download each as MP3
  - Handle failures gracefully (skip and report)

- [ ] **1.9** Implement directory scanning:
  - Find all .mp3 files in given directory
  - Top-level only (not recursive yet)
  - Alphabetical sort order

#### Rotation Algorithm
- [ ] **1.10** Implement Source class:
  - Store location (URL or path)
  - Store list of downloaded/found MP3 files
  - Validation methods

- [ ] **1.11** Implement circular rotation:
  - Calculate max_length = longest source
  - For each track_num (1 to max_length):
    - For each source: file_index = (track_num-1) % len(source)
    - Collect one file from each source
  - Return list of file combinations

#### Audio Concatenation
- [ ] **1.12** Implement combine_audio():
  - Use pydub AudioSegment
  - Load each MP3
  - Concatenate sequentially
  - Export as 320kbps MP3

#### Output Management
- [ ] **1.13** Implement output directory creation:
  - Base path: /app/output/{album_name}
  - Auto-increment if exists (.1, .2, etc.)
  - Create directory with proper permissions

- [ ] **1.14** Implement file naming:
  - Format: track-{num:02d}.mp3
  - Zero-padded 2 digits minimum

#### Cleanup
- [ ] **1.15** Implement temp file cleanup:
  - Delete all downloaded MP3s
  - Delete any other temp files
  - Keep only final combined tracks

#### Console Output
- [ ] **1.16** Implement progress reporting:
  - "Processing N sources" with details
  - Show which source (arg X) and status
  - Report skipped/failed items
  - Show valid source count
  - Show track count to create
  - Progress during creation
  - Final summary with location

### Testing Phase 1

**Test through wrapper scripts ONLY - never run docker/python directly!**

- [ ] **1.17** Test: Single YouTube video
  ```bash
  ./bhajan-mixer.sh --album "Test1" https://youtube.com/watch?v=dQw4w9WgXcQ
  ```
  - Verify: output/Test1/track-01.mp3 exists
  - Verify: File plays correctly
  - Verify: Temp files cleaned up

- [ ] **1.18** Test: Small YouTube playlist (3-5 videos)
  ```bash
  ./bhajan-mixer.sh --album "Test2" https://youtube.com/playlist?list=PLrAXtmErZgOeiKm4sgNOknGvNjby9efdf
  ```
  - Verify: Multiple track files created
  - Verify: Count matches playlist length
  - Verify: All files play

- [ ] **1.19** Test: Rotation with 2 video URLs
  ```bash
  ./bhajan-mixer.sh --album "Test3" \
    https://youtube.com/watch?v=VIDEO1 \
    https://youtube.com/watch?v=VIDEO2
  ```
  - Verify: track-01.mp3 contains VIDEO1+VIDEO2 combined
  - Verify: Both videos audible in sequence

- [ ] **1.20** Test: Local directory
  ```bash
  mkdir test-music
  cp ~/Music/song1.mp3 test-music/
  cp ~/Music/song2.mp3 test-music/
  ./bhajan-mixer.sh --album "Test4" test-music
  ```
  - Verify: Scans directory correctly
  - Verify: Creates combined tracks

- [ ] **1.21** Test: Mixed sources (3 different types)
  ```bash
  ./bhajan-mixer.sh --album "Test5" \
    https://youtube.com/watch?v=VIDEO \
    ~/Music/test \
    https://youtube.com/playlist?list=SMALL_LIST
  ```
  - Verify: Rotation works across all source types
  - Verify: Circular wrapping for shorter sources

- [ ] **1.22** Test: Error handling
  ```bash
  ./bhajan-mixer.sh --album "Test6" https://youtube.com/watch?v=INVALID
  ```
  - Verify: Helpful error message
  - Verify: No crash
  - Verify: Empty sources removed from rotation

- [ ] **1.23** Test: Album auto-increment
  ```bash
  ./bhajan-mixer.sh --album "Same" <source>
  ./bhajan-mixer.sh --album "Same" <source>
  ```
  - Verify: Creates Same/ and Same.1/

**Phase 1 Complete When:**
- All checklist items 1.1-1.23 are checked ✓
- All tests pass through wrapper scripts
- Code is clean and documented

---

## Phase 2: Metadata & Polish

### Metadata Implementation

- [ ] **2.1** Read IMPLEMENTATION_SPEC.md section 4 (Audio Processing - Metadata)

- [ ] **2.2** Implement title extraction:
  - From YouTube: Use yt-dlp metadata
  - From MP3: Use mutagen to read existing ID3
  - Fallback: Use filename

- [ ] **2.3** Implement title concatenation:
  - Join with " • " separator
  - If result > 80 chars: Use "Track NN (from X sources)" instead

- [ ] **2.4** Implement artist extraction:
  - Same sources as title
  - Join with " • " separator
  - Skip missing artists
  - Fallback: "Various Artists" if all missing

- [ ] **2.5** Implement ID3 tag writing:
  - Use mutagen library
  - Set: Album, Track (N/Total), Title, Artist
  - Apply to all output MP3s

### New Features

- [ ] **2.6** Implement --dry-run flag:
  - Parse argument
  - Show what would be created
  - Don't download or process
  - Display warning about accuracy

- [ ] **2.7** Implement --recurse flag:
  - Parse argument
  - Scan directories recursively when set
  - Default: false (top-level only)

### Console Output Enhancement

- [ ] **2.8** Add progress bars:
  - During downloads
  - During track creation
  - Use simple progress indicators

- [ ] **2.9** Improve error messages:
  - Make all errors actionable
  - Suggest solutions when possible
  - Use emojis for clarity (✓, ✗, ⚠️)

### Testing Phase 2

- [ ] **2.10** Test: Metadata on YouTube content
  ```bash
  ./bhajan-mixer.sh --album "Meta-Test" <playlist>
  ```
  - Verify: ID3 tags present and correct
  - Check: Album name matches
  - Check: Track numbers correct
  - Check: Titles concatenated with " • "

- [ ] **2.11** Test: Long titles (>80 chars)
  ```bash
  # Use sources with long titles
  ./bhajan-mixer.sh --album "Long-Titles" <sources-with-long-names>
  ```
  - Verify: Falls back to "Track NN (from X sources)"

- [ ] **2.12** Test: --dry-run flag
  ```bash
  ./bhajan-mixer.sh --dry-run --album "Preview" <sources>
  ```
  - Verify: Shows preview
  - Verify: No files created
  - Verify: No downloads happen

- [ ] **2.13** Test: --recurse flag
  ```bash
  mkdir -p deep/music/nested
  cp ~/Music/*.mp3 deep/music/nested/
  ./bhajan-mixer.sh --album "Deep" --recurse deep
  ```
  - Verify: Finds MP3s in subdirectories

- [ ] **2.14** Test: Album auto-increment still works
  ```bash
  ./bhajan-mixer.sh --album "Same" <source>
  ./bhajan-mixer.sh --album "Same" <source>
  ```
  - Verify: Creates Same/ and Same.1/

**Phase 2 Complete When:**
- All checklist items 2.1-2.14 are checked ✓
- Metadata is correct and rich
- All new flags work properly

---

## Phase 3: Video Support

### Video Infrastructure

- [ ] **3.1** Read IMPLEMENTATION_SPEC.md section 5 (Video Processing)

- [ ] **3.2** Implement --mp4out flag:
  - Parse argument
  - Enable video pipeline when set

- [ ] **3.3** Implement video download:
  - Use yt-dlp for best video quality
  - Download format: bestvideo+bestaudio/best
  - Save to temp directory

- [ ] **3.4** Implement video normalization:
  - Use ffmpeg to normalize all videos
  - Target: 1080p (1920x1080)
  - Framerate: 30fps
  - Aspect ratio: 16:9 (pad if needed)
  - See IMPLEMENTATION_SPEC section 5 for ffmpeg command

### Video Concatenation

- [ ] **3.5** Implement video concat:
  - Create concat demuxer file
  - Use ffmpeg to concatenate
  - Output: track-NN.mp4

- [ ] **3.6** Implement independent pipelines:
  - MP3 pipeline: Process all sources with audio
  - MP4 pipeline: Process only sources with video
  - Track counts may differ

### MP4 Handling

- [ ] **3.7** Handle MP4-only sources:
  - Detect MP4 files in directories
  - Extract audio using ffmpeg
  - Include in MP3 pipeline

- [ ] **3.8** Handle missing video:
  - Source with MP3 but no MP4: Skip in video pipeline
  - Report: Different MP3 vs MP4 track counts

### Testing Phase 3

- [ ] **3.9** Test: Video output basic
  ```bash
  ./bhajan-mixer.sh --album "Video-Test" --mp4out <youtube-video>
  ```
  - Verify: Creates both track-01.mp3 and track-01.mp4
  - Verify: Video is 1080p, 30fps
  - Verify: Video plays correctly

- [ ] **3.10** Test: Video playlist
  ```bash
  ./bhajan-mixer.sh --album "Video-List" --mp4out <playlist-url>
  ```
  - Verify: Multiple MP4s created
  - Verify: All normalized to same specs

- [ ] **3.11** Test: Mixed audio/video sources
  ```bash
  ./bhajan-mixer.sh --album "Mixed-AV" --mp4out \
    <video-playlist> \
    ~/Music/audio-only \
    <single-video>
  ```
  - Verify: MP3 count includes all sources
  - Verify: MP4 count only includes video sources

- [ ] **3.12** Test: MP4 extraction from directory
  ```bash
  mkdir test-mp4
  cp ~/Videos/video.mp4 test-mp4/
  ./bhajan-mixer.sh --album "Extract" test-mp4
  ```
  - Verify: Audio extracted from MP4
  - Verify: Included in rotation

- [ ] **3.13** Test: Console output shows both counts
  ```bash
  ./bhajan-mixer.sh --album "Counts" --mp4out <mixed-sources>
  ```
  - Verify: Reports "X audio tracks" and "Y video tracks"

**Phase 3 Complete When:**
- All checklist items 3.1-3.13 are checked ✓
- Video mixing works correctly
- Independent pipelines function properly

---

## Phase 4: Final Polish

### Error Handling

- [ ] **4.1** Review all error scenarios:
  - Invalid URLs
  - Network failures
  - Private/deleted videos
  - Empty directories
  - Permission issues
  - Disk space issues

- [ ] **4.2** Improve all error messages:
  - Make every error actionable
  - Suggest next steps
  - Use clear, friendly language

- [ ] **4.3** Add error recovery:
  - Retry failed downloads (max 3 attempts)
  - Graceful degradation
  - Never crash - always provide output if possible

### Edge Cases

- [ ] **4.4** Test: All sources fail
  ```bash
  ./bhajan-mixer.sh --album "All-Fail" \
    https://invalid-url \
    /nonexistent/path
  ```
  - Verify: Clear error message
  - Verify: Exit code non-zero
  - Verify: No crash

- [ ] **4.5** Test: Large playlist (50+ videos)
  ```bash
  ./bhajan-mixer.sh --album "Large" <large-playlist-url>
  ```
  - Verify: Progress shown clearly
  - Verify: Handles without issues
  - Verify: Performance acceptable

- [ ] **4.6** Test: Very long album names
  ```bash
  ./bhajan-mixer.sh --album "Very-Long-Album-Name-With-Many-Characters-That-Tests-Limits" <source>
  ```
  - Verify: Directory created successfully
  - Verify: No path length issues

- [ ] **4.7** Test: Special characters in album name
  ```bash
  ./bhajan-mixer.sh --album "Test/Album:Name" <source>
  ```
  - Verify: Special chars sanitized
  - Verify: Directory created successfully

- [ ] **4.8** Test: Concurrent runs (if relevant)
  ```bash
  # Start two runs simultaneously
  ./bhajan-mixer.sh --album "Run1" <source> &
  ./bhajan-mixer.sh --album "Run2" <source> &
  wait
  ```
  - Verify: No conflicts
  - Verify: Both complete successfully

### Performance

- [ ] **4.9** Profile slow operations:
  - Identify bottlenecks
  - Optimize if needed
  - Consider parallel downloads if very slow

### Documentation

- [ ] **4.10** Add inline code comments:
  - Document complex logic
  - Explain non-obvious choices
  - Add docstrings to functions

- [ ] **4.11** Verify README.md accuracy:
  - All examples work
  - All features documented
  - No outdated information

- [ ] **4.12** Verify SETUP.md accuracy:
  - Installation steps correct
  - Common issues covered
  - Troubleshooting helpful

### Final Validation

- [ ] **4.13** Run all Phase 1 tests again
- [ ] **4.14** Run all Phase 2 tests again
- [ ] **4.15** Run all Phase 3 tests again
- [ ] **4.16** Run edge case tests (4.4-4.8)

- [ ] **4.17** Test complete workflow:
  ```bash
  ./bhajan-mixer.sh --album "Final-Test" --mp4out --recurse \
    https://youtube.com/playlist?list=PLAYLIST1 \
    ~/Music/devotional \
    https://youtube.com/watch?v=VIDEO1
  ```
  - Verify: Everything works end-to-end
  - Verify: Output quality is excellent
  - Verify: Console output is clear
  - Verify: Error handling works

**Phase 4 Complete When:**
- All checklist items 4.1-4.17 are checked ✓
- All tests pass consistently
- Code is production-ready
- Documentation is accurate

---

## Final Sign-Off

- [ ] **5.1** All 4 phases complete (1-4)
- [ ] **5.2** All tests passing
- [ ] **5.3** No known bugs
- [ ] **5.4** Code is clean and commented
- [ ] **5.5** Documentation is accurate
- [ ] **5.6** Ready for users! 🎉

---

## Notes for Claude Code

**How to use this checklist:**

1. Start at Phase 1, item 1.1
2. Work through each item sequentially
3. Mark completed items with ✓
4. Do not skip ahead - each builds on previous
5. If test fails, fix and re-test before continuing
6. After completing a phase, announce completion before moving to next
7. Always test through wrapper scripts: `./bhajan-mixer.sh --album "Test" <sources>`

**When stuck:**
- Re-read CLAUDE.md
- Check IMPLEMENTATION_SPEC.md for details
- Review the specific section referenced in checklist item
- Ask for clarification if truly ambiguous

**Remember:**
- NEVER run `docker build/run` or `python` directly
- ALWAYS test through wrapper scripts
- Wrapper script IS the product
- Each phase builds working, testable software
