# Bhajan Mixer - Testing Guide

## Overview

This project includes a comprehensive test suite to ensure reliability and facilitate future development. Tests are organized into unit tests, integration tests, and network-dependent tests.

---

## Quick Start

### Installation

Install development dependencies:

```bash
# Install all dependencies including testing tools
pip install -r requirements-dev.txt

# Or install just the testing dependencies
pip install pytest pytest-cov pytest-mock pytest-timeout
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage report
pytest --cov

# Run specific test types
pytest -m unit              # Fast unit tests only
pytest -m integration       # Integration tests only
pytest -m "not slow"        # Skip slow tests

# Run specific test file
pytest tests/test_utils.py

# Run specific test
pytest tests/test_utils.py::TestSanitizeAlbumName::test_sanitize_basic_name

# Verbose output
pytest -v

# See print statements
pytest -s
```

---

## Test Organization

### Directory Structure

```
tests/
├── __init__.py              # Test package initialization
├── conftest.py              # Pytest fixtures and configuration
├── test_utils.py            # Utility function tests
├── test_source.py           # Source class tests
└── test_integration.py      # Integration and end-to-end tests
```

### Test Markers

Tests are organized with markers for selective execution:

| Marker | Description | Speed |
|--------|-------------|-------|
| `unit` | Fast, isolated unit tests | < 1s |
| `integration` | Tests that combine components | 1-10s |
| `slow` | Long-running tests (video processing) | > 10s |
| `requires_network` | Tests needing internet (YouTube) | varies |
| `requires_docker` | Tests needing Docker | varies |

### Running Specific Test Types

```bash
# Fast tests only (unit tests)
pytest -m unit

# Skip network-dependent tests (default)
pytest -m "not requires_network"

# Run network tests (downloads from YouTube)
pytest -m requires_network

# Skip slow tests
pytest -m "not slow"

# Skip both network and slow tests
pytest -m "not (requires_network or slow)"
```

---

## Test Coverage

### Viewing Coverage

```bash
# Run tests with coverage
pytest --cov

# Generate HTML coverage report
pytest --cov --cov-report=html

# Open HTML report (Linux/Mac)
open htmlcov/index.html

# Open HTML report (Windows)
start htmlcov/index.html
```

### Coverage Goals

- **Target**: 80%+ coverage for core functionality
- **Critical paths**: 90%+ coverage (Source class, rotation algorithm)
- **Documentation**: Exclude from coverage metrics

---

## Writing Tests

### Test Structure

```python
import pytest

class TestFeatureName:
    """Test suite for a specific feature"""

    @pytest.mark.unit
    def test_basic_functionality(self):
        """Test description"""
        # Arrange
        input_data = "test"

        # Act
        result = function_to_test(input_data)

        # Assert
        assert result == expected_output

    @pytest.mark.integration
    def test_integration_scenario(self, temp_dir):
        """Test using fixtures"""
        # Use fixtures from conftest.py
        test_file = temp_dir / "test.txt"
        test_file.write_text("content")
        assert test_file.exists()
```

### Using Fixtures

Available fixtures (defined in `conftest.py`):

```python
def test_with_fixtures(temp_dir, sample_mp3, sample_dir_with_mp3s):
    """Example using multiple fixtures"""
    # temp_dir: Temporary directory for test files
    # sample_mp3: A single valid MP3 file
    # sample_dir_with_mp3s: Directory with 3 MP3 files

    assert temp_dir.exists()
    assert sample_mp3.exists()
    assert len(list(sample_dir_with_mp3s.glob("*.mp3"))) == 3
```

### Mocking External Dependencies

```python
from pytest_mock import mocker

@pytest.mark.unit
def test_with_mock(mocker):
    """Test using mocks to avoid external dependencies"""
    # Mock yt-dlp download
    mock_ydl = mocker.patch('yt_dlp.YoutubeDL')

    # Test your code
    # ...

    # Verify mock was called
    mock_ydl.assert_called_once()
```

---

## Test Configuration Files

### pytest.ini

Main pytest configuration:
- Test discovery patterns
- Default options (coverage, verbosity)
- Marker definitions
- Timeout settings

### .coveragerc

Coverage measurement configuration:
- Source directories
- Files to exclude
- Coverage report formatting

### requirements-dev.txt

Development dependencies including:
- Testing frameworks (pytest, coverage)
- Code quality tools (black, flake8, pylint)
- Development utilities (ipython, ipdb)

---

## Continuous Testing

### Watch Mode (Optional)

Install pytest-watch for continuous testing:

```bash
pip install pytest-watch

# Auto-run tests on file changes
ptw
```

### Pre-commit Testing

Add to `.git/hooks/pre-commit`:

```bash
#!/bin/bash
pytest -m unit --maxfail=1
```

Make it executable:
```bash
chmod +x .git/hooks/pre-commit
```

---

## Testing Different Components

### 1. Utility Functions

```bash
pytest tests/test_utils.py -v
```

Tests:
- Album name sanitization
- Output directory creation
- Path handling

### 2. Source Class

```bash
pytest tests/test_source.py -v
```

Tests:
- YouTube URL detection
- Directory scanning (recursive/non-recursive)
- Metadata extraction

### 3. Integration Tests

```bash
pytest tests/test_integration.py -v
```

Tests:
- CLI interface
- Docker builds
- End-to-end workflows

### 4. Network Tests (Optional)

```bash
pytest tests/test_integration.py -m requires_network
```

Tests:
- YouTube downloads
- Cache functionality
- Real playlist processing

**Warning**: These tests download from YouTube and may be slow.

---

## Troubleshooting

### Common Issues

**Import errors:**
```bash
# Make sure you're in the project root
cd /path/to/bhajan-mixer
pytest
```

**Docker tests failing:**
```bash
# Build the Docker image first
docker build -t bhajan-mixer .
pytest -m requires_docker
```

**Coverage not showing:**
```bash
# Ensure coverage is installed
pip install pytest-cov

# Run with explicit coverage flags
pytest --cov=. --cov-report=term-missing
```

**Tests hanging:**
```bash
# Use timeout
pytest --timeout=60

# Or skip slow tests
pytest -m "not slow"
```

---

## Best Practices

### DO:
- ✅ Write tests for new features
- ✅ Run unit tests before committing
- ✅ Use markers to organize tests
- ✅ Mock external dependencies (YouTube, network)
- ✅ Use descriptive test names
- ✅ Keep tests independent

### DON'T:
- ❌ Commit failing tests
- ❌ Skip writing tests for bug fixes
- ❌ Rely on network in unit tests
- ❌ Create tests with side effects
- ❌ Hardcode paths or credentials

---

## Adding New Tests

### Workflow

1. **Identify what to test**
   - New feature? Write feature tests
   - Bug fix? Write regression test
   - Refactoring? Ensure existing tests pass

2. **Choose test type**
   - Pure function? → Unit test
   - Multiple components? → Integration test
   - Full workflow? → End-to-end test

3. **Write the test**
   ```python
   @pytest.mark.unit
   def test_new_feature(self):
       """Test that new feature works correctly"""
       result = new_feature("input")
       assert result == "expected"
   ```

4. **Run and verify**
   ```bash
   pytest tests/test_new_feature.py -v
   ```

5. **Add to appropriate test file**
   - Utils: `test_utils.py`
   - Source: `test_source.py`
   - Integration: `test_integration.py`

---

## Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [Pytest Fixtures](https://docs.pytest.org/en/stable/fixture.html)
- [Coverage.py](https://coverage.readthedocs.io/)
- [Testing Best Practices](https://docs.python-guide.org/writing/tests/)

---

## Questions?

For testing-related questions:
1. Check this guide
2. Review existing tests in `tests/`
3. Check pytest documentation
4. Open an issue on GitHub
