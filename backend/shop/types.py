from typing import TypedDict


class FkCropperPayload(TypedDict):
    field_name: str
    label: str
    input_id: str
    target_field_name: str
    target_input_id: str
    preview_shape: str
    crop_aspect_ratio: float
    visible_tab_panel: str
    lookup_url: str
    source_image_url: str
    output_width: int
    output_height: int
