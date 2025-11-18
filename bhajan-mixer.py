#!/usr/bin/env python3
"""
Bhajan Mixer - Audio rotation and mixing tool
Combines multiple YouTube playlists/videos and local music folders using circular rotation
"""

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import List, Optional, Dict
import yt_dlp
from pydub import AudioSegment
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, TIT2, TALB, TPE1, TRCK

# YouTube cache directory (on host, persists between runs)
YTCACHE_DIR = Path('.YTCACHE')
CACHE_EXPIRY_HOURS = 24

# TODO: Future enhancement - implement retry logic for failed downloads
# MAX_DOWNLOAD_RETRIES = 3
# RETRY_DELAY_SECONDS = 2


def cleanup_old_cache():
    """Remove cached YouTube downloads older than CACHE_EXPIRY_HOURS"""
    if not YTCACHE_DIR.exists():
        return

    current_time = time.time()
    expiry_seconds = CACHE_EXPIRY_HOURS * 3600
    cleaned_count = 0

    for file in YTCACHE_DIR.glob('*.mp3'):
        file_age = current_time - file.stat().st_mtime
        if file_age > expiry_seconds:
            try:
                file.unlink()
                cleaned_count += 1
            except Exception:
                pass

    if cleaned_count > 0:
        print(f"  🗑️  Cleaned {cleaned_count} old cached file(s)")


class Source:
    """Represents a media source (YouTube URL or local directory)

    Attributes:
        location: YouTube URL or filesystem path
        source_index: Numeric index of this source (for debugging)
        files: List of audio files (MP3) from this source
        video_files: List of video files (MP4) from this source
        metadata: Mapping of file paths to metadata dicts {title, artist}
        failed_count: Number of failed downloads/scans
        source_type: Human-readable type (e.g., "YouTube Video", "Directory")
        cached_count: Number of files loaded from cache
    """

    def __init__(self, location: str, source_index: int):
        self.location = location
        self.source_index = source_index
        self.files: List[Path] = []  # Audio files (MP3)
        self.video_files: List[Path] = []  # Video files (MP4)
        self.metadata: Dict[Path, Dict[str, str]] = {}  # file -> {title, artist}
        self.failed_count = 0
        self.source_type = ""
        self.cached_count = 0

    def is_youtube_url(self, url: str) -> bool:
        """Check if string is a YouTube URL"""
        youtube_patterns = ['youtube.com', 'youtu.be']
        return any(pattern in url.lower() for pattern in youtube_patterns)

    def is_playlist_url(self, url: str) -> bool:
        """Check if YouTube URL is a playlist"""
        return 'list=' in url

    def download_or_scan(self, temp_dir: Path, recurse: bool = False, mp4out: bool = False, cookies: Optional[str] = None) -> bool:
        """Download from YouTube or scan directory. Returns True if successful."""
        if self.is_youtube_url(self.location):
            # Create subdirectory for this source to avoid file mixing
            source_temp_dir = temp_dir / f"source_{self.source_index}"
            source_temp_dir.mkdir(exist_ok=True)

            # Download audio (always)
            audio_success = self._download_youtube(source_temp_dir, cookies)

            # Download video if --mp4out flag is set
            if mp4out:
                video_success = self._download_youtube_video(source_temp_dir, cookies)
            else:
                video_success = False

            return audio_success or video_success
        else:
            return self._scan_directory(recurse=recurse, mp4out=mp4out)

    def _get_cached_file(self, video_id: str, temp_dir: Path) -> Optional[Path]:
        """Check if video is cached and copy to temp dir if found"""
        if not YTCACHE_DIR.exists():
            YTCACHE_DIR.mkdir(exist_ok=True)
            return None

        cache_file = YTCACHE_DIR / f"{video_id}.mp3"
        if cache_file.exists():
            # Check if cache is still valid (within expiry time)
            file_age = time.time() - cache_file.stat().st_mtime
            if file_age < (CACHE_EXPIRY_HOURS * 3600):
                # Copy from cache to temp dir
                dest_file = temp_dir / f"{video_id}.mp3"
                shutil.copy2(cache_file, dest_file)
                self.cached_count += 1
                return dest_file
            else:
                # Cache expired, delete it
                try:
                    cache_file.unlink()
                except Exception:
                    pass

        return None

    def _cache_file(self, video_id: str, temp_file: Path):
        """Copy downloaded file to cache"""
        if not YTCACHE_DIR.exists():
            YTCACHE_DIR.mkdir(exist_ok=True)

        cache_file = YTCACHE_DIR / f"{video_id}.mp3"
        try:
            shutil.copy2(temp_file, cache_file)
        except Exception:
            pass  # Don't fail if caching doesn't work

    def _download_youtube(self, temp_dir: Path, cookies: Optional[str] = None) -> bool:
        """Download YouTube video(s) as MP3, using cache when available"""
        is_playlist = self.is_playlist_url(self.location)
        self.source_type = "YouTube Playlist" if is_playlist else "YouTube Video"

        ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '320',
            }],
            'outtmpl': str(temp_dir / '%(id)s.%(ext)s'),
            'quiet': True,
            'no_warnings': True,
            'ignoreerrors': True,  # Skip unavailable videos
        }

        # Add cookies if provided
        if cookies:
            ydl_opts['cookiefile'] = cookies

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # Extract info first to get video list
                info = ydl.extract_info(self.location, download=False)

                if info is None:
                    return False

                # Handle playlist vs single video
                if 'entries' in info:
                    # It's a playlist
                    videos = [entry for entry in info['entries'] if entry is not None]
                    total_videos = len(videos)

                    # Download each video (or use cache)
                    for entry in videos:
                        try:
                            video_id = entry.get('id')
                            if not video_id:
                                self.failed_count += 1
                                continue

                            # Store metadata
                            title = entry.get('title', video_id)
                            artist = entry.get('uploader') or entry.get('creator') or entry.get('artist')

                            # Check cache first
                            cached = self._get_cached_file(video_id, temp_dir)
                            if cached:
                                self.metadata[cached] = {'title': title, 'artist': artist}
                                continue  # Already copied from cache

                            # Download if not cached
                            video_url = entry.get('webpage_url') or entry.get('url')
                            if video_url:
                                ydl.download([video_url])
                                # Cache the downloaded file
                                downloaded_file = temp_dir / f"{video_id}.mp3"
                                if downloaded_file.exists():
                                    self._cache_file(video_id, downloaded_file)
                                    self.metadata[downloaded_file] = {'title': title, 'artist': artist}
                        except Exception:
                            self.failed_count += 1
                            continue
                else:
                    # Single video
                    total_videos = 1
                    video_id = info.get('id')
                    title = info.get('title', video_id)
                    artist = info.get('uploader') or info.get('creator') or info.get('artist')

                    if video_id:
                        # Check cache first
                        cached = self._get_cached_file(video_id, temp_dir)
                        if cached:
                            self.metadata[cached] = {'title': title, 'artist': artist}
                        else:
                            # Download if not cached
                            try:
                                ydl.download([self.location])
                                # Cache the downloaded file
                                downloaded_file = temp_dir / f"{video_id}.mp3"
                                if downloaded_file.exists():
                                    self._cache_file(video_id, downloaded_file)
                                    self.metadata[downloaded_file] = {'title': title, 'artist': artist}
                            except Exception:
                                self.failed_count += 1
                                return False
                    else:
                        return False

                # Find downloaded/cached MP3 files in temp dir
                self.files = sorted(temp_dir.glob('*.mp3'))

                return len(self.files) > 0

        except Exception as e:
            return False

    def _download_youtube_video(self, temp_dir: Path, cookies: Optional[str] = None) -> bool:
        """Download YouTube video(s) as MP4"""
        is_playlist = self.is_playlist_url(self.location)

        ydl_opts = {
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            'outtmpl': str(temp_dir / '%(id)s_video.%(ext)s'),
            'quiet': True,
            'no_warnings': True,
            'ignoreerrors': True,
        }

        # Add cookies if provided
        if cookies:
            ydl_opts['cookiefile'] = cookies

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(self.location, download=False)

                if info is None:
                    return False

                if 'entries' in info:
                    # Playlist
                    videos = [entry for entry in info['entries'] if entry is not None]

                    for entry in videos:
                        try:
                            video_id = entry.get('id')
                            if not video_id:
                                continue

                            video_url = entry.get('webpage_url') or entry.get('url')
                            if video_url:
                                ydl.download([video_url])
                        except Exception:
                            continue
                else:
                    # Single video
                    try:
                        ydl.download([self.location])
                    except Exception:
                        return False

                # Find downloaded MP4 files
                self.video_files = sorted(temp_dir.glob('*_video.mp4'))

                return len(self.video_files) > 0

        except Exception:
            return False

    def _scan_directory(self, recurse: bool = False, mp4out: bool = False) -> bool:
        """Scan local directory for MP3/MP4 files and extract metadata"""
        self.source_type = "Directory"

        path = Path(self.location)
        if not path.exists() or not path.is_dir():
            return False

        # Find all MP3 files (recursive if --recurse flag set)
        if recurse:
            self.files = sorted(path.rglob('*.mp3'))
            mp4_files = sorted(path.rglob('*.mp4')) if mp4out else []
        else:
            self.files = sorted(path.glob('*.mp3'))
            mp4_files = sorted(path.glob('*.mp4')) if mp4out else []

        # Extract metadata from each MP3 file
        for mp3_file in self.files:
            try:
                audio = MP3(mp3_file)
                title = None
                artist = None

                # Try to extract from ID3 tags
                if audio.tags:
                    title = audio.tags.get('TIT2')
                    artist = audio.tags.get('TPE1')
                    if title:
                        title = str(title)
                    if artist:
                        artist = str(artist)

                # Fallback to filename if no tags
                if not title:
                    title = mp3_file.stem

                self.metadata[mp3_file] = {'title': title, 'artist': artist}
            except Exception:
                # If metadata extraction fails, use filename
                self.metadata[mp3_file] = {'title': mp3_file.stem, 'artist': None}

        # Handle MP4 files if --mp4out flag is set
        if mp4out and mp4_files:
            self.video_files = mp4_files

            # For MP4 files without corresponding MP3, extract audio
            # (This will be handled in the rotation phase)
            for mp4_file in mp4_files:
                # Store basic metadata for MP4 files
                if mp4_file not in self.metadata:
                    self.metadata[mp4_file] = {'title': mp4_file.stem, 'artist': None}

        return len(self.files) > 0 or len(self.video_files) > 0


def parse_args():
    """Parse command-line arguments"""
    parser = argparse.ArgumentParser(
        description='Bhajan Mixer - Create varied audio mixes by rotating through multiple sources',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --album "Morning" https://youtube.com/playlist?list=PLxxx
  %(prog)s --album "Mix" https://youtube.com/watch?v=xxx /path/to/music
  %(prog)s --dry-run --album "Preview" <sources> (preview without downloading)
  %(prog)s --recurse --album "Deep" /path/to/music (scan subdirectories)
        """
    )

    parser.add_argument('sources', nargs='+',
                       help='YouTube URLs (video/playlist) or local directory paths')
    parser.add_argument('--album', default='run-1',
                       help='Album/folder name for outputs (default: run-1)')
    parser.add_argument('--mp4out', action='store_true',
                       help='Enable video (MP4) output in addition to audio')
    parser.add_argument('--dry-run', action='store_true',
                       help='Show what would be created without downloading/processing')
    parser.add_argument('--recurse', action='store_true',
                       help='Scan directories recursively (default: top-level only)')
    parser.add_argument('--LONG-MP3-MAX', type=float, dest='long_mp3_max',
                       help='Max duration (in minutes) before an MP3 is considered "long"')
    parser.add_argument('--LONG-MP3-CUTOFF', type=float, dest='long_mp3_cutoff',
                       help='Duration (in minutes) to keep from long MP3s (must be used with --LONG-MP3-MAX)')
    parser.add_argument('--cookies', type=str, dest='cookies',
                       help='Path to cookies file for YouTube authentication (for private/restricted videos)')

    return parser.parse_args()


def sanitize_album_name(album_name: str) -> str:
    """Sanitize album name by removing/replacing invalid filesystem characters"""
    # Replace invalid characters with underscores
    invalid_chars = '<>:"/\\|?*'
    sanitized = album_name
    for char in invalid_chars:
        sanitized = sanitized.replace(char, '_')

    # Remove leading/trailing dots and spaces (problematic on Windows)
    sanitized = sanitized.strip('. ')

    # Ensure name is not empty
    if not sanitized:
        sanitized = "output"

    # Limit length to avoid path issues (max 200 chars)
    if len(sanitized) > 200:
        sanitized = sanitized[:200]

    return sanitized


def create_output_dir(base_dir: str, album_name: str) -> Path:
    """Create output directory with auto-increment if needed

    Args:
        base_dir: Base output directory path
        album_name: Desired album/folder name (will be sanitized)

    Returns:
        Path object for the created directory
    """
    # Sanitize album name first
    safe_name = sanitize_album_name(album_name)
    base_path = Path(base_dir) / safe_name

    if not base_path.exists():
        base_path.mkdir(parents=True, exist_ok=True)
        return base_path

    # Directory exists, find next available increment
    counter = 1
    while counter < 1000:  # Prevent infinite loop
        new_path = Path(base_dir) / f"{safe_name}.{counter}"
        if not new_path.exists():
            new_path.mkdir(parents=True, exist_ok=True)
            return new_path
        counter += 1

    # If we somehow hit 1000 directories, append timestamp
    import datetime
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    fallback_path = Path(base_dir) / f"{safe_name}_{timestamp}"
    fallback_path.mkdir(parents=True, exist_ok=True)
    return fallback_path


def combine_audio(audio_files: List[Path], output_path: Path,
                  long_mp3_max: Optional[float] = None,
                  long_mp3_cutoff: Optional[float] = None) -> None:
    """Concatenate multiple audio files into one MP3

    Args:
        audio_files: List of MP3 file paths to combine (in order)
        output_path: Where to save the combined MP3 file
        long_mp3_max: Max duration (in minutes) before an MP3 is considered "long" (optional)
        long_mp3_cutoff: Duration (in minutes) to keep from long MP3s (optional)

    Note:
        Exports at 320kbps quality for best audio fidelity
    """
    combined = AudioSegment.empty()

    for audio_file in audio_files:
        try:
            segment = AudioSegment.from_mp3(str(audio_file))

            # Check if we need to truncate this segment
            if long_mp3_max is not None and long_mp3_cutoff is not None:
                duration_minutes = len(segment) / 1000.0 / 60.0  # Convert ms to minutes

                if duration_minutes > long_mp3_max:
                    # Truncate to first long_mp3_cutoff minutes
                    cutoff_ms = int(long_mp3_cutoff * 60 * 1000)  # Convert minutes to ms
                    segment = segment[:cutoff_ms]
                    print(f"  ✂️  Truncated {audio_file.name} from {duration_minutes:.1f} to {long_mp3_cutoff:.1f} minutes")

            combined += segment
        except Exception as e:
            print(f"  ⚠️  Warning: Could not process {audio_file.name}: {e}")
            continue

    # Export as high-quality MP3
    combined.export(str(output_path), format="mp3", bitrate="320k")


def normalize_video(input_file: Path, output_file: Path) -> bool:
    """Normalize video to 1080p, 30fps, 16:9 aspect ratio using ffmpeg"""
    try:
        cmd = [
            'ffmpeg', '-i', str(input_file),
            '-vf', 'scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2,fps=30',
            '-c:v', 'libx264', '-preset', 'medium', '-crf', '23',
            '-c:a', 'aac', '-b:a', '192k',
            '-y',  # Overwrite output file
            str(output_file)
        ]

        subprocess.run(cmd, check=True, capture_output=True)
        return True
    except Exception as e:
        print(f"  ⚠️  Warning: Could not normalize video {input_file.name}: {e}")
        return False


def combine_videos(video_files: List[Path], output_path: Path, temp_dir: Path) -> bool:
    """Concatenate multiple video files into one MP4"""
    try:
        # First, normalize all videos
        normalized_files = []
        for idx, video_file in enumerate(video_files):
            normalized = temp_dir / f"normalized_{idx}_{video_file.name}"
            if normalize_video(video_file, normalized):
                normalized_files.append(normalized)
            else:
                return False

        if not normalized_files:
            return False

        # Create concat file
        concat_file = temp_dir / "concat_list.txt"
        with open(concat_file, 'w') as f:
            for video_file in normalized_files:
                # Use absolute paths and escape single quotes
                f.write(f"file '{video_file.absolute()}'\n")

        # Concatenate videos
        cmd = [
            'ffmpeg', '-f', 'concat', '-safe', '0',
            '-i', str(concat_file),
            '-c', 'copy',
            '-y',
            str(output_path)
        ]

        subprocess.run(cmd, check=True, capture_output=True)
        return True
    except Exception as e:
        print(f"  ⚠️  Warning: Could not combine videos: {e}")
        return False


def write_id3_tags(output_file: Path, sources: List[Source], audio_files: List[Path],
                   album_name: str, track_num: int, total_tracks: int) -> None:
    """Write ID3 tags to the output MP3 file"""
    try:
        audio = MP3(output_file)

        # Initialize tags if they don't exist
        if audio.tags is None:
            audio.add_tags()

        # Collect titles and artists from source files
        titles = []
        artists = []

        for audio_file in audio_files:
            # Find which source this file belongs to
            for source in sources:
                if audio_file in source.metadata:
                    metadata = source.metadata[audio_file]
                    if metadata.get('title'):
                        titles.append(metadata['title'])
                    if metadata.get('artist'):
                        artists.append(metadata['artist'])
                    break

        # Create combined title with bullet separator
        combined_title = " • ".join(titles) if titles else f"Track {track_num:02d}"

        # If title is too long, use fallback
        if len(combined_title) > 80:
            combined_title = f"Track {track_num:02d} (from {len(audio_files)} sources)"

        # Create combined artist or use "Various Artists"
        combined_artist = " • ".join(artists) if artists else "Various Artists"

        # Write tags
        audio.tags.add(TIT2(encoding=3, text=combined_title))
        audio.tags.add(TALB(encoding=3, text=album_name))
        audio.tags.add(TPE1(encoding=3, text=combined_artist))
        audio.tags.add(TRCK(encoding=3, text=f"{track_num}/{total_tracks}"))

        audio.save()
    except Exception as e:
        print(f"  ⚠️  Warning: Could not write metadata to {output_file.name}: {e}")


def rotate_and_combine_videos(sources: List[Source], output_dir: Path, temp_dir: Path) -> int:
    """Apply circular rotation algorithm for video files and create combined MP4s"""
    # Filter sources that have video files
    video_sources = [s for s in sources if len(s.video_files) > 0]

    if not video_sources:
        return 0

    max_length = max(len(source.video_files) for source in video_sources)

    print(f"\n🎬 Creating {max_length} video track(s)...")

    created_count = 0
    for track_num in range(1, max_length + 1):
        # Collect one video from each source using circular indexing
        video_files = []
        for source in video_sources:
            file_index = (track_num - 1) % len(source.video_files)
            video_files.append(source.video_files[file_index])

        # Create combined video track
        output_file = output_dir / f"track-{track_num:02d}.mp4"

        try:
            if combine_videos(video_files, output_file, temp_dir):
                created_count += 1

                # Progress indicator
                if track_num % 5 == 0 or track_num == max_length:
                    print(f"  Progress: {track_num}/{max_length} video tracks created")
            else:
                print(f"  ✗ Error creating video track {track_num:02d}")
        except Exception as e:
            print(f"  ✗ Error creating video track {track_num:02d}: {e}")
            continue

    return created_count


def rotate_and_combine(sources: List[Source], output_dir: Path, temp_dir: Path, album_name: str,
                       long_mp3_max: Optional[float] = None,
                       long_mp3_cutoff: Optional[float] = None) -> int:
    """Apply circular rotation algorithm and create combined tracks"""
    # Filter sources that have audio files
    audio_sources = [s for s in sources if len(s.files) > 0]

    if not audio_sources:
        return 0

    max_length = max(len(source.files) for source in audio_sources)
    total_tracks = max_length

    print(f"\n🎼 Creating {max_length} track(s)...")

    created_count = 0
    for track_num in range(1, max_length + 1):
        # Collect one file from each source using circular indexing
        audio_files = []
        for source in audio_sources:
            file_index = (track_num - 1) % len(source.files)
            audio_files.append(source.files[file_index])

        # Create combined track
        output_file = output_dir / f"track-{track_num:02d}.mp3"

        try:
            combine_audio(audio_files, output_file, long_mp3_max, long_mp3_cutoff)

            # Write ID3 tags with metadata
            write_id3_tags(output_file, sources, audio_files, album_name, track_num, total_tracks)

            created_count += 1

            # Progress indicator
            if track_num % 5 == 0 or track_num == max_length:
                print(f"  Progress: {track_num}/{max_length} tracks created")
        except Exception as e:
            print(f"  ✗ Error creating track {track_num:02d}: {e}")
            continue

    return created_count


def main():
    """Main application entry point"""
    print("🎵 Bhajan Mixer\n")

    args = parse_args()

    # Validate LONG-MP3 parameters (both must be provided together)
    if (args.long_mp3_max is not None) != (args.long_mp3_cutoff is not None):
        print("❌ Error: --LONG-MP3-MAX and --LONG-MP3-CUTOFF must be used together")
        print("💡 Please provide both parameters or neither")
        return 1

    # Auto-adjust LONG-MP3-CUTOFF if it exceeds LONG-MP3-MAX
    if args.long_mp3_max is not None and args.long_mp3_cutoff is not None:
        if args.long_mp3_cutoff > args.long_mp3_max:
            print(f"⚠️  Warning: LONG-MP3-CUTOFF ({args.long_mp3_cutoff} min) > LONG-MP3-MAX ({args.long_mp3_max} min)")
            print(f"⚠️  Auto-adjusting LONG-MP3-CUTOFF to {args.long_mp3_max} minutes")
            args.long_mp3_cutoff = args.long_mp3_max

    # Handle dry-run mode
    if args.dry_run:
        print("⚠️  DRY RUN MODE - No files will be downloaded or created\n")
        print("📋 Preview only (actual results may vary):\n")

    # Clean up old cached files
    cleanup_old_cache()

    # Create temporary directory for downloads
    temp_dir = Path(tempfile.mkdtemp(prefix='bhajan-mixer-'))

    try:
        # Process all sources
        print(f"📥 Processing {len(args.sources)} source(s):\n")

        sources = []
        for idx, source_location in enumerate(args.sources, 1):
            source = Source(source_location, idx)

            print(f"  Source {idx}: {source_location}")

            # In dry-run mode, only scan directories (don't download YouTube)
            if args.dry_run and source.is_youtube_url(source_location):
                print(f"  ⚠️  Skipped (dry-run mode doesn't download YouTube)")
                continue

            if source.download_or_scan(temp_dir, recurse=args.recurse, mp4out=args.mp4out, cookies=args.cookies):
                audio_count = len(source.files)
                video_count = len(source.video_files)
                failed_msg = f" ({source.failed_count} failed)" if source.failed_count > 0 else ""
                cached_msg = f" ({source.cached_count} from cache)" if source.cached_count > 0 else ""

                if args.mp4out and video_count > 0:
                    print(f"  ✓ {source.source_type}: {audio_count} audio, {video_count} video{failed_msg}{cached_msg}")
                else:
                    print(f"  ✓ {source.source_type}: {audio_count} file(s){failed_msg}{cached_msg}")

                sources.append(source)
            else:
                print(f"  ✗ Failed - SKIPPING")

        # Check if we have any valid sources
        if not sources:
            print("\n❌ Error: No valid sources found. Nothing to process.")
            print("\n💡 Troubleshooting:")
            print("  • For YouTube: Check that URLs are valid and videos are not private/deleted")
            print("  • For directories: Verify path exists and contains MP3 files")
            print("  • Try --dry-run to preview without downloading")
            return 1

        # Calculate track counts
        audio_sources = [s for s in sources if len(s.files) > 0]
        video_sources = [s for s in sources if len(s.video_files) > 0]

        audio_track_count = max(len(s.files) for s in audio_sources) if audio_sources else 0
        video_track_count = max(len(s.video_files) for s in video_sources) if video_sources else 0

        print(f"\n📊 Valid sources: {len(sources)}")
        if args.mp4out and video_track_count > 0:
            print(f"📊 Will create {audio_track_count} audio track(s) and {video_track_count} video track(s)")
        else:
            print(f"📊 Will create {audio_track_count} track(s)")

        # In dry-run mode, stop here
        if args.dry_run:
            print("\n✅ Dry run complete! No files were created.")
            print("💡 Run without --dry-run to actually create tracks.")
            return 0

        # Create output directory
        output_base = os.getenv("OUTPUT_DIR", "/app/output")
        output_dir = create_output_dir(output_base, args.album)

        # Apply rotation and create audio tracks
        audio_created = rotate_and_combine(sources, output_dir, temp_dir, args.album,
                                          args.long_mp3_max, args.long_mp3_cutoff)

        # Apply rotation and create video tracks if --mp4out flag is set
        video_created = 0
        if args.mp4out:
            video_created = rotate_and_combine_videos(sources, output_dir, temp_dir)

        # Count intermediate files for cleanup report
        intermediate_files = list(temp_dir.glob('*'))
        intermediate_count = len(intermediate_files)

        # Report results
        if args.mp4out and video_created > 0:
            print(f"\n✅ Complete! Created {audio_created} audio and {video_created} video file(s) in: {output_dir.relative_to(output_base)}/")
        else:
            print(f"\n✅ Complete! Created {audio_created} file(s) in: {output_dir.relative_to(output_base)}/")

        if intermediate_count > 0:
            print(f"🗑️  Cleaned up {intermediate_count} intermediate file(s)")

        return 0

    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        return 130
    except PermissionError as e:
        print(f"\n❌ Permission Error: {e}")
        print("\n💡 Try running with appropriate permissions or choose a different output directory")
        return 1
    except OSError as e:
        if "No space left" in str(e):
            print(f"\n❌ Disk Space Error: {e}")
            print("\n💡 Free up disk space or choose a different output directory")
        else:
            print(f"\n❌ System Error: {e}")
            print("\n💡 Check file paths and system resources")
        return 1
    except Exception as e:
        print(f"\n❌ Unexpected Error: {e}")
        print("\n💡 If this persists, please report the issue with the error details above")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        # Cleanup temporary directory
        if temp_dir.exists():
            shutil.rmtree(temp_dir)


if __name__ == "__main__":
    sys.exit(main())
