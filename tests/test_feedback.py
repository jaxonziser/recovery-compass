from src.feedback import generate_feedback


def test_sparse_current_period_feedback():
    metrics = {
        "current_period": {
            "start_date": "2026-08-20",
            "end_date": "2026-08-26",
            "days_recorded": 2,
            "workout_days": 1,
            "total_training_minutes": 45,
            "average_sleep_hours": 7.5,
            "average_study_hours": 2.0,
            "average_mood_rating": 4.0,
            "mood_entries": 1,
            "average_training_exertion": 7.0,
        },
        "previous_period": None,
        "comparison_available": False,
        "differences": None,
    }

    result = generate_feedback(metrics)

    assert (
        "You recorded 2 of 7 days in the current period."
        in result
    )

    assert (
        "You recorded 1 workout day totaling 45 minutes."
        in result
    )

    assert (
        "Average sleep was 7.5 hours across 2 recorded days."
        in result
    )

    assert (
        "Average study time was 2.0 hours across 2 recorded days."
        in result
    )

    assert (
        "Average mood was 4.0 / 5 across 1 recorded rating."
        in result
    )

    assert (
        "Average perceived exertion was 7.0 / 10 "
        "across 1 workout day."
        in result
    )

    assert not any(
        "previous 7-day period" in statement
        for statement in result
    )


def test_no_workouts_and_no_mood():
    metrics = {
        "current_period": {
            "start_date": "2026-08-20",
            "end_date": "2026-08-26",
            "days_recorded": 3,
            "workout_days": 0,
            "total_training_minutes": 0,
            "average_sleep_hours": 8.0,
            "average_study_hours": 1.5,
            "average_mood_rating": None,
            "mood_entries": 0,
            "average_training_exertion": None,
        },
        "previous_period": None,
        "comparison_available": False,
        "differences": None,
    }

    result = generate_feedback(metrics)

    assert (
        "No actual workout days were recorded "
        "in the current period."
        in result
    )

    assert (
        "No mood ratings were recorded "
        "in the current period."
        in result
    )

    assert (
        "Average sleep was 8.0 hours across 3 recorded days."
        in result
    )

    assert (
        "Average study time was 1.5 hours across 3 recorded days."
        in result
    )

    assert not any(
        "Average perceived exertion" in statement
        for statement in result
    )


def test_complete_period_comparisons():
    metrics = {
        "current_period": {
            "start_date": "2026-08-06",
            "end_date": "2026-08-12",
            "days_recorded": 7,
            "workout_days": 5,
            "total_training_minutes": 200,
            "average_sleep_hours": 7.8,
            "average_study_hours": 2.4,
            "average_mood_rating": 4.4,
            "mood_entries": 5,
            "average_training_exertion": 6.6,
        },
        "previous_period": {
            "start_date": "2026-07-30",
            "end_date": "2026-08-05",
            "days_recorded": 7,
            "workout_days": 5,
            "total_training_minutes": 205,
            "average_sleep_hours": 7.4,
            "average_study_hours": 2.5,
            "average_mood_rating": 3.3,
            "mood_entries": 6,
            "average_training_exertion": 6.4,
        },
        "comparison_available": True,
        "differences": {
            "workout_days": 0,
            "total_training_minutes": -5,
            "average_sleep_hours": 0.4,
            "average_study_hours": -0.1,
            "average_mood_rating": 1.1,
            "average_training_exertion": 0.2,
        },
    }

    result = generate_feedback(metrics)

    assert (
        "Workout days were unchanged compared with "
        "the previous 7-day period."
        in result
    )

    assert (
        "Training time decreased by 5 minutes compared with "
        "the previous 7-day period."
        in result
    )

    assert (
        "Average sleep increased by 0.4 hours compared with "
        "the previous 7-day period."
        in result
    )

    assert (
        "Average study time decreased by 0.1 hours compared with "
        "the previous 7-day period."
        in result
    )

    assert (
        "Average mood increased by 1.1 points compared with "
        "the previous 7-day period."
        in result
    )

    assert (
        "Average perceived exertion increased by 0.2 points "
        "compared with the previous 7-day period."
        in result
    )


def test_same_metrics_produce_same_feedback():
    metrics = {
        "current_period": {
            "start_date": "2026-08-20",
            "end_date": "2026-08-26",
            "days_recorded": 1,
            "workout_days": 1,
            "total_training_minutes": 30,
            "average_sleep_hours": 8.0,
            "average_study_hours": 2.0,
            "average_mood_rating": 5.0,
            "mood_entries": 1,
            "average_training_exertion": 6.0,
        },
        "previous_period": None,
        "comparison_available": False,
        "differences": None,
    }

    first = generate_feedback(metrics)
    second = generate_feedback(metrics)

    assert first == second


def test_complete_comparison_handles_missing_optional_metrics():
    metrics = {
        "current_period": {
            "start_date": "2026-08-06",
            "end_date": "2026-08-12",
            "days_recorded": 7,
            "workout_days": 0,
            "total_training_minutes": 0,
            "average_sleep_hours": 8.0,
            "average_study_hours": 2.0,
            "average_mood_rating": None,
            "mood_entries": 0,
            "average_training_exertion": None,
        },
        "previous_period": {
            "start_date": "2026-07-30",
            "end_date": "2026-08-05",
            "days_recorded": 7,
            "workout_days": 0,
            "total_training_minutes": 0,
            "average_sleep_hours": 7.5,
            "average_study_hours": 2.0,
            "average_mood_rating": None,
            "mood_entries": 0,
            "average_training_exertion": None,
        },
        "comparison_available": True,
        "differences": {
            "workout_days": 0,
            "total_training_minutes": 0,
            "average_sleep_hours": 0.5,
            "average_study_hours": 0.0,
            "average_mood_rating": None,
            "average_training_exertion": None,
        },
    }

    result = generate_feedback(metrics)

    assert (
        "Workout days were unchanged compared with "
        "the previous 7-day period."
        in result
    )

    assert (
        "Training time was unchanged compared with "
        "the previous 7-day period."
        in result
    )

    assert (
        "Average sleep increased by 0.5 hours compared with "
        "the previous 7-day period."
        in result
    )

    assert (
        "Average study time was unchanged compared with "
        "the previous 7-day period."
        in result
    )

    assert not any(
        statement.startswith("Average mood increased")
        or statement.startswith("Average mood decreased")
        or statement.startswith("Average mood was unchanged")
        for statement in result
    )

    assert not any(
        statement.startswith(
            "Average perceived exertion increased"
        )
        or statement.startswith(
            "Average perceived exertion decreased"
        )
        or statement.startswith(
            "Average perceived exertion was unchanged"
        )
        for statement in result
    )