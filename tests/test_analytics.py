from datetime import date, timedelta

from src.analytics import calculate_metrics


def _record(
    record_date,
    workout_type="Strength",
    duration_minutes=30,
    perceived_exertion=6,
    sleep_hours=8.0,
    mood_rating=4,
    study_hours=2.0,
):
    return {
        "date": record_date,
        "workout_type": workout_type,
        "duration_minutes": duration_minutes,
        "perceived_exertion": perceived_exertion,
        "sleep_hours": sleep_hours,
        "mood_rating": mood_rating,
        "study_hours": study_hours,
    }


def test_current_period_uses_seven_calendar_days():
    records = [
        _record(
            "2026-08-05",
            duration_minutes=90,
        ),
        _record(
            "2026-08-06",
            workout_type="Rest",
            duration_minutes=0,
            perceived_exertion=0,
        ),
        _record(
            "2026-08-07",
            duration_minutes=40,
        ),
        _record(
            "2026-08-12",
            duration_minutes=45,
        ),
    ]

    metrics = calculate_metrics(
        records,
        period_end=date(2026, 8, 12),
    )

    current = metrics["current_period"]

    assert current["start_date"] == "2026-08-06"
    assert current["end_date"] == "2026-08-12"

    assert current["days_recorded"] == 3
    assert current["workout_days"] == 2
    assert current["total_training_minutes"] == 85


def test_rest_day_is_not_an_actual_workout():
    records = [
        _record(
            "2026-08-12",
            workout_type="Rest",
            duration_minutes=50,
            perceived_exertion=8,
        ),
    ]

    metrics = calculate_metrics(
        records,
        period_end=date(2026, 8, 12),
    )

    current = metrics["current_period"]

    assert current["workout_days"] == 0
    assert current["total_training_minutes"] == 0
    assert current["average_training_exertion"] is None


def test_missing_mood_is_not_treated_as_zero():
    records = [
        _record(
            "2026-08-11",
            mood_rating=None,
        ),
        _record(
            "2026-08-12",
            mood_rating=4,
        ),
    ]

    metrics = calculate_metrics(
        records,
        period_end=date(2026, 8, 12),
    )

    current = metrics["current_period"]

    assert current["mood_entries"] == 1
    assert current["average_mood_rating"] == 4.0


def test_sparse_period_does_not_enable_comparison():
    records = [
        _record(
            "2026-08-10",
        ),
        _record(
            "2026-08-12",
        ),
    ]

    metrics = calculate_metrics(
        records,
        period_end=date(2026, 8, 12),
    )

    assert metrics["comparison_available"] is False
    assert metrics["differences"] is None


def test_complete_consecutive_periods_enable_comparison():
    records = []

    previous_start = date(
        2026,
        7,
        30,
    )

    for offset in range(7):
        record_date = (
            previous_start
            + timedelta(days=offset)
        )

        records.append(
            _record(
                record_date.isoformat(),
                duration_minutes=20,
                perceived_exertion=5,
                sleep_hours=7.0,
                mood_rating=3,
                study_hours=1.0,
            )
        )

    current_start = date(
        2026,
        8,
        6,
    )

    for offset in range(7):
        record_date = (
            current_start
            + timedelta(days=offset)
        )

        records.append(
            _record(
                record_date.isoformat(),
                duration_minutes=30,
                perceived_exertion=6,
                sleep_hours=8.0,
                mood_rating=4,
                study_hours=2.0,
            )
        )

    metrics = calculate_metrics(
        records,
        period_end=date(2026, 8, 12),
    )

    assert metrics["comparison_available"] is True

    differences = metrics["differences"]

    assert differences["workout_days"] == 0
    assert differences["total_training_minutes"] == 70
    assert differences["average_sleep_hours"] == 1.0
    assert differences["average_study_hours"] == 1.0
    assert differences["average_mood_rating"] == 1.0
    assert differences["average_training_exertion"] == 1.0


def test_empty_data_has_safe_empty_metrics():
    metrics = calculate_metrics(
        [],
        period_end=date(2026, 8, 12),
    )

    current = metrics["current_period"]

    assert current["days_recorded"] == 0
    assert current["workout_days"] == 0
    assert current["total_training_minutes"] == 0
    assert current["average_sleep_hours"] is None
    assert current["average_mood_rating"] is None
    assert current["average_training_exertion"] is None

    assert metrics["comparison_available"] is False
    assert metrics["differences"] is None