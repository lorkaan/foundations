

def can_access_query(user, query, level="view"):
    if user.is_superuser:
        return True

    # Owner always has full access
    if query.owner == user:
        return True

    # System query → readable by default?
    if query.is_system and level == "view":
        return True

    # User-specific permission
    user_perm = query.permissions.filter(user=user).first()
    if user_perm and user_perm.level >= level:
        return True

    # Role-based permission
    role_perm = query.permissions.filter(role=user.role).first()
    if role_perm and role_perm.level >= level:
        return True

    return False