from pathlib import Path
import pandas as pd

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction


class BaseImportCommand(BaseCommand):
    """
    Generic import command.
    Subclass this and implement:
        - get_required_columns()
        - process_row(row)
    """

    help = "Base importer"

    # -----------------------------
    # CLI args
    # -----------------------------
    def add_arguments(self, parser):
        parser.add_argument("file", type=str)

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