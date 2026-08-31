# Recovery Compass Manual Testing

**Test date:** 2026-07-31
**Feature:** Daily-record validation and normalization
**Environment:** Windows PowerShell, Python command-line interface

## Test Results

| Case | Expected Result | Actual Result | Status |
|---|---|---|---|
| Valid baseline | Valid record is accepted and normalized | Record accepted; workout type standardized; numeric fields normalized; blank mood displayed as not provided | Pass |
| Missing Sleep Hours | Record is rejected with a specific required-field error | Record rejected with “Sleep Hours is required.”; no normalization or crash occurred | Pass |
| Unsupported Workout Type | Record is rejected with the allowed workout categories | Record rejected with the complete allowed-value message for Workout Type; no normalization or crash occurred | Pass |
| Workout Duration Above Range | Record is rejected when duration exceeds 300 minutes | Record rejected with “Workout Duration must be a whole number between 0 and 300.”; no normalization or crash occurred | Pass |
| Perceived Exertion Above Range | Record is rejected when exertion exceeds 10 | Record rejected with “Perceived Exertion must be a whole number between 0 and 10.”; no normalization or crash occurred | Pass |
| Blank Optional Mood | Blank mood is accepted and represented as missing data | Valid record accepted; blank Mood Rating displayed as “(not provided)” | Pass |
| Nonnumeric Study Hours | Record is rejected when Study Hours is not numeric | Record rejected with “Study Hours must be a number between 0 and 16.”; no normalization or crash occurred | Pass |

## Verification Summary

The command-line interface successfully accepted and normalized valid
input. It rejected missing, unsupported, out-of-range, and nonnumeric
values with field-specific messages.

None of the tested invalid inputs caused the program to crash. Invalid
records were stopped before normalization and were not displayed as
accepted.

## Current Limitations

- Records are not yet saved.
- Duplicate dates are not yet checked.
- CSV import and export are not yet implemented.
- Testing was performed manually rather than through automated tests.
- The graphical Streamlit interface has not yet been connected.

## 2026-08-05 — Local CSV Storage Round-Trip

### Test Objective

Verify that one valid normalized Recovery Compass record can be saved to a
local CSV file and then reloaded without changing its fields, values, or
Python data types.

### Synthetic Test Record

```python
{
    "date": "2026-08-05",
    "workout_type": "Strength",
    "duration_minutes": 45,
    "perceived_exertion": 7,
    "sleep_hours": 7.5,
    "mood_rating": None,
    "study_hours": 2.5,
}

## 2026-08-07 — Local CSV Storage Acceptance Matrix

### Test Objective

Verify that Recovery Compass v0.1 local storage behaves safely during normal
use, file errors, duplicate-date conflicts, export, and import.

The purpose of this acceptance pass was to confirm that invalid or conflicting
CSV data does not crash the program, silently corrupt stored records, or
partially alter the working dataset.

### Test Environment

The acceptance script used Python's `TemporaryDirectory()` so that all CSV
files contained only synthetic data and were automatically removed after the
test run.

No personal Recovery Compass data was used.

### Regression Check

Before the expanded acceptance matrix, the original Week 4 round-trip test was
run again.

The synthetic record:

```python
{
    "date": "2026-08-05",
    "workout_type": "Strength",
    "duration_minutes": 45,
    "perceived_exertion": 7,
    "sleep_hours": 7.5,
    "mood_rating": None,
    "study_hours": 2.5,
}
```

was saved and reloaded with the same fields, values, and Python data types.

**Result: Pass**

### Acceptance Matrix

#### Test 1 — Missing File

Expected behavior:

- loading a path that does not exist returns `[]`
- no crash occurs

Actual result:

```text
PASS 1 - Missing file returns an empty list.
```

**Status: Pass**

#### Test 2 — Empty File

Expected behavior:

- a zero-byte CSV represents zero stored records
- loading returns `[]`
- no crash occurs

Actual result:

```text
PASS 2 - Empty file returns an empty list.
```

**Status: Pass**

#### Test 3 — Valid Save and Reload

Expected behavior:

- one valid normalized record can be saved
- the record can be reloaded
- all values and documented Python types remain unchanged

Actual result:

```text
PASS 3 - Valid record survives save and reload.
```

**Status: Pass**

#### Test 4 — Wrong Headers

The test CSV deliberately replaced the approved `sleep_hours` header with an
incorrect header.

Expected behavior:

- the entire CSV is rejected
- the application does not guess or silently rename columns

Actual result:

```text
PASS 4 - Wrong headers are rejected.
```

**Status: Pass**

#### Test 5 — Malformed Row

The test CSV deliberately used the text `banana` for Workout Duration.

Expected behavior:

- the invalid row causes the file to be rejected
- no partial load is accepted

Actual result:

```text
PASS 5 - Malformed row is rejected.
```

**Status: Pass**

#### Test 6 — Duplicate Save

The test attempted to save a second record using a date already present in the
working CSV.

Expected behavior:

- `DuplicateDateError` is raised
- the existing record is not overwritten
- a second record for the same date is not appended

Actual result:

```text
PASS 6 - Duplicate save is rejected.
```

**Status: Pass**

#### Test 7 — Duplicate Dates Already Inside a CSV

A synthetic CSV was manually constructed with two individually valid records
using the same date.

Expected behavior:

- `load_records()` detects the duplicate even though the records did not enter
  through `save_record()`
- the file is rejected

Actual result:

```text
PASS 7 - Duplicate dates inside a CSV are rejected.
```

**Status: Pass**

#### Test 8 — Export Copy

Expected behavior:

- a separate CSV export is created
- the exported records match the working records
- the working CSV remains unchanged

Actual result:

```text
PASS 8 - Export creates a separate matching copy.
```

**Status: Pass**

#### Test 9 — Import and Conflict Protection

A valid synthetic CSV containing a new date was imported.

Expected behavior:

- the new record is added
- the function reports one imported record

The same CSV was then imported again, creating a duplicate-date conflict.

Expected behavior:

- the conflicting import is rejected
- no records from that conflicting import are added
- the working data remains exactly as it was before the failed import

Actual result:

```text
PASS 9 - Import works and conflicting import changes nothing.
```

**Status: Pass**

### Final Test Output

```text
PASS 1 - Missing file returns an empty list.
PASS 2 - Empty file returns an empty list.
PASS 3 - Valid record survives save and reload.
PASS 4 - Wrong headers are rejected.
PASS 5 - Malformed row is rejected.
PASS 6 - Duplicate save is rejected.
PASS 7 - Duplicate dates inside a CSV are rejected.
PASS 8 - Export creates a separate matching copy.
PASS 9 - Import works and conflicting import changes nothing.

All Week 4 storage acceptance tests passed.
```

### Acceptance Result

**9 of 9 storage acceptance checks passed.**

The original Week 4 round-trip regression test also continued to pass after
the storage module was expanded.

### Current Limitations

- Testing is still performed through manual test scripts rather than a full
  automated pytest suite.
- The command-line interface is not yet connected to the completed storage
  functions.
- The Streamlit graphical interface is not yet connected to storage.
- Browser-based CSV downloading and uploading have not yet been implemented.
- The current backend export function writes a separate CSV file to a supplied
  filesystem path. The later Streamlit interface should adapt this behavior to
  the browser's normal download workflow rather than attempting to choose a
  folder on the user's device.
- Editing or replacing an existing daily record is not implemented.
- Duplicate dates are rejected rather than merged or overwritten.
- Import is intentionally all-or-nothing; partial imports are not supported.

## Week 5 Analytics A - August 12, 2026

Implemented and manually verified the first deterministic analytics core in
`src/analytics.py`.

### Metric behavior tested

The analytics core uses consecutive seven-calendar-day periods rather than the
most recent seven records.

For a period ending 2026-08-12:

- Current period: 2026-08-06 through 2026-08-12
- Previous period: 2026-07-30 through 2026-08-05

A 14-record synthetic dataset was independently checked against expected
values.

Current-period verified results:

- Days recorded: 7
- Workout days: 5
- Total training minutes: 200
- Average sleep: 7.785714285714286 hours
- Average study: 2.4285714285714284 hours
- Average mood: 4.4
- Mood entries: 5
- Average training exertion: 6.6

Previous-period verified results:

- Days recorded: 7
- Workout days: 5
- Total training minutes: 205
- Average sleep: 7.357142857142857 hours
- Average study: 2.5 hours
- Average mood: 3.3333333333333335
- Mood entries: 6
- Average training exertion: 6.4

Verified comparison behavior:

- Comparison is available only when both seven-day periods contain 7/7 records.
- Differences are calculated as current period minus previous period.
- With a complete current period but no previous-period records,
  `comparison_available` is False and `differences` is None.
- Missing mood values are excluded rather than treated as zero.
- Rest days do not count as workout days and do not enter average training
  exertion.

Manual test command:

`python -m tests.manual_analytics_check`

Result:

PASS - Current period, previous period, and comparison all match the
independently calculated values.

## Week 5 Analytics B - August 14, 2026

Friday regression and edge-case testing confirmed the deterministic analytics
core remains stable.

Command used:

`python -m tests.manual_analytics_check`

The manual acceptance script now verifies four scenarios.

### 1. Complete current and previous periods

A full 14-record synthetic dataset correctly produced:

- 7/7 current-period coverage
- 7/7 previous-period coverage
- workout frequency
- total training duration
- sleep, study, and mood averages
- mood-entry count
- workout-only average exertion
- current-minus-previous differences
- `comparison_available = True`

The calculated values continued to match the independently hand-verified
expected values from Analytics A.

### 2. Complete current period with no previous-period data

With exactly seven current-period records and no records in the previous
period:

- current-period metrics remain available
- current coverage is 7/7
- previous coverage is 0/7
- `comparison_available = False`
- `differences = None`

### 3. Sparse current-period data

With only three current-period records:

- `days_recorded = 3`
- workout days = 2
- total training minutes = 75
- available sleep, study, mood, and exertion metrics are still calculated
  from the recorded observations
- missing days are not treated as zero
- formal week-to-week comparison remains unavailable

This confirms that Recovery Compass may show truthful current-period facts
with incomplete coverage while refusing to represent a partial period as a
complete comparison period.

### 4. Empty dataset

With no records:

- record count = 0
- workout days = 0
- training minutes = 0
- unavailable averages return `None`
- mood entries = 0
- `comparison_available = False`
- `differences = None`

Zero is used for factual counts and totals. `None` is used when no numerical
average exists.

Final result:

PASS - Full periods, one-period-only data, sparse data, empty data, and
comparison behavior all match the expected values.

## Week 5 - Chart-Ready Data Acceptance

Added and manually tested `prepare_chart_data()` in `src/analytics.py`.

Acceptance checks covered:

- sleep/mood, training, and study datasets
- chronological sorting even when source records are out of order
- preservation of missing mood as `None`
- preservation of workout type for future chart context/tooltips
- rest/no-workout days represented as `duration_minutes = 0` and
  `perceived_exertion = None`
- representative workout, sleep, mood, and study values
- empty input returning three empty datasets
- existing analytics regression suite still passing after the change

Result: PASS.

## Week 6 Dashboard Acceptance Testing — 2026-08-22

Recovery Compass dashboard rendering was manually qualified with deterministic synthetic QA scenarios generated by `tests/manual_dashboard_demo_data.py`.

Tested states:

- Complete: current and previous seven-day periods both contained 7/7 recorded days.
- Missing-data/rest case: current period remained 7/7 while mood values were missing on selected days, Rest-day exertion remained unavailable, and a legitimate non-Rest exertion value of 0 remained visible.
- Sparse: current period contained only 3/7 recorded days. Metrics used only recorded days, missing calendar dates remained gaps, and formal week-to-week comparison remained unavailable.
- Empty: no records existed. Counts and totals showed legitimate zero values, while unavailable averages showed `—`; all chart and Recent Records empty states rendered without error.

Qualified behaviors:

- Sleep and mood use separate scales.
- Missing mood values are never converted to zero.
- Missing calendar days remain visually missing rather than being compressed or converted to zero.
- Training duration shows Rest days at zero minutes.
- Perceived exertion uses a 0–10 scale, excludes Rest days, and preserves a legitimate recorded zero.
- Study charts preserve the full seven-day calendar in sparse periods.
- Formal week-to-week comparison is available only when both consecutive periods contain 7/7 recorded days.
- Dashboard empty states render cleanly without a data file.
- `python -m tests.manual_analytics_check` passed after dashboard work.
- `python -m tests.manual_chart_data_check` passed after dashboard work.

## 2026-08-26 — Streamlit User Data Workflow Qualification

Recovery Compass's first release-critical Streamlit data workflow was
qualified against the existing validation, storage, analytics, and chart
contracts.

### Daily entry / save

- PASS — Required blank fields were rejected with visible validation errors.
- PASS — A valid record was normalized and saved successfully.
- PASS — Saved records persisted after browser refresh / app reopen.
- PASS — A duplicate date was rejected without replacing the existing record.
- PASS — The dashboard remained functional after the save workflow was added.

### Import / export

- PASS — Existing Recovery Compass data exported as a CSV using the documented
  schema.
- PASS — Re-importing data containing existing dates was rejected
  all-or-nothing.
- PASS — A valid CSV containing a new date imported successfully.
- PASS — The imported record persisted after browser refresh.
- PASS — A CSV with malformed / incorrect headers was rejected without
  changing existing records.

### Regression checks

`python -m tests.manual_analytics_check`

PASS — Full periods, one-period-only data, sparse data, empty data, and
comparison behavior matched expected values.

`python -m tests.manual_chart_data_check`

PASS — Chart-ready data remained chronological, preserved missing values,
handled Rest days correctly, and matched representative records.

`python -m tests.manual_storage_acceptance`

PASS — All 9 storage acceptance checks passed.

`python -m tests.manual_storage_round_trip`

PASS — CSV headers and the synthetic record survived the storage round trip
accurately.

### Qualification result

**Streamlit User Data Workflow — QUALIFIED**

Known v1.0 UX follow-up items remain intentionally open:

- Progressive-disclosure redesign.
- First-run onboarding / welcome experience.
- Persistent Help / How It Works access.
- Visual-system cleanup and consistency pass.
- Rest-day UI should prevent or resolve contradictory nonzero training
  duration / exertion values.
- Some native Streamlit controls still need presentation polish.
- Some technical-detail text has insufficient contrast.

## 2026-08-28 — Deterministic Feedback and Automated Test Qualification

Recovery Compass added a deterministic factual feedback layer and established
the project's first real automated pytest suite.

### Deterministic feedback

`src/feedback.py` consumes the existing analytics result and converts qualified
metrics into reproducible factual statements.

The feedback layer does not:

- recalculate analytics;
- infer causes;
- diagnose health or recovery conditions;
- generate recommendations;
- create a recovery score;
- depend on a live AI model.

Qualified behaviors include:

- sparse current-period feedback;
- no-workout state;
- missing-mood state;
- missing exertion state;
- complete current/previous period comparison;
- positive, negative, and unchanged comparisons;
- omission of unavailable optional comparison metrics;
- deterministic repeatability.

The feedback was also integrated into `app.py` and visually checked against
the dashboard metrics.

### Automated pytest suite

Added real automated tests for:

- `src/validation.py`
- `src/storage.py`
- `src/analytics.py`
- `src/feedback.py`

Final automated result:

`python -m pytest -q`

PASS — 24 tests passed.

### Regression qualification

PASS — manual analytics check
PASS — manual chart-data check
PASS — all 9 manual storage acceptance checks
PASS — manual storage round-trip
PASS — `python -m py_compile app.py src/feedback.py`
PASS — `git diff --check`

### Result

**Deterministic Feedback — QUALIFIED**

**Automated Pytest Foundation — QUALIFIED**

## 2026-08-30 — Release-State Synthetic Qualification

Recovery Compass was evaluated against four date-relative synthetic
release-critical dashboard states using the real storage, analytics,
feedback, and Streamlit pathways.

### Broad regression baseline

PASS — 24 automated pytest tests
PASS — manual analytics regression
PASS — manual chart-data regression
PASS — all 9 storage acceptance checks
PASS — storage round-trip
PASS — Python compilation
PASS — Git whitespace check

### Synthetic dashboard scenarios

**Complete — PASS**
- Current 7-day period contained 7/7 recorded days.
- Previous 7-day period contained 7/7 recorded days.
- Formal comparison unlocked.
- Metrics, charts, deterministic feedback, and recent records populated.

**Sparse — PASS**
- Current period contained 3/7 recorded days.
- Missing calendar days remained missing rather than becoming zero.
- Formal previous-period comparison remained unavailable.
- Metrics, charts, and feedback remained stable.

**Empty — PASS**
- App loaded safely with no records.
- Coverage remained 0/7.
- Missing averages were not fabricated.
- Empty chart/record states rendered without failure.
- Daily-entry workflow remained available.

**Missing / Zero — PASS**
- Current period contained 7/7 recorded days.
- Missing mood ratings remained missing.
- Missing mood values were not converted to zero.
- Rest-day exertion remained excluded.
- A legitimate non-Rest perceived-exertion value of zero remained a real zero.
- Comparison and deterministic feedback remained stable.

### QA tooling repair

`tests/manual_dashboard_demo_data.py` was converted from fixed August 2026
dates to dates relative to the current day so that complete, sparse, empty,
and missing-data qualification remains valid in future runs.

Generated `data/dashboard_demo.csv` is now explicitly ignored by Git.

### Result

**Synthetic Release-State Evaluation — QUALIFIED**

## 2026-08-30 — Browser-Local Persistence Qualification

Recovery Compass v1.0 was converted from shared local-file runtime
persistence to browser-local persistence.

### Static qualification

PASS — Python compilation
PASS — 24 automated pytest tests
PASS — Git whitespace check

### Browser persistence

PASS — fresh browser storage started empty even though the developer
machine still contained `data/recovery_compass.csv`.

PASS — a synthetic Aug. 30 record was added successfully and propagated
through analytics, deterministic feedback, charts, and Recent Records.

PASS — the record survived a full browser refresh.

PASS — the record survived tab close and reopen in the same browser.

### Browser isolation

PASS — Chrome Guest opened the same Recovery Compass server with an empty
dataset while the normal Opera GX browser retained its existing record.

This confirms that separate browser storage contexts do not share the same
Recovery Compass dataset.

### Import / export portability

PASS — browser-local data downloaded successfully as Recovery Compass CSV.

PASS — the exported CSV imported successfully into a separate Chrome Guest
browser context.

PASS — attempting to import the same data again was rejected because the
date already existed.

PASS — duplicate rejection left existing browser data unchanged.

### Local-file isolation

The developer-machine `data/recovery_compass.csv` remained separate from
the browser-local Aug. 30 record. Public runtime data no longer depends on
the shared default CSV.

### Result

**Browser-Local v1.0 Data Architecture — QUALIFIED**

## 2026-08-31 — Rest-Day UX + Data Invariant Qualification

Recovery Compass now treats Rest as a cross-field data invariant.

PASS — Rest entry automatically uses 0 workout minutes and 0 perceived exertion.
PASS — Rest workout controls are disabled in the Streamlit entry workflow.
PASS — switching to a non-Rest workout restores editable workout controls.
PASS — a deliberately invalid imported Rest record with nonzero duration and exertion was rejected.
PASS — failed import left existing browser data unchanged.
PASS — existing browser-local persistence remained intact.
PASS — 26 automated pytest tests.
PASS — Python compilation.

**Rest-Day UX + Data Invariant — QUALIFIED**