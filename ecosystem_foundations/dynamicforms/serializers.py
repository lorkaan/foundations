from rest_framework import serializers
from .models import FormType, FormQuestion, FormInstance, FormAnswer
from .services import validate_answer, get_dynamic_options


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
        if obj.field_type == "enum":
            return obj.schema.get("choices", [])

        if obj.field_type == "dynamic":
            source = obj.schema.get("source")
            return get_dynamic_options(source)

        return None


class FormTypeSerializer(serializers.ModelSerializer):
    questions = FormQuestionSerializer(many=True, read_only=True)

    class Meta:
        model = FormType
        fields = ["id", "name", "code", "description", "version", "questions"]


class FormAnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = FormAnswer
        fields = ["question", "value"]

    def validate(self, data):
        question = data["question"]
        value = data["value"]

        validate_answer(question, value)
        return data


class FormInstanceSerializer(serializers.ModelSerializer):
    answers = FormAnswerSerializer(many=True)

    class Meta:
        model = FormInstance
        fields = ["id", "form_type", "answers", "status", "created_at"]
        read_only_fields = ["created_at", "status"]

    def create(self, validated_data):
        answers_data = validated_data.pop("answers")

        instance = FormInstance.objects.create(**validated_data)

        for answer_data in answers_data:
            FormAnswer.objects.create(
                form_instance=instance,
                **answer_data
            )

        return instance