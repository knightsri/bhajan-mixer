# 🎵 Bhajan Mixer

**Intelligent audio/video playlist mixer for devotional content**

Create varied listening experiences by rotating through multiple YouTube playlists, videos, and local music collections. Perfect for devotional music (bhajans, kirtans) where you want variety without repetition.

## Features

- 🔄 **Smart Rotation**: Combines multiple sources in round-robin fashion
- 🎬 **Video Support**: Optional MP4 output with normalized quality
- 📁 **Flexible Input**: YouTube URLs, playlists, and local directories
- 🎼 **Rich Metadata**: Automatic ID3 tags with album, track, and title info
- 🚀 **Production Ready**: Docker support, error handling, progress tracking
- 🧹 **Clean Operation**: Automatic cleanup of intermediate files

## Quick Start

### Prerequisites
- **Docker Desktop** installed and running ([Get Docker](https://www.docker.com/products/docker-desktop))
- **Wrapper scripts** included in this repo (bhajan-mixer.bat for Windows, bhajan-mixer.sh for Linux/Mac)

### First Run

**Windows:**
```bash
# First time - automatically builds Docker image
bhajan-mixer.bat --album "Morning Bhajans" ^
  https://youtube.com/playlist?list=PLxxx ^
  https://youtube.com/watch?v=yyyy
```

**Linux/Mac:**
```bash
# Make script executable (first time only)
chmod +x bhajan-mixer.sh

# First run - automatically builds Docker image
./bhajan-mixer.sh --album "Morning Bhajans" \
  https://youtube.com/playlist?list=PLxxx \
  https://youtube.com/watch?v=yyyy
```

**The wrapper script handles everything:**
- ✅ Checks Docker is installed and running
- ✅ Builds the Docker image automatically (first run only)
- ✅ Mounts output directory and any local music folders
- ✅ Runs the container with proper arguments
- ✅ Shows clean progress and error messages

**You never need to run `docker build` or `docker run` manually!**

### More Examples

**With local directories:**
```bash
# Windows
bhajan-mixer.bat --album "Collection" C:\Users\You\Music

# Linux/Mac
./bhajan-mixer.sh --album "Collection" ~/Music
```

**Generate videos too:**
```bash
# Windows
bhajan-mixer.bat --album "Visual Bhajans" --mp4out ^
  https://youtube.com/playlist?list=PLxxx

# Linux/Mac
./bhajan-mixer.sh --album "Visual Bhajans" --mp4out \
  https://youtube.com/playlist?list=PLxxx
```

## Usage

### Basic Syntax

```bash
bhajan-mixer [OPTIONS] <source1> <source2> ... <sourceN>
```

### Options

| Option | Description | Default |
|--------|-------------|---------|
| `--album <name>` | Album name for output folder | `run-1`, `run-2`, etc. |
| `--mp4out` | Generate MP4 video files | Audio only |
| `--dry-run` | Preview without downloading | Execute normally |
| `--recurse` | Scan directories recursively | Top-level only |

### Source Types

**YouTube Playlists:**
```bash
bhajan-mixer --album "Devotional" \
  https://youtube.com/playlist?list=PLxxxxxxxxxxx
```

**YouTube Videos:**
```bash
bhajan-mixer --album "Singles" \
  https://youtube.com/watch?v=xxxxxxxxxxx \
  https://youtube.com/watch?v=yyyyyyyyyyy
```

**Local Directories:**
```bash
bhajan-mixer --album "My Music" \
  /path/to/music/folder1 \
  /path/to/music/folder2
```

**Mixed Sources:**
```bash
bhajan-mixer --album "Combined" \
  https://youtube.com/playlist?list=PLxxx \
  /path/to/local/music \
  https://youtube.com/watch?v=yyyy
```

## How It Works

### The Rotation Algorithm

Bhajan Mixer treats all sources as circular playlists and rotates through them:

**Example:**
```
Source 1 (Playlist): [A1, A2, A3, A4, A5]  (5 videos)
Source 2 (Direct):   [B1]                  (1 video, repeats)
Source 3 (Playlist): [C1, C2, C3]          (3 videos, cycles)

Output:
  track-01.mp3: A1 • B1 • C1
  track-02.mp3: A2 • B1 • C2
  track-03.mp3: A3 • B1 • C3
  track-04.mp3: A4 • B1 • C1  ← Source 3 cycles back
  track-05.mp3: A5 • B1 • C2  ← Process stops (longest source exhausted)
```

Total outputs = Length of longest source

### Video Processing (--mp4out)

When `--mp4out` is enabled:
- All videos normalized to 1080p, 30fps, 16:9 aspect ratio
- Sources without video are skipped in MP4 pipeline
- MP3 and MP4 pipelines run independently
- May produce different numbers of audio vs video files

### Metadata Generation

Each combined track gets rich metadata:

```
Track 01:
  Album: "Morning Bhajans"
  Track: 1/22
  Title: "Hanuman Chalisa • Om Namah Shivaya • Krishna Bhajan"
  Artist: "Various Artists"
```

If title exceeds 80 characters:
```
  Title: "Track 01 (from 3 sources)"
```

## Output Structure

```
output/
├── Morning-Bhajans/          # First run
│   ├── track-01.mp3
│   ├── track-02.mp3
│   └── ...
├── Morning-Bhajans.1/        # Second run (auto-incremented)
│   └── ...
└── Evening-Bhajans/          # Different album
    └── ...
```

## Example Workflows

### Morning Devotional Mix
```bash
bhajan-mixer --album "Morning Practice" \
  https://youtube.com/playlist?list=hanuman_chalisa \
  https://youtube.com/playlist?list=gayatri_mantra \
  https://youtube.com/playlist?list=morning_bhajans
```

### Visual Bhajans with Lyrics
```bash
bhajan-mixer --album "Visual Devotional" --mp4out \
  https://youtube.com/playlist?list=bhajans_with_lyrics \
  /local/music/deity-videos
```

### Personal Collection Mix
```bash
bhajan-mixer --album "My Favorites" --recurse \
  /music/shiva \
  /music/krishna \
  /music/devi
```

### Preview Before Processing
```bash
bhajan-mixer --dry-run --album "Test Mix" \
  https://youtube.com/playlist?list=PLxxx \
  /local/music
```

## Error Handling

Bhajan Mixer gracefully handles:
- ❌ **Failed downloads**: Skips and reports
- ❌ **Private/deleted videos**: Excludes from playlist count
- ❌ **Invalid URLs**: Skips entire source
- ❌ **Missing files**: Ignores non-MP3/MP4 files
- ❌ **Empty sources**: Removes from rotation

Console output keeps you informed:
```
📥 Processing 3 sources:
  ✓ YouTube Playlist (arg 1): 15/18 videos (3 failed)
  ✗ Direct URL (arg 2): Download failed - SKIPPING
  ✓ Directory (arg 3): 8 MP3s, 5 MP4s found
```

## Requirements

- Python 3.8+
- ffmpeg (system package)
- yt-dlp
- pydub or ffmpeg-python
- mutagen (for ID3 tags)

## Docker Support

**Dockerfile included** for production deployment:
- Pre-installed dependencies
- Volume mounts for output and local music
- Automatic cleanup of intermediate files
- Optimized for continuous operation

## Advanced Usage

### Recursive Directory Scanning
```bash
bhajan-mixer --album "Deep Collection" --recurse /music/root
```

Scans all subdirectories for MP3/MP4 files.

### Large Playlists
For playlists with 100+ videos:
- Progress bars show download status
- Intermediate files auto-cleaned
- Disk space managed efficiently

### Quality Settings
- **Audio**: Best available quality from YouTube
- **Video**: 1080p, 30fps, normalized aspect ratio
- **MP3**: Best quality extraction from MP4 sources

## Troubleshooting

### "Context limit exceeded" or similar
This is a YouTube issue, not Bhajan Mixer. Try:
- Breaking large playlists into smaller ones
- Using direct video URLs instead

### Videos fail to download
Common causes:
- Age-restricted content (can't be downloaded)
- Geographic restrictions
- Private/deleted videos

Solution: Bhajan Mixer automatically skips these and continues.

### Different MP3 vs MP4 counts
This is expected behavior when sources have different media availability:
- MP3 pipeline processes all audio sources
- MP4 pipeline only processes sources with video
- Final counts may differ

## Use Cases

✅ **Devotional Music**: Rotate bhajans from multiple artists/traditions  
✅ **Study Playlists**: Mix educational content from different sources  
✅ **Workout Mixes**: Combine multiple music styles for variety  
✅ **Meditation**: Create flowing ambient soundscapes  
✅ **Language Learning**: Rotate through different lesson sources  

## Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Submit a pull request

## License

MIT License - see LICENSE file for details

## Acknowledgments

Built with:
- [yt-dlp](https://github.com/yt-dlp/yt-dlp) - YouTube extraction
- [ffmpeg](https://ffmpeg.org/) - Media processing
- [mutagen](https://github.com/quodlibet/mutagen) - Metadata handling

---

**Made with 🙏 for the devotional community**

*Questions? Issues? Open a GitHub issue or discussion!*
