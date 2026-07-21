from django.contrib.auth.models import BaseUserManager
from django.core.exceptions import ObjectDoesNotExist

from .models import UserRole


class UserManager(BaseUserManager):

    def _resolve_role(self, role_input):
        """
        Accepts:
        - None → default to 'guest'
        - string → lookup by key
        - UserRole instance → return as-is
        """
        if role_input is None:
            role_input = "guest"

        if isinstance(role_input, UserRole):
            return role_input

        if isinstance(role_input, str):
            try:
                return UserRole.objects.get(key=role_input)
            except ObjectDoesNotExist:
                raise ValueError(f"Invalid role: {role_input}")

        raise TypeError("role must be a string key or UserRole instance")

    def create_user(self, username, password=None, **extra_fields):
        if not username:
            raise ValueError("Users must have a username")

        role_input = extra_fields.pop("role", None)
        role = self._resolve_role(role_input)

        user = self.model(
            username=username,
            role=role,
            **extra_fields
        )

        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if not extra_fields.get("is_staff"):
            raise ValueError("Superuser must have is_staff=True.")

        if not extra_fields.get("is_superuser"):
            raise ValueError("Superuser must have is_superuser=True.")

        # Force admin role
        extra_fields["role"] = "admin"

        user  = self.create_user(username, password, **extra_fields)

        if user.role.key != "admin":
            raise ValueError("Superuser must have admin role")

        return user
    
