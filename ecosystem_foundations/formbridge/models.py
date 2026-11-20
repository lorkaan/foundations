from django.db import models
from django.contrib.contenttypes.models import ContentType
from ..dynamicforms.models import FormGroup, FormType
from django.core.exceptions import ValidationError
import pghistory

from ..base.models import ActiveMixin, BaseItemType, Configable, TimeAuditableMixin

class ModelDataBridge(TimeAuditableMixin, BaseItemType):
    config = models.JSONField()

    class Meta:
        abstract = True

# Create your models here.

# New Models to try a new system that is reminisciate of the Neural Network architecture
class DataVertex(Configable, ActiveMixin, models.Model):

    target_content_type = models.ForeignKey(ContentType, on_delete=models.PROTECT, blank=True, null=True)

    class Meta:
        abstract = True

    

class FormTypeDataEnvironment(Configable, models.Model):
    form_type = models.ForeignKey(FormType, on_delete=models.PROTECT, related_name="processors")

class FormDataVertex(DataVertex, models.Model):
    env = models.ForeignKey(FormTypeDataEnvironment, on_delete=models.CASCADE, related_name="nodes")
    form_group = models.ForeignKey(FormGroup, on_delete=models.PROTECT, blank=True, null=True, related_name="mappings")

    @property
    def is_input(self):
        return self.form_group_id is not None

    @property
    def is_output(self):
        return self.target_content_type_id is not None

    @property
    def is_hidden(self):
        return not self.is_input and not self.is_output


class FormDataEdge(models.Model):
    src = models.ForeignKey(FormDataVertex, on_delete=models.CASCADE, related_name="outgoing_edges")
    dst = models.ForeignKey(FormDataVertex, on_delete=models.CASCADE, related_name="incoming_edges")
    name = models.CharField(max_length=255)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=~models.Q(name=""),
                name="edge_name_not_empty",
            ),
            models.CheckConstraint(
                condition=~models.Q(src=models.F("dst")),
                name="edge_src_dst_must_differ",
            ),
            models.UniqueConstraint(
                fields=["src", "dst"],
                name="unique_edge_src_dst",
            ),
            models.UniqueConstraint(
                fields=["name", "dst"],
                name="unique_edge_name_dst",
            ),
        ]

    def clean(self):
        super().clean()

        if (
            self.src_id
            and self.dst_id
            and (
                self.src.env_id != self.dst.env_id
            )
        ):
            raise ValidationError(
                "Source, destination must belong to the same environment."
            )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

class FormDataDependency(models.Model):
    dependent = models.ForeignKey(
        FormDataVertex,
        on_delete=models.CASCADE,
        related_name="dependencies",
    )
    prerequisite = models.ForeignKey(
        FormDataVertex,
        on_delete=models.CASCADE,
        related_name="dependents",
    )

    name = models.CharField(max_length=255)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=~models.Q(name=""),
                name="dep_name_not_empty",
            ),
            models.CheckConstraint(
                condition=~models.Q(dependent=models.F("prerequisite")),
                name="dependent_prerequisite_must_differ",
            ),
            models.UniqueConstraint(
                fields=["dependent", "prerequisite"],
                name="unique_dependent_prerequisite",
            ),
            models.UniqueConstraint(
                fields=["name", "dependent"],
                name="unique_dep_name_dependent",
            ),
        ]

    def clean(self):
        super().clean()

        if self.dependent_id and self.prerequisite_id:
            if self.dependent.env_id != self.prerequisite.env_id:
                raise ValidationError(
                    "Dependent and prerequisite must belong to the same environment."
                )

            if not self.prerequisite.is_output:
                raise ValidationError(
                    "A prerequisite must be an output node."
                )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)