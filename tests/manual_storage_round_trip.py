"""Manual round-trip test for Recovery Compass CSV storage."""

from pathlib import Path
from tempfile import TemporaryDirectory

from src.storage import CSV_FIELDS, load_records, save_record


def main() -> None:
    """Save and reload one synthetic record, then compare the result."""

    original_record = {
        "date": "2026-08-05",
        "workout_type": "Strength",
        "duration_minutes": 45,
        "perceived_exertion": 7,
        "sleep_hours": 7.5,
        "mood_rating": None,
        "study_hours": 2.5,
    }

    with TemporaryDirectory() as temporary_directory:
        test_path = (
            Path(temporary_directory)
            / "recovery_compass_test.csv"
        )

        save_record(
            original_record,
            test_path,
        )

        loaded_records = load_records(test_path)

        print("CSV headers:")
        print(", ".join(CSV_FIELDS))
        print()

        print("Original record:")
        print(original_record)
        print()

        print("Loaded records:")
        print(loaded_records)
        print()

        if loaded_records != [original_record]:
            raise AssertionError(
                "The loaded record does not match "
                "the original normalized record."
            )

        print("Round-trip test passed.")
        print("The synthetic record was saved and reloaded accurately.")


if __name__ == "__main__":
    main()