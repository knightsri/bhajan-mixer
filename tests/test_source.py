"""
Unit tests for the Source class
"""
import sys
from pathlib import Path
import pytest

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from bhajan_mixer import Source
except ImportError:
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "bhajan_mixer",
        Path(__file__).parent.parent / "bhajan-mixer.py"
    )
    bhajan_mixer = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(bhajan_mixer)
    Source = bhajan_mixer.Source


class TestSource:
    """Test the Source class"""

    @pytest.mark.unit
    def test_source_initialization(self):
        """Test Source object is initialized correctly"""
        source = Source("https://youtube.com/watch?v=test", 1)
        assert source.location == "https://youtube.com/watch?v=test"
        assert source.source_index == 1
        assert source.files == []
        assert source.video_files == []
        assert source.metadata == {}
        assert source.failed_count == 0
        assert source.cached_count == 0

    @pytest.mark.unit
    def test_is_youtube_url_positive(self):
        """Test YouTube URL detection"""
        source = Source("https://youtube.com/watch?v=test", 1)
        assert source.is_youtube_url("https://youtube.com/watch?v=test") is True
        assert source.is_youtube_url("https://www.youtube.com/watch?v=test") is True
        assert source.is_youtube_url("https://youtu.be/test") is True
        assert source.is_youtube_url("https://m.youtube.com/watch?v=test") is True

    @pytest.mark.unit
    def test_is_youtube_url_negative(self):
        """Test non-YouTube URL detection"""
        source = Source("/path/to/music", 1)
        assert source.is_youtube_url("/path/to/music") is False
        assert source.is_youtube_url("https://example.com") is False
        assert source.is_youtube_url("") is False

    @pytest.mark.unit
    def test_is_playlist_url(self):
        """Test playlist URL detection"""
        source = Source("test", 1)
        assert source.is_playlist_url("https://youtube.com/playlist?list=PLxxx") is True
        assert source.is_playlist_url("https://youtube.com/watch?v=xxx&list=PLyyy") is True
        assert source.is_playlist_url("https://youtube.com/watch?v=xxx") is False

    @pytest.mark.unit
    def test_scan_directory_no_files(self, temp_dir):
        """Test scanning a directory with no MP3 files"""
        empty_dir = temp_dir / "empty"
        empty_dir.mkdir()

        source = Source(str(empty_dir), 1)
        result = source._scan_directory(recurse=False, mp4out=False)

        assert result is False
        assert len(source.files) == 0

    @pytest.mark.unit
    def test_scan_directory_with_mp3s(self, sample_dir_with_mp3s):
        """Test scanning a directory with MP3 files"""
        source = Source(str(sample_dir_with_mp3s), 1)
        result = source._scan_directory(recurse=False, mp4out=False)

        assert result is True
        assert len(source.files) == 3
        # Check files are sorted
        names = [f.name for f in source.files]
        assert names == sorted(names)

    @pytest.mark.unit
    def test_scan_directory_nonexistent(self, temp_dir):
        """Test scanning a directory that doesn't exist"""
        fake_dir = temp_dir / "nonexistent"

        source = Source(str(fake_dir), 1)
        result = source._scan_directory(recurse=False, mp4out=False)

        assert result is False
        assert len(source.files) == 0

    @pytest.mark.unit
    def test_scan_directory_recursive(self, temp_dir):
        """Test recursive directory scanning"""
        # Create nested structure
        level1 = temp_dir / "level1"
        level2 = level1 / "level2"
        level2.mkdir(parents=True)

        # Create MP3s at different levels
        (level1 / "song1.mp3").write_bytes(b'\xff\xfb\x90\x00' + b'\x00' * 100)
        (level2 / "song2.mp3").write_bytes(b'\xff\xfb\x90\x00' + b'\x00' * 100)

        # Scan without recursion
        source1 = Source(str(level1), 1)
        source1._scan_directory(recurse=False, mp4out=False)
        assert len(source1.files) == 1  # Only top-level

        # Scan with recursion
        source2 = Source(str(level1), 2)
        source2._scan_directory(recurse=True, mp4out=False)
        assert len(source2.files) == 2  # Both levels
