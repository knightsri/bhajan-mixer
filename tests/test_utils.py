"""
Unit tests for utility functions in bhajan-mixer
"""
import sys
from pathlib import Path
import pytest

# Add parent directory to path to import the main module
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import functions to test (will work after Docker build)
try:
    from bhajan_mixer import sanitize_album_name, create_output_dir
except ImportError:
    # If running outside container, import from file
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "bhajan_mixer",
        Path(__file__).parent.parent / "bhajan-mixer.py"
    )
    bhajan_mixer = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(bhajan_mixer)
    sanitize_album_name = bhajan_mixer.sanitize_album_name
    create_output_dir = bhajan_mixer.create_output_dir


class TestSanitizeAlbumName:
    """Test the sanitize_album_name function"""

    @pytest.mark.unit
    def test_sanitize_basic_name(self):
        """Test that basic album names pass through unchanged"""
        assert sanitize_album_name("Morning Bhajans") == "Morning Bhajans"
        assert sanitize_album_name("Mix-2024") == "Mix-2024"

    @pytest.mark.unit
    def test_sanitize_invalid_characters(self):
        """Test that invalid filesystem characters are replaced"""
        assert sanitize_album_name("Test/Album") == "Test_Album"
        assert sanitize_album_name("Test:Name") == "Test_Name"
        assert sanitize_album_name("Test<>|?*") == "Test_____"

    @pytest.mark.unit
    def test_sanitize_special_chars(self):
        """Test all invalid characters are replaced"""
        result = sanitize_album_name('Test<>:"/\\|?*Name')
        assert '<' not in result
        assert '>' not in result
        assert ':' not in result
        assert '"' not in result
        assert '/' not in result
        assert '\\' not in result
        assert '|' not in result
        assert '?' not in result
        assert '*' not in result

    @pytest.mark.unit
    def test_sanitize_leading_trailing_spaces(self):
        """Test that leading/trailing spaces and dots are removed"""
        assert sanitize_album_name("  Album  ") == "Album"
        assert sanitize_album_name("..Album..") == "Album"
        assert sanitize_album_name(". Album .") == "Album"

    @pytest.mark.unit
    def test_sanitize_empty_string(self):
        """Test that empty strings become 'output'"""
        assert sanitize_album_name("") == "output"
        assert sanitize_album_name("   ") == "output"
        assert sanitize_album_name("...") == "output"

    @pytest.mark.unit
    def test_sanitize_long_name(self):
        """Test that very long names are truncated"""
        long_name = "A" * 300
        result = sanitize_album_name(long_name)
        assert len(result) == 200


class TestCreateOutputDir:
    """Test the create_output_dir function"""

    @pytest.mark.unit
    def test_create_new_directory(self, temp_dir):
        """Test creating a new output directory"""
        result = create_output_dir(str(temp_dir), "TestAlbum")
        assert result.exists()
        assert result.is_dir()
        assert result.name == "TestAlbum"

    @pytest.mark.unit
    def test_create_with_sanitization(self, temp_dir):
        """Test that album names are sanitized"""
        result = create_output_dir(str(temp_dir), "Test/Album")
        assert result.exists()
        assert result.name == "Test_Album"

    @pytest.mark.unit
    def test_auto_increment_on_conflict(self, temp_dir):
        """Test that directory names are auto-incremented if they exist"""
        # Create first directory
        dir1 = create_output_dir(str(temp_dir), "Album")
        assert dir1.name == "Album"

        # Create second directory with same name
        dir2 = create_output_dir(str(temp_dir), "Album")
        assert dir2.name == "Album.1"

        # Create third directory with same name
        dir3 = create_output_dir(str(temp_dir), "Album")
        assert dir3.name == "Album.2"

    @pytest.mark.unit
    def test_creates_parent_directories(self, temp_dir):
        """Test that parent directories are created if needed"""
        deep_path = temp_dir / "level1" / "level2"
        result = create_output_dir(str(deep_path), "Album")
        assert result.exists()
        assert result.parent.parent.exists()  # level1/level2 created
