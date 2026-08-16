"""Manual acceptance check for Recovery Compass chart-ready data."""

from src.analytics import prepare_chart_data


RECORDS = [
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
        "date": "2026-08-06",
        "workout_type": "Rest",
        "duration_minutes": 0,
        "perceived_exertion": 0,
        "sleep_hours": 8.0,
        "mood_rating": None,
        "study_hours": 2.0,
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
    {
        "date": "2026-08-07",
        "workout_type": "Strength",
        "duration_minutes": 40,
        "perceived_exertion": 6,
        "sleep_hours": 7.5,
        "mood_rating": 4,
        "study_hours": 3.0,
    },
]


def main() -> None:
    """Run representative chart-data acceptance checks."""
    chart_data = prepare_chart_data(RECORDS)

    sleep_mood = chart_data["sleep_mood"]
    training = chart_data["training"]
    study = chart_data["study"]

    print("Recovery Compass - Manual Chart Data Check")
    print("------------------------------------------")
    print()
    print("Sleep / mood:")
    print(sleep_mood)
    print()
    print("Training:")
    print(training)
    print()
    print("Study:")
    print(study)
    print()

    # ---------------------------------------------------------
    # Overall structure
    # ---------------------------------------------------------

    assert set(chart_data.keys()) == {
        "sleep_mood",
        "training",
        "study",
    }

    assert len(sleep_mood) == 4
    assert len(training) == 4
    assert len(study) == 4

    # ---------------------------------------------------------
    # Chronological ordering
    # ---------------------------------------------------------

    expected_dates = [
        "2026-08-06",
        "2026-08-07",
        "2026-08-08",
        "2026-08-12",
    ]

    assert [row["date"] for row in sleep_mood] == expected_dates
    assert [row["date"] for row in training] == expected_dates
    assert [row["date"] for row in study] == expected_dates

    # ---------------------------------------------------------
    # August 6: Rest day + missing mood
    # ---------------------------------------------------------

    assert sleep_mood[0] == {
        "date": "2026-08-06",
        "sleep_hours": 8.0,
        "mood_rating": None,
    }

    assert training[0] == {
        "date": "2026-08-06",
        "workout_type": "Rest",
        "duration_minutes": 0,
        "perceived_exertion": None,
    }

    assert study[0] == {
        "date": "2026-08-06",
        "study_hours": 2.0,
    }

    # ---------------------------------------------------------
    # August 7: Real workout
    # ---------------------------------------------------------

    assert training[1] == {
        "date": "2026-08-07",
        "workout_type": "Strength",
        "duration_minutes": 40,
        "perceived_exertion": 6,
    }

    # ---------------------------------------------------------
    # August 12: Representative final row
    # ---------------------------------------------------------

    assert sleep_mood[3] == {
        "date": "2026-08-12",
        "sleep_hours": 8.5,
        "mood_rating": 5,
    }

    assert training[3] == {
        "date": "2026-08-12",
        "workout_type": "Strength",
        "duration_minutes": 45,
        "perceived_exertion": 7,
    }

    assert study[3] == {
        "date": "2026-08-12",
        "study_hours": 2.0,
    }

    # ---------------------------------------------------------
    # Empty input
    # ---------------------------------------------------------

    empty_chart_data = prepare_chart_data([])

    assert empty_chart_data == {
        "sleep_mood": [],
        "training": [],
        "study": [],
    }

    print(
        "PASS - Chart-ready data is chronological, preserves missing values, "
        "handles rest days correctly, and matches representative records."
    )


if __name__ == "__main__":
    main()