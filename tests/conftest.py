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
