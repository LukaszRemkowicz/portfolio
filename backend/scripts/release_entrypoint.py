"""Release-time backend configuration entry point."""

from __future__ import annotations

import logging
import subprocess
import sys

logger = logging.getLogger(__name__)

RELEASE_CONFIGURATION_COMMANDS: tuple[tuple[str, ...], ...] = (
    (sys.executable, "manage.py", "backfill_baseimage_fields"),
)


def main() -> int:
    """Run release-time configuration commands in a predictable order."""
    for command in RELEASE_CONFIGURATION_COMMANDS:
        printable_command = " ".join(command)
        logger.info("Running release configuration step", extra={"command": printable_command})
        print(f"Running release configuration step: {printable_command}")
        subprocess.run(command, check=True)

    logger.info("Release configuration complete")
    print("Release configuration complete.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
