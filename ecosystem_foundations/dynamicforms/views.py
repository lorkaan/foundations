from django.db import transaction
from django.core.exceptions import ValidationError as DjangoValidationError

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError as DRFValidationError
from rest_framework.response import Response

from .models import (
    FormType,
    FormInstance,
    FormInstanceStatus,
    FormGroupInstance,
    FormQuestion,
    FieldType,
)

from .serializers import (
    FormTypeSerializer,
    FormInstanceSerializer,
    FormQuestionSerializer,
)

from .services import (
    validate_answer,
    get_dynamic_options,
)


# ============================================================
# Form Type ViewSet
# ============================================================

class FormTypeViewSet(viewsets.ReadOnlyModelViewSet):

    serializer_class = FormTypeSerializer

    queryset = FormType.objects.prefetch_related(
        "sections"
    )

    @action(
        detail=False,
        methods=["get"],
        url_path="latest"
    )
    def latest(self, request):

        """
        GET /form-types/latest/?code=kyc
        """

        code = request.query_params.get("code")

        if not code:
            return Response(
                {"detail": "code is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        obj = (
            FormType.objects
            .filter(code=code)
            .order_by("-version")
            .prefetch_related("sections")
            .first()
        )

        if not obj:
            return Response(
                {"detail": "FormType not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = self.get_serializer(obj)

        return Response(serializer.data)


# ============================================================
# Form Instance ViewSet
# ============================================================

class FormInstanceViewSet(viewsets.ModelViewSet):

    serializer_class = FormInstanceSerializer

    def get_queryset(self):

        return (
            FormInstance.objects
            .select_related(
                "form_type",
                "submitted_by",
            )
            .prefetch_related(
                "group_instances",
                "group_instances__answers",
                "group_instances__answers__question",
            )
        )

    # --------------------------------------------------------
    # CREATE
    # --------------------------------------------------------

    def perform_create(self, serializer):

        serializer.save(
            status=FormInstanceStatus.DRAFT,
            submitted_by=(
                self.request.user
                if self.request.user.is_authenticated
                else None
            )
        )

    # --------------------------------------------------------
    # UPDATE
    # --------------------------------------------------------

    def update(self, request, *args, **kwargs):

        instance = self.get_object()

        if instance.status != FormInstanceStatus.DRAFT:
            return Response(
                {"detail": "Only draft forms can be edited."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if "sections" in request.data:
            raise DRFValidationError({
                "sections": (
                    "Nested section updates are not currently supported."
                )
            })

        return super().update(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):

        instance = self.get_object()

        if instance.status != FormInstanceStatus.DRAFT:
            return Response(
                {"detail": "Only draft forms can be edited."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if "sections" in request.data:
            raise DRFValidationError({
                "sections": (
                    "Nested section updates are not currently supported."
                )
            })

        return super().partial_update(request, *args, **kwargs)

    # --------------------------------------------------------
    # SUBMIT
    # --------------------------------------------------------

    @action(
        detail=True,
        methods=["post"]
    )
    def submit(self, request, pk=None):

        with transaction.atomic():

            instance = (
                FormInstance.objects
                .select_for_update()
                .get(pk=pk)
            )

            if instance.status == FormInstanceStatus.SUBMITTED:
                return Response(
                    {"detail": "Form already submitted."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if instance.status == FormInstanceStatus.LOCKED:
                return Response(
                    {
                        "detail": (
                            "Form is locked and cannot be submitted."
                        )
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

            errors = []

            group_instances = (
                FormGroupInstance.objects
                .filter(form_instance=instance)
                .select_related("group")
                .prefetch_related(
                    "answers",
                    "answers__question",
                    "group__questions",
                )
            )

            for group_instance in group_instances:

                answers = list(group_instance.answers.all())

                answered_question_ids = set()

                # Validate supplied answers
                for answer in answers:

                    answered_question_ids.add(
                        answer.question_id
                    )

                    try:
                        validate_answer(
                            answer.question,
                            answer.value
                        )

                    except DjangoValidationError as exc:

                        errors.append({
                            "answer": str(answer.id),
                            "group_instance": str(group_instance.id),
                            "question": str(answer.question_id),
                            "error": exc.messages,
                        })

                # Check for missing required answers
                required_questions = (
                    group_instance.group.questions.filter(
                        required=True
                    )
                )

                for question in required_questions:

                    if question.id not in answered_question_ids:

                        errors.append({
                            "answer": None,
                            "group_instance": str(group_instance.id),
                            "question": str(question.id),
                            "error": ["Required field"],
                        })

            if errors:
                return Response(
                    {
                        "detail": "Form contains invalid answers.",
                        "errors": errors,
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

            # All answers valid
            instance.status = FormInstanceStatus.SUBMITTED

            instance.save(
                update_fields=["status"]
            )

        return Response({
            "id": instance.id,
            "status": instance.status,
            "message": "Form submitted successfully",
        })

    # --------------------------------------------------------
    # LOCK
    # --------------------------------------------------------

    @action(
        detail=True,
        methods=["post"]
    )
    def lock(self, request, pk=None):

        with transaction.atomic():

            instance = (
                FormInstance.objects
                .select_for_update()
                .get(pk=pk)
            )

            if instance.status != FormInstanceStatus.SUBMITTED:
                return Response(
                    {
                        "detail": (
                            "Only submitted forms can be locked."
                        )
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

            instance.status = FormInstanceStatus.LOCKED

            instance.save(
                update_fields=["status"]
            )

        return Response({
            "id": instance.id,
            "status": instance.status,
            "message": "Form locked successfully",
        })


# ============================================================
# Form Question ViewSet
# ============================================================

class FormQuestionViewSet(viewsets.ReadOnlyModelViewSet):

    queryset = FormQuestion.objects.all()

    serializer_class = FormQuestionSerializer

    @action(
        detail=True,
        methods=["get"]
    )
    def options(self, request, pk=None):

        question = self.get_object()

        if question.field_type != FieldType.DYNAMIC:
            return Response([])

        source = (question.schema or {}).get("source")

        if not source:
            return Response([])

        options = get_dynamic_options(source)

        return Response(options)