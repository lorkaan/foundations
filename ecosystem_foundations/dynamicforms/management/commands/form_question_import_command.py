from django.core.management.base import CommandError

from ....base.management.commands.base_import_command import BaseImportCommand

from ...models import FormType, FormQuestion, FieldType


class Command(BaseImportCommand):

    help = "Import Form Questions"

    name="Form Question"

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

        # -------------------------
        # FormType (MUST EXIST)
        # -------------------------
        try:
            form_type = FormType.objects.get(
                code=row["form_code"],
                version=self.__class__.to_int(row.get("version", 1), 1, validator=lambda x: x > 0),
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
                "required": self.__class__.to_bool(row.get("required", False), default=False),
                "order": self.__class__.to_int(row.get("order", 1)),
                "schema": self.load_schema(row.get("schema")),
            }
        )