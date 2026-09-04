# Recovery Compass v1.0 Release Notes

**Release date:** September 4, 2026
**Status:** Public v1.0 release verified on Streamlit Community Cloud.

Recovery Compass v1.0 is the first public-product release of the project. It turns a small daily record of training, previous-night sleep, optional mood, and study time into a calm seven-day overview, focused Insights views, deterministic factual observations, and a portable browser-local data workflow.

## v1.0 Highlights

- Polished five-part Streamlit interface: Home, Log a Day, Insights, Data & Backup, and Help.
- Four-step first-visit guided tour that mirrors the actual product screens.
- Light, System, and Dark appearance modes with persistent browser preference.
- Browser-local record persistence with no Recovery Compass account or project cloud database.
- Portable CSV backup and atomic restore between browser profiles/devices.
- Rest/Workout conditional entry behavior with a protected Rest invariant.
- One-record-per-date validation and duplicate-date rejection.
- Field-specific validation, including distinct blank vs out-of-range Perceived Exertion messages.
- Previous-night sleep semantics tied explicitly to the selected record date.
- End-of-day logging guidance so the selected day's training and study are substantially complete before saving.
- Seven-day coverage and domain visualization where missing days remain missing.
- Home period averages for Sleep, Training, Mood, and Study. Training averages actual Workout days only and preserves total minutes as secondary context.
- Focused Sleep & Mood, Training, Study, and Recent Records views.
- Factual previous-period comparison when two consecutive seven-day periods are complete.
- Deterministic, non-medical plain-language observations.
- Responsive behavior, visible focus treatment, reduced-motion support, and color labels/icons so color is not the only carrier of meaning.

## Fresh-Eyes Release Test

An unfamiliar tester used the release candidate without coaching and successfully completed the required release-gate tasks, including explaining the app, recording a day, finding sleep/coverage information, using Help, downloading a backup, and explaining where records are stored.

The tester described the product as easy to use and attractive. Two substantive observations were recorded:

1. The Home Training card originally showed total weekly workout minutes while the other domain cards showed averages. This broke the visual mental model. v1.0 now shows average workout duration across actual Workout days, with total minutes retained as secondary context.
2. The tester wanted more in return for continued record-keeping, such as optional user-set weekly intentions or more useful personalized observations. This is recorded as a post-v1.0 product direction rather than added during the release freeze.

## Final Release-Polish Changes

The final release-candidate sequence also resolved:

- gray number-input clear-button artifacts by rendering an intentional theme-aware × control;
- Mood hover color so unselected Mood choices use a softer amber state rather than teal;
- explicit `PERIOD AVERAGES` wording on Home;
- `Previous night's sleep` labeling and Help/tutorial examples;
- best-time-to-log guidance;
- natural integral formatting such as `40 min` instead of `40.0 min`;
- Workout-day Perceived Exertion as a user-facing whole-number 1–10 scale, with Rest stored automatically as 0;
- separate errors for missing Perceived Exertion and values outside 1–10.

## Data and Privacy Model

- Persistent records are stored in the user's browser/profile using browser-local storage.
- There is no Recovery Compass account, authentication system, or Recovery Compass cloud database in v1.0.
- The active Streamlit session holds the runtime representation required to operate the app while it is open.
- Clearing browser/site data can remove records.
- CSV backup is the portable transfer and recovery path.
- Restore validates the entire file before changing current records and rejects duplicate-date collisions atomically.

## Known Limitations

- No edit or delete workflow for saved records.
- No automatic cloud/device synchronization.
- No reminders or notifications.
- No user-defined workout categories.
- Study remains required in the current student-focused schema.
- Weekly comparison requires two consecutive complete seven-day periods.
- No user-set weekly goals in v1.0.
- No live AI coach or LLM-dependent core behavior.
- No medical/recovery score, diagnosis, causal inference, treatment advice, injury assessment, performance guarantee, or automatic training prescription.
- Browser persistence depends on browser/site storage remaining available.
- The project has not undergone professional security, clinical, or production-scale audit.

## Post-v1.0 Candidates

The release freeze intentionally leaves the following for later evaluation:

- safe edit/delete record workflows;
- optional, user-controlled weekly intentions/goals without streak pressure or health judgment;
- richer deterministic feedback and longer-term pattern explanation;
- additional customization only where it does not compromise the simple daily workflow;
- broader target-user support beyond the current student-centered Study field.

## Qualification Evidence

Final local qualification on September 4, 2026:

```text
python -m pytest -q
26 passed

python -m py_compile app.py src\validation.py src\storage.py src\analytics.py src\feedback.py
PASS

git diff --check
PASS (exit code 0)

Full internal smoke regression
PASS

Fresh-eyes no-coaching usability test
PASS

Known release blockers
0

Public deployment smoke test
PASS

Live app
https://recovery-compass.streamlit.app
```

The public deployment was opened in a clean browser/profile and passed the release smoke test. The verified live app is https://recovery-compass.streamlit.app.
