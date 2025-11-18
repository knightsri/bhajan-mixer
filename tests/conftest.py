"""
Pytest configuration and fixtures for Bhajan Mixer tests
"""
import os
import tempfile
from pathlib import Path
import pytest
import shutil


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files"""
    temp = tempfile.mkdtemp(prefix='bhajan-test-')
    yield Path(temp)
    # Cleanup
    if Path(temp).exists():
        shutil.rmtree(temp)


@pytest.fixture
def sample_mp3(temp_dir):
    """Create a minimal valid MP3 file for testing"""
    mp3_file = temp_dir / "sample.mp3"
    # Create a minimal MP3 file (silence, very short)
    # This is a minimal valid MP3 frame header
    mp3_data = b'\xff\xfb\x90\x00' + b'\x00' * 100
    mp3_file.write_bytes(mp3_data)
    return mp3_file


@pytest.fixture
def sample_dir_with_mp3s(temp_dir):
    """Create a directory with multiple MP3 files"""
    music_dir = temp_dir / "music"
    music_dir.mkdir()

    # Create 3 sample MP3 files
    for i in range(1, 4):
        mp3_file = music_dir / f"song{i}.mp3"
        mp3_data = b'\xff\xfb\x90\x00' + b'\x00' * 100
        mp3_file.write_bytes(mp3_data)

    return music_dir


@pytest.fixture
def mock_youtube_url():
    """Return a mock YouTube URL (not actually used in tests requiring network)"""
    return "https://www.youtube.com/watch?v=dQw4w9WgXcQ"


@pytest.fixture
def mock_playlist_url():
    """Return a mock YouTube playlist URL"""
    return "https://www.youtube.com/playlist?list=PLrAXtmErZgOeiKm4sgNOknGvNjby9efdf"


@pytest.fixture
def long_mp3_file(temp_dir):
    """Create a long MP3 file (5 minutes of silence) for testing"""
    try:
        from pydub import AudioSegment
        from pydub.generators import Sine
    except ImportError:
        pytest.skip("pydub not available")

    # Create 5 minutes of silence
    duration_ms = 5 * 60 * 1000  # 5 minutes in milliseconds
    silence = AudioSegment.silent(duration=duration_ms)

    mp3_file = temp_dir / "long_song.mp3"
    silence.export(str(mp3_file), format="mp3", bitrate="320k")

    return mp3_file


@pytest.fixture
def dir_with_long_and_short_mp3s(temp_dir):
    """Create a directory with both long and short MP3 files"""
    try:
        from pydub import AudioSegment
    except ImportError:
        pytest.skip("pydub not available")

    music_dir = temp_dir / "mixed_music"
    music_dir.mkdir()

    # Create 1 long MP3 (5 minutes)
    long_silence = AudioSegment.silent(duration=5 * 60 * 1000)
    long_file = music_dir / "long_song.mp3"
    long_silence.export(str(long_file), format="mp3", bitrate="320k")

    # Create 2 short MP3s (30 seconds each)
    short_silence = AudioSegment.silent(duration=30 * 1000)
    for i in range(1, 3):
        short_file = music_dir / f"short_song{i}.mp3"
        short_silence.export(str(short_file), format="mp3", bitrate="320k")

    return music_dir
