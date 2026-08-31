"""Streamlit dashboard for Recovery Compass v0.1."""
# Build: 2026-08-31 Rest-day invariant + reactive entry UX

from datetime import date, timedelta
from html import escape
from pathlib import Path
from tempfile import TemporaryDirectory

import altair as alt
import streamlit as st

from src.analytics import calculate_metrics, prepare_chart_data
from src.feedback import generate_feedback
from src.storage import (
    DuplicateDateError,
    StorageError,
    export_records,
    import_records,
    load_records,
    save_record,
)
from src.validation import (
    WORKOUT_TYPES,
    normalize_record,
    validate_record,
)


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
# Browser-local persistence bridge
# ---------------------------------------------------------

_BROWSER_STORAGE_COMPONENT = st.components.v2.component(
    "recovery_compass_browser_storage",
    html='<span aria-hidden="true"></span>',
    css="""
        span {
            display: none;
        }
    """,
    js="""
        export default function(component) {
            const { data, setStateValue } = component;

            const action = data?.action ?? "idle";
            const storageKey = data?.storage_key ?? "";
            const revision = data?.revision ?? null;

            try {
                if (action === "read") {
                    const value = window.localStorage.getItem(storageKey);

                    setStateValue("response", {
                        status: "read",
                        revision: revision,
                        value: value,
                    });

                    return;
                }

                if (action === "write") {
                    window.localStorage.setItem(
                        storageKey,
                        data?.payload ?? "",
                    );

                    setStateValue("response", {
                        status: "written",
                        revision: revision,
                    });

                    return;
                }

                if (action === "remove") {
                    window.localStorage.removeItem(storageKey);

                    setStateValue("response", {
                        status: "removed",
                        revision: revision,
                    });
                }
            } catch (error) {
                setStateValue("response", {
                    status: "error",
                    revision: revision,
                    message: String(
                        error?.message ?? error ?? "Unknown browser-storage error"
                    ),
                });
            }
        }
    """,
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
           Daily-entry controls
        ------------------------------------------------- */

        div[data-testid="stDateInput"] label,
        div[data-testid="stNumberInput"] label,
        div[data-testid="stSelectbox"] label,
        div[data-testid="stDateInput"] [data-testid="stWidgetLabel"] p,
        div[data-testid="stNumberInput"] [data-testid="stWidgetLabel"] p,
        div[data-testid="stSelectbox"] [data-testid="stWidgetLabel"] p {
            color: var(--rc-text) !important;
            font-weight: 650 !important;
        }

        div[data-testid="stDateInput"] [data-testid="stTooltipIcon"] svg,
        div[data-testid="stNumberInput"] [data-testid="stTooltipIcon"] svg,
        div[data-testid="stSelectbox"] [data-testid="stTooltipIcon"] svg {
            color: var(--rc-muted) !important;
            fill: var(--rc-muted) !important;
        }

        div[data-testid="stDateInput"] input,
        div[data-testid="stNumberInput"] input {
            background: #FFFFFF !important;
            color: var(--rc-text) !important;
            border-color: #D5DCE5 !important;
        }

        div[data-testid="stNumberInput"] button {
            background: #F7F9FB !important;
            color: var(--rc-muted) !important;
            border-color: #D5DCE5 !important;
        }

        div[data-testid="stNumberInput"] input:disabled {
            background: #F3F5F8 !important;
            color: #667085 !important;
            -webkit-text-fill-color: #667085 !important;
            opacity: 1 !important;
        }

        div[data-testid="stSelectbox"] [data-baseweb="select"] > div {
            background: #FFFFFF !important;
            color: var(--rc-text) !important;
            border-color: #D5DCE5 !important;
        }

        div[data-testid="stSelectbox"] [data-baseweb="select"] span {
            color: var(--rc-text) !important;
        }

        div[data-testid="stButton"]
        button[data-testid="stBaseButton-primary"] {
            background: linear-gradient(
                100deg,
                var(--rc-navy-900) 0%,
                var(--rc-teal-700) 100%
            ) !important;
            color: #FFFFFF !important;
            border: 1px solid rgba(16, 42, 67, 0.16) !important;
            border-radius: 10px !important;
            font-weight: 700 !important;
            box-shadow: 0 4px 12px rgba(16, 42, 67, 0.12) !important;
        }

        div[data-testid="stButton"]
        button[data-testid="stBaseButton-primary"]:hover {
            filter: brightness(1.04);
            border-color: rgba(16, 42, 67, 0.28) !important;
        }


        /* -------------------------------------------------
           Deterministic feedback
        ------------------------------------------------- */

        .rc-feedback-panel {
            background: #FFFFFF;
            border: 1px solid var(--rc-border);
            border-radius: 16px;
            padding: 1rem 1.15rem;
            box-shadow:
                0 1px 2px rgba(16, 24, 40, 0.02),
                0 6px 18px rgba(16, 24, 40, 0.025);
        }

        .rc-feedback-list {
            margin: 0;
            padding-left: 1.2rem;
            color: var(--rc-text);
            font-size: 0.86rem;
            line-height: 1.55;
        }

        .rc-feedback-list li {
            color: var(--rc-text);
            margin: 0.3rem 0;
        }

        /* -------------------------------------------------
           Data tools
        ------------------------------------------------- */

        .rc-data-tool-title {
            color: var(--rc-navy-950);
            font-size: 1rem;
            line-height: 1.25;
            font-weight: 750;
            margin: 0 0 0.22rem 0;
        }

        .rc-data-tool-copy {
            color: var(--rc-muted);
            font-size: 0.79rem;
            line-height: 1.45;
            margin: 0 0 0.75rem 0;
        }

        div[data-testid="stDownloadButton"] button {
            background: linear-gradient(
                100deg,
                var(--rc-navy-900) 0%,
                var(--rc-teal-700) 100%
            ) !important;
            color: #FFFFFF !important;
            border: 1px solid rgba(16, 42, 67, 0.16) !important;
            border-radius: 10px !important;
            font-weight: 700 !important;
            box-shadow: 0 4px 12px rgba(16, 42, 67, 0.10) !important;
        }

        div[data-testid="stDownloadButton"] button:hover {
            filter: brightness(1.04);
            border-color: rgba(16, 42, 67, 0.28) !important;
        }

        div[data-testid="stFileUploader"] label,
        div[data-testid="stFileUploader"] [data-testid="stWidgetLabel"] p {
            color: var(--rc-text) !important;
            font-weight: 650 !important;
        }

        div[data-testid="stFileUploaderDropzone"] {
            background: #F8FAFC !important;
            border: 1px dashed #C7D0DC !important;
            border-radius: 12px !important;
        }

        div[data-testid="stFileUploaderDropzone"] button {
            background: #FFFFFF !important;
            color: var(--rc-navy-900) !important;
            border: 1px solid #C7D0DC !important;
            border-radius: 8px !important;
            font-weight: 650 !important;
        }

        div[data-testid="stFileUploaderDropzone"] small,
        div[data-testid="stFileUploaderDropzone"] span,
        div[data-testid="stFileUploaderDropzone"] p {
            color: var(--rc-muted) !important;
        }

        div[data-testid="stButton"] button {
            background: #FFFFFF !important;
            color: var(--rc-navy-900) !important;
            border: 1px solid #BFCAD6 !important;
            border-radius: 10px !important;
            font-weight: 700 !important;
        }

        div[data-testid="stButton"] button:hover:not(:disabled) {
            background: #F6FAFB !important;
            border-color: var(--rc-teal-700) !important;
            color: var(--rc-teal-700) !important;
        }

        div[data-testid="stButton"] button:disabled {
            background: #F3F5F8 !important;
            color: #98A2B3 !important;
            border-color: #D8DEE7 !important;
            opacity: 1 !important;
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


SESSION_RECORDS_KEY = "recovery_compass_records"
BROWSER_STORAGE_KEY = "recovery_compass_v1_csv"
BROWSER_STORAGE_HYDRATED_KEY = "recovery_compass_browser_storage_hydrated"
BROWSER_STORAGE_PENDING_KEY = "recovery_compass_browser_storage_pending"
BROWSER_STORAGE_REVISION_KEY = "recovery_compass_browser_storage_revision"
BROWSER_STORAGE_ERROR_KEY = "recovery_compass_browser_storage_error"
BROWSER_STORAGE_COMPONENT_KEY = "recovery_compass_browser_storage_bridge"


def _get_session_records() -> list[dict[str, object]]:
    """Return a defensive copy of this browser session's records."""

    if SESSION_RECORDS_KEY not in st.session_state:
        st.session_state[SESSION_RECORDS_KEY] = []

    return [
        dict(record)
        for record in st.session_state[SESSION_RECORDS_KEY]
    ]


def _write_records_to_path(
    records: list[dict[str, object]],
    file_path: Path,
) -> None:
    """Materialize records through the qualified CSV storage layer."""

    for record in records:
        save_record(
            record,
            file_path=file_path,
        )


def _records_to_csv_text(
    records: list[dict[str, object]],
) -> str:
    """Serialize validated records to Recovery Compass CSV text."""

    if not records:
        return ""

    with TemporaryDirectory() as temporary_directory:
        csv_path = (
            Path(temporary_directory)
            / "browser_records.csv"
        )

        _write_records_to_path(
            records,
            csv_path,
        )

        return csv_path.read_text(
            encoding="utf-8"
        )


def _records_from_csv_text(
    csv_text: str,
) -> list[dict[str, object]]:
    """Validate browser-stored CSV text and return normalized records."""

    if not csv_text.strip():
        return []

    with TemporaryDirectory() as temporary_directory:
        csv_path = (
            Path(temporary_directory)
            / "browser_records.csv"
        )

        csv_path.write_text(
            csv_text,
            encoding="utf-8",
        )

        return load_records(
            csv_path
        )


def _queue_browser_storage_write(
    records: list[dict[str, object]],
) -> None:
    """Queue one browser-local write that must be acknowledged."""

    payload = _records_to_csv_text(
        records
    )

    revision = (
        int(
            st.session_state.get(
                BROWSER_STORAGE_REVISION_KEY,
                0,
            )
        )
        + 1
    )

    st.session_state[
        BROWSER_STORAGE_REVISION_KEY
    ] = revision

    st.session_state[
        BROWSER_STORAGE_PENDING_KEY
    ] = {
        "revision": revision,
        "payload": payload,
    }


def _set_session_records(
    records: list[dict[str, object]],
) -> None:
    """Replace records and queue persistence to this browser."""

    validated_copy = [
        dict(record)
        for record in records
    ]

    _queue_browser_storage_write(
        validated_copy
    )

    st.session_state[
        SESSION_RECORDS_KEY
    ] = validated_copy


def _mount_browser_storage_bridge(
    *,
    action: str,
    revision: int,
    payload: str | None = None,
):
    """Mount the invisible browser-local storage bridge."""

    return _BROWSER_STORAGE_COMPONENT(
        data={
            "action": action,
            "storage_key": BROWSER_STORAGE_KEY,
            "revision": revision,
            "payload": payload,
        },
        default={
            "response": None,
        },
        on_response_change=lambda: None,
        key=BROWSER_STORAGE_COMPONENT_KEY,
    )


def _sync_browser_storage() -> None:
    """Hydrate from and persist to browser localStorage safely."""

    hydrated = bool(
        st.session_state.get(
            BROWSER_STORAGE_HYDRATED_KEY,
            False,
        )
    )

    if not hydrated:
        result = _mount_browser_storage_bridge(
            action="read",
            revision=0,
        )

        response = result.response

        if not isinstance(response, dict):
            st.stop()

        status = response.get("status")

        if status == "error":
            st.session_state[
                SESSION_RECORDS_KEY
            ] = []

            st.session_state[
                BROWSER_STORAGE_ERROR_KEY
            ] = (
                "Recovery Compass could not read browser-saved data: "
                + str(
                    response.get(
                        "message",
                        "unknown browser-storage error",
                    )
                )
            )

            st.session_state[
                BROWSER_STORAGE_HYDRATED_KEY
            ] = True

            return

        if status != "read":
            st.stop()

        stored_value = response.get("value")

        try:
            if stored_value is None:
                hydrated_records = []
            elif isinstance(stored_value, str):
                hydrated_records = _records_from_csv_text(
                    stored_value
                )
            else:
                raise StorageError(
                    "Browser-saved data has an unexpected format."
                )

        except (StorageError, OSError) as error:
            st.session_state[
                SESSION_RECORDS_KEY
            ] = []

            st.session_state[
                BROWSER_STORAGE_ERROR_KEY
            ] = (
                "Recovery Compass found browser-saved data "
                f"that could not be validated: {error}"
            )

        else:
            st.session_state[
                SESSION_RECORDS_KEY
            ] = [
                dict(record)
                for record in hydrated_records
            ]

            st.session_state.pop(
                BROWSER_STORAGE_ERROR_KEY,
                None,
            )

        st.session_state[
            BROWSER_STORAGE_HYDRATED_KEY
        ] = True

    pending = st.session_state.get(
        BROWSER_STORAGE_PENDING_KEY
    )

    if not pending:
        return

    revision = int(
        pending["revision"]
    )

    result = _mount_browser_storage_bridge(
        action="write",
        revision=revision,
        payload=str(
            pending["payload"]
        ),
    )

    response = result.response

    if (
        not isinstance(response, dict)
        or response.get("revision") != revision
    ):
        st.stop()

    status = response.get("status")

    if status == "written":
        st.session_state.pop(
            BROWSER_STORAGE_PENDING_KEY,
            None,
        )

        st.session_state.pop(
            BROWSER_STORAGE_ERROR_KEY,
            None,
        )

        return

    if status == "error":
        st.session_state.pop(
            BROWSER_STORAGE_PENDING_KEY,
            None,
        )

        st.session_state[
            BROWSER_STORAGE_ERROR_KEY
        ] = (
            "Recovery Compass could not save data in this browser: "
            + str(
                response.get(
                    "message",
                    "unknown browser-storage error",
                )
            )
        )

        return

    st.stop()


def _render_browser_storage_warning() -> None:
    """Explain when browser-local persistence is unavailable."""

    error = st.session_state.get(
        BROWSER_STORAGE_ERROR_KEY
    )

    if error is None:
        return

    st.warning(
        "Browser persistence is currently unavailable. "
        "Your current session can still work, but refreshing or closing "
        "the page may clear its records. Download your data before leaving."
    )

    st.caption(
        f"Technical detail: {error}"
    )


def _save_session_record(
    record: dict[str, object],
) -> None:
    """Validate and add one record to this browser's data atomically."""

    existing_records = _get_session_records()

    with TemporaryDirectory() as temporary_directory:
        working_path = (
            Path(temporary_directory)
            / "session_records.csv"
        )

        _write_records_to_path(
            existing_records,
            working_path,
        )

        save_record(
            record,
            file_path=working_path,
        )

        updated_records = load_records(
            working_path
        )

    _set_session_records(
        updated_records
    )


def _import_session_records(
    import_path: Path,
) -> int:
    """Import a valid CSV into this browser using all-or-nothing behavior."""

    existing_records = _get_session_records()

    with TemporaryDirectory() as temporary_directory:
        working_path = (
            Path(temporary_directory)
            / "session_records.csv"
        )

        _write_records_to_path(
            existing_records,
            working_path,
        )

        count = import_records(
            import_path,
            working_path=working_path,
        )

        updated_records = load_records(
            working_path
        )

    _set_session_records(
        updated_records
    )

    return count

def _render_daily_entry() -> None:
    """Render reactive daily-entry controls and save one validated record."""

    saved_date = st.session_state.pop(
        "recovery_compass_saved_date",
        None,
    )

    if saved_date is not None:
        readable_date = date.fromisoformat(
            saved_date
        ).strftime(
            "%B %d, %Y"
        )

        st.success(
            f"Entry for {readable_date} was saved in this browser."
        )

    st.html(
        """
        <div class="rc-section-heading">
            <div>
                <div class="rc-section-kicker">
                    Daily check-in
                </div>

                <div class="rc-section-title">
                    Add Today's Entry
                </div>

                <div class="rc-section-note">
                    Log one day of training, sleep, mood, and study.
                    Recovery Compass uses these entries to build your
                    seven-day overview.
                </div>
            </div>
        </div>
        """
    )

    with st.container(border=True):

        row_one = st.columns(
            2,
            gap="medium",
        )

        with row_one[0]:
            entry_date = st.date_input(
                "Date",
                value=date.today(),
                help="Choose the day this entry describes.",
                key="recovery_compass_entry_date",
            )

        with row_one[1]:
            workout_type = st.selectbox(
                "Workout Type",
                options=list(
                    WORKOUT_TYPES.values()
                ),
                help=(
                    "Choose Rest if you did not complete "
                    "a workout that day."
                ),
                key="recovery_compass_workout_type",
            )

        is_rest_day = (
            workout_type == WORKOUT_TYPES["rest"]
        )

        row_two = st.columns(
            2,
            gap="medium",
        )

        with row_two[0]:
            if is_rest_day:
                st.number_input(
                    "Workout Duration (minutes)",
                    min_value=0,
                    max_value=300,
                    value=0,
                    step=1,
                    disabled=True,
                    help=(
                        "Rest days automatically record "
                        "0 workout minutes."
                    ),
                    key=(
                        "recovery_compass_rest_"
                        "duration_display"
                    ),
                )

                duration_minutes = 0

            else:
                duration_minutes = st.number_input(
                    "Workout Duration (minutes)",
                    min_value=0,
                    max_value=300,
                    value=None,
                    step=1,
                    placeholder="Example: 45",
                    help=(
                        "Enter the number of minutes "
                        "you trained. Maximum: 300."
                    ),
                    key="recovery_compass_duration",
                )

        with row_two[1]:
            if is_rest_day:
                st.number_input(
                    "Perceived Exertion",
                    min_value=0,
                    max_value=10,
                    value=0,
                    step=1,
                    disabled=True,
                    help=(
                        "Rest days automatically record "
                        "0 perceived exertion."
                    ),
                    key=(
                        "recovery_compass_rest_"
                        "exertion_display"
                    ),
                )

                perceived_exertion = 0

            else:
                perceived_exertion = st.number_input(
                    "Perceived Exertion",
                    min_value=0,
                    max_value=10,
                    value=None,
                    step=1,
                    placeholder="0 to 10",
                    help=(
                        "0 means no effort. "
                        "10 means maximum perceived effort."
                    ),
                    key="recovery_compass_exertion",
                )

        row_three = st.columns(
            3,
            gap="medium",
        )

        with row_three[0]:
            sleep_hours = st.number_input(
                "Sleep Hours",
                min_value=0.0,
                max_value=16.0,
                value=None,
                step=0.1,
                placeholder="Example: 7.5",
                help=(
                    "Enter the approximate number of "
                    "hours you slept."
                ),
                key="recovery_compass_sleep",
            )

        with row_three[1]:
            mood_choice = st.selectbox(
                "Mood Rating",
                options=[
                    "Not recorded",
                    "1",
                    "2",
                    "3",
                    "4",
                    "5",
                ],
                help=(
                    "Optional. 1 is the lowest rating "
                    "and 5 is the highest."
                ),
                key="recovery_compass_mood",
            )

        with row_three[2]:
            study_hours = st.number_input(
                "Study Hours",
                min_value=0.0,
                max_value=16.0,
                value=None,
                step=0.1,
                placeholder="Example: 2.0",
                help=(
                    "Enter time spent studying or doing "
                    "academic work."
                ),
                key="recovery_compass_study",
            )

        submitted = st.button(
            "Save Entry",
            type="primary",
            width="stretch",
            key="recovery_compass_save_entry",
        )

    if not submitted:
        return

    candidate_record = {
        "date": entry_date.isoformat(),
        "workout_type": workout_type,
        "duration_minutes": (
            ""
            if duration_minutes is None
            else str(duration_minutes)
        ),
        "perceived_exertion": (
            ""
            if perceived_exertion is None
            else str(perceived_exertion)
        ),
        "sleep_hours": (
            ""
            if sleep_hours is None
            else str(sleep_hours)
        ),
        "mood_rating": (
            ""
            if mood_choice == "Not recorded"
            else mood_choice
        ),
        "study_hours": (
            ""
            if study_hours is None
            else str(study_hours)
        ),
    }

    errors = validate_record(
        candidate_record
    )

    if errors:
        st.error(
            "Your entry was not saved. "
            "Please fix the items below."
        )

        for error in errors:
            st.markdown(
                f"- {error}"
            )

        return

    try:
        normalized_record = normalize_record(
            candidate_record
        )

        _save_session_record(
            normalized_record
        )

    except DuplicateDateError:
        st.error(
            "Recovery Compass already has an entry for "
            f"{entry_date.strftime('%B %d, %Y')}. "
            "Only one entry is stored for each day."
        )

        return

    except StorageError as error:
        st.error(
            "Recovery Compass could not save this entry safely. "
            "Your current browser data was not changed."
        )

        st.caption(
            f"Technical detail: {error}"
        )

        return

    st.session_state[
        "recovery_compass_saved_date"
    ] = entry_date.isoformat()

    st.rerun()


def _build_export_bytes(
    records: list[dict[str, object]],
) -> bytes:
    """Build a validated CSV export from this session's records."""

    if not records:
        raise StorageError(
            "There are no Recovery Compass records to export."
        )

    with TemporaryDirectory() as temporary_directory:
        source_path = (
            Path(temporary_directory)
            / "session_records.csv"
        )

        export_path = (
            Path(temporary_directory)
            / "recovery_compass.csv"
        )

        _write_records_to_path(
            records,
            source_path,
        )

        export_records(
            export_path,
            source_path=source_path,
        )

        return export_path.read_bytes()


def _render_data_tools(
    records: list[dict[str, object]],
) -> None:
    """Render privacy-conscious import and export controls."""

    imported_count = st.session_state.pop(
        "recovery_compass_imported_count",
        None,
    )

    if imported_count is not None:
        noun = "record" if imported_count == 1 else "records"

        st.success(
            f"Imported {imported_count} {noun} into this browser. "
            "Your dashboard has been refreshed."
        )

    st.html(
        """
        <div class="rc-section-heading">
            <div>
                <div class="rc-section-kicker">
                    Your data
                </div>

                <div class="rc-section-title">
                    Import or Download Your Records
                </div>

                <div class="rc-section-note">
                    Keep a copy of your Recovery Compass history or
                    bring a previously saved Recovery Compass data file
                    back into the app.
                </div>
            </div>
        </div>
        """
    )

    with st.container(border=True):
        download_column, import_column = st.columns(
            2,
            gap="large",
        )

        with download_column:
            st.html(
                """
                <div class="rc-data-tool-title">Download My Data</div>
                <div class="rc-data-tool-copy">
                    Save a copy of all of your current Recovery Compass
                    records as a CSV file.
                </div>
                """
            )

            if not records:
                st.info(
                    "Save your first entry before downloading your data."
                )

            else:
                try:
                    export_bytes = _build_export_bytes(records)

                except StorageError as error:
                    st.error(
                        "Recovery Compass could not prepare your data "
                        "for download."
                    )
                    st.caption(
                        f"Technical detail: {error}"
                    )

                else:
                    st.download_button(
                        "Download My Data",
                        data=export_bytes,
                        file_name="recovery_compass.csv",
                        mime="text/csv",
                        type="primary",
                        width="stretch",
                    )

        with import_column:
            st.html(
                """
                <div class="rc-data-tool-title">Import My Data</div>
                <div class="rc-data-tool-copy">
                    Choose a Recovery Compass CSV file. The entire file is
                    checked before any existing records are changed.
                </div>
                """
            )

            uploaded_file = st.file_uploader(
                "Choose a Recovery Compass CSV file",
                type=["csv"],
                accept_multiple_files=False,
                key="recovery_compass_import_file",
            )

            import_clicked = st.button(
                "Import My Data",
                type="secondary",
                width="stretch",
                disabled=uploaded_file is None,
            )

            if import_clicked and uploaded_file is not None:
                try:
                    with TemporaryDirectory() as temporary_directory:
                        import_path = (
                            Path(temporary_directory)
                            / "recovery_compass_import.csv"
                        )

                        import_path.write_bytes(
                            uploaded_file.getvalue()
                        )

                        count = _import_session_records(
                            import_path
                        )

                except DuplicateDateError as error:
                    st.error(
                        "Import was not applied because at least one date "
                        "conflicts with data already in this Recovery "
                        "Compass session. Your current session was not changed."
                    )
                    st.caption(
                        f"Technical detail: {error}"
                    )

                except StorageError as error:
                    st.error(
                        "Recovery Compass could not import this file safely. "
                        "Your current session was not changed."
                    )
                    st.caption(
                        f"Technical detail: {error}"
                    )

                except OSError as error:
                    st.error(
                        "Recovery Compass could not read the selected file. "
                        "Your current session was not changed."
                    )
                    st.caption(
                        f"Technical detail: {error}"
                    )

                else:
                    st.session_state[
                        "recovery_compass_imported_count"
                    ] = count

                    st.rerun()


# ---------------------------------------------------------
# Load browser-local data
# ---------------------------------------------------------

_sync_browser_storage()

records = _get_session_records()

_render_browser_storage_warning()


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


_render_daily_entry()

_render_data_tools(records)


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
# Deterministic feedback
# ---------------------------------------------------------

feedback_statements = generate_feedback(metrics)

st.html(
    """
    <div class="rc-section-heading">
        <div>
            <div class="rc-section-kicker">
                Weekly facts
            </div>

            <div class="rc-section-title">
                What Your Data Shows
            </div>

            <div class="rc-section-note">
                Reproducible observations calculated from your recorded data.
                Recovery Compass does not infer causes or generate a recovery
                score.
            </div>
        </div>
    </div>
    """,
)

feedback_items = "".join(
    f"<li>{escape(statement)}</li>"
    for statement in feedback_statements
)

st.html(
    f"""
    <div class="rc-feedback-panel">
        <ul class="rc-feedback-list">
            {feedback_items}
        </ul>
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
**Coverage**
The number of recorded days in the current seven-calendar-day period.

**Workout Days**
Counts only days with a non-Rest workout and more than zero training minutes.

**Average Sleep**
Uses sleep values from the recorded days in the current period.

**Average Mood**
Uses only days where a mood rating was actually entered. Missing mood ratings
are never treated as zero.

**Average Study**
Uses study hours from the recorded days in the current period.

**Average Exertion**
Uses perceived exertion from actual workout days only.

**Training Duration Chart**
Shows recorded training minutes for each day. Rest days remain at zero minutes;
missing days remain missing.

**Perceived Exertion Chart**
Shows recorded exertion for non-Rest entries on a 0–10 scale. Rest days remain
blank, and a recorded zero stays visible as zero.

**Study Hours Chart**
Shows recorded study hours for each day. Missing days are left as gaps rather
than being converted to zero.

**Week-to-week comparison**
Becomes available only when both consecutive seven-day periods contain all
seven recorded days.
        """
    )
