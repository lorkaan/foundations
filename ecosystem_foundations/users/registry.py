from dataclasses import dataclass, field
from typing import Dict, Iterable

from base.registry import ModelRegistry

@dataclass(frozen=True)
class RoleDefinition:
    key: str
    label: str
    system: bool = False
    default_permissions: dict = field(default_factory=dict)

class UserRoleRegistry:
    """
    Typed registry for RoleDefinition objects.
    Designed for plugin-based role registration.
    """

    def __init__(self):
        self._roles: Dict[str, RoleDefinition] = {}
        self._locked = False

    # ------------------------
    # Registration
    # ------------------------
    def register(self, role: RoleDefinition, *, replace: bool = False) -> RoleDefinition:
        if self._locked:
            raise RuntimeError("UserRoleRegistry is locked")

        if not isinstance(role, RoleDefinition):
            raise TypeError("Only RoleDefinition instances can be registered")

        if not role.key or not role.key.strip():
            raise ValueError("Role key cannot be empty")

        if role.key in self._roles and not replace:
            raise ValueError(f"Role '{role.key}' is already registered")

        self._roles[role.key] = role
        return role

    # ------------------------
    # Accessors
    # ------------------------
    def get(self, key: str) -> RoleDefinition | None:
        return self._roles.get(key)

    def require(self, key: str) -> RoleDefinition:
        role = self.get(key)
        if not role:
            raise KeyError(f"Role '{key}' is not registered")
        return role

    def all(self) -> Iterable[RoleDefinition]:
        return self._roles.values()

    def keys(self):
        return self._roles.keys()

    def items(self):
        return self._roles.items()

    def __contains__(self, key: str):
        return key in self._roles

    def __len__(self):
        return len(self._roles)

    # ------------------------
    # Lifecycle
    # ------------------------
    def lock(self):
        """Prevent further registrations (call after app boot)"""
        self._locked = True


USER_ROLE_REGISTRY = UserRoleRegistry()

def register_role(key: str, label: str, *, system=False):
    role = RoleDefinition(key=key, label=label, system=system)
    return USER_ROLE_REGISTRY.register(role)

USER_ASSIGNABLE_MODELS_REGISTRY = ModelRegistry()