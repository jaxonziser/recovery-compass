"""Create deterministic, date-relative synthetic data scenarios for Recovery Compass dashboard QA."""

from datetime import date, timedelta
from pathlib import Path
import argparse

from src.storage import save_record

DEMO_PATH = Path("data/dashboard_demo.csv")


def _iso(days_from_today: int) -> str:
    return (date.today() + timedelta(days=days_from_today)).isoformat()


def _record(days_from_today, workout_type, duration_minutes, perceived_exertion,
            sleep_hours, mood_rating, study_hours):
    return {
        "date": _iso(days_from_today),
        "workout_type": workout_type,
        "duration_minutes": duration_minutes,
        "perceived_exertion": perceived_exertion,
        "sleep_hours": sleep_hours,
        "mood_rating": mood_rating,
        "study_hours": study_hours,
    }


PREVIOUS_COMPLETE = [
    _record(-13, "Rest", 0, 0, 7.5, 3, 2.5),
    _record(-12, "Strength", 45, 7, 7.0, 4, 3.0),
    _record(-11, "Cardio", 35, 6, 8.0, 4, 1.5),
    _record(-10, "Rest", 0, 0, 8.5, None, 1.0),
    _record(-9, "Strength", 60, 8, 6.5, 3, 4.0),
    _record(-8, "Mobility", 25, 4, 7.5, 4, 2.0),
    _record(-7, "Strength", 50, 7, 7.0, 3, 3.5),
]

CURRENT_COMPLETE = [
    _record(-6, "Rest", 0, 0, 8.0, 4, 2.0),
    _record(-5, "Strength", 40, 6, 7.5, 4, 3.0),
    _record(-4, "Cardio", 30, 7, 8.0, 5, 2.0),
    _record(-3, "Rest", 0, 0, 8.5, None, 1.0),
    _record(-2, "Strength", 55, 8, 7.0, 4, 4.0),
    _record(-1, "Mobility", 25, 5, 8.0, 4, 2.5),
    _record(0, "Strength", 45, 7, 8.5, 5, 2.0),
]

CURRENT_SPARSE = [
    _record(-5, "Strength", 40, 6, 7.5, 4, 3.0),
    _record(-3, "Rest", 0, 0, 8.5, 4, 1.0),
    _record(0, "Cardio", 30, 7, 8.0, 5, 2.0),
]

CURRENT_MISSING_AND_ZERO = [
    _record(-6, "Rest", 0, 0, 8.0, 4, 2.0),
    _record(-5, "Strength", 40, 0, 7.5, 4, 3.0),
    _record(-4, "Cardio", 30, 7, 8.0, None, 2.0),
    _record(-3, "Rest", 0, 0, 8.5, None, 1.0),
    _record(-2, "Strength", 55, 8, 7.0, 4, 4.0),
    _record(-1, "Mobility", 25, 5, 8.0, 4, 2.5),
    _record(0, "Strength", 45, 7, 8.5, 5, 2.0),
]

SCENARIOS = {
    "complete": PREVIOUS_COMPLETE + CURRENT_COMPLETE,
    "sparse": CURRENT_SPARSE,
    "empty": [],
    "missing": PREVIOUS_COMPLETE + CURRENT_MISSING_AND_ZERO,
}


def _reset_demo_file():
    if DEMO_PATH.exists():
        DEMO_PATH.unlink()


def _write_records(records):
    for record in records:
        save_record(record, file_path=DEMO_PATH)


def main():
    parser = argparse.ArgumentParser(
        description="Generate date-relative Recovery Compass dashboard QA data."
    )
    parser.add_argument(
        "scenario",
        nargs="?",
        default="complete",
        choices=SCENARIOS,
    )
    args = parser.parse_args()

    _reset_demo_file()
    records = SCENARIOS[args.scenario]
    if records:
        _write_records(records)

    current_start = date.today() - timedelta(days=6)
    previous_start = date.today() - timedelta(days=13)
    previous_end = date.today() - timedelta(days=7)

    print(
        f"PASS - Dashboard QA scenario '{args.scenario}' "
        f"prepared with {len(records)} records."
    )

    if args.scenario == "complete":
        print(
            f"Current period: {current_start.isoformat()} through "
            f"{date.today().isoformat()} (7/7)."
        )
        print(
            f"Previous period: {previous_start.isoformat()} through "
            f"{previous_end.isoformat()} (7/7)."
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
