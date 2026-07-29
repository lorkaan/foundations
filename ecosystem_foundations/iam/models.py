import enum

from django.db import models
from django.contrib.contenttypes.models import ContentType

from .flags import PermissionFlag

class FieldPermission(models.Model):

    permission = models.PositiveIntegerField(default=0)

    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    field_name = models.CharField(max_length=255)

    class Meta:
        abstract = True

    # -------------------------
    # Bitmask interface
    # -------------------------
    @property
    def permissions(self) -> PermissionFlag:
        return PermissionFlag(self.permission)

    @permissions.setter
    def permissions(self, value: PermissionFlag):
        self.permission = int(value)

    # -------------------------
    # Helpers
    # -------------------------
    def has(self, flag: PermissionFlag) -> bool:
        return bool(self.permissions & flag)

    def add(self, flag: PermissionFlag):
        self.permissions = self.permissions | flag

    def remove(self, flag: PermissionFlag):
        self.permissions = self.permissions & ~flag

# Create your models here.
class RoleFieldPermission(FieldPermission):
    role = models.ForeignKey("users.UserRole", on_delete=models.CASCADE)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=[
                    "role",
                    "content_type",
                    "field_name"
                ],
                name="%(app_label)s_%(class)s_unique"
            )
        ]


class UserFieldPermission(FieldPermission):
    user = models.ForeignKey("users.User", on_delete=models.CASCADE)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=[
                    "user",
                    "content_type",
                    "field_name"
                ],
                name="%(app_label)s_%(class)s_unique"
            )
        ]