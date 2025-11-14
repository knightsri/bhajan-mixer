#!/bin/bash
# Test runner script for Bhajan Mixer

set -e

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║          Bhajan Mixer - Test Suite                            ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Check if pytest is installed
if ! command -v pytest &> /dev/null; then
    echo "❌ pytest not found. Installing test dependencies..."
    pip install -r requirements-dev.txt
fi

# Parse arguments
TEST_TYPE="${1:-all}"

case "$TEST_TYPE" in
    unit)
        echo "🧪 Running unit tests (fast)..."
        pytest -m unit -v
        ;;
    integration)
        echo "🔗 Running integration tests..."
        pytest -m integration -v
        ;;
    quick)
        echo "⚡ Running quick tests (no network, no slow)..."
        pytest -m "unit and not slow" -v
        ;;
    coverage)
        echo "📊 Running tests with coverage..."
        pytest --cov --cov-report=term-missing --cov-report=html
        echo ""
        echo "📄 Coverage report generated: htmlcov/index.html"
        ;;
    network)
        echo "🌐 Running network tests (requires internet)..."
        pytest -m requires_network -v
        ;;
    all)
        echo "🧪 Running all tests..."
        pytest -v
        ;;
    *)
        echo "Usage: $0 [unit|integration|quick|coverage|network|all]"
        echo ""
        echo "  unit        - Run fast unit tests only"
        echo "  integration - Run integration tests"
        echo "  quick       - Run quick tests (no network/slow)"
        echo "  coverage    - Run with coverage report"
        echo "  network     - Run network-dependent tests"
        echo "  all         - Run all tests (default)"
        exit 1
        ;;
esac

exit_code=$?

echo ""
if [ $exit_code -eq 0 ]; then
    echo "✅ All tests passed!"
else
    echo "❌ Some tests failed. Exit code: $exit_code"
fi

exit $exit_code
