from dataclasses import dataclass
from enum import StrEnum
from typing import Any


class CropperPreviewShape(StrEnum):
    CIRCLE = "circle"
    ROUNDED_SQUARE = "rounded-square"


@dataclass(slots=True)
class CropperFieldConfig:
    field_name: str
    label: Any
    input_id: str
    target_field_name: str
    target_input_id: str
    spec_method: str
    preview_shape: CropperPreviewShape
    crop_aspect_ratio: float
