from django.db import transaction
from .services import validate_answer
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.core.exceptions import ValidationError

from .models import FormGroupInstance, FormInstanceStatus, FormType, FormInstance, FormQuestion
from .serializers import (
    FormGroupInstanceSerializer,
    FormGroupInstanceTreeSerializer,
    FormGroupInstanceWriteSerializer,
    FormTypeSerializer,
    FormInstanceSerializer,
    FormQuestionSerializer,
)
from .services import get_dynamic_options


class FormTypeViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = FormType.objects.prefetch_related("groups")
    serializer_class = FormTypeSerializer

    @action(detail=False, methods=["get"], url_path="latest")
    def latest(self, request):
        """
        GET /form-types/latest/?code=kyc
        """

        code = request.query_params.get("code")

        if not code:
            return Response(
                {"detail": "code is required"},
                status=400
            )

        obj = (
            FormType.objects
            .filter(code=code)
            .order_by("-version")
            .prefetch_related("groups")
            .first()
        )

        if not obj:
            return Response(
                {"detail": "FormType not found"},
                status=404
            )

        serializer = self.get_serializer(obj)
        return Response(serializer.data)


class FormInstanceViewSet(viewsets.ModelViewSet):
    queryset = FormInstance.objects.prefetch_related(
        "answers__question"
    ).select_related("form_type")
    serializer_class = FormInstanceSerializer

    # -------------------------
    # CREATE (always draft)
    # -------------------------
    def perform_create(self, serializer):
        serializer.save(status=FormInstanceStatus.DRAFT)

    # -------------------------
    # UPDATE (draft only)
    # -------------------------
    def update(self, request, *args, **kwargs):
        instance = self.get_object()

        if instance.status != FormInstanceStatus.DRAFT:
            return Response(
                {"detail": "Only draft forms can be edited."},
                status=status.HTTP_400_BAD_REQUEST
            )

        return super().update(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()

        if instance.status != FormInstanceStatus.DRAFT:
            return Response(
                {"detail": "Only draft forms can be edited."},
                status=status.HTTP_400_BAD_REQUEST
            )

        return super().partial_update(request, *args, **kwargs)

    # -------------------------
    # SUBMIT
    # -------------------------
    @action(detail=True, methods=["post"])
    def submit(self, request, pk=None):
        instance = self.get_object()

        if instance.status == FormInstanceStatus.SUBMITTED:
            return Response(
                {"detail": "Form already submitted."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if instance.status == FormInstanceStatus.LOCKED:
            return Response(
                {"detail": "Form is locked and cannot be submitted."},
                status=status.HTTP_400_BAD_REQUEST
            )

        answers = instance.answers.select_related("question")

        # Validate all answers
        for answer in answers:
            validate_answer(answer.question, answer.value)

        # Atomic state transition
        with transaction.atomic():
            instance.status = FormInstanceStatus.SUBMITTED
            instance.save(update_fields=["status"])

        return Response(
            {
                "id": instance.id,
                "status": instance.status,
                "message": "Form submitted successfully"
            }
        )

    # -------------------------
    # LOCK (optional lifecycle step)
    # -------------------------
    @action(detail=True, methods=["post"])
    def lock(self, request, pk=None):
        instance = self.get_object()

        if instance.status != FormInstanceStatus.SUBMITTED:
            return Response(
                {"detail": "Only submitted forms can be locked."},
                status=status.HTTP_400_BAD_REQUEST
            )

        instance.status = FormInstanceStatus.LOCKED
        instance.save(update_fields=["status"])

        return Response(
            {
                "id": instance.id,
                "status": instance.status,
                "message": "Form locked successfully"
            }
        )


class FormQuestionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = FormQuestion.objects.all()
    serializer_class = FormQuestionSerializer

    @action(detail=True, methods=["get"])
    def options(self, request, pk=None):
        question = self.get_object()

        if question.field_type != "dynamic":
            return Response([])

        source = question.schema.get("source")
        options = get_dynamic_options(source)

        return Response(options)

# Simple ViewSet for FormGroupInstance
class FormGroupInstanceViewSet(viewsets.ModelViewSet):
    serializer_class = FormGroupInstanceSerializer

    def get_queryset(self):
        queryset = (
            FormGroupInstance.objects
            .select_related(
                "form_instance",
                "group",
                "parent",
            )
            .prefetch_related("answers")  # ✅ important
        )

        form_instance_id = self.request.query_params.get("form_instance")

        if form_instance_id:
            queryset = queryset.filter(form_instance_id=form_instance_id)

        return queryset
# Tree Instance View Set
class FormGroupInstanceTreeViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = FormGroupInstanceTreeSerializer

    def get_queryset(self):
        queryset = (
            FormGroupInstance.objects
            .select_related("group", "parent")
            .prefetch_related(
                "answers",                          # root answers
                "children",                         # level 1
                "children__answers",                # level 1 answers
                "children__children",               # level 2
                "children__children__answers",      # level 2 answers
            )
        )

        form_instance_id = self.request.query_params.get("form_instance")

        if form_instance_id:
            queryset = queryset.filter(form_instance_id=form_instance_id)

        # Only root nodes
        return queryset.filter(parent__isnull=True)

# Write FormGroupInstance View Set
class FormGroupInstanceWriteViewSet(viewsets.ModelViewSet):
    serializer_class = FormGroupInstanceWriteSerializer

    def get_queryset(self):
        queryset = (
            FormGroupInstance.objects
            .select_related(
                "form_instance",
                "group",
                "parent",
            )
        )

        form_instance_id = self.request.query_params.get("form_instance")

        if form_instance_id:
            queryset = queryset.filter(form_instance_id=form_instance_id)

        return queryset

    def perform_create(self, serializer):
        # ✅ let serializer + model clean() handle validation
        serializer.save()

    def perform_update(self, serializer):
        instance = self.get_object()

        incoming_form_instance = self.request.data.get("form_instance")

        if (
            incoming_form_instance
            and int(incoming_form_instance) != instance.form_instance_id
        ):
            raise ValidationError(
                "Cannot change form_instance of an existing record"
            )

        serializer.save()