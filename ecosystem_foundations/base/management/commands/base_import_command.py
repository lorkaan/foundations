from pathlib import Path
import pandas as pd

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
import os
import json

class BaseImportCommand(BaseCommand):
    """
    Generic import command.
    Subclass this and implement:
        - get_required_columns()
        - process_row(row)
    """

    help = "Base importer"

    @classmethod
    def to_int(cls, v, default=0, validator=None):
        try:
            val = int(float(v))
        except Exception:
            val = default
        finally:
            if callable(validator):
                val = validator(val)
        return val

    @classmethod
    def to_bool(cls, v, default=False):
        val = str(v)
        if len(val):
            return str(v).lower() in ("1", "true", "yes", "y")
        else:
            return default

    @classmethod
    def parse_json(cls, v):
        if not v:
            return {}
        return json.loads(v)

    # -----------------------------
    # CLI args
    # -----------------------------
    def add_arguments(self, parser):
        parser.add_argument("file", type=str)

    # -----------------------------
    # Schema loader (PUT IT HERE 👇)
    # -----------------------------
    def load_schema(self, filename: str) -> dict:
        if not filename:
            return {}

        base_dir = settings.CONFIG_JSON_PATH

        path = Path(filename)

        if not path.is_absolute():
            path =  os.path.join(base_dir, filename)

        if not path.exists():
            raise CommandError(f"Schema file not found: {path}")

        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            raise CommandError(f"Invalid JSON in {path}: {e}")

    # -----------------------------
    # Entry point
    # -----------------------------
    @transaction.atomic
    def handle(self, *args, **options):
        file_path = Path(options["file"])

        if not file_path.exists():
            raise CommandError("File not found")

        df = self.load_file(file_path)
        df = self.normalize_dataframe(df)

        self.validate_columns(df)

        self.stdout.write(f"Processing {len(df)} rows...")

        for index, row in df.iterrows():
            try:
                self.process_row(row)
            except Exception as e:
                raise CommandError(f"Row {index + 2}: {e}")

        self.stdout.write(self.style.SUCCESS("Import complete"))

    # -----------------------------
    # File loading
    # -----------------------------
    def load_file(self, path: Path) -> pd.DataFrame:
        suffix = path.suffix.lower()

        try:
            if suffix == ".csv":
                return pd.read_csv(path)

            elif suffix in (".xls", ".xlsx"):
                return pd.read_excel(path)

            elif suffix == ".odf":
                return pd.read_excel(path, engine="odf")

            else:
                raise CommandError(f"Unsupported file format: {suffix}")

        except Exception as e:
            raise CommandError(f"Failed to read file: {e}")

    # -----------------------------
    # Normalize
    # -----------------------------
    def normalize_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        df.columns = df.columns.str.strip().str.lower()
        df = df.fillna("")

        for col in df.columns:
            df[col] = df[col].astype(str).str.strip()

        return df

    # -----------------------------
    # Validation
    # -----------------------------
    def validate_columns(self, df: pd.DataFrame):
        required = self.get_required_columns()
        missing = required - set(df.columns)

        if missing:
            raise CommandError(f"Missing columns: {missing}")

    # -----------------------------
    # Hooks (override these)
    # -----------------------------
    def get_required_columns(self) -> set:
        raise NotImplementedError

    def process_row(self, row: pd.Series):
        raise NotImplementedError