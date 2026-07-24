# Recovery Compass Data Schema v0.1

## Purpose

This document defines the structure of one Recovery Compass daily record. It establishes the field names, data types, validation rules, privacy boundaries, CSV format, and reason each field exists.

This is the initial schema created before the discovery interviews are completed. Interview evidence will be reviewed afterward. Any justified changes will be documented in a later version rather than silently altering this file.

## Schema Version

- Version: `0.1`
- Status: Initial freeze
- Storage format: CSV
- One record represents: One calendar day
- Interview validation status: Pending

## Field Definitions

| Field | Type | Required | Validation Rule | Example | Reason for Collection | Privacy / Interpretation Limit | Interview Evidence |
|---|---|---|---|---|---|---|---|
| `date` | ISO date | Yes | Must be a real date in `YYYY-MM-DD` format | `2026-07-24` | Identifies the daily record and supports chronological analysis | Does not include birth dates or other identifying date information | Pending |
| `workout_type` | Choice | Yes | Must be `Rest`, `Strength`, `Cardio`, `Sport`, `Mobility`, or `Other` | `Strength` | Provides broad context for the workout | Does not collect detailed exercise journals, injury information, or medical information | Pending |
| `duration_minutes` | Integer | Yes | Must be between `0` and `300` | `45` | Measures workout duration and supports training-load calculations | Does not prescribe how long the user should exercise | Pending |
| `perceived_exertion` | Integer | Yes | Must be between `0` and `10` | `7` | Measures subjective workout intensity and supports training-load calculations | Subjective reflection only; not a medical measurement | Pending |
| `sleep_hours` | Decimal | Yes | Must be between `0` and `16` | `7.5` | Supports reflection on sleep patterns and weekly averages | Does not diagnose sleep disorders or provide medical advice | Pending |
| `mood_rating` | Integer | No | May be blank or must be between `1` and `5` | `4` | Allows optional comparison between routine patterns and self-reported mood | Does not collect unrestricted mental-health journals, diagnoses, or crisis information | Pending |
| `study_hours` | Decimal | Yes | Must be between `0` and `16` | `2.5` | Represents daily academic workload | Does not collect school names, class names, grades, assignments, or academic records | Pending |

## Field Explanations

### `date`

The `date` field identifies the calendar day represented by the record.

The required format is:

```text
YYYY-MM-DD
```

Example:

```text
2026-07-24
```

This format avoids ambiguity between month-day-year and day-month-year formats.

Only one stored record should exist for each date in Version 1.0.

### `workout_type`

The `workout_type` field provides broad context for the user’s activity.

Allowed values:

```text
Rest
Strength
Cardio
Sport
Mobility
Other
```

The field uses fixed choices to prevent inconsistent entries such as:

```text
Weights
Weight lifting
Gym
Lifting
Strength session
```

These entries should all be represented by:

```text
Strength
```

### `duration_minutes`

The `duration_minutes` field records the workout duration as a whole number of minutes.

Valid examples:

```text
0
45
60
90
```

Invalid examples:

```text
-10
45.5
400
```

A rest day normally uses:

```text
0
```

The maximum value of `300` is an initial validation boundary intended to prevent obvious accidental input.

### `perceived_exertion`

The `perceived_exertion` field records how difficult the workout felt to the user.

The scale is:

```text
0 = No exertion or rest
1 = Extremely easy
5 = Moderate effort
10 = Maximum perceived effort
```

This is a subjective reflection value. It is not a medical measurement or professional training assessment.

### `sleep_hours`

The `sleep_hours` field records the user’s sleep duration from the previous night.

Valid examples:

```text
6
7.5
8.25
```

The field accepts decimals because sleep duration may include partial hours.

Recovery Compass may calculate trends and averages from this information, but it must not diagnose sleep conditions or claim that one number is medically correct for every user.

### `mood_rating`

The `mood_rating` field is an optional broad emotional check-in.

The scale is:

```text
1 = Very low
2 = Low
3 = Neutral
4 = Good
5 = Very good
```

The field may be left blank.

Recovery Compass will not collect unrestricted emotional journal entries, diagnoses, medication information, crisis information, or detailed mental-health histories.

### `study_hours`

The `study_hours` field records the approximate amount of focused academic work completed during the day.

Valid examples:

```text
0
1.5
2.75
4
```

The application does not need to know the user’s school, course names, grades, assignments, teachers, or academic records.

## CSV Column Order

Recovery Compass will use the following column order:

```text
date,workout_type,duration_minutes,perceived_exertion,sleep_hours,mood_rating,study_hours
```

CSV means comma-separated values.

One completed row might look like:

```text
2026-07-24,Strength,45,7,7.5,4,2.5
```

A record with no mood rating might look like:

```text
2026-07-25,Cardio,30,6,8,,1.5
```

The empty space between the two commas represents the optional blank `mood_rating` field.

Imported CSV files must use the required headers and expected column order.

## Record-Level Rules

1. A record will not be saved when a required field is missing.
2. A record will not be saved when any supplied value is invalid.
3. The application will not save partially valid records.
4. Validation messages will identify the specific invalid field.
5. All values will be validated before they are stored or analyzed.
6. Mood may be blank because it is optional.
7. A rest entry normally uses `0` for both `duration_minutes` and `perceived_exertion`.
8. Only one stored record should exist for each date.
9. A duplicate date will trigger a consistent replacement decision rather than silently creating another record.
10. Imported CSV files must contain all required headers.
11. Imported CSV files with missing, extra, duplicated, or incorrectly ordered columns will be rejected with an explanatory message.
12. Invalid imported records will not be silently corrected.
13. The application will not calculate analytics from a record until that record passes validation.

## Duplicate-Date Rule

If a user attempts to save a record for a date that already exists, Recovery Compass will not silently create a duplicate.

Version 1.0 should ask whether the user wants to replace the existing record.

Conceptual choices:

```text
Replace existing record
Cancel and keep existing record
```

The application must use the same duplicate-date behavior consistently.

## Validation Message Standard

Validation messages should identify:

1. the field that is invalid,
2. the value or condition that caused the problem,
3. the accepted format or range.

Weak message:

```text
Invalid input.
```

Preferred message:

```text
Duration must be a whole number between 0 and 300 minutes.
```

Another preferred message:

```text
Sleep hours must be a number between 0 and 16.
```

## Privacy Boundaries

Recovery Compass will not collect or store:

- names
- email addresses
- passwords
- account credentials
- school names
- teacher names
- class names
- grades
- precise locations
- home addresses
- dates of birth
- medical diagnoses
- mental-health diagnoses
- medications
- injuries
- treatment information
- unrestricted journal entries
- crisis information
- body weight
- calorie intake
- body measurements
- progress photographs
- health-record documents
- social-media information
- contact lists

Recovery Compass is a personal reflection tool.

It is not:

- a medical application
- a mental-health assessment
- a diagnostic tool
- a nutrition tracker
- a calorie tracker
- a weight-loss application
- an injury-treatment system
- a professional training prescription
- a replacement for a doctor, therapist, coach, teacher, or other qualified professional

## Interpretation Boundaries

Recovery Compass may calculate and display:

- session load
- weekly training load
- average sleep
- average study hours
- average optional mood rating
- changes between recent periods
- simple associations between recorded variables

Recovery Compass must not claim that:

- one recorded value caused another
- a user has a medical or psychological condition
- a user should follow a specific treatment
- a particular workout plan is safe for every person
- a particular amount of sleep is universally correct
- a particular mood score requires a diagnosis
- a statistical association proves causation

Feedback must remain cautious, descriptive, and transparent.

## Initial Training-Load Calculation

The initial session-load calculation is:

```text
session_load = duration_minutes × perceived_exertion
```

Example:

```text
duration_minutes = 45
perceived_exertion = 7

session_load = 45 × 7
session_load = 315
```

This result is a simplified reflection metric. It is not a medical measurement or professional training recommendation.

## Initial Missing-Value Rules

Required fields may not be blank:

```text
date
workout_type
duration_minutes
perceived_exertion
sleep_hours
study_hours
```

The following field may be blank:

```text
mood_rating
```

A blank optional mood value must remain missing rather than being automatically converted to zero.

A mood rating of zero would be invalid because the mood scale begins at one.

## Import Rules

A CSV import will be accepted only when:

- the file can be read as CSV data,
- the required headers are present,
- there are no unexpected headers,
- the column order matches the schema,
- every required value is present,
- every provided value uses the correct data type,
- every value falls within its permitted range,
- every date is valid,
- every workout type is an allowed choice.

When an imported row is invalid, the application should identify the row and field responsible for the error.

The application must not silently discard or rewrite invalid user data.

## Export Rules

CSV export will use the frozen column order:

```text
date,workout_type,duration_minutes,perceived_exertion,sleep_hours,mood_rating,study_hours
```

Exported data should contain only the fields defined in this schema.

No hidden identifiers, account information, device information, or private metadata should be added.

## Pending Interview Review

The following questions will be reviewed after the discovery interviews:

1. Would users consistently enter all required daily inputs?
2. Should `mood_rating` remain optional?
3. Is `study_hours` useful enough to remain required?
4. Are the workout-type choices understandable and complete?
5. Would users prefer workout duration to be entered in minutes, hours, or both?
6. Is CSV export useful to the intended users?
7. Are any current fields perceived as too private?
8. Is the entire daily-entry process realistic in under two minutes?
9. Would users understand the perceived-exertion scale without additional instructions?
10. What would make users stop entering data after several days?

Until the interviews are completed, the `Interview Evidence` column remains marked:

```text
Pending
```

## Interview Revision Procedure

After the interviews, each field will receive one of the following evidence labels:

```text
Confirmed
Questioned
Rejected
No evidence
```

The schema will not be changed merely because one participant expresses a preference.

A change should be supported by:

- a repeated pattern across participants,
- a serious privacy concern,
- an important usability problem,
- conflict with the two-minute daily-entry goal,
- evidence that a field does not support the product’s core purpose.

If changes are justified, they will be documented in:

```text
data_schema_v0_2.md
```

Version `0.1` will remain in the repository as a record of the original design.

## Current Non-Goals

Version 1.0 will not include:

- user accounts
- remote permanent databases
- cloud synchronization
- public profiles
- social comparison
- leaderboards
- coach dashboards
- medical recommendations
- injury advice
- nutrition logging
- calorie tracking
- body-weight tracking
- detailed journaling
- unrestricted custom fields
- automatic workout prescriptions
- live AI as a requirement for basic operation

## Acceptance Criteria

The initial schema is complete when:

- all seven fields are defined,
- every field has a type,
- every field has a required or optional status,
- every field has a validation rule,
- every field has an example,
- every field has a documented purpose,
- privacy and interpretation limits are explicit,
- CSV column order is frozen,
- record-level rules are documented,
- duplicate-date behavior is defined,
- import and export expectations are documented,
- pending interview questions are listed,
- future changes require a new documented version.

## Change Log

### Version 0.1

- Defined the seven initial daily-record fields.
- Established data types and validation ranges.
- Established the CSV column order.
- Defined required and optional fields.
- Added privacy and interpretation boundaries.
- Added duplicate-date handling.
- Added import and export expectations.
- Marked discovery-interview evidence as pending.
