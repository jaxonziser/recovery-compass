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