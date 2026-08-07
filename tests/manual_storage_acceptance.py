"""Manual acceptance tests for Recovery Compass v0.1 CSV storage."""

from pathlib import Path
from tempfile import TemporaryDirectory

from src.storage import (
    CSV_FIELDS,
    DuplicateDateError,
    StorageError,
    export_records,
    import_records,
    load_records,
    save_record,
)


BASE_RECORD = {
    "date": "2026-08-05",
    "workout_type": "Strength",
    "duration_minutes": 45,
    "perceived_exertion": 7,
    "sleep_hours": 7.5,
    "mood_rating": None,
    "study_hours": 2.5,
}


def check(
    condition: bool,
    message: str,
) -> None:
    """Raise an assertion when one acceptance condition fails."""

    if not condition:
        raise AssertionError(message)


def main() -> None:
    """Run the Week 4 storage acceptance matrix."""

    with TemporaryDirectory() as temporary_directory:
        root = Path(temporary_directory)

        # 1. Missing file
        missing_path = root / "missing.csv"

        check(
            load_records(missing_path) == [],
            "Missing file did not load as [].",
        )

        print(
            "PASS 1 - Missing file returns an empty list."
        )

        # 2. Empty file
        empty_path = root / "empty.csv"
        empty_path.touch()

        check(
            load_records(empty_path) == [],
            "Empty file did not load as [].",
        )

        print(
            "PASS 2 - Empty file returns an empty list."
        )

        # 3. Valid round trip
        working_path = root / "working.csv"

        save_record(
            BASE_RECORD,
            working_path,
        )

        check(
            load_records(working_path)
            == [BASE_RECORD],
            "Valid round trip changed the record.",
        )

        print(
            "PASS 3 - Valid record survives save and reload."
        )

        # 4. Wrong header
        wrong_header_path = (
            root / "wrong_header.csv"
        )

        wrong_header_path.write_text(
            "date,workout_type,duration_minutes,"
            "perceived_exertion,sleep,"
            "mood_rating,study_hours\n"
            "2026-08-05,Strength,45,7,7.5,,2.5\n",
            encoding="utf-8",
        )

        try:
            load_records(
                wrong_header_path
            )

        except StorageError:
            print(
                "PASS 4 - Wrong headers are rejected."
            )

        else:
            raise AssertionError(
                "Wrong headers were accepted."
            )

        # 5. Malformed row
        malformed_path = root / "malformed.csv"

        malformed_path.write_text(
            ",".join(CSV_FIELDS)
            + "\n"
            + "2026-08-05,Strength,"
            + "banana,7,7.5,,2.5\n",
            encoding="utf-8",
        )

        try:
            load_records(
                malformed_path
            )

        except StorageError:
            print(
                "PASS 5 - Malformed row is rejected."
            )

        else:
            raise AssertionError(
                "Malformed row was accepted."
            )

        # 6. Duplicate save
        try:
            save_record(
                BASE_RECORD,
                working_path,
            )

        except DuplicateDateError:
            print(
                "PASS 6 - Duplicate save is rejected."
            )

        else:
            raise AssertionError(
                "Duplicate save was accepted."
            )

        # 7. Duplicate dates inside CSV
        duplicate_file_path = (
            root / "duplicate_file.csv"
        )

        duplicate_file_path.write_text(
            ",".join(CSV_FIELDS)
            + "\n"
            + "2026-08-05,Strength,45,7,7.5,,2.5\n"
            + "2026-08-05,Cardio,30,6,8.0,4,3.0\n",
            encoding="utf-8",
        )

        try:
            load_records(
                duplicate_file_path
            )

        except DuplicateDateError:
            print(
                "PASS 7 - Duplicate dates inside a CSV "
                "are rejected."
            )

        else:
            raise AssertionError(
                "Duplicate dates inside a CSV were accepted."
            )

        # 8. Export copy
        export_path = root / "export.csv"

        export_records(
            export_path,
            working_path,
        )

        check(
            export_path.exists(),
            "Export file was not created.",
        )

        check(
            load_records(export_path)
            == load_records(working_path),
            "Export does not match working data.",
        )

        check(
            load_records(working_path)
            == [BASE_RECORD],
            "Export changed the working data.",
        )

        print(
            "PASS 8 - Export creates a separate matching copy."
        )

        # 9. Import
        import_source = (
            root / "import_source.csv"
        )

        imported_record = {
            "date": "2026-08-06",
            "workout_type": "Cardio",
            "duration_minutes": 30,
            "perceived_exertion": 6,
            "sleep_hours": 8.0,
            "mood_rating": 4,
            "study_hours": 3.0,
        }

        save_record(
            imported_record,
            import_source,
        )

        imported_count = import_records(
            import_source,
            working_path,
        )

        check(
            imported_count == 1,
            "Import count was incorrect.",
        )

        check(
            load_records(working_path)
            == [
                BASE_RECORD,
                imported_record,
            ],
            "Valid import did not add the expected record.",
        )

        before_conflict = load_records(
            working_path
        )

        try:
            import_records(
                import_source,
                working_path,
            )

        except DuplicateDateError:
            pass

        else:
            raise AssertionError(
                "Conflicting import was accepted."
            )

        check(
            load_records(working_path)
            == before_conflict,
            "Conflicting import changed working data.",
        )

        print(
            "PASS 9 - Import works and conflicting "
            "import changes nothing."
        )

        print()
        print(
            "All Week 4 storage acceptance tests passed."
        )


if __name__ == "__main__":
    main()