from django import forms

from .models import GlobalParameter
from .services import coerce_value, set_parameter_value


class GlobalParameterAdminForm(forms.ModelForm):
    value = forms.CharField(
        required=False,
        widget=forms.Textarea,
        help_text="Enter value matching the selected type",
    )

    class Meta:
        model = GlobalParameter
        fields = ["name", "description", "type", "is_active"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.instance and self.instance.pk:
            self.fields["value"].initial = self.instance.get_value()

    def clean(self):
        cleaned = super().clean()

        param_type = cleaned.get("type")
        raw_value = cleaned.get("value")

        cleaned["value"] = coerce_value(param_type, raw_value)

        return cleaned

    def save(self, commit=True):
        instance = super().save(commit)

        value = self.cleaned_data.get("value")
        set_parameter_value(instance, value)

        return instance