from django.db import transaction
from django.contrib.contenttypes.models import ContentType
from ..models import UserRole
from iam.models import RoleFieldPermission
from ..registry import user_role_registry

@transaction.atomic
def sync_roles():
    for key, role_def in user_role_registry.items():
        role, _ = UserRole.objects.update_or_create(
            key=key,
            defaults={
                "label": role_def.label,
                "is_system": role_def.system,
            }
        )

        # Apply default permissions (only if not exists)
        for (model_path, field_name), perm in role_def.default_permissions.items():
            app_label, model_name = model_path.split(".")

            ct = ContentType.objects.get(
                app_label=app_label,
                model=model_name.lower()
            )

            RoleFieldPermission.objects.get_or_create(
                role=role,
                content_type=ct,
                field_name=field_name,
                defaults={"permission": perm}
            )