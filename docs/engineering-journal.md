# Recovery Compass Engineering Journal

## 2026-07-31 — Daily-Record Validation and Normalization

### Objective

Add a reusable validation layer that checks one Recovery Compass daily record before the application attempts to use it.

The feature should:

- accept valid input
- reject missing, unsupported, out-of-range, or incorrectly formatted input
- display clear field-specific error messages
- convert valid text input into appropriate Python data types
- prevent invalid records from advancing through the program
- avoid saving any data during this development block

### User Problem

Users may accidentally enter values that the application cannot interpret correctly, such as text in a numerical field, an unsupported workout type, or a value outside the accepted range.

Without validation, these values could cause later calculations to fail or produce misleading results. The validation layer gives users understandable feedback before their data reaches storage or analytics.

### Architecture

The implementation separates the command-line interface from the reusable data rules.

#### `cli.py`

Responsible for:

- displaying prompts
- collecting the user's answers as strings
- calling the validation functions
- displaying errors
- displaying an accepted normalized record

#### `src/validation.py`

Responsible for:

- required-field rules
- workout-type rules
- date validation
- integer and decimal validation
- accepted numerical ranges
- normalization into consistent Python data types

The main data flow is:

```text
User input
    ↓
Candidate record containing strings
    ↓
validate_record()
    ↓
Errors found? ── Yes → Display errors and stop
    ↓ No
normalize_record()
    ↓
Display accepted normalized record
```

### Major Functions

#### `validate_record(record)`

Receives one candidate record and returns a list containing every validation error that was found.

A valid record returns an empty list:

```python
[]
```

An invalid record returns one or more error-message strings.

#### `normalize_record(record)`

Receives a valid record and converts its values into consistent Python data types.

Examples:

- `"45"` becomes the integer `45`
- `"7.5"` becomes the float `7.5`
- `"strength"` becomes the standardized string `"Strength"`
- a blank optional mood becomes `None`

The function validates the record again before normalization so that another part of the program cannot safely normalize invalid input.

### Product Decisions

#### Accepted

- A record must be fully valid before it advances.
- All detected errors should be displayed together.
- Mood Rating remains optional.
- Workout types are limited to Rest, Strength, Cardio, Sport, Mobility, and Other.
- Workout-type capitalization is accepted flexibly and then standardized.
- Sleep Hours and Study Hours allow decimals.
- Duration, Perceived Exertion, and Mood Rating require whole numbers.
- User-facing labels use readable names such as `Workout Type`.
- Internal keys remain stable snake_case names such as `workout_type`.
- Prompts explain accepted values before the user encounters an error.
- A missing mood value is represented internally as `None`.

#### Deferred

- broader Study/Work Hours support
- custom workout categories
- user-defined targets
- controlled free-text labels
- expanded help text in the later graphical interface

#### Rejected for the MVP

- unrestricted free-text data interpreted entirely by an LLM
- using an LLM to calculate or determine core metrics
- changing the frozen internal field names
- CSV storage during this validation block
- Streamlit integration during this validation block

### Verification Performed

Seven required behaviors were checked manually:

1. valid baseline record
2. missing required Sleep Hours
3. unsupported Workout Type
4. Workout Duration above 300
5. Perceived Exertion above 10
6. blank optional Mood Rating
7. nonnumeric Study Hours

All seven tests passed.

The application:

- accepted and normalized valid input
- rejected every tested invalid input
- displayed field-specific error messages
- stopped invalid records before normalization
- did not crash during any tested case
- did not save any data

Detailed results are recorded in `docs/testing.md`.

### What I Learned

I learned that input collected by `input()` initially enters the program as text, even when the user types a number. Validation checks whether that text can safely represent the required kind of value, while normalization converts valid text into integers, floats, standardized strings, or `None`.

I also learned that `validate_record()` always returns a list. An empty list means no errors were found, while a nonempty list contains error messages. Python treats an empty list as false and a nonempty list as true, which is why the program can use:

```python
if errors:
```

I learned that `return` inside the invalid-record branch exits `main()` and prevents the record from reaching normalization or being displayed as accepted.

Internal field keys and user-facing labels serve different purposes. Stable snake_case keys are useful for code, tests, CSV headers, and analytics, while formatted labels are easier for users to read.

### AI Collaboration

The validation architecture and much of the implementation were proposed and written with AI assistance.

My role was to:

- review and approve the product behavior
- question and refine design decisions
- learn the purpose of the major functions
- explain the validation flow in my own words
- run the required test cases
- evaluate whether the outputs matched the expected behavior
- document the results and limitations
- accept the feature before it was added to the project

The AI-assistance details are recorded separately in `docs/ai-assistance-log.md`.

### Limitations

- Testing is manual rather than automated.
- Records are not yet stored.
- Duplicate dates are not checked.
- CSV import and export are not implemented.
- The graphical Streamlit interface is not connected.
- Weekly metrics and feedback are not implemented.
- The current tests do not cover every possible invalid input.

### Outcome

The daily-record validation and normalization feature passed its defined manual acceptance tests.

The Week 3 validation pass condition was satisfied:

- one valid synthetic record was accepted and normalized
- six invalid or special cases produced the expected field-specific results
- no tested case caused a crash
- the MVP and v0.1 data model were marked frozen

The feature is accepted for the Recovery Compass v0.1 command-line prototype.

### Next Technical Action

During the next scheduled Recovery Compass development phase, connect validated records to local CSV storage and define consistent behavior for saving, loading, importing, exporting, malformed files, and duplicate dates.

---

## 2026-08-05 — Local CSV Storage, Block A

### Objective

Create the smallest reusable local-storage system capable of saving one valid Recovery Compass record to CSV and reloading it accurately.

### User Problem

Validated information currently disappears when the command-line program closes.

Recovery Compass therefore needs a local storage system that preserves accepted records between sessions without requiring accounts, cloud storage, or a remote database.

The storage system must also protect users from:

- corrupted files
- incorrect columns
- malformed rows
- duplicate dates
- unexpected or missing fields
- silent loss or alteration of data

### Approved Storage Contract

- The private working file will be stored at `data/recovery_compass.csv`.
- The frozen CSV header order is:
  `date`, `workout_type`, `duration_minutes`,
  `perceived_exertion`, `sleep_hours`, `mood_rating`,
  and `study_hours`.
- Only records matching the frozen schema may be stored.
- A blank optional mood is written as an empty CSV cell and reloaded as `None`.
- A missing or zero-byte file represents zero saved records and loads as an empty list.
- Duplicate dates will be rejected rather than silently appended or overwritten.
- Wrong headers or malformed rows will reject the load rather than produce silently incomplete data.
- The application’s private working CSV and a user-downloaded export will be separate files.
- Only synthetic data will be used in repository tests and documentation.

The exact CSV header row is:

```csv
date,workout_type,duration_minutes,perceived_exertion,sleep_hours,mood_rating,study_hours
```

### Architecture

The reusable storage logic is contained in `src/storage.py` and does not import Streamlit.

The current storage flow is:

```text
Normalized record
    ↓
save_record()
    ↓
Schema and validation checks
    ↓
Existing-file and duplicate-date checks
    ↓
CSV file written or appended
    ↓
load_records()
    ↓
Headers and rows checked
    ↓
Values restored to documented Python types
```

The primary functions and components are described below.

#### `CSV_FIELDS`

`CSV_FIELDS` defines the exact names and order of the seven frozen columns.

This prevents the application from accidentally:

- rearranging columns
- omitting required columns
- accepting unexpected columns
- storing a record that no longer matches the approved schema

#### `DEFAULT_DATA_PATH`

`DEFAULT_DATA_PATH` defines the normal location of the application-controlled working file:

```text
data/recovery_compass.csv
```

Functions may also receive a different path so tests can use disposable synthetic files without touching the application’s working data.

#### `save_record()`

This function:

- receives one record
- checks that its fields match the frozen schema
- validates and normalizes it
- loads existing data safely
- checks for a duplicate date
- creates the folder and CSV when necessary
- writes the header once
- appends the record

#### `load_records()`

This function:

- returns an empty list when the file does not exist or is empty
- verifies the exact CSV headers
- validates each row
- reconstructs the documented Python data types
- returns a list of normalized record dictionaries
- rejects malformed or unsafe data

#### `_prepare_csv_row()`

This internal helper protects the storage layer from invalid callers.

It:

- checks for missing fields
- checks for unexpected fields
- converts values into text understood by the validation system
- validates the complete record
- normalizes the values
- converts a missing mood from `None` into a blank CSV cell

The leading underscore indicates that the function is intended to support the storage module internally rather than act as a primary application feature.

#### `StorageError`

`StorageError` represents a broader problem that prevents Recovery Compass data from being saved or loaded safely.

Examples include:

- incorrect headers
- malformed rows
- missing required fields
- unexpected fields
- invalid values

#### `DuplicateDateError`

`DuplicateDateError` is a more specific storage error used when a record already exists for the same date.

The current v0.1 policy is to reject the new record clearly rather than overwrite or silently duplicate existing data.

### Defensive Validation Decision

The storage layer validates records independently even when an interface has already validated them.

This is necessary because storage may later be called by:

- the command-line interface
- the Streamlit interface
- CSV import logic
- tests
- another future application feature

The storage module cannot assume that every caller has supplied safe data.

`_prepare_csv_row()` converts the supplied values into text so the existing validation system can check them consistently before anything is written.

### Missing-File and Empty-File Decision

A missing file or zero-byte file returns:

```python
[]
```

An empty list represents zero stored records.

This allows the application to treat first use as a normal state rather than an error. The first successful save can then create the folder, file, header, and initial row automatically.

### Duplicate-Date Decision

`save_record()` loads the existing records before appending a new one.

This is necessary so the application can:

1. check whether the current file is structurally valid;
2. determine whether another record already uses the same date.

Without loading the existing records first, the application could create duplicate entries or append valid information to an already corrupted file.

The v0.1 duplicate policy is:

```text
Reject the new record and display a clear error.
```

Editing or replacing an existing record remains outside the current storage implementation.

### Working File and Export Decision

Both the working CSV and an exported CSV are human-readable files.

For example:

```csv
date,workout_type,duration_minutes
2026-08-05,Strength,45
```

The difference concerns purpose and control rather than readability.

#### Working CSV

The working CSV:

- is controlled by Recovery Compass
- acts as the local source of truth
- is read and updated by the application
- must retain the frozen column names
- should not be committed publicly when it contains personal information

#### Exported CSV

An exported CSV:

- is a separate user-controlled copy
- can be opened in spreadsheet software
- may be used for viewing, backup, or transfer
- may eventually be imported back into Recovery Compass
- can be moved or deleted without directly changing the working file

Editing an exported copy does not automatically alter the application’s working data.

### CSV Usability Finding

Approximately five interview participants did not know what a CSV file was.

The following interface requirement was therefore accepted:

- the download area must explain that a CSV stores entries in spreadsheet rows and columns;
- it must state that CSV files can be opened with Excel, Google Sheets, Apple Numbers, or similar software;
- the post-download message must explain that original column names should remain unchanged if the file will later be imported;
- the import area must explain that changed or missing columns can prevent a safe import.

Possible interface wording:

```text
A CSV is a spreadsheet file that stores your Recovery Compass entries
in rows and columns. You can open it with Excel, Google Sheets,
Apple Numbers, or another spreadsheet program.
```

Possible post-download guidance:

```text
Your data was downloaded. Keep the original column names unchanged
if you plan to import the file back into Recovery Compass.
```

Possible import guidance:

```text
Upload a Recovery Compass CSV file with the original column names.
Files with changed or missing columns cannot be imported safely.
```

This is a usability requirement for the existing export feature, not a new data field or an expansion of the frozen MVP.

### Verification

A synthetic normalized record was saved to a temporary CSV and reloaded.

The test record was:

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

The loaded list matched the original normalized record exactly.

The test verified that:

- the exact frozen header order was used
- `duration_minutes` remained an integer
- `perceived_exertion` remained an integer
- `sleep_hours` remained a float
- `study_hours` remained a float
- the blank optional mood returned as `None`
- no crash occurred
- the temporary CSV was removed automatically after the test

Detailed evidence is recorded in `docs/testing.md`.

### What I Learned

I learned that a storage module should validate its own input instead of trusting that another interface has already performed validation.

I also learned that converting values into text is not the primary reason for validating again. The main purpose is defensive validation: the storage system must protect itself from invalid information regardless of which part of the application calls it.

A missing file can represent the normal state of having zero records, so returning an empty list allows first use to proceed without a crash.

Existing records must be loaded before appending so that duplicate dates can be detected and the current file can be checked before new information is added.

I also learned that CSV files store information as plain text, but spreadsheet programs display the values conveniently in rows and columns.

Finally, a working CSV and an exported CSV can contain the same readable format while serving different purposes: one is controlled by the application, while the other is a user-controlled copy.

### AI Collaboration

The storage contract, architecture, implementation, and manual test were developed with significant AI assistance.

AI assistance was used to:

- explain CSV storage and file responsibilities
- propose the storage contract
- define the working-file and export-file distinction
- propose the architecture of `src/storage.py`
- write most of the unfamiliar storage implementation
- create the synthetic manual round-trip test
- explain defensive validation
- explain missing-file behavior
- explain duplicate-date detection
- explain type reconstruction
- help organize the testing and engineering documentation

My role was to:

- review and approve the proposed storage behavior
- refine the product requirements
- identify the CSV-literacy problem through user interviews
- add CSV explanation and download guidance as an interface requirement
- review the purpose of the major functions
- answer questions about the storage flow
- correct my understanding after receiving explanations
- personally create and run the round-trip test
- inspect the original and loaded records
- confirm that all values and types matched
- accept the successful storage result

The detailed AI-assistance record is maintained separately in `docs/ai-assistance-log.md`.

### Current Limitations

- Only one valid record has been manually tested.
- Duplicate-date rejection has not yet been manually tested.
- Missing-file behavior has not yet been manually tested.
- Empty-file behavior has not yet been manually tested.
- Wrong headers have not yet been manually tested.
- Malformed rows have not yet been manually tested.
- Export-copy behavior has not yet been implemented or tested.
- The command-line interface is not yet connected to storage.
- Automated pytest tests have not yet been created.
- The graphical Streamlit interface is not yet connected.
- Weekly metrics and feedback have not yet been implemented.

### Outcome

Storage Block A passed its defined round-trip acceptance test.

One valid synthetic record successfully completed this flow:

```text
normalized record
    ↓
CSV save
    ↓
CSV reload
    ↓
same fields, values, and Python data types
```

The reusable storage module is accepted as the working foundation for the second Week 4 Recovery Compass block.

### Next Technical Action

During Storage Block B:

- test missing-file behavior
- test empty-file behavior
- test duplicate-date rejection
- test wrong-header rejection
- test malformed-row rejection
- define and implement bounded import/export behavior
- connect storage to the command-line flow if the reusable module remains stable
- update testing documentation
- update the engineering journal
- update the AI-assistance log
- commit and push the coherent storage unit

---

## 2026-08-07 — Local CSV Storage, Block B

### Objective

Complete the Recovery Compass v0.1 local-storage reliability layer by defining
and testing failure behavior, duplicate protection, CSV export, and
all-or-nothing CSV import.

### Starting State

Storage Block A had already established that:

- one normalized synthetic record could be saved to CSV
- the record could be loaded again accurately
- the frozen seven-column schema was preserved
- blank optional Mood Rating values could round-trip as `None`
- the private working CSV was separated conceptually from user-controlled
  exports

The original round-trip test was rerun before the expanded acceptance test and
continued to pass.

### Final Storage Behavior

#### Missing File

A missing working CSV represents zero saved records.

`load_records()` returns:

```python
[]
```

This is treated as a normal first-use condition rather than an error.

#### Empty File

A zero-byte CSV also represents zero stored records and loads as:

```python
[]
```

The next valid save can create the approved header and first record.

#### Wrong Headers

CSV headers must exactly match the frozen schema:

```text
date
workout_type
duration_minutes
perceived_exertion
sleep_hours
mood_rating
study_hours
```

Recovery Compass does not guess what renamed, missing, extra, or rearranged
columns mean.

A file with incorrect headers is rejected.

#### Malformed Rows

Every row is validated before the file is accepted.

If one row contains invalid information, such as text where a numerical value
is required, the file is rejected rather than partially accepted.

This follows an all-or-nothing approach: a file either passes its required
checks or does not alter the application's working dataset.

#### Duplicate Save

Recovery Compass continues to allow only one record per date.

`save_record()` loads existing records before appending so that it can:

1. verify that the existing CSV can be read safely;
2. determine whether the new date already exists.

If the date exists, `DuplicateDateError` is raised.

The existing record is not silently overwritten and a second record is not
appended.

#### Duplicate Dates Inside a CSV

Duplicate protection was expanded beyond `save_record()`.

`load_records()` now tracks dates it has already encountered using a set.

This is necessary because a CSV may have been:

- manually edited
- imported
- copied from another location
- created without using Recovery Compass's normal save function

Therefore, a CSV containing two records for the same date is itself considered
invalid.

### `seen_dates`

During loading, the application keeps a set of dates already encountered.

Conceptually:

```python
seen_dates = set()
```

For every valid row:

- if its date has not been seen, the date is added to the set;
- if its date is already present, the file is rejected.

This ensures that the one-record-per-date rule applies regardless of where the
CSV came from.

### Safe Rewrite Strategy

The new `_write_records()` helper is used when Recovery Compass needs to create
a complete replacement CSV, including after a successful import.

Rather than writing directly over the current destination, it first creates a
temporary file such as:

```text
.working.csv.tmp
```

The complete replacement dataset is written there first.

Only after the write succeeds does the temporary file replace the destination.

The purpose is not primarily to save computer memory. It is to reduce the risk
of damaging the real working CSV with a partial write.

The flow is:

```text
existing working CSV remains intact
        ↓
write complete proposed replacement to temporary file
        ↓
write succeeds?
    No ──→ original remains intact
        ↓ Yes
replace destination with completed file
```

### Export Behavior

`export_records()` creates a separate validated CSV copy.

The export:

- contains the same approved schema
- contains the same stored records
- does not move or rename the private working CSV
- does not modify the private working CSV
- cannot silently overwrite an already existing destination file
- is rejected when there are no records to export

The important distinction is control:

- the working CSV is Recovery Compass's application-controlled source of truth;
- the export is a user-controlled copy.

Moving the working CSV itself would remove the file the application depends on,
so exporting must create a separate copy instead.

### Import Behavior

`import_records()` allows Recovery Compass-generated CSV data to be restored or
transferred back into the application.

Potential uses include:

- restoring a previously downloaded copy
- moving records between environments or devices
- recovering records after local working data is lost
- maintaining user-controlled backups

The import process is intentionally all-or-nothing.

Conceptually:

```text
select incoming CSV
        ↓
validate headers
        ↓
validate every row
        ↓
check duplicate dates inside incoming CSV
        ↓
compare incoming dates with existing working records
        ↓
any error or conflict?
    Yes ──→ import nothing
        ↓ No
write complete combined dataset
```

If a single imported date conflicts with an existing date, the entire import is
rejected.

Recovery Compass does not import only the nonconflicting subset.

This prevents users from being left with a partially imported dataset whose
contents may be difficult to understand or reconstruct.

### CSV Interface Terminology

A usability discussion refined the terminology planned for the future
graphical interface.

The preferred labels are:

```text
Download Data (.CSV)
Import Data (.CSV)
```

rather than relying only on technical terms such as `Export CSV` or describing
every download only as a backup.

The planned helper text should explain that the downloaded CSV:

- contains the user's Recovery Compass records in spreadsheet rows and columns
- can be opened in Excel, Google Sheets, Apple Numbers, or similar software
- can serve as a backup
- can later be imported to restore or transfer records
- should retain the original Recovery Compass column names if it will be
  imported again

The import interface should explain that it is primarily intended for restoring
or transferring Recovery Compass data.

This requirement was prompted by user interviews in which approximately five
participants did not know what a CSV file was.

### Download Location Decision

The eventual Streamlit application should not attempt to save a CSV directly
beside the application on the user's device.

In a deployed web application, the Recovery Compass application directory may
exist on the server rather than on the user's computer.

The intended user flow is therefore:

```text
Recovery Compass
        ↓
Download Data (.CSV)
        ↓
browser handles the download
        ↓
normal browser Downloads location or user-selected location
```

The backend storage module remains responsible for producing valid CSV data.
The later Streamlit interface will be responsible for presenting that data
through the browser's download mechanism.

### Acceptance Testing

A nine-check synthetic acceptance matrix was run.

The checks were:

1. missing file
2. empty file
3. valid save and reload
4. wrong header
5. malformed row
6. duplicate save
7. duplicate dates already inside a CSV
8. separate matching export
9. successful import followed by a conflicting import

All nine tests passed.

The conflicting import test also verified that the working dataset remained
unchanged after the rejected import.

Detailed output is recorded in `docs/testing.md`.

### What I Learned

I learned that duplicate protection cannot exist only inside `save_record()`
because CSV files can enter or be changed outside the normal save flow.
`load_records()` therefore needs to enforce the one-record-per-date rule
independently.

I learned that temporary-file replacement protects the existing working data
from partial writes. Recovery Compass writes the proposed complete replacement
first and changes the real destination only after that write succeeds.

I learned why import uses an all-or-nothing rule. Even when most rows are
valid, partially accepting a file could leave the user unsure which records
were actually imported.

I also clarified the distinction between export and moving the working file.
An export creates a separate user-controlled copy while the application keeps
its own working source of truth in place.

Finally, I learned that an import containing even one date that conflicts with
existing data must currently be rejected completely rather than partially
merged.

### AI Collaboration

AI assistance was used extensively for the Block B architecture and unfamiliar
implementation.

AI assistance included:

- proposing the remaining storage behavior
- explaining import and export use cases
- proposing all-or-nothing import behavior
- adding duplicate-date detection during CSV loading
- designing the temporary-file rewrite strategy
- writing much of the updated storage implementation
- writing the expanded acceptance test
- explaining the purpose of the new functions and failure paths
- helping refine future CSV interface terminology
- helping document decisions, test evidence, and limitations

My role was to:

- approve or modify each storage behavior before implementation
- question the purpose of CSV import
- decide to keep import after understanding its restore and transfer use cases
- identify the need to explain CSV files to users based on interviews
- refine the future download/import terminology
- decide that browser-controlled downloads are more appropriate for the
  eventual graphical interface
- personally run the original regression test
- personally run the nine-check acceptance matrix
- inspect the actual pass/fail outputs
- answer the storage understanding questions
- correct and refine my understanding after explanation
- accept the storage behavior based on the test evidence

### Current Limitations

- The CLI is not yet connected to the storage functions.
- The Streamlit graphical interface is not yet connected to storage.
- Browser upload/download controls are not yet implemented.
- The current backend export helper uses a supplied filesystem destination;
  the later Streamlit layer must adapt export to browser downloading.
- Editing or replacing an existing date is not implemented.
- Duplicate records are rejected rather than merged.
- Partial imports are intentionally unsupported.
- Testing currently uses manual scripts rather than a full automated pytest
  suite.
- Analytics, charts, and feedback remain separate future work.

### Outcome

The Week 4 storage reliability layer passed all nine defined acceptance checks.

Recovery Compass can now:

- safely represent missing or empty local storage
- save and reload valid records
- reject incorrect headers
- reject invalid rows
- reject duplicate dates
- detect duplicate dates already present inside a CSV
- create a separate export copy
- import valid nonconflicting records
- reject a conflicting import without changing working data

The storage module is accepted as the current v0.1 foundation.

### Next Technical Action

Do not add Streamlit, analytics, or visual polish during this block.

The next scheduled development phase should build on the accepted storage
module rather than redesigning it.

## 2026-08-12 - Deterministic Analytics Core

Created `src/analytics.py` as a pure calculation layer between stored records
and future feedback/UI features.

Architecture decision:

`storage.py` owns persistence and loading. `analytics.py` receives already
normalized records and does not read or write CSV files itself.

The first analytics implementation calculates:

- total record count,
- seven-day coverage,
- workout frequency,
- total training duration,
- average sleep,
- average study time,
- average mood using only recorded mood values,
- mood-entry count,
- average perceived exertion on workout days,
- previous seven-day metrics,
- absolute current-minus-previous differences when both periods are complete.

The period end date is supplied explicitly so calendar-window behavior is
deterministic and reproducible in testing.

Formal week-to-week comparison requires 7/7 records in both periods. Incomplete
periods may still produce factual current-period metrics, but they do not
produce a formal comparison.

Unavailable averages use `None` rather than a fabricated numerical value.

The analytics layer makes no causal, medical, predictive, or recommendation
claims.

Chart-data preparation and UI integration remain out of scope for this block.

## 2026-08-14 - Analytics B Acceptance and Sparse-Data Rules

Completed the Week 5 analytics acceptance pass without changing the approved
metric contract.

Regression testing confirmed the Wednesday analytics implementation remains
stable.

Final sparse-data decision:

Current-period metrics may be calculated from incomplete coverage when they
are based only on values the user actually recorded. Coverage must remain
explicit so the application does not imply that missing days were observed.

Formal current-versus-previous comparison remains stricter. Both seven-day
periods must contain 7/7 records before comparison differences are produced.

This prevents a partial period and a complete period from being presented as
equivalent full-week samples.

Empty-data behavior also distinguishes factual zeros from unavailable values:

- counts and accumulated totals may legitimately equal 0
- averages with no observations return `None`

No additional analytics metrics, Streamlit work, model interpretation, causal
claims, or visual work were added during this block.

The existing `analytics.py` implementation required no defect repair.

## Week 5 - Chart-Ready Analytics Data

Added `prepare_chart_data(records)` to the deterministic analytics layer.

The function receives already-valid normalized records and prepares three
chronological factual datasets for future visualization:

- sleep + mood
- training duration + perceived exertion + workout type
- study hours

The analytics layer does not read CSV files directly and does not contain
Streamlit, chart styling, interpretation, recommendations, or UI logic.

For chart semantics, a day without an actual workout keeps
`duration_minutes = 0`, while `perceived_exertion` becomes `None`.
This distinguishes factual zero training time from the absence of an
applicable exertion measurement.

No changes were required to the previously qualified metric calculations.

## 2026-08-22 — Dashboard B Qualification

Completed the first full Recovery Compass analytics dashboard.

The dashboard now includes:

- Current seven-day summary cards
- Sleep and Mood visualizations
- Training Duration visualization
- Perceived Exertion visualization
- Study Hours visualization
- Recent Records
- Metric/calculation transparency section
- Explicit sparse-data and empty-data behavior

The visual system uses a light application surface with dark analytics panels, restrained metric-specific accents, consistent hierarchy, units, spacing, and explanatory labels.

No new analytics metrics were introduced. The dashboard remains a presentation layer over the previously qualified deterministic analytics and chart-ready data contracts.

Important semantic decisions retained:

- Missing data is distinct from zero.
- Rest-day exertion is unavailable rather than zero.
- A recorded non-Rest exertion value of zero remains a legitimate visible value.
- Sparse periods display available facts but do not unlock formal week-to-week comparison.
- Calendar gaps remain visible rather than compressing time.

Four deterministic dashboard scenarios—complete, missing/rest/zero, sparse, and empty—were manually visually accepted.

Dashboard A/B is qualified as the stable visual baseline.

## 2026-08-26 — Streamlit User Data Workflow

Implemented the first production user-input workflow in `app.py`.

The Streamlit layer now connects to the existing qualified application
architecture rather than duplicating business logic:

Streamlit UI
→ `validate_record()`
→ `normalize_record()`
→ `save_record()`
→ persisted Recovery Compass data
→ existing analytics / dashboard

Added:

- Daily entry form for all seven schema fields.
- Optional mood handling.
- Friendly validation-error presentation.
- Duplicate-date handling.
- Save confirmation and dashboard rerun.
- Download/export workflow.
- CSV upload/import workflow.
- All-or-nothing import failure presentation.

The implementation deliberately preserves `src/validation.py` as the
validation authority and `src/storage.py` as the persistence authority.
`app.py` does not independently redefine those rules.

Runtime qualification passed for invalid input, valid save, persistence,
duplicate dates, export, conflicting import, valid import, import persistence,
and malformed import.

Existing analytics, chart-data, and storage regression checks all passed after
integration.

The current layout is not the intended public-release interface. A dedicated
v1.0 progressive-disclosure, onboarding, navigation, and visual-consistency
pass remains required before release.

**Result: Streamlit User Data Workflow — QUALIFIED.**

## 2026-08-28 — Deterministic Feedback + Pytest Foundation

Created `src/feedback.py` as a dedicated deterministic presentation layer.

Architecture now follows:

stored records
→ analytics
→ deterministic feedback
→ Streamlit presentation

The feedback module consumes analytics output rather than recalculating
metrics. This keeps calculation ownership in `analytics.py` and presentation
logic in `feedback.py`.

The module handles sparse data, absent mood/exertion values, zero-workout
periods, and complete-period comparisons without inventing missing values.

The Streamlit application now includes a "What Your Data Shows" section that
presents these deterministic observations.

Also established the first real pytest suite:

- 5 feedback tests
- 7 validation tests
- 6 storage tests
- 6 analytics tests

Total: 24 automated tests.

All existing manual analytics, chart-data, and storage regressions passed after
integration.

**Result: deterministic feedback and automated-test foundation qualified.**

## 2026-08-28 — v1.0 Optional-Scope Freeze

Following qualification of deterministic feedback and the automated pytest
foundation, optional feature expansion is frozen for Recovery Compass v1.0.

### Required before v1.0 public release

- Progressive-disclosure information architecture and navigation.
- First-run welcome / onboarding experience.
- Persistent Help / How Recovery Compass Works access.
- Full visual-system and usability cleanup.
- Resolve contradictory Rest-day input behavior so Rest cannot coexist
  confusingly with nonzero workout duration / exertion.
- Finished-product usability testing with users unfamiliar with the project.
- Final public deployment and data-architecture decision, including privacy
  and persistence behavior.
- README, setup, usage, release, and portfolio documentation.
- Final end-to-end release qualification.
- Public v1.0 deployment.

### Frozen out of v1.0

The following remain valid future roadmap ideas but are not required for the
initial release:

- Live GPT / LLM advisor.
- Dynamic AI-generated training, sleep, study, or wellness recommendations.
- Sourced AI guidance and external-information retrieval.
- Additional analytics or metrics beyond the frozen v1.0 contract.
- Additional chart types or nonessential visualizations.
- Decorative animation or other nonessential presentation features.
- Feature expansion unrelated to a remaining required release blocker.

Required v1.0 work remains buildable after this freeze. The freeze prevents
new optional scope from competing with release completion.

## 2026-08-30 — Release Qualification and Deployment Architecture

Ran the broad Recovery Compass regression set and a date-relative synthetic
release-state evaluation covering complete, sparse, empty, and missing/zero
data conditions. No new core analytics, storage, chart, or deterministic
feedback defects were exposed.

The existing dashboard QA helper used fixed August 2026 dates and had become
stale as the current seven-day analytics window advanced. It was replaced
with a date-relative generator so the same scenarios remain reusable.

### v1.0 deployment decision

Recovery Compass v1.0 will use privacy-safe session-scoped user data.

Public v1.0 will not use:

- a shared server-side user CSV;
- user accounts;
- authentication;
- permanent cloud database storage.

Users will preserve data through Recovery Compass CSV download/export and
restore it through import on a later visit.

The onboarding and Help experience must make this persistence limitation
explicit before public release.

Persistent user accounts and cloud-backed history remain post-v1.0 roadmap
work.

### Remaining required release sequence

1. Session-scoped public data architecture.
2. Rest-day contradictory-input UX repair.
3. Progressive-disclosure information architecture.
4. First-run welcome / onboarding.
5. Persistent Help / How It Works.
6. Unified visual-system cleanup.
7. Internal end-to-end qualification.
8. Fresh-eyes external usability testing.
9. Fix only test-discovered release blockers.
10. README / public-use / privacy / limitations documentation.
11. Clean deployment test.
12. Final release qualification.
13. Public v1.0 deployment.