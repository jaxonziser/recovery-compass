"""Local CSV storage for Recovery Compass v0.1 records."""

import csv
from pathlib import Path
from typing import Mapping

from src.validation import normalize_record, validate_record


CSV_FIELDS = (
    "date",
    "workout_type",
    "duration_minutes",
    "perceived_exertion",
    "sleep_hours",
    "mood_rating",
    "study_hours",
)

DEFAULT_DATA_PATH = Path("data") / "recovery_compass.csv"


class StorageError(Exception):
    """Raised when Recovery Compass data cannot be stored or loaded safely."""


class DuplicateDateError(StorageError):
    """Raised when a record already exists for the same date."""


def _prepare_csv_row(
    record: Mapping[str, object],
) -> dict[str, object]:
    """Validate a record and convert it into a CSV-ready row."""

    missing_fields = [
        field
        for field in CSV_FIELDS
        if field not in record
    ]

    extra_fields = [
        field
        for field in record
        if field not in CSV_FIELDS
    ]

    if missing_fields or extra_fields:
        details = []

        if missing_fields:
            details.append(
                f"missing fields: {', '.join(missing_fields)}"
            )

        if extra_fields:
            details.append(
                f"unexpected fields: {', '.join(extra_fields)}"
            )

        raise StorageError(
            "Record does not match the frozen Recovery Compass schema "
            f"({'; '.join(details)})."
        )

    candidate_record = {
        field: (
            ""
            if record[field] is None
            else str(record[field])
        )
        for field in CSV_FIELDS
    }

    errors = validate_record(candidate_record)

    if errors:
        raise StorageError(
            "Record cannot be saved: "
            + "; ".join(errors)
        )

    normalized_record = normalize_record(candidate_record)

    return {
        field: (
            ""
            if normalized_record[field] is None
            else normalized_record[field]
        )
        for field in CSV_FIELDS
    }


def _write_records(
    records: list[Mapping[str, object]],
    file_path: str | Path,
) -> None:
    """Replace one CSV safely with the supplied validated records."""

    path = Path(file_path)

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    temporary_path = path.with_name(
        f".{path.name}.tmp"
    )

    try:
        with temporary_path.open(
            "w",
            encoding="utf-8",
            newline="",
        ) as csv_file:

            writer = csv.DictWriter(
                csv_file,
                fieldnames=CSV_FIELDS,
                lineterminator="\n",
            )

            writer.writeheader()

            for record in records:
                writer.writerow(
                    _prepare_csv_row(record)
                )

        temporary_path.replace(path)

    except OSError as error:
        if temporary_path.exists():
            temporary_path.unlink()

        raise StorageError(
            f"CSV file could not be written: {error}"
        ) from error


def load_records(
    file_path: str | Path = DEFAULT_DATA_PATH,
) -> list[dict[str, object]]:
    """Load and normalize every record from a Recovery Compass CSV."""

    path = Path(file_path)

    if (
        not path.exists()
        or path.stat().st_size == 0
    ):
        return []

    try:
        with path.open(
            "r",
            encoding="utf-8",
            newline="",
        ) as csv_file:

            reader = csv.DictReader(
                csv_file,
                strict=True,
            )

            if reader.fieldnames != list(CSV_FIELDS):
                raise StorageError(
                    "CSV headers do not match the "
                    "Recovery Compass schema."
                )

            records = []
            seen_dates = set()

            for row_number, row in enumerate(
                reader,
                start=2,
            ):
                if None in row:
                    raise StorageError(
                        f"CSV row {row_number} contains "
                        "unexpected extra values."
                    )

                candidate_record = {
                    field: (
                        ""
                        if row.get(field) is None
                        else row[field]
                    )
                    for field in CSV_FIELDS
                }

                errors = validate_record(
                    candidate_record
                )

                if errors:
                    raise StorageError(
                        f"CSV row {row_number} is invalid: "
                        + "; ".join(errors)
                    )

                normalized_record = normalize_record(
                    candidate_record
                )

                record_date = normalized_record["date"]

                if record_date in seen_dates:
                    raise DuplicateDateError(
                        "CSV contains more than one record "
                        f"for {record_date}."
                    )

                seen_dates.add(record_date)

                records.append(
                    normalized_record
                )

            return records

    except csv.Error as error:
        raise StorageError(
            f"CSV file could not be read: {error}"
        ) from error

    except OSError as error:
        raise StorageError(
            f"CSV file could not be opened: {error}"
        ) from error


def save_record(
    record: Mapping[str, object],
    file_path: str | Path = DEFAULT_DATA_PATH,
) -> None:
    """Append one valid record unless its date already exists."""

    path = Path(file_path)

    csv_row = _prepare_csv_row(record)

    existing_records = load_records(path)

    if any(
        existing_record["date"] == csv_row["date"]
        for existing_record in existing_records
    ):
        raise DuplicateDateError(
            f"A record already exists for "
            f"{csv_row['date']}."
        )

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    file_needs_header = (
        not path.exists()
        or path.stat().st_size == 0
    )

    mode = (
        "w"
        if file_needs_header
        else "a"
    )

    try:
        with path.open(
            mode,
            encoding="utf-8",
            newline="",
        ) as csv_file:

            writer = csv.DictWriter(
                csv_file,
                fieldnames=CSV_FIELDS,
                lineterminator="\n",
            )

            if file_needs_header:
                writer.writeheader()

            writer.writerow(csv_row)

    except OSError as error:
        raise StorageError(
            f"CSV file could not be written: {error}"
        ) from error


def export_records(
    destination_path: str | Path,
    source_path: str | Path = DEFAULT_DATA_PATH,
) -> None:
    """Export a separate CSV copy of all valid working records."""

    destination = Path(destination_path)

    if destination.exists():
        raise StorageError(
            "Export destination already exists."
        )

    records = load_records(source_path)

    if not records:
        raise StorageError(
            "There are no Recovery Compass records to export."
        )

    _write_records(
        records,
        destination,
    )


def import_records(
    import_path: str | Path,
    working_path: str | Path = DEFAULT_DATA_PATH,
) -> int:
    """Import a valid CSV using all-or-nothing behavior."""

    incoming_records = load_records(
        import_path
    )

    if not incoming_records:
        raise StorageError(
            "There are no Recovery Compass records to import."
        )

    existing_records = load_records(
        working_path
    )

    existing_dates = {
        record["date"]
        for record in existing_records
    }

    duplicate_dates = [
        record["date"]
        for record in incoming_records
        if record["date"] in existing_dates
    ]

    if duplicate_dates:
        duplicate_text = ", ".join(
            duplicate_dates
        )

        raise DuplicateDateError(
            "Import would duplicate existing date(s): "
            f"{duplicate_text}. Nothing was imported."
        )

    combined_records = (
        existing_records
        + incoming_records
    )

    _write_records(
        combined_records,
        working_path,
    )

    return len(incoming_records)