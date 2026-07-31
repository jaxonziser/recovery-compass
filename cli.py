"""Command-line input flow for Recovery Compass v0.1.

Current scope:
- collect one candidate daily record,
- validate all entered values,
- display errors or the accepted normalized record,
- do not save data yet.
"""

from src.validation import (
    FIELD_LABELS,
    normalize_record,
    validate_record,
)


def collect_candidate_record() -> dict[str, str]:
    """Prompt the user for one unvalidated daily record."""
    print("Recovery Compass - Daily Entry")
    print("--------------------------------")
    print("Required fields are marked with *.")
    print()

    record = {
        "date": input(
            "Date* (YYYY-MM-DD): "
        ).strip(),
        "workout_type": input(
            "Workout Type* "
            "(Rest, Strength, Cardio, Sport, Mobility, Other): "
        ).strip(),
        "duration_minutes": input(
            "Workout Duration* "
            "(whole number of minutes, 0-300): "
        ).strip(),
        "perceived_exertion": input(
            "Perceived Exertion* "
            "(whole number, 0=no effort and 10=maximum effort): "
        ).strip(),
        "sleep_hours": input(
            "Sleep Hours* "
            "(number, 0-16; decimals allowed): "
        ).strip(),
        "mood_rating": input(
            "Mood Rating "
            "(optional whole number, 1-5; press Enter to skip): "
        ).strip(),
        "study_hours": input(
            "Study Hours* "
            "(number, 0-16; decimals allowed): "
        ).strip(),
    }

    return record


def display_errors(errors: list[str]) -> None:
    """Display every validation error found in a candidate record."""
    print()
    print("Record Not Accepted")
    print("-------------------")

    for error in errors:
        print(f"- {error}")

    print()
    print("Please correct the listed fields and try again.")


def display_accepted_record(record: dict[str, object]) -> None:
    """Display one valid and normalized record."""
    print()
    print("Accepted Record")
    print("---------------")

    for field, value in record.items():
        label = FIELD_LABELS.get(field, field)
        displayed_value = "(not provided)" if value is None else value
        print(f"{label}: {displayed_value}")

    print()
    print("This record passed validation but has not been saved.")


def main() -> None:
    """Collect, validate, normalize, and display one daily record."""
    candidate_record = collect_candidate_record()
    errors = validate_record(candidate_record)

    if errors:
        display_errors(errors)
        return

    normalized_record = normalize_record(candidate_record)
    display_accepted_record(normalized_record)


if __name__ == "__main__":
    main()