import os
import shutil
import subprocess
import sys


def run_in_docker(command):
    """Run a command inside the portfolio-test container."""
    # Check if we should use Doppler for secret injection
    # If DOPPLER_CONFIG is set, we are already in a doppler run bubble
    use_doppler = shutil.which("doppler") and not os.environ.get("DOPPLER_CONFIG")

    full_cmd = []
    if use_doppler:
        full_cmd.extend(["doppler", "run", "--"])

    full_cmd.extend(["docker", "compose", "run", "--rm", "--remove-orphans", "portfolio-test"])
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
