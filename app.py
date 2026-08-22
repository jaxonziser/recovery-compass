"""Streamlit dashboard for Recovery Compass v0.1."""

from datetime import date, timedelta
from html import escape

import altair as alt
import streamlit as st

from src.analytics import calculate_metrics, prepare_chart_data
from src.storage import load_records


# ---------------------------------------------------------
# Page configuration
# ---------------------------------------------------------

st.set_page_config(
    page_title="Recovery Compass",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="collapsed",
)


# ---------------------------------------------------------
# Visual system
# ---------------------------------------------------------

st.html(
    """
    <style>
        :root {
            --rc-navy-950: #102A43;
            --rc-navy-900: #17365D;
            --rc-blue-700: #24527A;
            --rc-teal-700: #117A84;
            --rc-teal-500: #2A9D9F;

            --rc-text: #172033;
            --rc-muted: #667085;
            --rc-muted-light: #8993A4;

            --rc-border: #E3E8EF;
            --rc-border-soft: #EBEFF4;

            --rc-surface: #FFFFFF;
            --rc-background: #F3F6FA;

            --rc-sleep: #5367A5;
            --rc-training: #2D6A91;
            --rc-mood: #B7791F;
            --rc-study: #557A72;
        }

        html,
        body,
        [class*="css"] {
            font-family:
                Inter,
                ui-sans-serif,
                -apple-system,
                BlinkMacSystemFont,
                "Segoe UI",
                sans-serif;
        }

        [data-testid="stAppViewContainer"] {
            background:
                radial-gradient(
                    circle at 85% 5%,
                    rgba(17, 122, 132, 0.055),
                    transparent 24rem
                ),
                var(--rc-background);
        }

        [data-testid="stHeader"] {
            background: transparent;
        }

        [data-testid="stToolbar"] {
            right: 1rem;
        }

        .block-container {
            max-width: 1180px;
            padding-top: 1.55rem;
            padding-bottom: 4rem;
        }

        /* -------------------------------------------------
           Hero
        ------------------------------------------------- */

        .rc-hero {
            position: relative;
            overflow: hidden;

            background:
                linear-gradient(
                    120deg,
                    #102A43 0%,
                    #173F62 52%,
                    #117A84 130%
                );

            border: 1px solid rgba(255, 255, 255, 0.07);
            border-radius: 22px;

            padding: 2rem 2.15rem 1.9rem 2.15rem;
            margin-bottom: 1.8rem;

            box-shadow:
                0 1px 2px rgba(16, 24, 40, 0.04),
                0 14px 38px rgba(16, 42, 67, 0.12);
        }

        .rc-hero::after {
            content: "";
            position: absolute;

            width: 280px;
            height: 280px;

            border-radius: 50%;

            right: -105px;
            top: -135px;

            background:
                rgba(255, 255, 255, 0.055);
        }

        .rc-hero-top {
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            gap: 1rem;
        }

        .rc-eyebrow {
            color: #99D6D5;

            font-size: 0.72rem;
            font-weight: 750;
            letter-spacing: 0.135em;
            text-transform: uppercase;

            margin-bottom: 0.55rem;
        }

        .rc-hero h1.rc-title {
            color: #FFFFFF !important;

            font-size: 2.45rem;
            line-height: 1.06;
            font-weight: 760;
            letter-spacing: -0.04em;

            margin: 0;
        }

        .rc-hero-tagline {
            color: #FFFFFF;

            font-size: 1.05rem;
            font-weight: 560;

            margin-top: 0.65rem;
        }

        .rc-hero-description {
            color: #D5E0EA;

            font-size: 0.91rem;
            line-height: 1.55;

            max-width: 650px;
            margin-top: 0.45rem;
        }

        .rc-hero-badges {
            display: flex;
            gap: 0.55rem;
            flex-wrap: wrap;

            margin-top: 1.25rem;
        }

        .rc-hero-badge {
            display: inline-flex;
            align-items: center;
            gap: 0.42rem;

            color: #E7F1F5;
            background: rgba(255, 255, 255, 0.085);

            border: 1px solid rgba(255, 255, 255, 0.12);
            border-radius: 999px;

            padding: 0.4rem 0.7rem;

            font-size: 0.76rem;
            font-weight: 550;
        }

        .rc-badge-dot {
            width: 7px;
            height: 7px;

            border-radius: 50%;
            background: #6FD0C9;

            display: inline-block;
        }

        /* -------------------------------------------------
           Sections
        ------------------------------------------------- */

        .rc-section-heading {
            display: flex;
            align-items: flex-end;
            justify-content: space-between;
            gap: 1rem;

            margin-top: 1.8rem;
            margin-bottom: 0.8rem;
        }

        .rc-section-title {
            color: var(--rc-navy-950);

            font-size: 1.25rem;
            line-height: 1.25;
            font-weight: 750;

            margin: 0;
        }

        .rc-section-note {
            color: var(--rc-muted);

            font-size: 0.84rem;
            line-height: 1.45;

            margin-top: 0.25rem;
        }

        .rc-section-kicker {
            color: var(--rc-teal-700);

            font-size: 0.68rem;
            font-weight: 750;
            letter-spacing: 0.09em;
            text-transform: uppercase;

            margin-bottom: 0.3rem;
        }

        /* -------------------------------------------------
           Metric cards
        ------------------------------------------------- */

        .rc-card {
            --accent: var(--rc-teal-700);

            position: relative;
            overflow: hidden;

            background: var(--rc-surface);

            border: 1px solid var(--rc-border);
            border-radius: 16px;

            min-height: 145px;

            padding: 1.05rem 1.08rem 1rem 1.08rem;

            box-shadow:
                0 1px 2px rgba(16, 24, 40, 0.025),
                0 6px 16px rgba(16, 24, 40, 0.035);
        }

        .rc-card::before {
            content: "";

            position: absolute;
            left: 0;
            top: 0;

            width: 100%;
            height: 4px;

            background: var(--accent);
        }

        .rc-card-header {
            display: flex;
            justify-content: space-between;
            align-items: center;

            margin-bottom: 0.55rem;
        }

        .rc-card-label {
            color: var(--rc-muted);

            font-size: 0.69rem;
            font-weight: 750;
            letter-spacing: 0.085em;
            text-transform: uppercase;
        }

        .rc-card-dot {
            width: 8px;
            height: 8px;

            border-radius: 50%;
            background: var(--accent);

            opacity: 0.85;
        }

        .rc-card-value {
            color: var(--rc-navy-950);

            font-size: 1.75rem;
            line-height: 1.1;
            font-weight: 760;
            letter-spacing: -0.03em;

            margin-top: 0.2rem;
        }

        .rc-card-note {
            color: var(--rc-muted);

            font-size: 0.76rem;
            line-height: 1.35;

            margin-top: 0.6rem;
        }

        /* -------------------------------------------------
           Status
        ------------------------------------------------- */

        .rc-status-row {
            display: flex;
            align-items: flex-start;
            gap: 0.7rem;

            background: #F8FBFC;

            border: 1px solid #DCEBEB;
            border-radius: 12px;

            color: #466265;

            padding: 0.72rem 0.88rem;
            margin-top: 0.75rem;

            font-size: 0.8rem;
            line-height: 1.4;
        }

        .rc-status-icon {
            flex: 0 0 auto;

            width: 20px;
            height: 20px;

            border-radius: 50%;

            display: flex;
            align-items: center;
            justify-content: center;

            color: #FFFFFF;
            background: var(--rc-teal-700);

            font-size: 0.68rem;
            font-weight: 750;

            margin-top: 0.02rem;
        }

        /* -------------------------------------------------
           Empty states
        ------------------------------------------------- */

        .rc-empty-state {
            background:
                linear-gradient(
                    180deg,
                    #FFFFFF 0%,
                    #FAFBFC 100%
                );

            border: 1px solid var(--rc-border);
            border-radius: 16px;

            text-align: center;

            padding: 2rem 1.2rem;
        }

        .rc-empty-symbol {
            width: 40px;
            height: 40px;

            display: flex;
            align-items: center;
            justify-content: center;

            margin: 0 auto 0.8rem auto;

            border-radius: 50%;
            border: 1px solid #D7DEE7;

            background: #F7F9FB;

            color: var(--rc-teal-700);

            font-size: 1.15rem;
            font-weight: 600;
        }

        .rc-empty-title {
            color: var(--rc-navy-950);

            font-size: 0.92rem;
            font-weight: 700;
        }

        .rc-empty-copy {
            color: var(--rc-muted);

            font-size: 0.79rem;
            line-height: 1.45;

            margin-top: 0.3rem;
        }

        /* -------------------------------------------------
           Streamlit containers / dataframe / expander
        ------------------------------------------------- */

        div[data-testid="stVerticalBlockBorderWrapper"] {
            background: #FFFFFF;

            border-color: var(--rc-border) !important;
            border-radius: 18px !important;

            box-shadow:
                0 1px 2px rgba(16, 24, 40, 0.02),
                0 6px 18px rgba(16, 24, 40, 0.025);
        }

        div[data-testid="stDataFrame"] {
            border: 1px solid var(--rc-border);
            border-radius: 14px;
            overflow: hidden;
        }

        /* -------------------------------------------------
           Altair chart surface
        ------------------------------------------------- */

        div[data-testid="stVegaLiteChart"] {
            background: #0F1117 !important;
            border: 1px solid #252A33 !important;
            border-radius: 16px !important;
            overflow: hidden;
            box-shadow:
                0 1px 2px rgba(0, 0, 0, 0.18),
                0 8px 22px rgba(16, 24, 40, 0.08);
        }

        div[data-testid="stVegaLiteChart"] > div,
        div[data-testid="stVegaLiteChart"] .vega-embed,
        div[data-testid="stVegaLiteChart"] canvas,
        div[data-testid="stVegaLiteChart"] svg {
            background: #0F1117 !important;
        }


        /* -------------------------------------------------
           Recent records table
        ------------------------------------------------- */

        .rc-table-wrap {
            overflow-x: auto;
            background: #0F1117;
            border: 1px solid #252A33;
            border-radius: 16px;
            box-shadow:
                0 1px 2px rgba(0, 0, 0, 0.18),
                0 8px 22px rgba(16, 24, 40, 0.08);
        }

        .rc-table {
            width: 100%;
            border-collapse: collapse;
            background: #0F1117;
            font-size: 0.79rem;
        }

        .rc-table thead th {
            background: #171A21;
            color: #AEB8C6;
            font-size: 0.67rem;
            font-weight: 750;
            letter-spacing: 0.055em;
            text-transform: uppercase;
            text-align: left;
            padding: 0.78rem 0.75rem;
            border-bottom: 1px solid #2B313B;
            white-space: nowrap;
        }

        .rc-table tbody td {
            color: #E8EDF4;
            padding: 0.76rem 0.75rem;
            border-bottom: 1px solid #252A33;
            white-space: nowrap;
        }

        .rc-table tbody tr:last-child td {
            border-bottom: none;
        }

        .rc-table tbody tr:hover {
            background: #171A21;
        }

        .rc-table-muted {
            color: #7F8A99 !important;
        }

        details {
            background: #FFFFFF !important;

            border: 1px solid var(--rc-border) !important;
            border-radius: 14px !important;

            padding-left: 0.2rem;
            padding-right: 0.2rem;
        }

        details [data-testid="stExpanderDetails"],
        details [data-testid="stExpanderDetails"] p,
        details [data-testid="stExpanderDetails"] li,
        details [data-testid="stExpanderDetails"] strong,
        details [data-testid="stExpanderDetails"] span {
            color: var(--rc-text) !important;
        }

        details:not([open]) summary,
        details:not([open]) summary p,
        details:not([open]) summary span {
            color: var(--rc-text) !important;
        }

        details[open] summary,
        details[open] summary p,
        details[open] summary span {
            color: #FFFFFF !important;
        }

        details:not([open]) summary svg {
            color: var(--rc-text) !important;
            fill: var(--rc-text) !important;
        }

        details[open] summary svg {
            color: #FFFFFF !important;
            fill: #FFFFFF !important;
        }


        hr {
            border-color: #E8ECF1;
        }

        /* -------------------------------------------------
           Mobile / narrower layouts
        ------------------------------------------------- */

        @media (max-width: 800px) {
            .rc-hero {
                padding: 1.55rem 1.4rem;
            }

            .rc-hero h1.rc-title {
                font-size: 2rem;
            }

            .rc-title {
                font-size: 2rem;
            }

            .block-container {
                padding-left: 1rem;
                padding-right: 1rem;
            }
        }
    </style>
    """,
)


# ---------------------------------------------------------
# Presentation helpers
# ---------------------------------------------------------

def _format_date_range(
    start_date: str,
    end_date: str,
) -> str:
    """Return a compact human-readable date range."""
    start = date.fromisoformat(start_date)
    end = date.fromisoformat(end_date)

    if start.year == end.year:
        return (
            f"{start.strftime('%b')} {start.day}"
            f" – "
            f"{end.strftime('%b')} {end.day}, {end.year}"
        )

    return (
        f"{start.strftime('%b')} {start.day}, {start.year}"
        f" – "
        f"{end.strftime('%b')} {end.day}, {end.year}"
    )


def _display_number(
    value: int | float | None,
    decimals: int = 1,
) -> str:
    """Format a metric value for the interface."""
    if value is None:
        return "—"

    if isinstance(value, int):
        return str(value)

    return f"{value:.{decimals}f}"


def _metric_card(
    label: str,
    value: str,
    note: str,
    accent: str,
) -> None:
    """Render one visually consistent Recovery Compass metric card."""
    st.html(
        f"""
        <div class="rc-card" style="--accent: {escape(accent)};">
            <div class="rc-card-header">
                <div class="rc-card-label">{escape(label)}</div>
                <span class="rc-card-dot"></span>
            </div>

            <div class="rc-card-value">{escape(value)}</div>

            <div class="rc-card-note">
                {escape(note)}
            </div>
        </div>
        """,
    )


def _empty_state(
    title: str,
    copy: str,
) -> None:
    """Render an intentional empty-state panel."""
    st.html(
        f"""
        <div class="rc-empty-state">
            <div class="rc-empty-symbol">○</div>

            <div class="rc-empty-title">
                {escape(title)}
            </div>

            <div class="rc-empty-copy">
                {escape(copy)}
            </div>
        </div>
        """,
    )


def _current_period_rows(
    rows: list[dict[str, object]],
    start_date: str,
    end_date: str,
) -> list[dict[str, object]]:
    """Return chart rows inside the current analytics period."""
    return [
        row
        for row in rows
        if start_date <= row["date"] <= end_date
    ]



def _display_recent_records(
    records: list[dict[str, object]],
) -> None:
    """Render the seven most recent records as a light factual table."""
    recent_records = sorted(
        records,
        key=lambda record: record["date"],
        reverse=True,
    )[:7]

    rows_html = []

    for record in recent_records:
        record_date = date.fromisoformat(
            str(record["date"])
        ).strftime("%b %d, %Y")

        is_workout = (
            record["workout_type"] != "Rest"
            and record["duration_minutes"] > 0
        )

        exertion = (
            str(record["perceived_exertion"])
            if is_workout
            else "—"
        )

        mood = (
            str(record["mood_rating"])
            if record["mood_rating"] is not None
            else "—"
        )

        exertion_class = (
            ""
            if is_workout
            else ' class="rc-table-muted"'
        )

        mood_class = (
            ""
            if record["mood_rating"] is not None
            else ' class="rc-table-muted"'
        )

        rows_html.append(
            f"""
            <tr>
                <td>{escape(record_date)}</td>
                <td>{escape(str(record["workout_type"]))}</td>
                <td>{escape(str(record["duration_minutes"]))}</td>
                <td{exertion_class}>{escape(exertion)}</td>
                <td>{escape(str(record["sleep_hours"]))}</td>
                <td{mood_class}>{escape(mood)}</td>
                <td>{escape(str(record["study_hours"]))}</td>
            </tr>
            """
        )

    st.html(
        f"""
        <div class="rc-table-wrap">
            <table class="rc-table">
                <thead>
                    <tr>
                        <th>Date</th>
                        <th>Workout</th>
                        <th>Duration (min)</th>
                        <th>Exertion</th>
                        <th>Sleep (hr)</th>
                        <th>Mood</th>
                        <th>Study (hr)</th>
                    </tr>
                </thead>

                <tbody>
                    {''.join(rows_html)}
                </tbody>
            </table>
        </div>
        """
    )


# ---------------------------------------------------------
# Load data
# ---------------------------------------------------------

try:
    records = load_records()
except Exception as exc:
    st.error(
        "Recovery Compass could not load the saved records. "
        "The underlying data file may be unavailable or malformed."
    )

    st.caption(f"Technical detail: {exc}")

    st.stop()


period_end = date.today()

metrics = calculate_metrics(
    records,
    period_end=period_end,
)

chart_data = prepare_chart_data(records)

current = metrics["current_period"]

period_label = _format_date_range(
    current["start_date"],
    current["end_date"],
)


# ---------------------------------------------------------
# Current-period values
# ---------------------------------------------------------

days_recorded = current["days_recorded"]
workout_days = current["workout_days"]
training_minutes = current["total_training_minutes"]

average_sleep = current["average_sleep_hours"]
average_mood = current["average_mood_rating"]
average_study = current["average_study_hours"]
average_exertion = current["average_training_exertion"]

mood_entries = current["mood_entries"]


# ---------------------------------------------------------
# Hero
# ---------------------------------------------------------

st.html(
    f"""
    <div class="rc-hero">

        <div class="rc-eyebrow">
            Personal Analytics
        </div>

        <h1 class="rc-title">
            Recovery Compass
        </h1>

        <div class="rc-hero-tagline">
            See the week clearly.
        </div>

        <div class="rc-hero-description">
            A focused view of your recent training, sleep, mood,
            and academic workload — built from the data you actually record.
        </div>

        <div class="rc-hero-badges">

            <div class="rc-hero-badge">
                <span class="rc-badge-dot"></span>
                Current period
            </div>

            <div class="rc-hero-badge">
                {escape(period_label)}
            </div>

            <div class="rc-hero-badge">
                {days_recorded} of 7 days logged
            </div>

        </div>
    </div>
    """,
)


# ---------------------------------------------------------
# Current 7-day overview
# ---------------------------------------------------------

st.html(
    """
    <div class="rc-section-heading">

        <div>
            <div class="rc-section-kicker">
                At a glance
            </div>

            <div class="rc-section-title">
                Current 7-Day Overview
            </div>

            <div class="rc-section-note">
                Key facts from the current calendar period.
                Coverage stays visible so partial data is never mistaken
                for a complete week.
            </div>
        </div>

    </div>
    """,
)


row_one = st.columns(
    4,
    gap="medium",
)

with row_one[0]:
    _metric_card(
        "Coverage",
        f"{days_recorded} / 7",
        "Days recorded in the current period",
        "#117A84",
    )

with row_one[1]:
    _metric_card(
        "Workout Days",
        str(workout_days),
        "Days containing an actual workout",
        "#2D6A91",
    )

with row_one[2]:
    _metric_card(
        "Training",
        f"{training_minutes} min",
        "Total actual workout time",
        "#2D6A91",
    )

with row_one[3]:
    sleep_note = (
        f"{days_recorded} of 7 days recorded"
        if average_sleep is not None
        else "No sleep records in this period"
    )

    _metric_card(
        "Avg Sleep",
        (
            f"{_display_number(average_sleep)} hr"
            if average_sleep is not None
            else "—"
        ),
        sleep_note,
        "#5367A5",
    )


row_two = st.columns(
    3,
    gap="medium",
)

with row_two[0]:
    mood_note = (
        (
            f"{mood_entries} mood rating"
            + ("" if mood_entries == 1 else "s")
            + " recorded"
        )
        if average_mood is not None
        else "No mood ratings recorded"
    )

    _metric_card(
        "Avg Mood",
        (
            f"{_display_number(average_mood)} / 5"
            if average_mood is not None
            else "—"
        ),
        mood_note,
        "#B7791F",
    )

with row_two[1]:
    study_note = (
        f"{days_recorded} of 7 days recorded"
        if average_study is not None
        else "No study records in this period"
    )

    _metric_card(
        "Avg Study",
        (
            f"{_display_number(average_study)} hr"
            if average_study is not None
            else "—"
        ),
        study_note,
        "#557A72",
    )

with row_two[2]:
    exertion_note = (
        (
            f"Across {workout_days} workout day"
            + ("" if workout_days == 1 else "s")
        )
        if average_exertion is not None
        else "No actual workouts recorded"
    )

    _metric_card(
        "Avg Exertion",
        (
            f"{_display_number(average_exertion)} / 10"
            if average_exertion is not None
            else "—"
        ),
        exertion_note,
        "#6B7280",
    )


# ---------------------------------------------------------
# Comparison state
# ---------------------------------------------------------

if metrics["comparison_available"]:
    comparison_copy = (
        "A complete previous 7-day period is available. "
        "Recovery Compass can compare the two periods without "
        "mixing complete and incomplete weeks."
    )

else:
    comparison_copy = (
        "Previous-week comparison will unlock when both consecutive "
        "7-day periods contain all seven recorded days."
    )


st.html(
    f"""
    <div class="rc-status-row">

        <div class="rc-status-icon">
            i
        </div>

        <div>
            {escape(comparison_copy)}
        </div>

    </div>
    """,
)


# ---------------------------------------------------------
# Patterns section
# ---------------------------------------------------------

st.html(
    """
    <div class="rc-section-heading">

        <div>
            <div class="rc-section-kicker">
                Your patterns
            </div>

            <div class="rc-section-title">
                Sleep & Mood
            </div>

            <div class="rc-section-note">
                Sleep and mood use separate scales for clarity.
                Missing days and missing mood entries appear as gaps rather
                than being connected or converted to zero.
            </div>
        </div>

    </div>
    """,
)


sleep_mood_rows = _current_period_rows(
    chart_data["sleep_mood"],
    current["start_date"],
    current["end_date"],
)


period_start_date = date.fromisoformat(
    current["start_date"]
)

period_dates = [
    period_start_date + timedelta(days=offset)
    for offset in range(7)
]

date_labels = [
    period_date.strftime("%b %d")
    for period_date in period_dates
]

sleep_mood_by_date = {
    row["date"]: row
    for row in sleep_mood_rows
}


sleep_rows = []
mood_rows = []

sleep_segment = 0
mood_segment = 0


for period_date in period_dates:
    iso_date = period_date.isoformat()
    date_label = period_date.strftime("%b %d")

    row = sleep_mood_by_date.get(
        iso_date
    )

    sleep_value = (
        row["sleep_hours"]
        if row is not None
        else None
    )

    mood_value = (
        row["mood_rating"]
        if row is not None
        else None
    )

    if sleep_value is None:
        sleep_segment += 1

    else:
        sleep_rows.append(
            {
                "date": iso_date,
                "date_label": date_label,
                "sleep_hours": sleep_value,
                "segment": sleep_segment,
            }
        )

    if mood_value is None:
        mood_segment += 1

    else:
        mood_rows.append(
            {
                "date": iso_date,
                "date_label": date_label,
                "mood_rating": mood_value,
                "segment": mood_segment,
            }
        )


with st.container(border=True):

    if not sleep_rows and not mood_rows:
        _empty_state(
            "No sleep or mood data yet",
            (
                "Log your first day in this period to begin building "
                "the Sleep & Mood timeline."
            ),
        )

    else:
        dark_chart_background = "#0F1117"
        dark_chart_grid = "#252A33"
        dark_chart_text = "#AEB8C6"
        dark_chart_domain = "#3A414D"

        charts = []

        if sleep_rows:
            sleep_base = (
                alt.Chart(
                    alt.Data(values=sleep_rows)
                )
                .encode(
                    x=alt.X(
                        "date_label:N",
                        title=None,
                        sort=date_labels,
                        scale=alt.Scale(
                            domain=date_labels,
                            padding=0.25,
                        ),
                        axis=None,
                    ),
                    y=alt.Y(
                        "sleep_hours:Q",
                        title="Sleep (hours)",
                        scale=alt.Scale(
                            zero=False,
                            padding=18,
                        ),
                        axis=alt.Axis(
                            titleColor="#8FA8FF",
                            labelColor=dark_chart_text,
                            grid=True,
                            gridColor=dark_chart_grid,
                            gridOpacity=1,
                            domainColor=dark_chart_domain,
                            tickColor=dark_chart_domain,
                            labelPadding=7,
                        ),
                    ),
                )
            )

            sleep_line = (
                sleep_base
                .mark_line(
                    strokeWidth=3,
                    color="#6F8DDE",
                )
                .encode(
                    detail="segment:N",
                )
            )

            sleep_points = (
                sleep_base
                .mark_point(
                    filled=True,
                    size=72,
                    color="#77BDFB",
                    stroke="#0F1117",
                    strokeWidth=1.5,
                )
                .encode(
                    tooltip=[
                        alt.Tooltip(
                            "date:T",
                            title="Date",
                            format="%B %d, %Y",
                        ),
                        alt.Tooltip(
                            "sleep_hours:Q",
                            title="Sleep",
                            format=".1f",
                        ),
                    ],
                )
            )

            sleep_chart = (
                alt.layer(
                    sleep_line,
                    sleep_points,
                )
                .properties(
                    height=205,
                    title=alt.Title(
                        text="Sleep",
                        subtitle="Hours recorded each day",
                        color="#F4F7FB",
                        subtitleColor="#8F9AA8",
                        fontSize=15,
                        subtitleFontSize=11,
                        anchor="start",
                        offset=12,
                    ),
                )
            )

            charts.append(
                sleep_chart
            )

        if mood_rows:
            mood_base = (
                alt.Chart(
                    alt.Data(values=mood_rows)
                )
                .encode(
                    x=alt.X(
                        "date_label:N",
                        title=None,
                        sort=date_labels,
                        scale=alt.Scale(
                            domain=date_labels,
                            padding=0.25,
                        ),
                        axis=alt.Axis(
                            labelAngle=0,
                            labelColor=dark_chart_text,
                            labelPadding=10,
                            grid=False,
                            domainColor=dark_chart_domain,
                            tickColor=dark_chart_domain,
                        ),
                    ),
                    y=alt.Y(
                        "mood_rating:Q",
                        title="Mood (1–5)",
                        scale=alt.Scale(
                            domain=[1, 5],
                            padding=18,
                        ),
                        axis=alt.Axis(
                            values=[1, 2, 3, 4, 5],
                            titleColor="#D89B3D",
                            labelColor=dark_chart_text,
                            grid=True,
                            gridColor=dark_chart_grid,
                            gridOpacity=1,
                            domainColor=dark_chart_domain,
                            tickColor=dark_chart_domain,
                            labelPadding=7,
                        ),
                    ),
                )
            )

            mood_line = (
                mood_base
                .mark_line(
                    strokeWidth=3,
                    color="#C98216",
                )
                .encode(
                    detail="segment:N",
                )
            )

            mood_points = (
                mood_base
                .mark_point(
                    filled=True,
                    size=72,
                    color="#E1A13A",
                    stroke="#0F1117",
                    strokeWidth=1.5,
                )
                .encode(
                    tooltip=[
                        alt.Tooltip(
                            "date:T",
                            title="Date",
                            format="%B %d, %Y",
                        ),
                        alt.Tooltip(
                            "mood_rating:Q",
                            title="Mood",
                            format=".0f",
                        ),
                    ],
                )
            )

            mood_chart = (
                alt.layer(
                    mood_line,
                    mood_points,
                )
                .properties(
                    height=205,
                    title=alt.Title(
                        text="Mood",
                        subtitle="Recorded rating on the 1–5 scale",
                        color="#F4F7FB",
                        subtitleColor="#8F9AA8",
                        fontSize=15,
                        subtitleFontSize=11,
                        anchor="start",
                        offset=12,
                    ),
                )
            )

            charts.append(
                mood_chart
            )

        if len(charts) == 2:
            sleep_mood_chart = (
                alt.vconcat(
                    charts[0],
                    charts[1],
                    spacing=24,
                )
                .resolve_scale(
                    x="shared",
                )
                .properties(
                    background=dark_chart_background,
                    padding={
                        "left": 18,
                        "right": 24,
                        "top": 8,
                        "bottom": 10,
                    },
                )
            )

        else:
            sleep_mood_chart = (
                charts[0]
                .properties(
                    background=dark_chart_background,
                    padding={
                        "left": 18,
                        "right": 24,
                        "top": 8,
                        "bottom": 10,
                    },
                )
            )

        sleep_mood_chart = (
            sleep_mood_chart
            .configure_view(
                stroke=None,
                fill=dark_chart_background,
            )
            .configure_axis(
                labelFontSize=11,
                titleFontSize=12,
                titleFontWeight=600,
            )
            .configure_title(
                font="Inter",
                subtitleFont="Inter",
            )
        )

        st.altair_chart(
            sleep_mood_chart,
            width="stretch",
        )


# ---------------------------------------------------------
# Training visualization
# ---------------------------------------------------------

st.html(
    """
    <div class="rc-section-heading">
        <div>
            <div class="rc-section-kicker">
                Training patterns
            </div>

            <div class="rc-section-title">
                Training
            </div>

            <div class="rc-section-note">
                Daily training duration is shown separately from perceived
                exertion. Rest days stay at zero minutes and blank exertion.
                A recorded exertion value of zero remains visible as zero.
            </div>
        </div>
    </div>
    """,
)


training_period_rows = _current_period_rows(
    chart_data["training"],
    current["start_date"],
    current["end_date"],
)

training_by_date = {
    row["date"]: row
    for row in training_period_rows
}

training_rows = []
exertion_rows = []
exertion_segment = 0


for period_date in period_dates:
    iso_date = period_date.isoformat()
    date_label = period_date.strftime("%b %d")

    row = training_by_date.get(
        iso_date
    )

    if row is None:
        training_rows.append(
            {
                "date": iso_date,
                "date_label": date_label,
                "workout_type": "Not recorded",
                "duration_minutes": None,
            }
        )

        exertion_segment += 1
        continue

    training_rows.append(
        {
            "date": iso_date,
            "date_label": date_label,
            "workout_type": row["workout_type"],
            "duration_minutes": row["duration_minutes"],
        }
    )

    exertion_value = row["perceived_exertion"]

    if exertion_value is None:
        exertion_segment += 1

    else:
        exertion_rows.append(
            {
                "date": iso_date,
                "date_label": date_label,
                "workout_type": row["workout_type"],
                "perceived_exertion": exertion_value,
                "segment": exertion_segment,
            }
        )


with st.container(border=True):

    if not any(
        row["duration_minutes"] is not None
        for row in training_rows
    ):
        _empty_state(
            "No training data yet",
            (
                "Log a day in this period to begin building "
                "your Training timeline."
            ),
        )

    else:
        dark_chart_background = "#0F1117"
        dark_chart_grid = "#252A33"
        dark_chart_text = "#AEB8C6"
        dark_chart_domain = "#3A414D"

        duration_chart = (
            alt.Chart(
                alt.Data(values=training_rows)
            )
            .mark_bar(
                color="#2F7FA6",
                cornerRadiusTopLeft=4,
                cornerRadiusTopRight=4,
                size=38,
            )
            .encode(
                x=alt.X(
                    "date_label:N",
                    title=None,
                    sort=date_labels,
                    axis=None,
                ),
                y=alt.Y(
                    "duration_minutes:Q",
                    title="Minutes",
                    scale=alt.Scale(
                        zero=True,
                        nice=True,
                    ),
                    axis=alt.Axis(
                        titleColor="#67B7D1",
                        labelColor=dark_chart_text,
                        grid=True,
                        gridColor=dark_chart_grid,
                        gridOpacity=1,
                        domainColor=dark_chart_domain,
                        tickColor=dark_chart_domain,
                        labelPadding=7,
                    ),
                ),
                tooltip=[
                    alt.Tooltip(
                        "date:T",
                        title="Date",
                        format="%B %d, %Y",
                    ),
                    alt.Tooltip(
                        "workout_type:N",
                        title="Workout",
                    ),
                    alt.Tooltip(
                        "duration_minutes:Q",
                        title="Duration",
                        format=".0f",
                    ),
                ],
            )
            .properties(
                height=205,
                title=alt.Title(
                    text="Training Duration",
                    subtitle="Minutes recorded each day",
                    color="#F4F7FB",
                    subtitleColor="#8F9AA8",
                    fontSize=15,
                    subtitleFontSize=11,
                    anchor="start",
                    offset=12,
                ),
            )
        )

        training_charts = [
            duration_chart
        ]

        if exertion_rows:
            exertion_base = (
                alt.Chart(
                    alt.Data(values=exertion_rows)
                )
                .encode(
                    x=alt.X(
                        "date_label:N",
                        title=None,
                        sort=date_labels,
                        scale=alt.Scale(
                            domain=date_labels,
                            padding=0.25,
                        ),
                        axis=alt.Axis(
                            labelAngle=0,
                            labelColor=dark_chart_text,
                            labelPadding=10,
                            grid=False,
                            domainColor=dark_chart_domain,
                            tickColor=dark_chart_domain,
                        ),
                    ),
                    y=alt.Y(
                        "perceived_exertion:Q",
                        title="Exertion (0–10)",
                        scale=alt.Scale(
                            domain=[0, 10],
                            padding=18,
                        ),
                        axis=alt.Axis(
                            values=[0, 2, 4, 6, 8, 10],
                            titleColor="#8CA3B4",
                            labelColor=dark_chart_text,
                            grid=True,
                            gridColor=dark_chart_grid,
                            gridOpacity=1,
                            domainColor=dark_chart_domain,
                            tickColor=dark_chart_domain,
                            labelPadding=7,
                        ),
                    ),
                )
            )

            exertion_line = (
                exertion_base
                .mark_line(
                    strokeWidth=3,
                    color="#8396A8",
                )
                .encode(
                    detail="segment:N",
                )
            )

            exertion_points = (
                exertion_base
                .mark_point(
                    filled=True,
                    size=72,
                    color="#A9B7C4",
                    stroke="#0F1117",
                    strokeWidth=1.5,
                )
                .encode(
                    tooltip=[
                        alt.Tooltip(
                            "date:T",
                            title="Date",
                            format="%B %d, %Y",
                        ),
                        alt.Tooltip(
                            "workout_type:N",
                            title="Workout",
                        ),
                        alt.Tooltip(
                            "perceived_exertion:Q",
                            title="Exertion",
                            format=".0f",
                        ),
                    ],
                )
            )

            exertion_chart = (
                alt.layer(
                    exertion_line,
                    exertion_points,
                )
                .properties(
                    height=205,
                    title=alt.Title(
                        text="Perceived Exertion",
                        subtitle="Recorded non-Rest exertion; Rest days blank",
                        color="#F4F7FB",
                        subtitleColor="#8F9AA8",
                        fontSize=15,
                        subtitleFontSize=11,
                        anchor="start",
                        offset=12,
                    ),
                )
            )

            training_charts.append(
                exertion_chart
            )

        if len(training_charts) == 2:
            training_chart = (
                alt.vconcat(
                    training_charts[0],
                    training_charts[1],
                    spacing=24,
                )
                .resolve_scale(
                    x="shared",
                )
                .properties(
                    background=dark_chart_background,
                    padding={
                        "left": 18,
                        "right": 24,
                        "top": 8,
                        "bottom": 10,
                    },
                )
            )

        else:
            training_chart = (
                training_charts[0]
                .encode(
                    x=alt.X(
                        "date_label:N",
                        title=None,
                        sort=date_labels,
                        scale=alt.Scale(
                            domain=date_labels,
                            padding=0.25,
                        ),
                        axis=alt.Axis(
                            labelAngle=0,
                            labelColor=dark_chart_text,
                            labelPadding=10,
                            grid=False,
                            domainColor=dark_chart_domain,
                            tickColor=dark_chart_domain,
                        ),
                    ),
                )
                .properties(
                    background=dark_chart_background,
                    padding={
                        "left": 18,
                        "right": 24,
                        "top": 8,
                        "bottom": 10,
                    },
                )
            )

        training_chart = (
            training_chart
            .configure_view(
                stroke=None,
                fill=dark_chart_background,
            )
            .configure_axis(
                labelFontSize=11,
                titleFontSize=12,
                titleFontWeight=600,
            )
            .configure_title(
                font="Inter",
                subtitleFont="Inter",
            )
        )

        st.altair_chart(
            training_chart,
            width="stretch",
        )


# ---------------------------------------------------------
# Study visualization
# ---------------------------------------------------------

st.html(
    """
    <div class="rc-section-heading">
        <div>
            <div class="rc-section-kicker">
                Academic patterns
            </div>

            <div class="rc-section-title">
                Study
            </div>

            <div class="rc-section-note">
                Study hours are plotted across the same seven-calendar-day
                period. Missing days stay missing rather than being treated
                as zero hours.
            </div>
        </div>
    </div>
    """,
)


study_period_rows = _current_period_rows(
    chart_data["study"],
    current["start_date"],
    current["end_date"],
)

study_by_date = {
    row["date"]: row
    for row in study_period_rows
}

study_rows = []
study_segment = 0


for period_date in period_dates:
    iso_date = period_date.isoformat()
    date_label = period_date.strftime("%b %d")

    row = study_by_date.get(
        iso_date
    )

    study_value = (
        row["study_hours"]
        if row is not None
        else None
    )

    if study_value is None:
        study_segment += 1

    else:
        study_rows.append(
            {
                "date": iso_date,
                "date_label": date_label,
                "study_hours": study_value,
                "segment": study_segment,
            }
        )


with st.container(border=True):

    if not study_rows:
        _empty_state(
            "No study data yet",
            (
                "Log your first day in this period to begin building "
                "your Study timeline."
            ),
        )

    else:
        dark_chart_background = "#0F1117"
        dark_chart_grid = "#252A33"
        dark_chart_text = "#AEB8C6"
        dark_chart_domain = "#3A414D"

        study_base = (
            alt.Chart(
                alt.Data(values=study_rows)
            )
            .encode(
                x=alt.X(
                    "date_label:N",
                    title=None,
                    sort=date_labels,
                    scale=alt.Scale(
                        domain=date_labels,
                        padding=0.25,
                    ),
                    axis=alt.Axis(
                        labelAngle=0,
                        labelColor=dark_chart_text,
                        labelPadding=10,
                        grid=False,
                        domainColor=dark_chart_domain,
                        tickColor=dark_chart_domain,
                    ),
                ),
                y=alt.Y(
                    "study_hours:Q",
                    title="Study (hours)",
                    scale=alt.Scale(
                        zero=True,
                        nice=True,
                    ),
                    axis=alt.Axis(
                        titleColor="#79B7A7",
                        labelColor=dark_chart_text,
                        grid=True,
                        gridColor=dark_chart_grid,
                        gridOpacity=1,
                        domainColor=dark_chart_domain,
                        tickColor=dark_chart_domain,
                        labelPadding=7,
                    ),
                ),
            )
        )

        study_line = (
            study_base
            .mark_line(
                strokeWidth=3,
                color="#5D9B8A",
            )
            .encode(
                detail="segment:N",
            )
        )

        study_points = (
            study_base
            .mark_point(
                filled=True,
                size=72,
                color="#78B7A5",
                stroke="#0F1117",
                strokeWidth=1.5,
            )
            .encode(
                tooltip=[
                    alt.Tooltip(
                        "date:T",
                        title="Date",
                        format="%B %d, %Y",
                    ),
                    alt.Tooltip(
                        "study_hours:Q",
                        title="Study",
                        format=".1f",
                    ),
                ],
            )
        )

        study_chart = (
            alt.layer(
                study_line,
                study_points,
            )
            .properties(
                height=255,
                background=dark_chart_background,
                padding={
                    "left": 18,
                    "right": 24,
                    "top": 12,
                    "bottom": 10,
                },
                title=alt.Title(
                    text="Study Hours",
                    subtitle="Recorded academic workload each day",
                    color="#F4F7FB",
                    subtitleColor="#8F9AA8",
                    fontSize=15,
                    subtitleFontSize=11,
                    anchor="start",
                    offset=12,
                ),
            )
            .configure_view(
                stroke=None,
                fill=dark_chart_background,
            )
            .configure_axis(
                labelFontSize=11,
                titleFontSize=12,
                titleFontWeight=600,
            )
            .configure_title(
                font="Inter",
                subtitleFont="Inter",
            )
        )

        st.altair_chart(
            study_chart,
            width="stretch",
        )


# ---------------------------------------------------------
# Recent activity
# ---------------------------------------------------------

st.html(
    """
    <div class="rc-section-heading">

        <div>
            <div class="rc-section-kicker">
                Details
            </div>

            <div class="rc-section-title">
                Recent Records
            </div>

            <div class="rc-section-note">
                A compact factual view of your most recently recorded days.
            </div>
        </div>

    </div>
    """,
)


if not records:
    with st.container(border=True):
        _empty_state(
            "No records saved yet",
            (
                "Once your first Recovery Compass entry is saved, "
                "your recent activity will appear here."
            ),
        )

else:
    _display_recent_records(
        records
    )


# ---------------------------------------------------------
# Explanation
# ---------------------------------------------------------

st.html(
    """
    <div class="rc-section-heading">

        <div>
            <div class="rc-section-kicker">
                Transparency
            </div>

            <div class="rc-section-title">
                How the numbers work
            </div>

            <div class="rc-section-note">
                Recovery Compass keeps its calculations visible and
                understandable rather than hiding them behind a score.
            </div>
        </div>

    </div>
    """,
)


with st.expander(
    "How Recovery Compass calculates these metrics"
):
    st.markdown(
        """
        **Coverage**<br>
        The number of recorded days in the current seven-calendar-day period.

        **Workout Days**<br>
        Counts only days with a non-Rest workout and more than zero
        training minutes.

        **Average Sleep**<br>
        Uses sleep values from the recorded days in the current period.

        **Average Mood**<br>
        Uses only days where a mood rating was actually entered.
        Missing mood ratings are never treated as zero.

        **Average Study**<br>
        Uses study hours from the recorded days in the current period.

        **Average Exertion**<br>
        Uses perceived exertion from actual workout days only.

        **Training Duration Chart**<br>
        Shows recorded training minutes for each day. Rest days remain at
        zero minutes; missing days remain missing.

        **Perceived Exertion Chart**<br>
        Shows recorded exertion for non-Rest entries on a 0–10 scale.
        Rest days remain blank, and a recorded zero stays visible as zero.

        **Study Hours Chart**<br>
        Shows recorded study hours for each day. Missing days are left as
        gaps rather than being converted to zero.

        **Week-to-week comparison**<br>
        Becomes available only when both consecutive seven-day periods
        contain all seven recorded days.
        """
    )