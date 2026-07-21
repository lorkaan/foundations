
def can_view(user, sensitivity: str) -> bool:
    if user.is_superuser:
        return True

    if sensitivity == "P":
        return True

    if sensitivity == "I":
        return user.is_staff

    if sensitivity == "S":
        return getattr(user, "can_view_sensitive", False)

    if sensitivity == "H":
        return getattr(user, "can_view_highly_sensitive", False)

    return False