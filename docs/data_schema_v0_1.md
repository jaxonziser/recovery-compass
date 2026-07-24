# Recovery Compass Data Schema v0.1

## Purpose

This document defines the information stored in one Recovery Compass daily record. It establishes field names, data types, validation rules, privacy boundaries, and the reason each field exists.

This is the initial schema created before user interviews are completed. Interview evidence will be reviewed afterward, and justified changes will be recorded in a later version.

## Field Definitions

| Field | Type | Required | Validation Rule | Example | Reason for Collection | Privacy / Interpretation Limit | Interview Evidence |
|---|---|---|---|---|---|---|---|
| date | ISO date | Yes | Must be a real date in YYYY-MM-DD format | 2026-07-24 | Identifies the daily record and supports chronological analysis | Does not include birth date or other identifying dates | Pending |
| workout_type | Choice | Yes | Rest, Strength, Cardio, Sport, Mobility, or Other | Strength | Provides basic context for the workout | Does not collect detailed injury or exercise-journal information | Pending |
| duration_minutes | Integer | Yes | 0–300 | 45 | Measures session duration and supports training-load calculation | Does not prescribe training duration | Pending |
| perceived_exertion | Integer | Yes | 0–10 | 7 | Measures subjective session intensity and supports training-load calculation | Subjective reflection only; not a medical measurement | Pending |
| sleep_hours | Decimal | Yes | 0–16 | 7.5 | Supports weekly reflection on sleep patterns | Does not diagnose sleep conditions | Pending |
| mood_rating | Integer | No | Blank or 1–5 | 4 | Allows optional comparison between routine patterns and self-reported mood | No free-text mental-health journal or diagnosis | Pending |
| study_hours | Decimal | Yes | 0–16 | 2.5 | Represents academic workload | No school, class, grade, or assignment details | Pending |

## CSV Column Order



Recovery Compass will use the following column order:

```text
date,workout_type,duration_minutes,perceived_exertion,sleep_hours,mood_rating,study_hours

CSV means comma-separated values. Later, one row might look like:

```text
2026-07-24,Strength,45,7,7.5,4,2.5

## Record-Level Rules

1. A record will not be saved when a required field is missing or invalid.
2. The application will not save partially valid records.
3. Validation messages will identify the specific invalid field.
4. A duplicate date will trigger a consistent replacement decision rather than silently creating duplicate records.
5. Imported CSV files must contain the exact required headers.
6. Mood may be blank because it is optional.
7. Rest entries normally use zero duration and zero perceived exertion.
8. All values will be validated before they are stored or analyzed.

## Privacy Boundaries

Recovery Compass will not collect or store:

- names
- email addresses
- account credentials
- school names
- precise locations
- diagnoses
- medications
- injuries
- unrestricted journal entries
- body weight
- calorie intake
- body measurements
- photographs
- health-record documents

The application is a reflection tool. It is not a medical, mental-health, nutrition, or training-prescription system.

## Pending Interview Review

The following questions will be reviewed after the discovery interviews:

1. Would users consistently enter all six required daily inputs?
2. Should mood remain optional?
3. Is study time useful enough to retain?
4. Are the workout-type choices understandable and complete?
5. Would users prefer minutes, hours, or both for workout duration?
6. Is CSV export useful to the intended users?
7. Are any current fields perceived as too private?
8. Is the total daily entry process realistic in under two minutes?