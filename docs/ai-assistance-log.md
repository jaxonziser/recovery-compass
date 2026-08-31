# Recovery Compass AI-Assistance Log

## 2026-07-31 — Daily-Record Validation and Normalization

### Task

Create a reusable validation and normalization system for Recovery Compass v0.1 daily records and connect it to the command-line interface.

### AI Assistance Used

AI assistance was used to:

- explain the purpose of validation and normalization
- propose the separation between `cli.py` and `src/validation.py`
- define the responsibilities of each file
- propose the `validate_record()` and `normalize_record()` functions
- write most of the initial validation and command-line implementation
- define helper functions for integer, decimal, and blank-value handling
- propose user-facing field labels and error messages
- explain Python concepts used in the implementation
- define the manual test sequence
- help organize the testing and engineering documentation

### My Contribution

I:

- reviewed and approved the product behavior before implementation
- approved the required and optional fields
- approved the accepted workout categories and numerical ranges
- approved case-insensitive workout input with standardized stored values
- approved using readable user-facing labels while retaining internal snake_case keys
- approved representing a missing Mood Rating as `None`
- questioned whether field explanations should be shown before errors occur
- considered and evaluated possible future dynamic or LLM-based input
- rejected unrestricted LLM interpretation for the MVP
- reviewed explanations of the major functions and program flow
- explained the validation logic in my own words
- corrected my understanding after receiving feedback
- personally ran the command-line program
- personally entered every required test case
- compared the actual output with the expected behavior
- confirmed that all seven required tests passed
- approved the completed feature for the v0.1 prototype
- documented the results, limitations, and decisions

### Concepts Reviewed

During this block, I reviewed and discussed:

- how `input()` returns strings
- why numerical strings must be converted before calculations
- how validation differs from normalization
- how an empty error list represents a valid record
- how Python treats empty and nonempty lists in conditions
- how `return` stops an invalid record from advancing
- why optional missing data can be represented with `None`
- why internal field identifiers differ from user-facing labels
- why invalid input should not reach storage or analytics

### Verification Performed

The following cases were personally tested through the command-line interface:

1. valid baseline record
2. missing required Sleep Hours
3. unsupported Workout Type
4. Workout Duration above the maximum
5. Perceived Exertion above the maximum
6. blank optional Mood Rating
7. nonnumeric Study Hours

All seven cases produced the expected result.

No tested invalid input caused the program to crash.

### Ownership and Role

My role in Recovery Compass is **Creator and Product Lead of an AI-assisted Python application**.

For this feature, AI acted as a technical instructor, architect, and implementation collaborator. I was responsible for reviewing the proposed behavior, making product decisions, learning the major logic, personally testing the implementation, evaluating the results, and accepting the feature.

I am not claiming that I independently designed or wrote all of the code.

### Current Limitations

- The validation feature was tested manually rather than with automated tests.
- The code has not undergone professional security or production review.
- Records are not yet stored.
- Duplicate dates are not yet checked.
- CSV import and export are not yet implemented.
- The graphical interface is not yet connected.

## 2026-08-05 — Local CSV Storage, Block A

### AI Assistance Used

AI assistance was used to:

- propose the local CSV storage contract
- explain working-file and export-file responsibilities
- design the `src/storage.py` architecture
- write most of the unfamiliar storage implementation
- create the synthetic manual round-trip test
- explain defensive validation, missing-file behavior, duplicate detection,
  and type reconstruction
- help document the architecture, decisions, test result, and limitations

### My Contribution

I:

- approved or refined the storage behavior before implementation
- identified through approximately five user interviews that users needed an
  explanation of CSV files
- added CSV education and post-download guidance as a product requirement
- reviewed the major functions
- answered understanding questions and corrected my understanding
- created and ran the synthetic round-trip test
- verified the actual loaded values and types
- accepted the successful round-trip result

I am not claiming that I independently designed or wrote the storage module.

## 2026-08-07 — Local CSV Storage, Block B

### AI Assistance Used

AI assistance was used to:

- propose final behavior for missing and empty files
- define strict wrong-header and malformed-row handling
- preserve the one-record-per-date policy
- add duplicate-date detection to CSV loading
- explain the purpose of importing previously exported Recovery Compass data
- design all-or-nothing import behavior
- distinguish the application-controlled working CSV from a user-controlled
  export
- design a temporary-file rewrite strategy
- write much of the expanded `src/storage.py` implementation
- write `tests/manual_storage_acceptance.py`
- explain `seen_dates`, temporary replacement, import atomicity, and export
  behavior
- help refine planned interface wording for CSV download and import
- help document the actual test results and current limitations

### Product Decisions I Made

I approved the following behavior:

- missing and empty files represent zero records
- wrong headers reject the file
- malformed rows reject the file
- duplicate dates are rejected
- duplicate dates already inside a CSV are also rejected
- export creates a separate copy and does not move the working CSV
- imports are all-or-nothing
- an import conflicting with an existing date changes nothing
- CSV import remains in the product because it provides restore and transfer
  functionality
- the future interface should explain what a CSV is and why users might import
  one
- the preferred future labels are `Download Data (.CSV)` and
  `Import Data (.CSV)`
- browser download behavior should be used in the eventual Streamlit
  interface rather than assuming that the application folder exists on the
  user's device

### My Contribution

I:

- reviewed and approved the proposed behavior before implementation
- questioned why a Recovery Compass CSV would ever be imported back into the
  application
- decided to retain import after understanding the backup, restore, and
  transfer use cases
- contributed interview evidence that approximately five users did not know
  what CSV files were
- required additional CSV explanation in the eventual interface
- questioned how exported files should be delivered to the user's computer
- participated in the design decision to use the browser's normal download
  workflow later
- personally ran the syntax check
- personally reran the original round-trip regression test
- personally ran the nine-check storage acceptance matrix
- verified that all nine checks passed
- answered the understanding questions in my own words
- corrected my understanding where necessary
- accepted the implementation based on actual test evidence

### Understanding Demonstrated

I can now explain that:

- `save_record()` alone cannot prevent every duplicate because CSV files may
  enter the system without going through that function
- `load_records()` therefore checks for duplicate dates itself
- temporary-file replacement helps protect the real working CSV from a failed
  partial rewrite
- imports are all-or-nothing so users are not left with an unclear partial
  dataset
- export creates a separate copy while preserving the application's source of
  truth
- one conflicting imported date currently causes the entire import to be
  rejected

### Verification

The original synthetic round-trip test continued to pass after the storage
changes.

The expanded acceptance test then passed all nine checks:

1. missing file
2. empty file
3. valid round trip
4. wrong headers
5. malformed row
6. duplicate save
7. duplicate dates inside a CSV
8. export copy
9. valid import and conflicting-import protection

No real personal data was used in the tests.

### Current Limitation of AI Assistance

I am not claiming that I independently designed or wrote the storage
implementation.

The architecture and much of the unfamiliar code were AI-assisted. My work
focused on product decisions, questioning design choices, understanding the
major logic, personally executing tests, evaluating the results, and
accepting or rejecting the feature.

## 2026-08-12 - Analytics A

AI role:
- Helped define the analytics architecture after the metric behavior was
  approved.
- Wrote most of the initial unfamiliar `src/analytics.py` implementation.
- Explained the major functions, data flow, date-window logic, missing-data
  behavior, and comparison gate.
- Proposed the synthetic verification dataset and manual acceptance checks.

Student role:
- Approved the metric contract and architecture before implementation.
- Explained the major analytics behavior and functions in own words.
- Independently calculated representative expected metric values.
- Identified and corrected the distinction between workout-only exertion and
  exertion averaged across all recorded days.
- Personally ran the manual analytics tests.
- Verified current-period, previous-period, comparison, and insufficient-data
  behavior.
- Accepted the implementation after the tests matched independently calculated
  results.

No LLM-generated interpretation, causal inference, medical advice, prediction,
or recommendation was added to the product.

## 2026-08-14 - Analytics B

AI role:
- Reviewed the previously qualified analytics state.
- Proposed the remaining empty-data and sparse-current-period acceptance cases.
- Updated the manual test structure to include the final edge-case matrix.
- Explained the distinction between factual current-period metrics and formal
  full-period comparison.

Student role:
- Personally reran the existing analytics regression test.
- Replaced and ran the expanded manual acceptance script.
- Verified that all full-period, one-period-only, sparse-data, and empty-data
  assertions passed.
- Explained why incomplete current data can still support factual current
  metrics but not a formal full-week comparison.
- Explained the difference between numerical zero and unavailable `None`
  values.
- Accepted the analytics behavior after the final test evidence passed.

No analytics feature was accepted solely because AI predicted it would work.
Actual test output and student understanding were required.

## Week 5 - Chart-Ready Data

AI assistance was used to:

- propose the chart-data architecture and output contract
- explain separation between storage, analytics, and future UI layers
- propose `prepare_chart_data()` implementation
- explain rest-day `0` versus `None` semantics
- propose representative manual acceptance tests

Student responsibilities included:

- reviewing and approving the chart-data contract
- entering and running the implementation
- running the existing analytics regression suite
- running the new manual chart-data acceptance test
- reviewing the generated datasets
- explaining the architecture and missing-value behavior in their own words
- accepting the feature only after successful testing and understanding

## 2026-08-22 — Recovery Compass Dashboard

AI assistance was used to:

- propose and implement the Streamlit dashboard presentation layer;
- design the visual hierarchy and dark chart treatment;
- implement Altair visualizations from the already-approved chart-ready datasets;
- identify visual/semantic defects during iterative QA;
- create a deterministic multi-scenario dashboard QA generator;
- explain distinctions between missing values, Rest-day values, and legitimate zero values;
- update deprecated Streamlit chart-width usage.

Student responsibilities included:

- approving the dashboard behavior and visual direction;
- running the application locally;
- visually reviewing each complete, missing, sparse, and empty scenario;
- identifying aesthetic preferences and requesting revisions;
- verifying metric behavior against the underlying records;
- running the final analytics and chart-data regression checks;
- accepting or rejecting each dashboard revision.

The dashboard was not accepted solely on the basis of AI prediction. Final acceptance required local execution and student review.

## 2026-08-26 — Streamlit User Data Workflow Integration

AI assistance was used as a technical implementation and architecture
collaborator for the Streamlit user-data workflow.

AI assistance included:

- Inspecting the existing validation, storage, and dashboard architecture.
- Identifying the correct integration points in `app.py`.
- Drafting the Streamlit daily-entry/save implementation.
- Drafting the import/export interface and integration.
- Explaining how UI values flow through validation, normalization, storage,
  rerun, and dashboard recalculation.
- Identifying presentation defects during visual review and proposing UI
  corrections.
- Defining runtime acceptance tests for save, persistence, duplicate-date
  protection, export, valid import, conflicting import, and malformed import.

The creator personally:

- Reviewed and approved the intended behavior.
- Replaced and ran the generated `app.py`.
- Performed the runtime acceptance tests.
- Inspected the resulting UI states.
- Verified persistence through refresh / app reopen.
- Verified the exported CSV.
- Verified valid, conflicting, and malformed imports.
- Ran the existing analytics, chart-data, and storage regression checks.
- Accepted the workflow as qualified while identifying the current UI as
  insufficiently polished for public release.

No claim is made that the Streamlit implementation was independently coded
without AI assistance.

## 2026-08-28 — Deterministic Feedback and Automated Testing

AI assistance was used as a technical implementation and testing collaborator.

AI assistance included:

- defining the deterministic-feedback architecture;
- drafting `src/feedback.py`;
- identifying edge cases involving missing mood/exertion values;
- drafting pytest coverage for feedback, validation, storage, and analytics;
- explaining the distinction between factual deterministic observations and
  future AI-generated recommendations;
- assisting with Streamlit integration and presentation fixes;
- defining the final regression sequence.

The creator personally:

- reviewed and approved the feedback contract;
- created/replaced the implementation files;
- ran all pytest tests;
- reviewed and corrected feedback wording;
- visually verified feedback against displayed dashboard metrics;
- ran all existing manual regression checks;
- ran Python compilation and Git whitespace checks;
- accepted the deterministic feedback and automated-test foundation after
  qualification.

No claim is made that these implementation or test files were independently
coded without AI assistance.

## 2026-08-30 — Release-State Qualification and Deployment Planning

AI assistance was used to:

- review the frozen v1.0 release state;
- identify that the dashboard QA fixture had become date-stale;
- convert the fixture to date-relative synthetic scenarios;
- define complete, sparse, empty, and missing/zero acceptance criteria;
- review release-state screenshots;
- perform the repository privacy/deployment audit;
- evaluate v1.0 persistence architecture options;
- define the final Week 8 release runway.

The creator personally ran the regression suite, generated and inspected all
four synthetic scenarios, restored the working dataset, reviewed repository
privacy state, and selected session-scoped data plus CSV import/export as the
v1.0 persistence model.

## 2026-08-30 — Browser-Local Persistence Architecture

AI assistance was used to design and implement the v1.0 browser-local
persistence architecture, preserving the existing qualified validation,
CSV, duplicate-date, import, export, analytics, and feedback behavior.

The creator personally tested:

- empty startup isolation;
- record creation;
- analytics propagation;
- browser refresh persistence;
- tab close/reopen persistence;
- separate-browser-profile isolation;
- CSV download and cross-browser import;
- duplicate-import rejection.

The creator accepted browser-local persistence plus CSV portability as the
v1.0 public data model.

# docs/ai-assistance-log.md

## 2026-08-31 — Rest-Day UX and Final UX Planning

AI assistance was used to identify the correct cross-field Rest invariant,
implement the validation/UI repair, add automated tests, define runtime
qualification cases, and formalize the final v1.0 information architecture
and release criteria.

The creator personally ran the automated regression suite and compilation
checks and manually qualified Rest behavior, non-Rest behavior, invalid-import
rejection, atomic failure behavior, and continued browser-local persistence.