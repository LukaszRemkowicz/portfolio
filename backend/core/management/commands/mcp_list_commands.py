"""List landingpage Django commands exposed to the MCP socket connector."""

from __future__ import annotations

import json
from typing import Any

from django.core.management.base import BaseCommand

COMMANDS: list[dict[str, Any]] = [
    {
        "name": "media_inventory",
        "description": "Inspect DB image references and media files on disk.",
        "read_only": True,
        "params": {},
    }
]


class Command(BaseCommand):
    """Return the fixed landingpage Django command inventory for MCP."""

    help = "List fixed landingpage Django commands exposed to the MCP socket connector."

    def add_arguments(self, parser):
        parser.add_argument(
            "--json",
            action="store_true",
            dest="json_output",
            help="Return the command inventory as JSON.",
        )

    def handle(self, *args, **options):
        payload = {"commands": COMMANDS}
        if options["json_output"]:
            self.stdout.write(json.dumps(payload, separators=(",", ":")))
            return

        for command in COMMANDS:
            self.stdout.write(f"{command['name']}: {command['description']}")
