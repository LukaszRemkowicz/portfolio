"""Release-time backend configuration entry point."""

from __future__ import annotations

import logging
import subprocess
import sys

logger = logging.getLogger(__name__)

# One-off release steps go here as manage.py argument tuples; remove them once
# they have run in production.
RELEASE_CONFIGURATION_COMMANDS: tuple[tuple[str, ...], ...] = ()


def main() -> int:
    """Run release-time configuration commands in a predictable order."""
    for command_args in RELEASE_CONFIGURATION_COMMANDS:
        logger.info("Running release configuration step", extra={"command": command_args[0]})
        subprocess.run(
            (sys.executable, "manage.py", *command_args),
            check=True,
        )

    logger.info("Release configuration complete")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
