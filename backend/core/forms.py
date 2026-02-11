# core/forms.py
from django import forms

from .widgets import RangeWidget


class RangeField(forms.MultiValueField):
    """
    A MultiValueField that uses RangeWidget to manage [min, max] pairs.
    """

    def __init__(self, field_class, placeholder_min="", placeholder_max="", *args, **kwargs):
        self.widget = RangeWidget(placeholder_min=placeholder_min, placeholder_max=placeholder_max)
        fields = (
            field_class(),
            field_class(),
        )
        super().__init__(fields, *args, **kwargs)

    def compress(self, data_list):
        if data_list:
            # Sort to ensure [min, max] if applicable
            try:
                # Filter None values and sort
                valid_values = [x for x in data_list if x is not None]
                return sorted(valid_values)
            except TypeError:
                return list(data_list)
        return list()
