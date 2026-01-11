import subprocess
import sys


def test():
    """Run all tests using pytest."""
    result = subprocess.run(["pytest"])
    sys.exit(result.returncode)


def test_cov():
    """Run tests with coverage report."""
    result = subprocess.run(["pytest", "--cov=.", "--cov-report=term-missing"])
    sys.exit(result.returncode)


def safety_check():
    """Run security scan on dependencies."""
    result = subprocess.run(["safety", "scan"])
    sys.exit(result.returncode)
