# Training Load Calculator

## Specification

1. Inputs: workout duration in minutes and perceived exertion from 1 to 10.
2. Conversions: convert the submitted text into numbers.
3. Calculation: multiply duration by exertion.
4. Output: display duration, exertion, and session load.
5. Non-goals: no interface, database, charts, storage, or advanced validation.

## Pseudocode

START

Ask for workout duration.
Ask for perceived exertion.
Convert both answers into numbers.
Multiply duration by exertion.
Display the session summary.

END

## How to Run

From the main recovery-compass folder:

```cmd
python mini_projects\training_load_calculator\calculator.py

## Manual Test Cases

| Test             | Duration | Exertion | Expected | Actual | Result |
| ---------------- | -------: | -------: | -------: | -----: | ------ |
| Ordinary workout |       45 |        7 |    315.0 |  315.0 | Pass   |
| Rest day         |        0 |        5 |      0.0 |    0.0 | Pass   |
| Decimal input    |     37.5 |      6.5 |   243.75 | 243.75 | Pass   |

## Current Limitations

Does not reject exertion values outside 1-10.
Does not handle blank or nonnumeric input.
Does not save results.
Calculates only one workout at a time.
Has no graphical interface.