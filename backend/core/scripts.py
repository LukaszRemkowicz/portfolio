import subprocess
import sys


def run_in_docker(command):
    """Run a command inside the portfolio-test container."""
    full_cmd = ["docker", "compose", "run", "--rm"]
    full_cmd.append("portfolio-test")
    full_cmd.extend(command)

    result = subprocess.run(full_cmd)
    sys.exit(result.returncode)


def test():
    """Run tests in Docker with optional arguments."""
    run_in_docker(["pytest"] + sys.argv[1:])


def test_cov():
    """Run tests with coverage in Docker with optional arguments."""
    run_in_docker(["pytest", "--cov=.", "--cov-report=term-missing"] + sys.argv[1:])


def security():
    """Run security scan locally with optional arguments."""
    cmd = ["safety", "scan"] + sys.argv[1:]
    result = subprocess.run(cmd)
    sys.exit(result.returncode)
