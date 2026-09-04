from src.validation import normalize_record, validate_record


def _valid_record(**overrides):
    record = {
        "date": "2026-08-28",
        "workout_type": "Strength",
        "duration_minutes": "45",
        "perceived_exertion": "7",
        "sleep_hours": "7.5",
        "mood_rating": "4",
        "study_hours": "2.0",
    }

    record.update(overrides)

    return record


def test_valid_record_has_no_errors():
    record = _valid_record()

    assert validate_record(record) == []
    assert (
        "Perceived Exertion must be a whole number between 1 and 10."
    ) in validate_record(_valid_record(perceived_exertion="0"))


def test_normalize_record_uses_documented_types():
    result = normalize_record(
        _valid_record()
    )

    assert result == {
        "date": "2026-08-28",
        "workout_type": "Strength",
        "duration_minutes": 45,
        "perceived_exertion": 7,
        "sleep_hours": 7.5,
        "mood_rating": 4,
        "study_hours": 2.0,
    }


def test_blank_mood_normalizes_to_none():
    result = normalize_record(
        _valid_record(
            mood_rating="",
        )
    )

    assert result["mood_rating"] is None


def test_invalid_calendar_date_is_rejected():
    errors = validate_record(
        _valid_record(
            date="2026-02-30",
        )
    )

    assert any(
        "Date" in error
        for error in errors
    )


def test_invalid_workout_type_is_rejected():
    errors = validate_record(
        _valid_record(
            workout_type="Flying",
        )
    )

    assert any(
        "Workout Type" in error
        for error in errors
    )


def test_out_of_range_values_are_rejected():
    errors = validate_record(
        _valid_record(
            duration_minutes="301",
            perceived_exertion="11",
            sleep_hours="17",
            mood_rating="6",
            study_hours="17",
        )
    )

    assert len(errors) == 5
    assert (
        "Perceived Exertion must be a whole number between 1 and 10."
    ) in errors


def test_missing_required_values_are_rejected():
    errors = validate_record(
        _valid_record(
            duration_minutes="",
            perceived_exertion="",
            sleep_hours="",
            study_hours="",
        )
    )

    assert len(errors) >= 4
    assert "Perceived Exertion is required." in errors

def test_rest_record_requires_zero_duration_and_exertion():
    errors = validate_record(
        _valid_record(
            workout_type="Rest",
            duration_minutes="50",
            perceived_exertion="6",
        )
    )

    assert (
        "Workout Duration must be 0 when "
        "Workout Type is Rest."
    ) in errors

    assert (
        "Perceived Exertion must be 0 when "
        "Workout Type is Rest."
    ) in errors


def test_valid_rest_record_normalizes_with_zero_workout_values():
    result = normalize_record(
        _valid_record(
            workout_type="Rest",
            duration_minutes="0",
            perceived_exertion="0",
        )
    )

    assert result["workout_type"] == "Rest"
    assert result["duration_minutes"] == 0
    assert result["perceived_exertion"] == 0
