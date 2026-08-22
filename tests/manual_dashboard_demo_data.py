"""Create deterministic synthetic data scenarios for Recovery Compass dashboard QA."""

from pathlib import Path
import argparse

from src.storage import save_record


DEMO_PATH = Path("data/dashboard_demo.csv")


PREVIOUS_COMPLETE = [
    {
        "date": "2026-08-09",
        "workout_type": "Rest",
        "duration_minutes": 0,
        "perceived_exertion": 0,
        "sleep_hours": 7.5,
        "mood_rating": 3,
        "study_hours": 2.5,
    },
    {
        "date": "2026-08-10",
        "workout_type": "Strength",
        "duration_minutes": 45,
        "perceived_exertion": 7,
        "sleep_hours": 7.0,
        "mood_rating": 4,
        "study_hours": 3.0,
    },
    {
        "date": "2026-08-11",
        "workout_type": "Cardio",
        "duration_minutes": 35,
        "perceived_exertion": 6,
        "sleep_hours": 8.0,
        "mood_rating": 4,
        "study_hours": 1.5,
    },
    {
        "date": "2026-08-12",
        "workout_type": "Rest",
        "duration_minutes": 0,
        "perceived_exertion": 0,
        "sleep_hours": 8.5,
        "mood_rating": None,
        "study_hours": 1.0,
    },
    {
        "date": "2026-08-13",
        "workout_type": "Strength",
        "duration_minutes": 60,
        "perceived_exertion": 8,
        "sleep_hours": 6.5,
        "mood_rating": 3,
        "study_hours": 4.0,
    },
    {
        "date": "2026-08-14",
        "workout_type": "Mobility",
        "duration_minutes": 25,
        "perceived_exertion": 4,
        "sleep_hours": 7.5,
        "mood_rating": 4,
        "study_hours": 2.0,
    },
    {
        "date": "2026-08-15",
        "workout_type": "Strength",
        "duration_minutes": 50,
        "perceived_exertion": 7,
        "sleep_hours": 7.0,
        "mood_rating": 3,
        "study_hours": 3.5,
    },
]


CURRENT_COMPLETE = [
    {
        "date": "2026-08-16",
        "workout_type": "Rest",
        "duration_minutes": 0,
        "perceived_exertion": 0,
        "sleep_hours": 8.0,
        "mood_rating": 4,
        "study_hours": 2.0,
    },
    {
        "date": "2026-08-17",
        "workout_type": "Strength",
        "duration_minutes": 40,
        "perceived_exertion": 6,
        "sleep_hours": 7.5,
        "mood_rating": 4,
        "study_hours": 3.0,
    },
    {
        "date": "2026-08-18",
        "workout_type": "Cardio",
        "duration_minutes": 30,
        "perceived_exertion": 7,
        "sleep_hours": 8.0,
        "mood_rating": 5,
        "study_hours": 2.0,
    },
    {
        "date": "2026-08-19",
        "workout_type": "Rest",
        "duration_minutes": 0,
        "perceived_exertion": 0,
        "sleep_hours": 8.5,
        "mood_rating": None,
        "study_hours": 1.0,
    },
    {
        "date": "2026-08-20",
        "workout_type": "Strength",
        "duration_minutes": 55,
        "perceived_exertion": 8,
        "sleep_hours": 7.0,
        "mood_rating": 4,
        "study_hours": 4.0,
    },
    {
        "date": "2026-08-21",
        "workout_type": "Mobility",
        "duration_minutes": 25,
        "perceived_exertion": 5,
        "sleep_hours": 8.0,
        "mood_rating": 4,
        "study_hours": 2.5,
    },
    {
        "date": "2026-08-22",
        "workout_type": "Strength",
        "duration_minutes": 45,
        "perceived_exertion": 7,
        "sleep_hours": 8.5,
        "mood_rating": 5,
        "study_hours": 2.0,
    },
]


CURRENT_SPARSE = [
    {
        "date": "2026-08-17",
        "workout_type": "Strength",
        "duration_minutes": 40,
        "perceived_exertion": 6,
        "sleep_hours": 7.5,
        "mood_rating": 4,
        "study_hours": 3.0,
    },
    {
        "date": "2026-08-19",
        "workout_type": "Rest",
        "duration_minutes": 0,
        "perceived_exertion": 0,
        "sleep_hours": 8.5,
        "mood_rating": 4,
        "study_hours": 1.0,
    },
    {
        "date": "2026-08-22",
        "workout_type": "Cardio",
        "duration_minutes": 30,
        "perceived_exertion": 7,
        "sleep_hours": 8.0,
        "mood_rating": 5,
        "study_hours": 2.0,
    },
]


CURRENT_MISSING_AND_ZERO = [
    {
        "date": "2026-08-16",
        "workout_type": "Rest",
        "duration_minutes": 0,
        "perceived_exertion": 0,
        "sleep_hours": 8.0,
        "mood_rating": 4,
        "study_hours": 2.0,
    },
    {
        "date": "2026-08-17",
        "workout_type": "Strength",
        "duration_minutes": 40,
        "perceived_exertion": 0,
        "sleep_hours": 7.5,
        "mood_rating": 4,
        "study_hours": 3.0,
    },
    {
        "date": "2026-08-18",
        "workout_type": "Cardio",
        "duration_minutes": 30,
        "perceived_exertion": 7,
        "sleep_hours": 8.0,
        "mood_rating": None,
        "study_hours": 2.0,
    },
    {
        "date": "2026-08-19",
        "workout_type": "Rest",
        "duration_minutes": 0,
        "perceived_exertion": 0,
        "sleep_hours": 8.5,
        "mood_rating": None,
        "study_hours": 1.0,
    },
    {
        "date": "2026-08-20",
        "workout_type": "Strength",
        "duration_minutes": 55,
        "perceived_exertion": 8,
        "sleep_hours": 7.0,
        "mood_rating": 4,
        "study_hours": 4.0,
    },
    {
        "date": "2026-08-21",
        "workout_type": "Mobility",
        "duration_minutes": 25,
        "perceived_exertion": 5,
        "sleep_hours": 8.0,
        "mood_rating": 4,
        "study_hours": 2.5,
    },
    {
        "date": "2026-08-22",
        "workout_type": "Strength",
        "duration_minutes": 45,
        "perceived_exertion": 7,
        "sleep_hours": 8.5,
        "mood_rating": 5,
        "study_hours": 2.0,
    },
]


SCENARIOS = {
    "complete": PREVIOUS_COMPLETE + CURRENT_COMPLETE,
    "sparse": CURRENT_SPARSE,
    "empty": [],
    "missing": PREVIOUS_COMPLETE + CURRENT_MISSING_AND_ZERO,
}


def _reset_demo_file() -> None:
    """Remove any prior generated dashboard QA CSV."""
    if DEMO_PATH.exists():
        DEMO_PATH.unlink()


def _write_records(records: list[dict[str, object]]) -> None:
    """Write records through the real Recovery Compass storage layer."""
    for record in records:
        save_record(
            record,
            file_path=DEMO_PATH,
        )


def main() -> None:
    """Create the requested dashboard QA scenario."""
    parser = argparse.ArgumentParser(
        description=(
            "Generate deterministic Recovery Compass dashboard QA data."
        )
    )

    parser.add_argument(
        "scenario",
        nargs="?",
        default="complete",
        choices=SCENARIOS,
        help=(
            "QA scenario to generate: complete, sparse, empty, or missing."
        ),
    )

    args = parser.parse_args()

    _reset_demo_file()

    records = SCENARIOS[args.scenario]

    if records:
        _write_records(records)

    print(
        "PASS - Dashboard QA scenario "
        f"'{args.scenario}' prepared with {len(records)} records."
    )

    if args.scenario == "complete":
        print(
            "Current period: Aug 16–22 (7/7). "
            "Previous period: Aug 9–15 (7/7)."
        )

    elif args.scenario == "sparse":
        print(
            "Current period has 3 recorded days. "
            "Formal previous-week comparison should be unavailable."
        )

    elif args.scenario == "empty":
        print(
            "No demo CSV remains. "
            "load_records() should return an empty record list."
        )

    elif args.scenario == "missing":
        print(
            "Current period is 7/7 with missing mood values, Rest days, "
            "and a legitimate non-Rest exertion value of 0."
        )


if __name__ == "__main__":
    main()