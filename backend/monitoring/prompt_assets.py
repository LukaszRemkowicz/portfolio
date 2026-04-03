import json
from pathlib import Path

type JSONPrimitive = str | int | float | bool | None
type JSONValue = JSONPrimitive | list[JSONValue] | dict[str, JSONValue]
type JSONObject = dict[str, JSONValue]


class PromptAssetLoader:
    def __init__(self, base_dir: Path | None = None) -> None:
        resolved_base_dir: Path = base_dir or Path(__file__).resolve().parent / "agent_assets"
        self.base_dir: Path = resolved_base_dir

    def get_path(self, relative_path: str) -> Path:
        asset_path: Path = self.base_dir / relative_path
        if not asset_path.exists():
            raise FileNotFoundError(f"Prompt asset not found: {asset_path}")
        return asset_path

    def load_text(self, relative_path: str) -> str:
        asset_path: Path = self.get_path(relative_path)
        return asset_path.read_text(encoding="utf-8")

    def load_json(self, relative_path: str) -> JSONObject:
        asset_path: Path = self.get_path(relative_path)
        with asset_path.open(encoding="utf-8") as handle:
            payload: JSONValue = json.load(handle)

        if not isinstance(payload, dict):
            raise ValueError(f"Prompt asset JSON must be an object: {asset_path}")

        return payload
