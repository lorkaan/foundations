import json

from django.core.management.base import CommandError

from ...base.management.base_import_command import BaseImportCommand

from ..models import FormType, FormQuestion, FieldType


class Command(BaseImportCommand):

    help = "Import Form Questions"

    # -----------------------------
    def get_required_columns(self):
        return {
            "form_code",
            "version",
            "question_label",
            "field_type",
        }

    # -----------------------------
    def process_row(self, row):

        def to_int(v, default=1):
            try:
                return int(float(v))
            except Exception:
                return default

        def to_bool(v):
            return str(v).lower() in ("1", "true", "yes", "y")

        def parse_json(v):
            if not v:
                return {}
            return json.loads(v)

        # -------------------------
        # FormType (MUST EXIST)
        # -------------------------
        try:
            form_type = FormType.objects.get(
                code=row["form_code"],
                version=to_int(row.get("version", 1)),
            )
        except FormType.DoesNotExist:
            raise CommandError(
                f"FormType not found for code='{row['form_code']}', "
                f"version='{row.get('version', 1)}'"
            )

        # -------------------------
        # Question
        # -------------------------
        field_type = row["field_type"]

        if field_type not in FieldType.values:
            raise CommandError(f"Invalid field type: {field_type}")

        FormQuestion.objects.update_or_create(
            form_type=form_type,
            label=row["question_label"],
            defaults={
                "field_type": field_type,
                "required": to_bool(row.get("required")),
                "order": to_int(row.get("order", 1)),
                "schema": parse_json(row.get("schema")),
            }
        )