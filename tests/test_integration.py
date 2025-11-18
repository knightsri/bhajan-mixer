"""
Integration tests for bhajan-mixer

These tests verify that different components work together correctly.
Some tests are marked as 'requires_network' and will be skipped unless
explicitly enabled with: pytest -m requires_network
"""
import sys
from pathlib import Path
import pytest
import subprocess
import os

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestCLI:
    """Test the command-line interface"""

    @pytest.mark.integration
    def test_help_output(self):
        """Test that --help works"""
        result = subprocess.run(
            ["python", "bhajan-mixer.py", "--help"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent
        )
        assert result.returncode == 0
        assert "Bhajan Mixer" in result.stdout
        assert "--album" in result.stdout
        assert "--mp4out" in result.stdout
        assert "--dry-run" in result.stdout

    @pytest.mark.integration
    def test_dry_run_with_directory(self, sample_dir_with_mp3s):
        """Test dry-run mode with a local directory"""
        result = subprocess.run(
            [
                "python", "bhajan-mixer.py",
                "--dry-run",
                "--album", "TestRun",
                str(sample_dir_with_mp3s)
            ],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent
        )
        assert result.returncode == 0
        assert "DRY RUN MODE" in result.stdout
        assert "Dry run complete" in result.stdout

    @pytest.mark.integration
    def test_invalid_source_error(self):
        """Test that invalid sources produce helpful error"""
        result = subprocess.run(
            [
                "python", "bhajan-mixer.py",
                "--album", "FailTest",
                "/nonexistent/path"
            ],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent
        )
        assert result.returncode == 1
        assert "No valid sources found" in result.stdout or "No valid sources found" in result.stderr


class TestDockerBuild:
    """Test Docker-related functionality"""

    @pytest.mark.integration
    @pytest.mark.requires_docker
    def test_docker_builds(self):
        """Test that Docker image builds successfully"""
        result = subprocess.run(
            ["docker", "build", "-t", "bhajan-mixer-test", "."],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent
        )
        assert result.returncode == 0

    @pytest.mark.integration
    @pytest.mark.requires_docker
    def test_docker_help(self):
        """Test running --help in Docker"""
        result = subprocess.run(
            [
                "docker", "run", "--rm",
                "bhajan-mixer-test",
                "--help"
            ],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert "Bhajan Mixer" in result.stdout


@pytest.mark.requires_network
class TestNetworkOperations:
    """Tests that require network access (YouTube)

    Run with: pytest -m requires_network
    """

    @pytest.mark.integration
    @pytest.mark.slow
    def test_youtube_dry_run(self):
        """Test dry-run with a YouTube URL (no download)"""
        # This should not actually download in dry-run mode
        result = subprocess.run(
            [
                "python", "bhajan-mixer.py",
                "--dry-run",
                "--album", "YTTest",
                "https://www.youtube.com/watch?v=jNQXAC9IVRw"
            ],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent
        )
        # Dry-run should skip YouTube downloads
        assert "Skipped (dry-run mode doesn't download YouTube)" in result.stdout


class TestLongMP3Feature:
    """Test the LONG-MP3-MAX and LONG-MP3-CUTOFF feature"""

    @pytest.mark.integration
    def test_help_shows_long_mp3_options(self):
        """Test that --help shows the new LONG-MP3 options"""
        result = subprocess.run(
            ["python", "bhajan-mixer.py", "--help"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent
        )
        assert result.returncode == 0
        assert "--LONG-MP3-MAX" in result.stdout
        assert "--LONG-MP3-CUTOFF" in result.stdout

    @pytest.mark.integration
    def test_error_when_only_max_provided(self, sample_dir_with_mp3s):
        """Test that error occurs when only --LONG-MP3-MAX is provided"""
        result = subprocess.run(
            [
                "python", "bhajan-mixer.py",
                "--album", "ErrorTest",
                "--LONG-MP3-MAX", "3",
                str(sample_dir_with_mp3s)
            ],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent
        )
        assert result.returncode == 1
        assert "must be used together" in result.stdout

    @pytest.mark.integration
    def test_error_when_only_cutoff_provided(self, sample_dir_with_mp3s):
        """Test that error occurs when only --LONG-MP3-CUTOFF is provided"""
        result = subprocess.run(
            [
                "python", "bhajan-mixer.py",
                "--album", "ErrorTest",
                "--LONG-MP3-CUTOFF", "2",
                str(sample_dir_with_mp3s)
            ],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent
        )
        assert result.returncode == 1
        assert "must be used together" in result.stdout

    @pytest.mark.integration
    def test_auto_adjust_when_cutoff_exceeds_max(self, sample_dir_with_mp3s):
        """Test that LONG-MP3-CUTOFF is auto-adjusted when it exceeds LONG-MP3-MAX"""
        result = subprocess.run(
            [
                "python", "bhajan-mixer.py",
                "--dry-run",
                "--album", "AutoAdjustTest",
                "--LONG-MP3-MAX", "3",
                "--LONG-MP3-CUTOFF", "5",
                str(sample_dir_with_mp3s)
            ],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent
        )
        assert result.returncode == 0
        assert "Auto-adjusting LONG-MP3-CUTOFF" in result.stdout

    @pytest.mark.integration
    @pytest.mark.slow
    def test_truncation_of_long_mp3(self, dir_with_long_and_short_mp3s, temp_dir):
        """Test that long MP3 files are actually truncated"""
        # Set OUTPUT_DIR environment variable
        output_dir = temp_dir / "output"
        output_dir.mkdir()

        result = subprocess.run(
            [
                "python", "bhajan-mixer.py",
                "--album", "TruncateTest",
                "--LONG-MP3-MAX", "3",
                "--LONG-MP3-CUTOFF", "2",
                str(dir_with_long_and_short_mp3s)
            ],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent,
            env={**os.environ, "OUTPUT_DIR": str(output_dir)}
        )

        assert result.returncode == 0
        # Check that truncation message appears
        assert "Truncated" in result.stdout
        # Verify output files were created
        output_files = list(output_dir.glob("**/*.mp3"))
        assert len(output_files) > 0
