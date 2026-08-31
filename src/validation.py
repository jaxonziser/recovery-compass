"""Validation and normalization for Recovery Compass v0.1 daily records."""

from datetime import date
import math


FIELD_LABELS = {
    "date": "Date",
    "workout_type": "Workout Type",
    "duration_minutes": "Workout Duration",
    "perceived_exertion": "Perceived Exertion",
    "sleep_hours": "Sleep Hours",
    "mood_rating": "Mood Rating",
    "study_hours": "Study Hours",
}


WORKOUT_TYPES = {
    "rest": "Rest",
    "strength": "Strength",
    "cardio": "Cardio",
    "sport": "Sport",
    "mobility": "Mobility",
    "other": "Other",
}


REQUIRED_FIELDS = (
    "date",
    "workout_type",
    "duration_minutes",
    "perceived_exertion",
    "sleep_hours",
    "study_hours",
)


def _clean(value: object) -> str:
    """Convert a value to stripped text, treating None as blank."""
    if value is None:
        return ""

    return str(value).strip()


def _validate_integer_field(
    record: dict[str, str],
    field: str,
    minimum: int,
    maximum: int,
    errors: list[str],
) -> None:
    """Validate one whole-number field when it is not blank."""
    raw_value = _clean(record.get(field))

    if raw_value == "":
        return

    try:
        number = int(raw_value)
    except ValueError:
        errors.append(
            f"{FIELD_LABELS[field]} must be a whole number "
            f"between {minimum} and {maximum}."
        )
        return

    if not minimum <= number <= maximum:
        errors.append(
            f"{FIELD_LABELS[field]} must be a whole number "
            f"between {minimum} and {maximum}."
        )


def _validate_decimal_field(
    record: dict[str, str],
    field: str,
    minimum: float,
    maximum: float,
    errors: list[str],
) -> None:
    """Validate one decimal-capable field when it is not blank."""
    raw_value = _clean(record.get(field))

    if raw_value == "":
        return

    try:
        number = float(raw_value)
    except ValueError:
        errors.append(
            f"{FIELD_LABELS[field]} must be a number "
            f"between {minimum:g} and {maximum:g}."
        )
        return

    if not math.isfinite(number) or not minimum <= number <= maximum:
        errors.append(
            f"{FIELD_LABELS[field]} must be a number "
            f"between {minimum:g} and {maximum:g}."
        )


def validate_record(record: dict[str, str]) -> list[str]:
    """Return all validation errors found in one candidate record."""
    errors: list[str] = []

    # Check that every required field contains a value.
    for field in REQUIRED_FIELDS:
        if _clean(record.get(field)) == "":
            errors.append(f"{FIELD_LABELS[field]} is required.")

    # Check that the date uses YYYY-MM-DD and is a real calendar date.
    date_value = _clean(record.get("date"))

    if date_value != "":
        try:
            date.fromisoformat(date_value)
        except ValueError:
            errors.append(
                "Date must be a real calendar date in YYYY-MM-DD format."
            )

    # Check and later normalize the workout category.
    workout_value = _clean(record.get("workout_type"))

    if workout_value != "" and workout_value.lower() not in WORKOUT_TYPES:
        allowed_values = ", ".join(WORKOUT_TYPES.values())
        errors.append(
            f"Workout Type must be one of: {allowed_values}."
        )

    _validate_integer_field(
        record,
        "duration_minutes",
        minimum=0,
        maximum=300,
        errors=errors,
    )

    _validate_integer_field(
        record,
        "perceived_exertion",
        minimum=0,
        maximum=10,
        errors=errors,
    )

    # A Rest record cannot contain workout activity.
    # This cross-field invariant protects manual entry, imported CSV data,
    # browser-local data, and any future pathway using shared validation.
    if workout_value.lower() == "rest":
        duration_value = _clean(
            record.get("duration_minutes")
        )
        exertion_value = _clean(
            record.get("perceived_exertion")
        )

        try:
            if (
                duration_value != ""
                and int(duration_value) != 0
            ):
                errors.append(
                    "Workout Duration must be 0 when "
                    "Workout Type is Rest."
                )
        except ValueError:
            # The normal integer validator already reports malformed values.
            pass

        try:
            if (
                exertion_value != ""
                and int(exertion_value) != 0
            ):
                errors.append(
                    "Perceived Exertion must be 0 when "
                    "Workout Type is Rest."
                )
        except ValueError:
            # The normal integer validator already reports malformed values.
            pass

    _validate_decimal_field(
        record,
        "sleep_hours",
        minimum=0,
        maximum=16,
        errors=errors,
    )

    # Mood is optional, so a blank value is allowed.
    _validate_integer_field(
        record,
        "mood_rating",
        minimum=1,
        maximum=5,
        errors=errors,
    )

    _validate_decimal_field(
        record,
        "study_hours",
        minimum=0,
        maximum=16,
        errors=errors,
    )

    return errors


def normalize_record(record: dict[str, str]) -> dict[str, object]:
    """Convert a valid candidate record into documented Python types."""
    errors = validate_record(record)

    if errors:
        joined_errors = "; ".join(errors)
        raise ValueError(
            f"Cannot normalize an invalid record: {joined_errors}"
        )

    mood_value = _clean(record.get("mood_rating"))
    workout_key = _clean(record.get("workout_type")).lower()

    return {
        "date": _clean(record.get("date")),
        "workout_type": WORKOUT_TYPES[workout_key],
        "duration_minutes": int(
            _clean(record.get("duration_minutes"))
        ),
        "perceived_exertion": int(
            _clean(record.get("perceived_exertion"))
        ),
        "sleep_hours": float(
            _clean(record.get("sleep_hours"))
        ),
        "mood_rating": (
            None if mood_value == "" else int(mood_value)
        ),
        "study_hours": float(
            _clean(record.get("study_hours"))
        ),
    }