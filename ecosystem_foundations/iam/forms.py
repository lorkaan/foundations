from django import forms
from .models import RoleFieldPermission, UserFieldPermission
from .flags import PermissionFlag


class BaseFieldPermissionForm(forms.ModelForm):
    view = forms.BooleanField(required=False)
    edit = forms.BooleanField(required=False)
    add = forms.BooleanField(required=False)
    delete = forms.BooleanField(required=False)

    FLAG_MAP = {
        "view": PermissionFlag.VIEW,
        "edit": PermissionFlag.EDIT,
        "add": PermissionFlag.ADD,
        "delete": PermissionFlag.DELETE,
    }

    class Meta:
        abstract = True  # purely conceptual, Django ignores this but we keep intent clear
        fields = "__all__"

    # -------------------------
    # Init (populate checkboxes)
    # -------------------------
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.instance and self.instance.pk:
            for field_name, flag in self.FLAG_MAP.items():
                self.fields[field_name].initial = self.instance.has(flag)

    # -------------------------
    # Save (build bitmask)
    # -------------------------
    def save(self, commit=True):
        instance = super().save(commit=False)

        permissions = PermissionFlag(0)

        for field_name, flag in self.FLAG_MAP.items():
            if self.cleaned_data.get(field_name):
                permissions |= flag

        instance.permissions = permissions  # uses your property setter

        if commit:
            instance.save()

        return instance

class RoleFieldPermissionForm(BaseFieldPermissionForm):
    class Meta:
        model = RoleFieldPermission
        fields = "__all__"

class UserFieldPermissionForm(BaseFieldPermissionForm):
    class Meta:
        model = UserFieldPermission
        fields = "__all__"