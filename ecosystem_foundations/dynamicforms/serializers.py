from ..base.serializers import RepeatableOrderedSerializerMixin
from rest_framework import serializers
from django.db import transaction
from .models import FormGroup, FormGroupInstance, FormSection, FormType, FormQuestion, FormInstance, FormAnswer, FieldType
from .services import validate_answer, get_dynamic_options
from django.core.exceptions import ValidationError


class FormQuestionSerializer(serializers.ModelSerializer):
    options = serializers.SerializerMethodField()

    class Meta:
        model = FormQuestion
        fields = [
            "id",
            "label",
            "field_type",
            "required",
            "order",
            "schema",
            "options",
        ]

    def get_options(self, obj):
        if obj.field_type == FieldType.ENUM:
            return obj.schema.get("choices", [])

        if obj.field_type == FieldType.DYNAMIC:
            source = obj.schema.get("source")
            return get_dynamic_options(source)

        return None

class FormGroupSerializer(RepeatableOrderedSerializerMixin):
    questions = FormQuestionSerializer(many=True, read_only=True)

    children = serializers.SerializerMethodField()

    class Meta:
        model = FormGroup
        fields = "__all__"

    def get_children(self, obj):
        children = obj.children.all().order_by("order")
        return FormGroupSerializer(children, many=True, context=self.context).data

class FormSectionSerializer(RepeatableOrderedSerializerMixin):

    groups = serializers.SerializerMethodField()

    class Meta:
        model = FormSection
        fields = "__all__"

    def get_groups(self, obj):
        root_groups = obj.groups.filter(parent__isnull=True).order_by("order")
        return FormGroupSerializer(root_groups, many=True, context=self.context).data


class FormTypeSerializer(serializers.ModelSerializer):
    sections = FormSectionSerializer(many=True, read_only=True)

    class Meta:
        model = FormType
        fields = ["id", "name", "code", "description", "version", "sections"]


# ============================================================
# Form Answer Serializer
# ============================================================

class FormAnswerSerializer(serializers.ModelSerializer):

    question = serializers.PrimaryKeyRelatedField(
        queryset=FormQuestion.objects.all()
    )

    value = serializers.JSONField()

    class Meta:
        model = FormAnswer
        fields = [
            "id",
            "question",
            "value",
        ]
        read_only_fields = ["id"]

    def validate(self, attrs):
        question = attrs["question"]
        value = attrs.get("value")

        try:
            validate_answer(question, value)

        except Exception as exc:

            if isinstance(exc, ValidationError):
                raise serializers.ValidationError({
                    "value": exc.messages
                })

            raise

        return attrs
    


# ============================================================
# Form Group Instance Data Serializer
# ============================================================

class FormGroupInstanceDataSerializer(serializers.Serializer):

    id = serializers.UUIDField(
        required=False,
        allow_null=True,
        default=None
    )

    group = serializers.PrimaryKeyRelatedField(
        queryset=FormGroup.objects.all()
    )

    answers = FormAnswerSerializer(
        many=True,
        required=False,
        default=list
    )

    def validate(self, attrs):
        group = attrs["group"]

        for answer in attrs.get("answers", []):
            question = answer["question"]

            if question.form_group_id != group.pk:
                raise serializers.ValidationError({
                    "answers": (
                        f"Question {question.pk} does not belong "
                        f"to FormGroup {group.pk}."
                    )
                })

        return attrs


# ============================================================
# Form Group Instance Tree Input Serializer
# ============================================================

class FormGroupInstanceTreeInputSerializer(serializers.Serializer):

    data = FormGroupInstanceDataSerializer()

    children = serializers.ListField(
        child=serializers.DictField(),
        required=False,
        default=list
    )

    def validate(self, attrs):

        validated_children = []

        for child in attrs.get("children", []):

            serializer = FormGroupInstanceTreeInputSerializer(
                data=child,
                context=self.context
            )

            serializer.is_valid(raise_exception=True)

            validated_children.append(serializer.validated_data)

        attrs["children"] = validated_children

        return attrs


# ============================================================
# Form Section Tree Collection Serializer
# ============================================================

class FormSectionTreeSerializer(serializers.Serializer):

    section = serializers.PrimaryKeyRelatedField(
        queryset=FormSection.objects.all()
    )

    trees = FormGroupInstanceTreeInputSerializer(
        many=True
    )


# ============================================================
# Form Section Mapping Serializer
# ============================================================

class FormSectionMappingSerializer(serializers.Serializer):

    """
    Validates a mapping of:

        {
            section_id: [
                TreeNode,
                TreeNode,
                ...
            ]
        }

    Each section contains a list of independent root trees.
    """

    def to_internal_value(self, data):

        if not isinstance(data, dict):
            raise serializers.ValidationError(
                "Expected a dictionary of section IDs and trees."
            )

        validated_data = {}

        for section_id, trees in data.items():

            try:
                section = FormSection.objects.get(pk=section_id)

            except (
                FormSection.DoesNotExist,
                ValueError,
                TypeError
            ):
                raise serializers.ValidationError({
                    section_id: "Invalid FormSection ID."
                })

            if not isinstance(trees, list):
                raise serializers.ValidationError({
                    section_id: "Expected a list of trees."
                })

            tree_serializer = FormGroupInstanceTreeInputSerializer(
                data=trees,
                many=True,
                context=self.context
            )

            tree_serializer.is_valid(raise_exception=True)

            validated_data[section.pk] = {
                "section": section,
                "trees": tree_serializer.validated_data
            }

        return validated_data


# ============================================================
# Form Instance Serializer
# ============================================================

class FormInstanceSerializer(serializers.ModelSerializer):

    sections = FormSectionMappingSerializer(
        required=False,
        write_only=True
    )

    class Meta:
        model = FormInstance

        fields = [
            "id",
            "form_type",
            "submitted_by",
            "status",
            "sections",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "submitted_by",
            "status",
            "created_at",
            "updated_at",
        ]

    def validate(self, attrs):

        form_type = attrs.get(
            "form_type",
            getattr(self.instance, "form_type", None)
        )

        if form_type is None:
            raise serializers.ValidationError({
                "form_type": "This field is required."
            })

        sections = attrs.get("sections", {})

        for section_id, section_data in sections.items():

            section = section_data["section"]

            if section.form_type_id != form_type.pk:
                raise serializers.ValidationError({
                    "sections": (
                        f"Section {section_id} does not belong "
                        "to this FormType."
                    )
                })

            for tree in section_data["trees"]:

                self._validate_tree_section(
                    tree,
                    section.pk
                )

        return attrs

    def _validate_tree_section(self, node_data, section_id):

        group = node_data["data"]["group"]

        if group.form_section_id != section_id:
            raise serializers.ValidationError(
                f"Group {group.pk} does not belong to "
                f"FormSection {section_id}."
            )

        for child in node_data.get("children", []):

            self._validate_tree_section(
                child,
                section_id
            )

    # --------------------------------------------------------
    # CREATE
    # --------------------------------------------------------

    @transaction.atomic
    def create(self, validated_data):

        sections_data = validated_data.pop(
            "sections",
            {}
        )

        form_instance = FormInstance.objects.create(
            **validated_data
        )

        for section_data in sections_data.values():

            for tree_data in section_data["trees"]:

                self._create_group_tree(
                    form_instance=form_instance,
                    node_data=tree_data
                )

        return form_instance

    def _create_group_tree(
        self,
        form_instance,
        node_data,
        parent=None
    ):

        data = node_data["data"]

        group_instance = FormGroupInstance.objects.create(
            form_instance=form_instance,
            group=data["group"],
            parent=parent
        )

        for answer_data in data.get("answers", []):

            FormAnswer.objects.create(
                group_instance=group_instance,
                **answer_data
            )

        for child_data in node_data.get("children", []):

            self._create_group_tree(
                form_instance=form_instance,
                node_data=child_data,
                parent=group_instance
            )

        return group_instance