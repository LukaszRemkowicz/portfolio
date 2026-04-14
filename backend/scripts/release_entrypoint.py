"""Release-time backend configuration entry point."""

from __future__ import annotations

import subprocess
import sys

RELEASE_CONFIGURATION_COMMANDS: tuple[tuple[str, ...], ...] = (
    (sys.executable, "manage.py", "configure_shop"),
)


def main() -> int:
    """Run release-time configuration commands in a predictable order."""
    for command in RELEASE_CONFIGURATION_COMMANDS:
        printable_command = " ".join(command)
        print(f"Running release configuration step: {printable_command}")
        subprocess.run(command, check=True)

    print("Release configuration complete.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
