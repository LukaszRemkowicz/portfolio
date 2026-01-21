from django_countries import countries
from taggit.models import Tag

from django import forms
from django.contrib.admin.widgets import FilteredSelectMultiple
from django.utils.translation import gettext_lazy as _

from core.widgets import ThemedSelect2Widget

from .models import AstroImage, Place


class AstroImageForm(forms.ModelForm):
    tags = forms.ModelMultipleChoiceField(
        queryset=Tag.objects.all(),
        required=False,
        widget=FilteredSelectMultiple("Tags", is_stacked=False),
        label="Tags",
    )

    class Meta:
        model = AstroImage
        fields = "__all__"
        widgets = {
            "location": ThemedSelect2Widget(),
            "place": ThemedSelect2Widget(
                tags=True,
                attrs={
                    "data-placeholder": _("Select or type place..."),
                    "data-allow-clear": "true",
                },
            ),
        }

    def clean_place(self):
        place = self.cleaned_data.get("place")
        if not place:
            # If empty, but we might have typed something
            place_name = self.data.get("place")
            if place_name:
                place, _ = Place.objects.get_or_create(name=place_name)
        elif isinstance(place, str):
            # If Select2 returned the string directly because it's a new tag
            place, _ = Place.objects.get_or_create(name=place)
        return place

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Enhance location (country) labels with codes for better searchability
        if "location" in self.fields:
            enhanced_choices = [("", "---------")]
            for code, name in self.fields["location"].choices:
                if code:
                    alpha3 = countries.alpha3(code)
                    label = f"{name} ({code}"
                    if alpha3:
                        label += f", {alpha3}"
                    label += ")"
                    enhanced_choices.append((code, label))
            self.fields["location"].choices = enhanced_choices

        if self.instance.pk:
            self.fields["tags"].initial = self.instance.tags.all()

    def save(self, commit=True):
        instance = super().save(commit=False)

        def save_tags():
            instance.tags.set(self.cleaned_data["tags"])

        # Override save_m2m to handle taggit manager
        old_save_m2m = self.save_m2m

        def save_m2m():
            old_save_m2m()
            save_tags()

        self.save_m2m = save_m2m

        if commit:
            instance.save()
            self.save_m2m()

        return instance
