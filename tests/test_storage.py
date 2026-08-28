import pytest

from src.storage import (
    DuplicateDateError,
    StorageError,
    export_records,
    import_records,
    load_records,
    save_record,
)


def _record(
    record_date,
    workout_type="Strength",
    duration_minutes=45,
    perceived_exertion=7,
    sleep_hours=7.5,
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


def test_missing_file_loads_as_empty(tmp_path):
    path = tmp_path / "missing.csv"

    assert load_records(path) == []


def test_save_and_reload_round_trip(tmp_path):
    path = tmp_path / "working.csv"

    original = _record(
        "2026-08-28"
    )

    save_record(
        original,
        path,
    )

    loaded = load_records(path)

    assert loaded == [original]


def test_duplicate_date_is_rejected(tmp_path):
    path = tmp_path / "working.csv"

    save_record(
        _record("2026-08-28"),
        path,
    )

    with pytest.raises(DuplicateDateError):
        save_record(
            _record(
                "2026-08-28",
                duration_minutes=60,
            ),
            path,
        )

    loaded = load_records(path)

    assert len(loaded) == 1
    assert loaded[0]["duration_minutes"] == 45


def test_export_creates_matching_separate_copy(tmp_path):
    source = tmp_path / "working.csv"
    destination = tmp_path / "export.csv"

    save_record(
        _record("2026-08-27"),
        source,
    )

    save_record(
        _record(
            "2026-08-28",
            workout_type="Cardio",
            duration_minutes=30,
            perceived_exertion=5,
        ),
        source,
    )

    export_records(
        destination,
        source,
    )

    assert destination.exists()

    assert (
        load_records(destination)
        == load_records(source)
    )


def test_valid_import_adds_new_record(tmp_path):
    working = tmp_path / "working.csv"
    incoming = tmp_path / "incoming.csv"

    save_record(
        _record("2026-08-27"),
        working,
    )

    save_record(
        _record(
            "2026-08-28",
            workout_type="Cardio",
            duration_minutes=30,
            perceived_exertion=5,
        ),
        incoming,
    )

    imported_count = import_records(
        incoming,
        working,
    )

    assert imported_count == 1

    loaded = load_records(working)

    assert len(loaded) == 2

    assert {
        record["date"]
        for record in loaded
    } == {
        "2026-08-27",
        "2026-08-28",
    }


def test_conflicting_import_changes_nothing(tmp_path):
    working = tmp_path / "working.csv"
    incoming = tmp_path / "incoming.csv"

    save_record(
        _record("2026-08-27"),
        working,
    )

    save_record(
        _record("2026-08-28"),
        incoming,
    )

    save_record(
        _record(
            "2026-08-27",
            duration_minutes=60,
        ),
        incoming,
    )

    before = load_records(working)

    with pytest.raises(StorageError):
        import_records(
            incoming,
            working,
        )

    after = load_records(working)

    assert after == before