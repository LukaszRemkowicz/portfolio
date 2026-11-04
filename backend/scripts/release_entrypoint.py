"""Release-time backend configuration entry point."""

from __future__ import annotations

import logging
import os
import subprocess
import sys

logger = logging.getLogger(__name__)

RELEASE_CONFIGURATION_COMMANDS: tuple[str, ...] = ("backfill_image_variants",)


def main() -> int:
    """Run release-time configuration commands in a predictable order."""
    commands: list[tuple[str, ...]] = [
        (command, "--verbosity", "0", "--silent") for command in RELEASE_CONFIGURATION_COMMANDS
    ]
    if os.environ.get("ENVIRONMENT") in {"prod", "production"}:
        commands.append(
            (
                "repair_travel_place",
                "--place-id",
                "53",
                "--country",
                "PL",
                "--apply",
                "--if-country-empty",
            )
        )

    for command_args in commands:
        logger.info("Running release configuration step", extra={"command": command_args[0]})
        subprocess.run(
            (sys.executable, "manage.py", *command_args),
            check=True,
        )

    logger.info("Release configuration complete")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
