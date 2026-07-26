# Recovery Compass Discovery Interviews

## Research Method

Two short interviews were conducted with students who exercise and attempt to track aspects of their routines. A structured self-observation was also completed.

Participants are identified only as P1, P2, and Self-observation. No names, schools, diagnoses, injuries, medications, or other identifying information are included.

## Participant Summaries

### P1

- Currently tracks nutrition-related information, sleep, studying, and workout progression.
- Finds existing tracking inefficient and sometimes inaccurate.
- Wants visible week-to-week progress.
- Prefers realistic, nonjudgmental feedback.
- Would stop using a system that requires excessive effort.
- Expressed interest in reminders and detailed workout progression.

### P2

- Currently tracks exercises, weights, water, vitamins, and meditation.
- Finds note-based tracking slow.
- Values muscle-growth and progression patterns.
- Wants entry to remain quick and uncomplicated.
- Would stop using the application if entry became tedious.
- Values feedback, patterns, and exportable records.

### Self-observation

- Currently does not consistently track daily recovery or workload information.
- Would benefit from one consolidated system rather than several disconnected notes.
- Would realistically enter sleep, mood, and study information if the process were fast.
- Expects workout entry to require more effort than the other fields.
- Values dynamic, constructive, and motivational feedback.
- Would stop using the application if entry became slow or feedback became repetitive.
- Values CSV export for reviewing historical entries and feedback.

## Synthesis

### Repeated Needs

1. Daily entry must be fast and simple.
2. The application should show visible weekly progress and patterns.
3. Feedback should be constructive, realistic, and motivational.
4. Feedback should not repeat identical language continuously.
5. The application should consolidate information that users currently keep in scattered notes or do not track consistently.

### Important Differences

Participants differed substantially in what they wanted to track. Suggested fields included nutrition, water, vitamins, meditation, detailed exercises, workout splits, and progressive overload.

This variation supports keeping the MVP narrow rather than attempting to satisfy every tracking preference.

### Privacy Findings

No participant identified a concern with the current basic fields when reasonable privacy protections are present.

The application should continue avoiding highly private information, unrestricted journals, medical information, and judgmental feedback.

### Assumptions Confirmed

- Low-friction entry is necessary for continued use.
- Weekly patterns are more useful than isolated daily numbers.
- Constructive feedback is important.
- CSV or historical export has value.
- Sleep, workout, mood, and study information can support useful reflection.

### Assumptions Questioned

- A broad workout category may not provide enough detail for users focused on progressive overload.
- Users may not consistently complete workout entry if it takes substantially longer than the other fields.
- Reusable feedback templates could become repetitive without sufficient variation.

### Design Implications

1. Preserve the small v0.1 schema.
2. Target a daily entry time under two minutes.
3. Use fixed choices wherever possible.
4. Keep mood optional.
5. Make weekly trends central to the interface.
6. Ensure feedback is constructive and varied.
7. Keep detailed workout logging as a future consideration.
8. Do not add nutrition, community, or health-related expansion to the MVP.

## Schema Evidence Review

| Field | Evidence Label | Interview Finding | Decision |
|---|---|---|---|
| date | Confirmed indirectly | Participants valued daily records and weekly progress | Keep |
| workout_type | Questioned | Some users want exercise-level progression rather than broad categories | Keep broad for MVP; consider optional detail later |
| duration_minutes | No direct evidence | Participants did not specifically discuss workout duration | Keep for session-load calculation |
| perceived_exertion | No direct evidence | Participants did not specifically discuss exertion ratings | Keep for session-load calculation |
| sleep_hours | Confirmed | Sleep tracking was explicitly valued | Keep required |
| mood_rating | Confirmed | Self-observation indicated mood could be entered quickly | Keep optional |
| study_hours | Confirmed | Studying and workload tracking were valued | Keep required |
| CSV export | Confirmed | Export and historical review were considered useful | Retain |