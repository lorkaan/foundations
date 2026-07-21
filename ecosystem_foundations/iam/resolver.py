from django.contrib.contenttypes.models import ContentType
from .models import UserFieldPermission, RoleFieldPermission

def has_field_permission(user, model, field_name, flag):
    if user.is_superuser:
        return True

    ct = ContentType.objects.get_for_model(model)

    # 1. User override
    user_perm = UserFieldPermission.objects.filter(
        user=user,
        content_type=ct,
        field_name=field_name
    ).first()

    if user_perm:
        return bool(user_perm.permission & flag)

    # 2. Role fallback
    role_perm = RoleFieldPermission.objects.filter(
        role=user.role,
        content_type=ct,
        field_name=field_name
    ).first()

    if role_perm:
        return bool(role_perm.permission & flag)

    return False