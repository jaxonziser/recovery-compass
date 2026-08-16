"""Deterministic analytics for Recovery Compass v0.1."""

from datetime import date, timedelta


PERIOD_DAYS = 7


def _to_date(value: str | date) -> date:
    """Return a date object from an ISO date string or date object."""
    if isinstance(value, date):
        return value

    return date.fromisoformat(value)


def _select_period_records(
    records: list[dict[str, object]],
    start_date: date,
    end_date: date,
) -> list[dict[str, object]]:
    """Return records whose dates fall inside the inclusive date window."""
    selected_records = []

    for record in records:
        record_date = _to_date(record["date"])

        if start_date <= record_date <= end_date:
            selected_records.append(record)

    return selected_records


def _is_workout(record: dict[str, object]) -> bool:
    """Return True when a record represents an actual workout."""
    return (
        record["workout_type"] != "Rest"
        and record["duration_minutes"] > 0
    )


def _average(values: list[int | float]) -> float | None:
    """Return the average of values, or None when no values exist."""
    if not values:
        return None

    return sum(values) / len(values)


def _calculate_period_metrics(
    records: list[dict[str, object]],
    start_date: date,
    end_date: date,
) -> dict[str, object]:
    """Calculate the approved metrics for one seven-day period."""
    period_records = _select_period_records(
        records,
        start_date,
        end_date,
    )

    workout_records = [
        record
        for record in period_records
        if _is_workout(record)
    ]

    mood_values = [
        record["mood_rating"]
        for record in period_records
        if record["mood_rating"] is not None
    ]

    sleep_values = [
        record["sleep_hours"]
        for record in period_records
    ]

    study_values = [
        record["study_hours"]
        for record in period_records
    ]

    exertion_values = [
        record["perceived_exertion"]
        for record in workout_records
    ]

    return {
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "days_recorded": len(period_records),
        "workout_days": len(workout_records),
        "total_training_minutes": sum(
            record["duration_minutes"]
            for record in workout_records
        ),
        "average_sleep_hours": _average(sleep_values),
        "average_study_hours": _average(study_values),
        "average_mood_rating": _average(mood_values),
        "mood_entries": len(mood_values),
        "average_training_exertion": _average(exertion_values),
    }


def _metric_difference(
    current_value: int | float | None,
    previous_value: int | float | None,
) -> int | float | None:
    """Return current minus previous, or None when either value is missing."""
    if current_value is None or previous_value is None:
        return None

    return current_value - previous_value


def calculate_metrics(
    records: list[dict[str, object]],
    period_end: str | date,
) -> dict[str, object]:
    """Calculate Recovery Compass metrics for current and previous periods."""
    end_date = _to_date(period_end)

    current_start = end_date - timedelta(
        days=PERIOD_DAYS - 1
    )

    previous_end = current_start - timedelta(days=1)

    previous_start = previous_end - timedelta(
        days=PERIOD_DAYS - 1
    )

    current_period = _calculate_period_metrics(
        records,
        current_start,
        end_date,
    )

    previous_period = _calculate_period_metrics(
        records,
        previous_start,
        previous_end,
    )

    comparison_available = (
        current_period["days_recorded"] == PERIOD_DAYS
        and previous_period["days_recorded"] == PERIOD_DAYS
    )

    differences = None

    if comparison_available:
        differences = {
            "workout_days": _metric_difference(
                current_period["workout_days"],
                previous_period["workout_days"],
            ),
            "total_training_minutes": _metric_difference(
                current_period["total_training_minutes"],
                previous_period["total_training_minutes"],
            ),
            "average_sleep_hours": _metric_difference(
                current_period["average_sleep_hours"],
                previous_period["average_sleep_hours"],
            ),
            "average_study_hours": _metric_difference(
                current_period["average_study_hours"],
                previous_period["average_study_hours"],
            ),
            "average_mood_rating": _metric_difference(
                current_period["average_mood_rating"],
                previous_period["average_mood_rating"],
            ),
            "average_training_exertion": _metric_difference(
                current_period["average_training_exertion"],
                previous_period["average_training_exertion"],
            ),
        }

    return {
        "total_records": len(records),
        "current_period": current_period,
        "previous_period": previous_period,
        "comparison_available": comparison_available,
        "differences": differences,
    }


def prepare_chart_data(
    records: list[dict[str, object]],
) -> dict[str, list[dict[str, object]]]:
    """Prepare chronological factual datasets for future charts."""
    sorted_records = sorted(
        records,
        key=lambda record: _to_date(record["date"]),
    )

    sleep_mood = []
    training = []
    study = []

    for record in sorted_records:
        record_date = _to_date(record["date"]).isoformat()

        sleep_mood.append(
            {
                "date": record_date,
                "sleep_hours": record["sleep_hours"],
                "mood_rating": record["mood_rating"],
            }
        )

        training.append(
            {
                "date": record_date,
                "workout_type": record["workout_type"],
                "duration_minutes": record["duration_minutes"],
                "perceived_exertion": (
                    record["perceived_exertion"]
                    if _is_workout(record)
                    else None
                ),
            }
        )

        study.append(
            {
                "date": record_date,
                "study_hours": record["study_hours"],
            }
        )

    return {
        "sleep_mood": sleep_mood,
        "training": training,
        "study": study,
    }