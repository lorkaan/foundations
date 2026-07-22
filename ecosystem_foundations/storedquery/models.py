from django.db import models
from django.db.models import Q
from django.apps import apps
from django.contrib.contenttypes.models import ContentType
import pghistory

from base.models import BaseUuidPrimaryKeyModel, TimeAuditableMixin
from users.models import User

# Create your models here.
@pghistory.track()
class SavedQuery(TimeAuditableMixin, BaseUuidPrimaryKeyModel):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)

    query = models.JSONField()

    owner = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="owned_queries"
    )

    is_system = models.BooleanField(
        default=False,
        help_text="System-managed default query"
    )

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=(
                    Q(is_system=True, owner__isnull=True) |
                    Q(is_system=False)
                ),
                name="system_queries_have_no_owner"
            )
        ]

    def to_ast_payload(self):
        return {
            "query": self.query,
            "model": self.model
        }
    
    def get_model_class(self):
        app_label, model_name = self.model.split(".")
        return apps.get_model(app_label, model_name)

class SavedQueryPermission(models.Model):

    query = models.ForeignKey(
        SavedQuery,
        on_delete=models.CASCADE,
        related_name="permissions"
    )

    role = models.ForeignKey(
        "users.UserRole",
        null=True,
        blank=True,
        on_delete=models.CASCADE
    )

    user = models.ForeignKey(
        "users.User",
        null=True,
        blank=True,
        on_delete=models.CASCADE
    )

    level = models.PositiveSmallIntegerField(
        choices=Level.choices,
        default=Level.VIEW
    )

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=(
                    models.Q(role__isnull=False, user__isnull=True) |
                    models.Q(role__isnull=True, user__isnull=False)
                ),
                name="query_permission_role_xor_user"
            ),
            models.UniqueConstraint(
                fields=["query", "role"],
                condition=models.Q(role__isnull=False),
                name="unique_query_role_permission"
            ),
            models.UniqueConstraint(
                fields=["query", "user"],
                condition=models.Q(user__isnull=False),
                name="unique_query_user_permission"
            ),
        ]