from django.db import models
from django.contrib.contenttypes.models import ContentType

# Create your models here.
class RoleFieldPermission(models.Model):
    role = models.ForeignKey("users.UserRole", on_delete=models.CASCADE)

    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    field_name = models.CharField(max_length=255)

    permission = models.PositiveIntegerField(default=0)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=[
                    "role",
                    "content_type",
                    "field_name"
                ],
                name="unique_role_field_permission"
            )
        ]

class UserFieldPermission(models.Model):
    user = models.ForeignKey("users.User", on_delete=models.CASCADE)

    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    field_name = models.CharField(max_length=255)

    permission = models.PositiveIntegerField(default=0)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=[
                    "user",
                    "content_type",
                    "field_name"
                ],
                name="unique_user_field_permission"
            )
        ]