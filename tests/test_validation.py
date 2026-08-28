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


def test_missing_required_values_are_rejected():
    errors = validate_record(
        _valid_record(
            duration_minutes="",
            sleep_hours="",
            study_hours="",
        )
    )

    assert len(errors) >= 3