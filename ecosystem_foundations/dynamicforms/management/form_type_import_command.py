import json

from django.core.management.base import CommandError

from ...base.management.base_import_command import BaseImportCommand

from ..models import FormType


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

        def to_int(v, default=1):
            try:
                return int(float(v))
            except Exception:
                return default

        # -------------------------
        # FormType
        # -------------------------
        form_type, _ = FormType.objects.update_or_create(
            code=row["form_code"],
            version=to_int(row.get("version", 1)),
            defaults={
                "name": row["form_name"],
            }
        )
