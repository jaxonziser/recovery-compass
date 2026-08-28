"""Deterministic factual feedback for Recovery Compass."""

from typing import Any


def _format_number(
    value: int | float,
    decimals: int = 1,
) -> str:
    """Return a compact display value."""

    if isinstance(value, int):
        return str(value)

    return f"{value:.{decimals}f}"


def _plural(
    value: int | float,
    singular: str,
    plural: str | None = None,
) -> str:
    """Return the correct singular or plural label."""

    if abs(value) == 1:
        return singular

    if plural is not None:
        return plural

    return f"{singular}s"


def _comparison_sentence(
    label: str,
    difference: int | float | None,
    unit: str,
    *,
    plural_unit: str | None = None,
    decimals: int = 1,
    unchanged_verb: str = "was",
) -> str | None:
    """Return one factual current-vs-previous comparison sentence."""

    if difference is None:
        return None

    if difference == 0:
        return (
            f"{label} {unchanged_verb} unchanged compared with "
            "the previous 7-day period."
        )

    direction = (
        "increased"
        if difference > 0
        else "decreased"
    )

    amount = abs(difference)

    formatted_amount = _format_number(
        amount,
        decimals=decimals,
    )

    unit_label = _plural(
        amount,
        unit,
        plural_unit,
    )

    return (
        f"{label} {direction} by "
        f"{formatted_amount} {unit_label} "
        "compared with the previous 7-day period."
    )


def generate_feedback(
    metrics: dict[str, Any],
) -> list[str]:
    """Return deterministic factual observations from analytics metrics."""

    current = metrics["current_period"]

    feedback: list[str] = []

    days_recorded = current["days_recorded"]
    workout_days = current["workout_days"]
    training_minutes = current["total_training_minutes"]

    average_sleep = current["average_sleep_hours"]
    average_study = current["average_study_hours"]
    average_mood = current["average_mood_rating"]
    mood_entries = current["mood_entries"]
    average_exertion = current["average_training_exertion"]

    # ---------------------------------------------------------
    # Coverage
    # ---------------------------------------------------------

    feedback.append(
        f"You recorded {days_recorded} of 7 days "
        "in the current period."
    )

    # ---------------------------------------------------------
    # Training
    # ---------------------------------------------------------

    if workout_days == 0:
        feedback.append(
            "No actual workout days were recorded "
            "in the current period."
        )

    else:
        feedback.append(
            f"You recorded {workout_days} "
            f"{_plural(workout_days, 'workout day')} "
            f"totaling {training_minutes} minutes."
        )

    # ---------------------------------------------------------
    # Sleep
    # ---------------------------------------------------------

    if average_sleep is not None:
        feedback.append(
            f"Average sleep was "
            f"{_format_number(average_sleep)} hours "
            f"across {days_recorded} recorded "
            f"{_plural(days_recorded, 'day')}."
        )

    # ---------------------------------------------------------
    # Study
    # ---------------------------------------------------------

    if average_study is not None:
        feedback.append(
            f"Average study time was "
            f"{_format_number(average_study)} hours "
            f"across {days_recorded} recorded "
            f"{_plural(days_recorded, 'day')}."
        )

    # ---------------------------------------------------------
    # Mood
    # ---------------------------------------------------------

    if average_mood is None:
        feedback.append(
            "No mood ratings were recorded "
            "in the current period."
        )

    else:
        feedback.append(
            f"Average mood was "
            f"{_format_number(average_mood)} / 5 "
            f"across {mood_entries} recorded "
            f"{_plural(mood_entries, 'rating')}."
        )

    # ---------------------------------------------------------
    # Perceived exertion
    # ---------------------------------------------------------

    if average_exertion is not None:
        feedback.append(
            f"Average perceived exertion was "
            f"{_format_number(average_exertion)} / 10 "
            f"across {workout_days} "
            f"{_plural(workout_days, 'workout day')}."
        )

    # ---------------------------------------------------------
    # Complete-period comparison
    # ---------------------------------------------------------

    if metrics["comparison_available"]:
        differences = metrics["differences"]

        comparisons = [
            _comparison_sentence(
                "Workout days",
                differences["workout_days"],
                "day",
                decimals=0,
                unchanged_verb="were",
            ),
            _comparison_sentence(
                "Training time",
                differences["total_training_minutes"],
                "minute",
                decimals=0,
            ),
            _comparison_sentence(
                "Average sleep",
                differences["average_sleep_hours"],
                "hour",
            ),
            _comparison_sentence(
                "Average study time",
                differences["average_study_hours"],
                "hour",
            ),
            _comparison_sentence(
                "Average mood",
                differences["average_mood_rating"],
                "point",
            ),
            _comparison_sentence(
                "Average perceived exertion",
                differences["average_training_exertion"],
                "point",
            ),
        ]

        feedback.extend(
            comparison
            for comparison in comparisons
            if comparison is not None
        )

    return feedback