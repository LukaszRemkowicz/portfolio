from taggit.models import Tag

from django import forms
from django.contrib.admin.widgets import FilteredSelectMultiple

from .models import AstroImage


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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
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
