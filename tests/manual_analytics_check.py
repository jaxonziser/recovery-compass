"""Manual hand-verification check for Recovery Compass analytics."""

from math import isclose

from src.analytics import calculate_metrics


RECORDS = [
    {
        "date": "2026-07-30",
        "workout_type": "Strength",
        "duration_minutes": 45,
        "perceived_exertion": 7,
        "sleep_hours": 7.0,
        "mood_rating": 3,
        "study_hours": 2.0,
    },
    {
        "date": "2026-07-31",
        "workout_type": "Rest",
        "duration_minutes": 0,
        "perceived_exertion": 0,
        "sleep_hours": 8.0,
        "mood_rating": 4,
        "study_hours": 1.0,
    },
    {
        "date": "2026-08-01",
        "workout_type": "Cardio",
        "duration_minutes": 30,
        "perceived_exertion": 6,
        "sleep_hours": 7.5,
        "mood_rating": None,
        "study_hours": 3.0,
    },
    {
        "date": "2026-08-02",
        "workout_type": "Strength",
        "duration_minutes": 60,
        "perceived_exertion": 8,
        "sleep_hours": 6.5,
        "mood_rating": 2,
        "study_hours": 4.0,
    },
    {
        "date": "2026-08-03",
        "workout_type": "Rest",
        "duration_minutes": 0,
        "perceived_exertion": 0,
        "sleep_hours": 8.0,
        "mood_rating": 4,
        "study_hours": 2.0,
    },
    {
        "date": "2026-08-04",
        "workout_type": "Mobility",
        "duration_minutes": 20,
        "perceived_exertion": 4,
        "sleep_hours": 7.0,
        "mood_rating": 3,
        "study_hours": 3.0,
    },
    {
        "date": "2026-08-05",
        "workout_type": "Strength",
        "duration_minutes": 50,
        "perceived_exertion": 7,
        "sleep_hours": 7.5,
        "mood_rating": 4,
        "study_hours": 2.5,
    },
    {
        "date": "2026-08-06",
        "workout_type": "Rest",
        "duration_minutes": 0,
        "perceived_exertion": 0,
        "sleep_hours": 8.0,
        "mood_rating": None,
        "study_hours": 2.0,
    },
    {
        "date": "2026-08-07",
        "workout_type": "Strength",
        "duration_minutes": 40,
        "perceived_exertion": 6,
        "sleep_hours": 7.5,
        "mood_rating": 4,
        "study_hours": 3.0,
    },
    {
        "date": "2026-08-08",
        "workout_type": "Cardio",
        "duration_minutes": 35,
        "perceived_exertion": 7,
        "sleep_hours": 8.0,
        "mood_rating": 4,
        "study_hours": 2.0,
    },
    {
        "date": "2026-08-09",
        "workout_type": "Rest",
        "duration_minutes": 0,
        "perceived_exertion": 0,
        "sleep_hours": 7.0,
        "mood_rating": None,
        "study_hours": 1.0,
    },
    {
        "date": "2026-08-10",
        "workout_type": "Strength",
        "duration_minutes": 55,
        "perceived_exertion": 8,
        "sleep_hours": 7.5,
        "mood_rating": 5,
        "study_hours": 4.0,
    },
    {
        "date": "2026-08-11",
        "workout_type": "Mobility",
        "duration_minutes": 25,
        "perceived_exertion": 5,
        "sleep_hours": 8.0,
        "mood_rating": 4,
        "study_hours": 3.0,
    },
    {
        "date": "2026-08-12",
        "workout_type": "Strength",
        "duration_minutes": 45,
        "perceived_exertion": 7,
        "sleep_hours": 8.5,
        "mood_rating": 5,
        "study_hours": 2.0,
    },
]


def main() -> None:
    """Run the hand-verified Week 5 analytics acceptance checks."""

    # =========================================================
    # Full 14-day dataset
    # =========================================================

    metrics = calculate_metrics(
        RECORDS,
        "2026-08-12",
    )

    current = metrics["current_period"]
    previous = metrics["previous_period"]
    differences = metrics["differences"]

    print("Recovery Compass - Manual Analytics Check")
    print("-----------------------------------------")
    print()
    print("Current period:")
    print(current)
    print()
    print("Previous period:")
    print(previous)
    print()
    print("Differences:")
    print(differences)
    print()

    # ---------------------------------------------------------
    # Current period: August 6 through August 12
    # ---------------------------------------------------------

    assert metrics["total_records"] == 14

    assert current["start_date"] == "2026-08-06"
    assert current["end_date"] == "2026-08-12"

    assert current["days_recorded"] == 7
    assert current["workout_days"] == 5
    assert current["total_training_minutes"] == 200

    assert isclose(
        current["average_sleep_hours"],
        54.5 / 7,
    )

    assert isclose(
        current["average_study_hours"],
        17 / 7,
    )

    assert isclose(
        current["average_mood_rating"],
        22 / 5,
    )

    assert current["mood_entries"] == 5

    assert isclose(
        current["average_training_exertion"],
        33 / 5,
    )

    # ---------------------------------------------------------
    # Previous period: July 30 through August 5
    # ---------------------------------------------------------

    assert previous["start_date"] == "2026-07-30"
    assert previous["end_date"] == "2026-08-05"

    assert previous["days_recorded"] == 7
    assert previous["workout_days"] == 5
    assert previous["total_training_minutes"] == 205

    assert isclose(
        previous["average_sleep_hours"],
        51.5 / 7,
    )

    assert isclose(
        previous["average_study_hours"],
        17.5 / 7,
    )

    assert isclose(
        previous["average_mood_rating"],
        20 / 6,
    )

    assert previous["mood_entries"] == 6

    assert isclose(
        previous["average_training_exertion"],
        32 / 5,
    )

    # ---------------------------------------------------------
    # Current-versus-previous comparison
    # ---------------------------------------------------------

    assert metrics["comparison_available"] is True
    assert differences is not None

    assert differences["workout_days"] == 0

    assert differences["total_training_minutes"] == -5

    assert isclose(
        differences["average_sleep_hours"],
        (54.5 / 7) - (51.5 / 7),
    )

    assert isclose(
        differences["average_study_hours"],
        (17 / 7) - (17.5 / 7),
    )

    assert isclose(
        differences["average_mood_rating"],
        (22 / 5) - (20 / 6),
    )

    assert isclose(
        differences["average_training_exertion"],
        (33 / 5) - (32 / 5),
    )

    # =========================================================
    # Complete current period but no previous-period data
    # =========================================================

    current_only_metrics = calculate_metrics(
        RECORDS[7:],
        "2026-08-12",
    )

    current_only_current = current_only_metrics["current_period"]
    current_only_previous = current_only_metrics["previous_period"]

    assert current_only_metrics["total_records"] == 7

    assert current_only_current["days_recorded"] == 7
    assert current_only_previous["days_recorded"] == 0

    assert current_only_metrics["comparison_available"] is False
    assert current_only_metrics["differences"] is None

    # =========================================================
    # Empty dataset
    # =========================================================

    empty_metrics = calculate_metrics(
        [],
        "2026-08-12",
    )

    empty_current = empty_metrics["current_period"]
    empty_previous = empty_metrics["previous_period"]

    assert empty_metrics["total_records"] == 0

    assert empty_current["start_date"] == "2026-08-06"
    assert empty_current["end_date"] == "2026-08-12"

    assert empty_current["days_recorded"] == 0
    assert empty_current["workout_days"] == 0
    assert empty_current["total_training_minutes"] == 0

    assert empty_current["average_sleep_hours"] is None
    assert empty_current["average_study_hours"] is None
    assert empty_current["average_mood_rating"] is None
    assert empty_current["mood_entries"] == 0
    assert empty_current["average_training_exertion"] is None

    assert empty_previous["days_recorded"] == 0

    assert empty_metrics["comparison_available"] is False
    assert empty_metrics["differences"] is None

    # =========================================================
    # Sparse current period: only 3 of 7 days recorded
    # =========================================================

    sparse_metrics = calculate_metrics(
        RECORDS[7:10],
        "2026-08-12",
    )

    sparse_current = sparse_metrics["current_period"]
    sparse_previous = sparse_metrics["previous_period"]

    assert sparse_metrics["total_records"] == 3

    assert sparse_current["start_date"] == "2026-08-06"
    assert sparse_current["end_date"] == "2026-08-12"

    assert sparse_current["days_recorded"] == 3
    assert sparse_current["workout_days"] == 2
    assert sparse_current["total_training_minutes"] == 75

    assert isclose(
        sparse_current["average_sleep_hours"],
        23.5 / 3,
    )

    assert isclose(
        sparse_current["average_study_hours"],
        7 / 3,
    )

    assert isclose(
        sparse_current["average_mood_rating"],
        4.0,
    )

    assert sparse_current["mood_entries"] == 2

    assert isclose(
        sparse_current["average_training_exertion"],
        6.5,
    )

    assert sparse_previous["days_recorded"] == 0

    assert sparse_metrics["comparison_available"] is False
    assert sparse_metrics["differences"] is None

    print(
        "PASS - Full periods, one-period-only data, sparse data, "
        "empty data, and comparison behavior all match the expected values."
    )


if __name__ == "__main__":
    main()