from ..base.serializers import RepeatableOrderedSerializerMixin
from rest_framework import serializers
from django.db import transaction
from .models import FormGroup, FormGroupInstance, FormSection, FormType, FormQuestion, FormInstance, FormAnswer, FieldType
from .services import validate_answer, get_dynamic_options
from django.core.exceptions import ValidationError as DjangoValidationError


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


class FormAnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = FormAnswer
        fields = ["question", "value"]

    def validate(self, data):
        question = data["question"]
        value = data["value"]

        validate_answer(question, value)
        return data


# Single Instance
class FormGroupInstanceInputSerializer(serializers.Serializer):
    id = serializers.IntegerField(required=False)
    group = serializers.IntegerField()

    answers = FormAnswerSerializer(many=True, required=False)
    children = serializers.ListField(required=False)


class FormInstanceSerializer(serializers.ModelSerializer):
    group_instances = FormGroupInstanceInputSerializer(many=True)

    class Meta:
        model = FormInstance
        fields = ["id", "form_type", "group_instances", "status", "created_at"]
        read_only_fields = ["created_at", "status"]

    @transaction.atomic
    def create(self, validated_data):
        group_data = validated_data.pop("group_instances")

        instance = FormInstance.objects.create(**validated_data)

        # --- Step 1: flatten tree ---
        flat_nodes = []
        self._flatten(group_data, flat_nodes)

        # --- Step 2: create all group instances ---
        for node in flat_nodes:
            obj = FormGroupInstance.objects.create(
                form_instance=instance,
                group_id=node["group"],
                parent=None,
            )
            node["_instance"] = obj

        # --- Step 3: assign parents ---
        for node in flat_nodes:
            parent = node.get("parent_ref")
            if parent:
                node["_instance"].parent = parent["_instance"]
                node["_instance"].save(update_fields=["parent"])

        # --- Step 4: create answers ---
        answers_to_create = []

        for node in flat_nodes:
            for ans in node.get("answers", []):
                answers_to_create.append(
                    FormAnswer(
                        group_instance=node["_instance"],
                        question_id=ans["question"],
                        value=ans["value"],
                    )
                )

        FormAnswer.objects.bulk_create(answers_to_create)

        return instance

    def _flatten(self, nodes, flat, parent=None):
        for node in nodes:
            current = {
                "group": node["group"],
                "answers": node.get("answers", []),
                "parent_ref": parent,
            }

            flat.append(current)

            children = node.get("children", [])
            self._flatten(children, flat, current)

class FormGroupInstanceSerializer(serializers.ModelSerializer):
    answers = FormAnswerSerializer(many=True, read_only=True)

    class Meta:
        model = FormGroupInstance
        fields = [
            "id",
            "form_instance",
            "group",
            "parent",
            "answers",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]

    def validate(self, attrs):
        """
        Run model-level validation (clean) to enforce tree + schema rules.
        """
        instance = self.instance or FormGroupInstance()

        # Apply incoming attrs to instance for validation
        for attr, value in attrs.items():
            setattr(instance, attr, value)

        try:
            instance.clean()
        except DjangoValidationError as e:
            raise serializers.ValidationError(
                e.message_dict if hasattr(e, "message_dict") else e.messages
            )

        return attrs

# Recursive Instance
class FormGroupInstanceTreeSerializer(serializers.ModelSerializer):
    children = serializers.SerializerMethodField()
    answers = FormAnswerSerializer(many=True, read_only=True)

    class Meta:
        model = FormGroupInstance
        fields = [
            "id",
            "group",
            "parent",
            "answers",
            "children",
        ]

    def get_children(self, obj):
        return FormGroupInstanceTreeSerializer(
            obj.children.all().order_by("id"),
            many=True
        ).data
    
# Write Serializer
class FormGroupInstanceWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = FormGroupInstance
        fields = [
            "id",
            "form_instance",
            "group",
            "parent",
        ]

    def validate(self, attrs):
        instance = self.instance or FormGroupInstance()

        for attr, value in attrs.items():
            setattr(instance, attr, value)

        try:
            instance.clean()
        except DjangoValidationError as e:
            raise serializers.ValidationError(e.messages)

        return attrs