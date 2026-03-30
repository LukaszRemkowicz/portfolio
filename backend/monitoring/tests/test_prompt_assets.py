from pathlib import Path

import pytest

from monitoring.prompt_assets import JSONObject, PromptAssetLoader


class TestPromptAssetLoader:
    def test_load_text_reads_existing_prompt(self):
        loader: PromptAssetLoader = PromptAssetLoader()

        content: str = loader.load_text("prompts/monitoring_job_system.md")

        assert "scheduled monitoring job" in content

    def test_load_json_reads_existing_schema(self):
        loader: PromptAssetLoader = PromptAssetLoader()

        payload: JSONObject = loader.load_json("schemas/monitoring_job_response.schema.json")

        assert payload["type"] == "object"
        assert payload["required"] == ["summary", "findings"]

    def test_missing_asset_raises_file_not_found(self, tmp_path: Path):
        loader: PromptAssetLoader = PromptAssetLoader(base_dir=tmp_path)

        with pytest.raises(FileNotFoundError, match="Prompt asset not found"):
            loader.load_text("prompts/missing.md")

    def test_load_json_requires_object_root(self, tmp_path: Path):
        schema_path: Path = tmp_path / "schemas"
        schema_path.mkdir()
        (schema_path / "bad.json").write_text('["not", "an", "object"]', encoding="utf-8")
        loader: PromptAssetLoader = PromptAssetLoader(base_dir=tmp_path)

        with pytest.raises(ValueError, match="JSON must be an object"):
            loader.load_json("schemas/bad.json")
