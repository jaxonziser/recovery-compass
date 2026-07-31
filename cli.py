"""Temporary command-line input flow for Recovery Compass.

Week 3 Wednesday scope:
- collect one candidate daily record,
- display the collected values,
- do not validate or save data yet.
"""


def collect_candidate_record() -> dict[str, str]:
    """Prompt the user for one unvalidated daily record."""

    print("Recovery Compass - Daily Entry")
    print("--------------------------------")
    print("Required fields are marked with *.")
    print()

    record = {
        "date": input("Date* (YYYY-MM-DD): ").strip(),
        "workout_type": input(
            "Workout type* "
            "(Rest, Strength, Cardio, Sport, Mobility, Other): "
        ).strip(),
        "duration_minutes": input(
            "Workout duration* in minutes (0-300): "
        ).strip(),
        "perceived_exertion": input(
            "Perceived exertion* (0-10): "
        ).strip(),
        "sleep_hours": input("Sleep hours* (0-16): ").strip(),
        "mood_rating": input(
            "Mood rating (1-5, optional; press Enter to skip): "
        ).strip(),
        "study_hours": input("Study hours* (0-16): ").strip(),
    }

    return record


def display_candidate_record(record: dict[str, str]) -> None:
    """Display the candidate record without validating or saving it."""

    print()
    print("Candidate Record")
    print("----------------")

    for field, value in record.items():
        displayed_value = value if value else "(blank)"
        print(f"{field}: {displayed_value}")

    print()
    print("This record has not been validated or saved.")


def main() -> None:
    """Run the temporary Recovery Compass input flow."""

    candidate_record = collect_candidate_record()
    display_candidate_record(candidate_record)


if __name__ == "__main__":
    main()