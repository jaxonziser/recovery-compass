## Problem Statement

Students who exercise and manage substantial academic workloads often either do not track their routines or use several disconnected and inefficient tools. Existing tracking can become slow, overly detailed, or repetitive, causing users to abandon it.

Recovery Compass will provide one fast daily entry system for basic workout, sleep, optional mood, and study information. It will transform those records into visible weekly patterns and constructive, nonjudgmental feedback without requiring detailed health, nutrition, or personal information.

## Primary User

A student who exercises, studies regularly, and wants to reflect on weekly patterns without maintaining several complicated tracking systems.

## Job to Be Done

When I am balancing exercise, sleep, mood, and schoolwork, I want to record a small amount of information quickly so that I can see useful weekly patterns and make more deliberate decisions.

## Success Criteria

- A user can complete normal daily entry in under two minutes.
- Weekly trends are clearly visible.
- Feedback is constructive and nonjudgmental.
- Feedback does not repeat identical responses unnecessarily.
- A user can export or review their records.
- The product remains useful without collecting sensitive personal information.

## Future Considerations

- Optional exercise-level workout details
- Progressive-overload tracking
- Reminders
- Water tracking
- More varied deterministic feedback language

## MVP Freeze

**Status:** MVP FROZEN  
**Version:** v0.1  
**Freeze date:** 2026-07-31

### Purpose of the Freeze

The Recovery Compass summer MVP scope is now fixed so that development can focus on implementing, testing, documenting, and completing the agreed product rather than continually adding new features.

The MVP freeze does not mean that the application is finished. It means that the features and data fields planned for v0.1 will not expand unless an existing feature of comparable scope is removed.

### Target User

Recovery Compass v0.1 is designed primarily for high-school students who balance physical training with academic responsibilities and want a simple way to reflect on patterns involving training, sleep, mood, and study workload.

### Frozen Daily-Record Fields

The v0.1 daily record contains:

- `date`
- `workout_type`
- `duration_minutes`
- `perceived_exertion`
- `sleep_hours`
- `mood_rating`, optional
- `study_hours`

The internal snake_case identifiers remain stable for code, testing, CSV headers, and later analytics.

The interface may display clearer labels such as:

- Date
- Workout Type
- Workout Duration
- Perceived Exertion
- Sleep Hours
- Mood Rating
- Study Hours

### Frozen Validation Rules

- Date must use `YYYY-MM-DD` and represent a real calendar date.
- Workout Type must be Rest, Strength, Cardio, Sport, Mobility, or Other.
- Workout Duration must be a whole number from 0 to 300 minutes.
- Perceived Exertion must be a whole number from 0 to 10.
- Sleep Hours must be a number from 0 to 16.
- Mood Rating may be blank or a whole number from 1 to 5.
- Study Hours must be a number from 0 to 16.
- Required fields may not be blank.
- Invalid records are rejected rather than partially accepted.
- Field-specific errors are shown before invalid data reaches storage or analytics.
- Valid records are normalized into consistent Python data types.

### Included in the Summer MVP

The frozen summer MVP includes:

- structured daily-record entry
- reusable validation and normalization
- local CSV storage
- CSV import and export
- duplicate-date handling
- transparent weekly calculations
- chart-ready data
- deterministic, non-medical feedback
- a Streamlit interface
- manual and automated testing
- documentation
- an optional language-model explanation layer only after the non-AI version works reliably

### Explicit Non-Goals

The summer MVP will not include:

- medical diagnosis or treatment
- injury assessment or advice
- mental-health diagnosis or assessment
- nutrition, calorie, weight, or body-comparison tracking
- detailed lift or exercise-set tracking
- automatic training prescriptions
- performance guarantees
- accounts or authentication
- public profiles
- social features
- leaderboards
- coach or parent portals
- reminders or notifications
- permanent cloud storage
- a mobile application
- custom machine-learning model training
- unrestricted free-text health or personal notes
- unrestricted LLM interpretation of user input
- an LLM calculating core metrics
- advanced visual polish beyond what is necessary for a usable MVP

### Deferred Ideas

The following ideas may be reconsidered after v1.0 but are not part of the frozen MVP:

- changing Study Hours to Study/Work Hours
- expanding the target user beyond students
- custom workout categories
- user-defined personal target ranges
- controlled free-text workout labels
- additional dashboard customization
- expanded field explanations and tooltips
- broader language-model personalization

### Change-Control Rule

A proposed feature may enter the summer MVP only when:

1. it directly supports the existing target user and product purpose;
2. it does not introduce medical, privacy, or safety risks;
3. it can be tested reliably;
4. it does not endanger the completion timeline; and
5. an existing feature or equivalent amount of scope is removed.

Otherwise, the proposal must be marked Deferred or Rejected.

### Current Implementation Status

At the time of the freeze:

- the wireframes have been completed and tested with two users;
- the command-line entry flow has been created;
- reusable validation and normalization have been implemented;
- all seven required manual validation cases have passed;
- records are not yet stored;
- duplicate-date handling is not yet implemented;
- CSV import and export are not yet implemented;
- weekly metrics and feedback are not yet implemented;
- the Streamlit interface is not yet connected.

### Ownership and Development Model

Recovery Compass is an AI-assisted Python product-development project.

The project creator serves as **Creator and Product Lead**, with responsibility for:

- defining and approving product behavior
- conducting and interpreting user research
- controlling scope
- reviewing proposed features
- learning the major technical logic
- personally testing implementations
- evaluating results
- documenting decisions and limitations
- accepting or rejecting completed features

AI serves as a technical instructor, architect, and implementation collaborator. Significant AI assistance is documented separately in `docs/ai-assistance-log.md`.