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