
from ...base.management.commands.base_import_command import BaseImportCommand

from ...models import FormType


class Command(BaseImportCommand):

    help = "Import Form Types"

    # -----------------------------
    def get_required_columns(self):
        return {
            "form_code",
            "form_name",
            "version",
            "description"
        }

    # -----------------------------
    def process_row(self, row):

        # -------------------------
        # FormType
        # -------------------------
        form_type, _ = FormType.objects.update_or_create(
            code=row["form_code"],
            version=self.__class__.to_int(row.get("version", 1), default=1, validator=lambda x: x > 0),
            defaults={
                "name": row["form_name"],
                "description": row.get("description", "")
            }
        )
