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


def _prepare_csv_row(record: Mapping[str, object]) -> dict[str, object]:
    """Validate a record and convert it into a CSV-ready row."""

    missing_fields = [
        field for field in CSV_FIELDS
        if field not in record
    ]

    extra_fields = [
        field for field in record
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
        field: "" if record[field] is None else str(record[field])
        for field in CSV_FIELDS
    }

    errors = validate_record(candidate_record)

    if errors:
        raise StorageError(
            "Record cannot be saved: " + "; ".join(errors)
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


def load_records(
    file_path: str | Path = DEFAULT_DATA_PATH,
) -> list[dict[str, object]]:
    """Load and normalize every record from a Recovery Compass CSV file."""

    path = Path(file_path)

    if not path.exists() or path.stat().st_size == 0:
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

                errors = validate_record(candidate_record)

                if errors:
                    raise StorageError(
                        f"CSV row {row_number} is invalid: "
                        + "; ".join(errors)
                    )

                records.append(
                    normalize_record(candidate_record)
                )

            return records

    except csv.Error as error:
        raise StorageError(
            f"CSV file could not be read: {error}"
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
            f"A record already exists for {csv_row['date']}."
        )

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    file_needs_header = (
        not path.exists()
        or path.stat().st_size == 0
    )

    mode = "w" if file_needs_header else "a"

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