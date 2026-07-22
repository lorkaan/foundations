from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.utils import timezone
import pghistory

from base.models import ActiveMixin, BaseUuidPrimaryKeyModel, CreatedByMixin, RequiredGenericUuidTargetMixin, TimeAuditableMixin
from .registry import USER_ASSIGNABLE_MODELS_REGISTRY
from .managers import UserManager

@pghistory.track()
class UserRole(models.Model):
    key = models.CharField(max_length=50, unique=True)
    label = models.CharField(max_length=255)

    is_system = models.BooleanField(default=False)

    def __str__(self):
        return self.label

@pghistory.track()
class User(AbstractBaseUser, PermissionsMixin, ActiveMixin, TimeAuditableMixin, BaseUuidPrimaryKeyModel):
    username = models.CharField(max_length=150, unique=True)
    full_name = models.CharField(max_length=255, blank=True)
    email = models.EmailField(unique=True, null=True, blank=True)
    #role = models.CharField(max_length=1, choices=UserRole.choices, default=UserRole.GUEST)
    role = models.ForeignKey(UserRole, on_delete=models.PROTECT, related_name="users")

    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)

    objects = UserManager()

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = []  # no other required fields for createsuperuser

    def __str__(self):
        return self.username
    
@pghistory.track()
class UserAssignment(RequiredGenericUuidTargetMixin, ActiveMixin, CreatedByMixin, TimeAuditableMixin, BaseUuidPrimaryKeyModel):

    user = models.ForeignKey(User, on_delete=models.PROTECT)

    def get_allowed_registry(self):
        return USER_ASSIGNABLE_MODELS_REGISTRY

    def __str__(self):
        return f"UserAssignment({self.id})"

