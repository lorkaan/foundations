import numbers
import uuid

from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone

# Create your models here.

"""
    UUID Primary Key Base Model. Used for things that need tracking.

    Additionally, due to tracking requirements, added created_at and updated_at 
    to enable the capacity for audits
"""
class BaseUuidPrimaryKeyModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    class Meta:
        abstract = True

"""
    Handles the Mixins for Time based auditable data. Specifically, adds a created_at and updated_at
    which is useful for data that needs to be auditable, or for syncing data.
"""
class TimeAuditableMixin(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

"""
    This will be a mixin class that allows a row to marked as Active or Not Active.
"""
class ActiveMixin(models.Model):
    is_active = models.BooleanField(default=True, db_index=True)
    deactivated_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        abstract = True

    def deactivate(self):
        self.is_active = False
        self.deactivated_at = timezone.now()

    def activate(self):
        self.is_active = True
        self.deactivated_at = None

"""
    Soft Delete functionality allowed to perform quick actions and delete data later.
"""
class SoftDeleteMixin(models.Model):
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        abstract = True

    def delete(self, using=None, keep_parents=False):
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save()

"""
    Base Mixin class for handling the Generic Relations without specifying the Target's Primary Key
"""
class BaseGenericTargetMixin(models.Model):

    content_object = GenericForeignKey(
        "content_type",
        "object_id"
    )

    class Meta:
        abstract = True

    def set_target(self, obj):
        pk = obj.pk
        self.validate_pk(pk)

        self.content_type = ContentType.objects.get_for_model(obj)
        self.object_id = pk


    def validate_pk(self, pk):
        """Override in subclasses"""
        return True

"""
    This is the Base class for Required Generic Target Mixins.
    All the classes that implement specifically typed Primary Key models will inherit from this.
    Specifically, this class requires that this relation must exist.
"""
class BaseRequiredGenericTargetMixin(BaseGenericTargetMixin):

    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)

    class Meta:
        abstract = True

    def set_target(self, obj):
        if obj is None:
            raise ValueError("Target cannot be None for required relation")
        super().set_target(obj)

"""
    This is the Base class for Required Generic Target Mixins.
    All the classes that implement specifically typed Primary Key models will inherit from this.
    Specifically, this class does not require that this relation exist, allowing it to be None.
"""
class BaseOptionalGenericTargetMixin(BaseGenericTargetMixin):

    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    class Meta:
        abstract = True
        constraints = [
            models.CheckConstraint(
                condition=(
                    models.Q(content_type__isnull=True, object_id__isnull=True) |
                    models.Q(content_type__isnull=False, object_id__isnull=False)
                ),
                name="%(app_label)s_%(class)s_valid_generic_relation"
            )
        ]

    def set_target(self, obj):
        if obj is None:
            self.content_type = None
            self.object_id = None
        else:
            super().set_target(obj)

"""
    This is the model for a Generic Relation to a Target with a UUID Primary Key.
    Specifically, this enforces that the generic relation must exist, or is required.
"""
class RequiredGenericUuidTargetMixin(BaseRequiredGenericTargetMixin):
    object_id = models.UUIDField()

    class Meta:
        abstract = True

    def validate_pk(self, pk):
        """ UUID validation that is Required """
        try:
            uuid.UUID(str(pk))
        except Exception:
            raise TypeError("Expected UUID primary key")

"""
    This is the model for a Generic Relation to a Target with a UUID Primary Key.
    Specifically, this enforces that the generic relation must exist, or is required.
"""
class RequiredGenericIntTargetMixin(BaseRequiredGenericTargetMixin):

    object_id = models.PositiveBigIntegerField()

    class Meta:
        abstract = True

    def validate_pk(self, pk):
        """ Bit Int validation that is Required """
        if not isinstance(pk, numbers.Integral) or pk <= 0:
            raise TypeError("Expected Positive Integer primary key")


"""
    This is the model for a Generic Relation to a Target with a UUID Primary Key.
    Specifically, this relation is optional, or can be None or Null.
"""
class OptionalGenericUuidTargetMixin(BaseOptionalGenericTargetMixin):

    object_id = models.UUIDField(null=True, blank=True)

    class Meta:
        abstract = True

    def validate_pk(self, pk):
        """ UUID validation that is Required """
        try:
            uuid.UUID(str(pk))
        except Exception:
            raise TypeError("Expected UUID primary key")


"""
    This is a optional, or non-required, Generic Relation to a Target that
    has a Positive Big Integer as the Primary Key.
"""
class OptionalGenericIntTargetMixin(BaseOptionalGenericTargetMixin):

    # For BigAutoField / bigint PKs
    object_id = models.PositiveBigIntegerField(
        null=True,
        blank=True
    )

    class Meta:
        abstract = True

    def validate_pk(self, pk):
        """ Bit Int validation that is Required """
        if not isinstance(pk, numbers.Integral) or pk <= 0:
            raise TypeError("Expected Positive Integer primary key")

"""
    Mixin for storing a reference to a Django model (not an instance).

    This allows dynamic, pluggable behavior based on model types.
"""  
class GenericPointerToClassMixin(models.Model):

    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
    )

    class Meta:
        abstract = True
        indexes = [
            models.Index(fields=["content_type"]),
        ]

    # ---------- Shared Helper Function ------------

    @classmethod
    def _as_iterable(cls, value):
        if value is None:
            return []
        if isinstance(value, (list, tuple, set)):
            return value
        return [value]

    # ---------- Core API ----------

    def set_model(self, model_or_instance):
        """
        Accepts a model class or instance and stores its ContentType.
        """
        model_class = self._resolve_model_class(model_or_instance)

        self.validate_model(model_class)

        self.content_type = ContentType.objects.get_for_model(
            model_class,
            for_concrete_model=self.use_concrete_model()
        )

    def get_model_class(self):
        """
        Returns the Django model class.
        """
        model_class = self.content_type.model_class()

        if model_class is None:
            raise LookupError(
                f"ContentType {self.content_type} no longer resolves to a model"
            )

        return model_class

    # ---------- Hooks for subclasses ----------

    def validate_model(self, model_class):
        """
        Override to restrict allowed models.
        """
        pass

    def use_concrete_model(self):
        """
        Override if you want proxy models collapsed to concrete ones.
        """
        return False

    # ---------- Internal helpers ----------

    def _resolve_model_class(self, model_or_instance):
        """
        Normalizes input into a model class.
        """
        if isinstance(model_or_instance, type):
            return model_or_instance

        return model_or_instance.__class__

    # ---------- Representation ----------

    def __str__(self):
        model = self.content_type.model

        parts = [model]

        # Optional attributes (safe access)
        field_name = getattr(self, "field_name", None)
        label = getattr(self, "label", None)

        if field_name:
            parts.append(field_name)
        if label:
            parts.append(f"→ {label}")

        return ".".join(parts)
    
"""
    White Lists Allowed classes that can be pointed to by this Mixin.

    Option 1: Allow multiple model types (whitelist)
"""
class ModelRestrictedPointerToClassMixin(GenericPointerToClassMixin):

    class Meta:
        abstract = True

    ALLOWED_MODELS = None

    def validate_model(self, model_class):
        super().validate_model(model_class)

        allowed = self.__class__._as_iterable(self.ALLOWED_MODELS)

        if allowed and model_class not in allowed:
            raise ValueError(
                f"{model_class.__name__} not allowed. "
                f"Allowed: {[m.__name__ for m in allowed]}"
            )
        
"""
    Enables Interface based restrictions for allowed classes that can be pointed to by this Mixin.

    Option 3: Restrict by interface (very powerful)   
"""
class InterfaceRestrictedPointerToClassMixin(GenericPointerToClassMixin):

    class Meta:
        abstract = True

    REQUIRED_ATTRIBUTES = None  # list of attribute names

    def validate_model(self, model_class):
        super().validate_model(model_class)

        attrs = self.__class__._as_iterable(self.REQUIRED_ATTRIBUTES)

        for attr in attrs:
            if not hasattr(model_class, attr):
                raise ValueError(
                    f"{model_class.__name__} must implement '{attr}'"
                )

"""
    Option 2: Restrict by app 
"""
class AppRestrictedPointerToClassMixin(GenericPointerToClassMixin):

    class Meta:
        abstract = True

    ALLOWED_APPS = None

    def validate_model(self, model_class):
        super().validate_model(model_class)

        allowed = self.__class__._as_iterable(self.ALLOWED_APPS)

        if allowed and model_class._meta.app_label not in allowed:
            raise ValueError(
                f"{model_class.__name__} must belong to one of {allowed}"
            )

"""
    Abstract model for handling models that represent something that should be run, 
    such as Actions, and need to store for audit purposes.
"""
class BaseRunModel(TimeAuditableMixin, BaseUuidPrimaryKeyModel):

    class RunStatus(models.TextChoices):
        PENDING = "P", "Pending"
        RUNNING = "R", "Running"
        COMPLETED = "C", "Completed"
        FAILED = "F", "Failed"

    status = models.CharField(
        max_length=1,
        choices=RunStatus.choices,
        default=RunStatus.PENDING
    )

    class Meta:
        abstract = True