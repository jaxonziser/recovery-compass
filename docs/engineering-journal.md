## Week 3 Validation Pass Condition

One valid synthetic record is accepted and normalized. Six invalid or
special cases produce the expected field-specific result without crashing.
The MVP and v0.1 data model are then marked frozen.

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

The function validates the record again before normalization so that it cannot safely be called with invalid input by another part of the program.

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

The feature is accepted for the Recovery Compass v0.1 command-line prototype.

### Next Technical Action

During the next scheduled Recovery Compass development phase, connect validated records to local CSV storage and define consistent behavior for saving, loading, importing, exporting, malformed files, and duplicate dates.