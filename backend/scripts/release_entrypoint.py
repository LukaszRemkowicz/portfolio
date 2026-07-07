"""Release-time backend configuration entry point."""

from __future__ import annotations

import logging
import subprocess
import sys

logger = logging.getLogger(__name__)

RELEASE_CONFIGURATION_COMMANDS: tuple[str, ...] = ("backfill_image_variants",)


def main() -> int:
    """Run release-time configuration commands in a predictable order."""
    for command in RELEASE_CONFIGURATION_COMMANDS:
        logger.info("Running release configuration step", extra={"command": command})
        subprocess.run(
            (sys.executable, "manage.py", command, "--verbosity", "0", "--silent"),
            check=True,
        )

    logger.info("Release configuration complete")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
