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