from django.db import transaction
from .services import validate_answer
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import FormInstanceStatus, FormType, FormInstance, FormQuestion
from .serializers import (
    FormTypeSerializer,
    FormInstanceSerializer,
    FormQuestionSerializer,
)
from .services import get_dynamic_options


class FormTypeViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = FormType.objects.prefetch_related("questions")
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
            .prefetch_related("questions")
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