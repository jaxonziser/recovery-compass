"""Recovery Compass V10.0.14 guided-tour viewport-finish candidate."""
# Build: 2026-09-03 V10.0.11 one-time browser-local onboarding from V10.0.10

from datetime import date, timedelta
import base64
from html import escape
from pathlib import Path
from tempfile import TemporaryDirectory

import altair as alt
import streamlit as st
from PIL import Image

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

ASSET_DIR = Path(__file__).resolve().parent / "assets"
BRAND_MARK_PATH = ASSET_DIR / "recovery_compass_mark.png"
PAGE_ICON = Image.open(BRAND_MARK_PATH)
BRAND_IMAGE_URI = "data:image/png;base64," + base64.b64encode(BRAND_MARK_PATH.read_bytes()).decode("ascii")

st.set_page_config(
    page_title="Recovery Compass",
    page_icon=PAGE_ICON,
    layout="wide",
    initial_sidebar_state="expanded",
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
# V9.0.3 appearance state machine + interaction architecture
# ---------------------------------------------------------

THEME_PREFERENCE_STORAGE_KEY = "recovery_compass.appearance.v9"
THEME_PREFERENCE_SESSION_KEY = "recovery_compass_theme_preference_v9"
THEME_DESKTOP_WIDGET_KEY = "recovery_compass_theme_desktop_v9"
THEME_MOBILE_WIDGET_KEY = "recovery_compass_theme_mobile_v9"
THEME_HYDRATED_KEY = "recovery_compass_theme_hydrated_v9_0_2"
THEME_SYSTEM_DARK_KEY = "recovery_compass_theme_system_dark_v9_0_2"
THEME_PENDING_WRITE_KEY = "recovery_compass_theme_pending_write_v9_0_2"
THEME_WRITE_REVISION_KEY = "recovery_compass_theme_write_revision_v9_0_2"
THEME_PREFERENCES = ("light", "system", "dark")
THEME_LABELS = {
    "light": "Light",
    "system": "System",
    "dark": "Dark",
}
THEME_CODES = {label: code for code, label in THEME_LABELS.items()}

_THEME_PREFERENCE_COMPONENT = st.components.v2.component(
    "recovery_compass_theme_preference_v9_0_2",
    html='<span aria-hidden="true"></span>',
    css="""
        span {
            display: none;
        }
    """,
    js="""
        export default function(component) {
            const { data, setStateValue } = component;
            const storageKey = data?.storage_key ?? "recovery_compass.appearance.v9";
            const action = data?.action ?? "read";
            const preference = data?.preference ?? null;
            const revision = data?.revision ?? 0;
            const allowed = new Set(["light", "system", "dark"]);
            const media = window.matchMedia?.("(prefers-color-scheme: dark)");

            try {
                if (action === "read") {
                    const stored = window.localStorage.getItem(storageKey);
                    setStateValue("response", {
                        status: "read",
                        preference: allowed.has(stored) ? stored : "system",
                        system_is_dark: Boolean(media?.matches),
                        revision: revision,
                    });
                    return;
                }

                if (action === "write") {
                    if (allowed.has(preference)) {
                        window.localStorage.setItem(storageKey, preference);
                    }
                    // Deliberately do not publish a response here. A theme click
                    // already causes exactly one Streamlit rerun. Publishing an
                    // acknowledgement caused the V9 rerun/flicker feedback loop.
                    return;
                }

                if (action === "watch-system") {
                    const onSystemChange = (event) => {
                        setStateValue("response", {
                            status: "system-change",
                            system_is_dark: Boolean(event?.matches),
                            revision: Date.now(),
                        });
                    };

                    media?.addEventListener?.("change", onSystemChange);
                    return () => {
                        media?.removeEventListener?.("change", onSystemChange);
                    };
                }
            } catch (error) {
                if (action !== "write") {
                    setStateValue("response", {
                        status: "error",
                        message: String(error?.message ?? error ?? "Unknown appearance error"),
                        revision: revision,
                    });
                }
            }
        }
    """,
)


def _mount_theme_preference_bridge(
    *,
    action: str,
    key: str,
    preference: str | None = None,
    revision: int = 0,
    reactive: bool = False,
):
    """Read, persist, or watch the browser appearance preference without loops."""

    kwargs = {
        "data": {
            "storage_key": THEME_PREFERENCE_STORAGE_KEY,
            "action": action,
            "preference": preference,
            "revision": revision,
        },
        "key": key,
    }

    # Streamlit Components V2 only permits a key in `default` when the
    # corresponding on_<state>_change callback is registered. Read/watch calls
    # publish `response`, so they own that state. Fire-and-forget writes publish
    # nothing and therefore must not declare a `response` default at all.
    if reactive:
        kwargs["default"] = {"response": None}
        kwargs["on_response_change"] = lambda: None

    return _THEME_PREFERENCE_COMPONENT(**kwargs)


try:
    _native_theme_fallback = st.context.theme.type
except Exception:
    _native_theme_fallback = "light"

# Hydrate the browser preference once per Streamlit session. V9's original
# bridge published on every render, which could recursively rerun the app while
# Light/System/Dark were changing. This read-once state machine removes that
# feedback path entirely.
if not bool(st.session_state.get(THEME_HYDRATED_KEY, False)):
    _theme_read_result = _mount_theme_preference_bridge(
        action="read",
        key="recovery_compass_theme_read_v9_0_2",
        reactive=True,
    )
    _theme_read_response = getattr(_theme_read_result, "response", None)

    if not isinstance(_theme_read_response, dict):
        st.stop()

    _theme_read_status = _theme_read_response.get("status")
    if _theme_read_status == "read":
        _hydrated_preference = _theme_read_response.get("preference")
        if _hydrated_preference not in THEME_PREFERENCES:
            _hydrated_preference = "system"
        _hydrated_system_dark = bool(
            _theme_read_response.get(
                "system_is_dark",
                _native_theme_fallback == "dark",
            )
        )
    elif _theme_read_status == "error":
        _hydrated_preference = "system"
        _hydrated_system_dark = _native_theme_fallback == "dark"
    else:
        st.stop()

    st.session_state[THEME_PREFERENCE_SESSION_KEY] = _hydrated_preference
    st.session_state[THEME_SYSTEM_DARK_KEY] = _hydrated_system_dark
    st.session_state[THEME_HYDRATED_KEY] = True
    st.rerun()

RC_THEME_PREFERENCE = st.session_state.get(
    THEME_PREFERENCE_SESSION_KEY,
    "system",
)
if RC_THEME_PREFERENCE not in THEME_PREFERENCES:
    RC_THEME_PREFERENCE = "system"
    st.session_state[THEME_PREFERENCE_SESSION_KEY] = RC_THEME_PREFERENCE

_system_is_dark = bool(
    st.session_state.get(
        THEME_SYSTEM_DARK_KEY,
        _native_theme_fallback == "dark",
    )
)

# Theme writes are fire-and-forget. The UI reruns once because the segmented
# control changed, then this hidden component only persists the preference. It
# never acknowledges the write back into Streamlit, eliminating the flicker.
_pending_theme_write = st.session_state.pop(THEME_PENDING_WRITE_KEY, None)
if _pending_theme_write in THEME_PREFERENCES:
    _write_revision = int(
        st.session_state.get(THEME_WRITE_REVISION_KEY, 0)
    ) + 1
    st.session_state[THEME_WRITE_REVISION_KEY] = _write_revision
    _mount_theme_preference_bridge(
        action="write",
        preference=_pending_theme_write,
        revision=_write_revision,
        key=f"recovery_compass_theme_write_v9_0_2_{_write_revision}",
        reactive=False,
    )

# System mode listens for OS/browser preference changes while the app remains
# open. Unlike V9's original bridge, this watcher publishes only when the media
# query actually changes.
if RC_THEME_PREFERENCE == "system":
    _system_watch_result = _mount_theme_preference_bridge(
        action="watch-system",
        key="recovery_compass_theme_system_watch_v9_0_2",
        reactive=True,
    )
    _system_watch_response = getattr(_system_watch_result, "response", None)
    if (
        isinstance(_system_watch_response, dict)
        and _system_watch_response.get("status") == "system-change"
        and isinstance(_system_watch_response.get("system_is_dark"), bool)
    ):
        _new_system_is_dark = _system_watch_response["system_is_dark"]
        if _new_system_is_dark != _system_is_dark:
            st.session_state[THEME_SYSTEM_DARK_KEY] = _new_system_is_dark
            st.rerun()

if RC_THEME_PREFERENCE == "system":
    RC_THEME_TYPE = "dark" if _system_is_dark else "light"
else:
    RC_THEME_TYPE = RC_THEME_PREFERENCE

RC_IS_DARK = RC_THEME_TYPE == "dark"


# ---------------------------------------------------------
# V10.0.11 first-visit quick-tour persistence
# ---------------------------------------------------------

QUICK_TOUR_STORAGE_KEY = "recovery_compass.quick_tour.v1"
QUICK_TOUR_HYDRATED_KEY = "recovery_compass_quick_tour_hydrated_v1"
QUICK_TOUR_SEEN_KEY = "recovery_compass_quick_tour_seen_v1"
QUICK_TOUR_ACTIVE_KEY = "recovery_compass_quick_tour_active_v1"
QUICK_TOUR_STEP_KEY = "recovery_compass_quick_tour_step_v1"
QUICK_TOUR_PENDING_WRITE_KEY = "recovery_compass_quick_tour_pending_write_v1"
QUICK_TOUR_WRITE_REVISION_KEY = "recovery_compass_quick_tour_write_revision_v1"
QUICK_TOUR_STEP_COUNT = 4

_QUICK_TOUR_PREFERENCE_COMPONENT = st.components.v2.component(
    "recovery_compass_quick_tour_preference_v1",
    html='<span aria-hidden="true"></span>',
    css="""
        span {
            display: none;
        }
    """,
    js="""
        export default function(component) {
            const { data, setStateValue } = component;
            const storageKey = data?.storage_key ?? "recovery_compass.quick_tour.v1";
            const action = data?.action ?? "read";
            const revision = data?.revision ?? 0;

            try {
                if (action === "read") {
                    const stored = window.localStorage.getItem(storageKey);
                    setStateValue("response", {
                        status: "read",
                        complete: stored === "complete",
                        revision: revision,
                    });
                    return;
                }

                if (action === "write-complete") {
                    window.localStorage.setItem(storageKey, "complete");
                    // Fire-and-forget. The button click already reran Streamlit,
                    // so publishing an acknowledgement would add a needless rerun.
                    return;
                }
            } catch (error) {
                if (action === "read") {
                    setStateValue("response", {
                        status: "error",
                        message: String(error?.message ?? error ?? "Unknown quick-tour storage error"),
                        revision: revision,
                    });
                }
            }
        }
    """,
)


def _mount_quick_tour_preference_bridge(
    *,
    action: str,
    key: str,
    revision: int = 0,
    reactive: bool = False,
):
    """Read or persist the one-time quick-tour completion flag without rerun loops."""

    kwargs = {
        "data": {
            "storage_key": QUICK_TOUR_STORAGE_KEY,
            "action": action,
            "revision": revision,
        },
        "key": key,
    }

    if reactive:
        kwargs["default"] = {"response": None}
        kwargs["on_response_change"] = lambda: None

    return _QUICK_TOUR_PREFERENCE_COMPONENT(**kwargs)


if not bool(st.session_state.get(QUICK_TOUR_HYDRATED_KEY, False)):
    _quick_tour_read_result = _mount_quick_tour_preference_bridge(
        action="read",
        key="recovery_compass_quick_tour_read_v1",
        reactive=True,
    )
    _quick_tour_read_response = getattr(_quick_tour_read_result, "response", None)

    if not isinstance(_quick_tour_read_response, dict):
        st.stop()

    _quick_tour_read_status = _quick_tour_read_response.get("status")
    if _quick_tour_read_status == "read":
        _quick_tour_seen = bool(_quick_tour_read_response.get("complete", False))
    elif _quick_tour_read_status == "error":
        # If localStorage is unavailable, keep onboarding functional for the
        # current session. The existing storage warning still handles the
        # broader persistence limitation.
        _quick_tour_seen = False
    else:
        st.stop()

    st.session_state[QUICK_TOUR_SEEN_KEY] = _quick_tour_seen
    st.session_state[QUICK_TOUR_ACTIVE_KEY] = not _quick_tour_seen
    st.session_state[QUICK_TOUR_STEP_KEY] = 0
    st.session_state[QUICK_TOUR_HYDRATED_KEY] = True
    st.rerun()

_pending_quick_tour_write = st.session_state.pop(
    QUICK_TOUR_PENDING_WRITE_KEY,
    False,
)
if _pending_quick_tour_write:
    _quick_tour_write_revision = int(
        st.session_state.get(QUICK_TOUR_WRITE_REVISION_KEY, 0)
    ) + 1
    st.session_state[QUICK_TOUR_WRITE_REVISION_KEY] = _quick_tour_write_revision
    _mount_quick_tour_preference_bridge(
        action="write-complete",
        revision=_quick_tour_write_revision,
        key=f"recovery_compass_quick_tour_write_v1_{_quick_tour_write_revision}",
        reactive=False,
    )

if RC_IS_DARK:
    RC_BG = "#08111F"
    RC_SURFACE = "#101C2C"
    RC_SURFACE_2 = "#142235"
    RC_TEXT = "#F5F8FC"
    RC_MUTED = "#AEBCCD"
    RC_BORDER = "#293A50"
    RC_BORDER_STRONG = "#39516A"
    RC_BRAND_SOFT = "#12383C"
    RC_SLEEP_SOFT = "#182442"
    RC_TRAINING_SOFT = "#102D3E"
    RC_MOOD_SOFT = "#342817"
    RC_STUDY_SOFT = "#173229"
    RC_BACKUP_SOFT = "#10343A"
    RC_AMBIENT_1 = "rgba(34, 173, 177, 0.11)"
    RC_AMBIENT_2 = "rgba(125, 150, 255, 0.055)"
    RC_SHADOW_SM = "0 12px 28px rgba(0,0,0,.18)"
    RC_SHADOW_HOVER = "0 18px 36px rgba(0,0,0,.24)"
    RC_CHART_BG = "#0C1522"
    RC_CHART_GRID = "#263449"
    RC_CHART_TEXT = "#B9C5D3"
    RC_CHART_DOMAIN = "#35465D"
    RC_CHART_TITLE = "#F5F8FC"
    RC_CHART_SUBTITLE = "#9EADBD"
else:
    RC_BG = "#F4F7FB"
    RC_SURFACE = "#FFFFFF"
    RC_SURFACE_2 = "#F7FAFC"
    RC_TEXT = "#102A43"
    RC_MUTED = "#667085"
    RC_BORDER = "#DFE6EE"
    RC_BORDER_STRONG = "#C8D4E1"
    RC_BRAND_SOFT = "#E9F8F6"
    RC_SLEEP_SOFT = "#F1F2FF"
    RC_TRAINING_SOFT = "#EBF8FD"
    RC_MOOD_SOFT = "#FFF7E8"
    RC_STUDY_SOFT = "#EEF8F3"
    RC_BACKUP_SOFT = "#EAF8F8"
    RC_AMBIENT_1 = "rgba(42, 157, 159, 0.10)"
    RC_AMBIENT_2 = "rgba(83, 103, 165, 0.045)"
    RC_SHADOW_SM = "0 14px 34px rgba(16,42,67,.075)"
    RC_SHADOW_HOVER = "0 20px 42px rgba(16,42,67,.12)"
    RC_CHART_BG = "#FFFFFF"
    RC_CHART_GRID = "#E7EDF3"
    RC_CHART_TEXT = "#64748B"
    RC_CHART_DOMAIN = "#CFD9E5"
    RC_CHART_TITLE = "#102A43"
    RC_CHART_SUBTITLE = "#718096"

RC_BRAND = "#15939A"
RC_SLEEP = "#7184E8"
RC_TRAINING = "#39A9D2"
RC_MOOD = "#D99A28"
RC_STUDY = "#62A88D"
RC_BACKUP = "#29A9AE"

_design_css = (ASSET_DIR / "recovery_compass.css").read_text(encoding="utf-8")
st.html(
    f"""
    <style>
        :root {{
            --rc-bg: {RC_BG};
            --rc-surface: {RC_SURFACE};
            --rc-surface-2: {RC_SURFACE_2};
            --rc-text: {RC_TEXT};
            --rc-muted: {RC_MUTED};
            --rc-border: {RC_BORDER};
            --rc-border-strong: {RC_BORDER_STRONG};
            --rc-brand: {RC_BRAND};
            --rc-brand-soft: {RC_BRAND_SOFT};
            --rc-sleep: {RC_SLEEP};
            --rc-training: {RC_TRAINING};
            --rc-mood: {RC_MOOD};
            --rc-study: {RC_STUDY};
            --rc-backup: {RC_BACKUP};
            --rc-sleep-soft: {RC_SLEEP_SOFT};
            --rc-training-soft: {RC_TRAINING_SOFT};
            --rc-mood-soft: {RC_MOOD_SOFT};
            --rc-study-soft: {RC_STUDY_SOFT};
            --rc-backup-soft: {RC_BACKUP_SOFT};
            --rc-ambient-1: {RC_AMBIENT_1};
            --rc-ambient-2: {RC_AMBIENT_2};
            --rc-shadow-sm: {RC_SHADOW_SM};
            --rc-shadow-hover: {RC_SHADOW_HOVER};
        }}
    </style>
    <style>{_design_css}</style>
    """
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


def _valid_workout_exertion(value: object) -> bool:
    """Return True when a Workout-day exertion value is an integer from 1 to 10."""
    if value is None:
        return False

    try:
        number = int(value)
    except (TypeError, ValueError):
        return False

    return 1 <= number <= 10


BRAND_SVG = f'<img class="rc-brand-symbol" src="{BRAND_IMAGE_URI}" alt="" aria-hidden="true">'


def _icon_svg(name: str, size: int = 22) -> str:
    """Return a CSS-mask icon that survives Streamlit HTML sanitization."""
    safe_name = name if name in {
        "home", "log", "insights", "backup", "help", "moon", "training",
        "mood", "study", "browser", "file", "device", "arrow", "check",
        "calendar", "gauge", "download", "restore", "info",
    } else "info"
    return (
        f'<span class="rc-icon rc-icon-{safe_name}" aria-hidden="true" '
        f'style="--rc-icon-size:{int(size)}px"></span>'
    )


QUICK_TOUR_STAGES = (
    {
        "nav": "Week",
        "eyebrow": "Your week, clearly",
        "title": "See the whole week without a score.",
        "copy": (
            "Recovery Compass turns the days you actually record into one seven-day "
            "picture of Sleep, Training, optional Mood, and Study. It keeps missing "
            "days visible instead of filling the gaps for you."
        ),
        "visual": "week",
        "accent": "brand",
        "callouts": ("Missing stays missing", "Four clear domains", "No recovery score"),
    },
    {
        "nav": "Log",
        "eyebrow": "A check-in that adapts",
        "title": "Record a day in about a minute.",
        "copy": (
            "Choose Rest day or Workout day, then enter only what applies. Sleep and "
            "Study are required, Mood is optional, and the live review shows exactly "
            "what will be saved before you commit it."
        ),
        "visual": "log",
        "accent": "training",
        "callouts": ("Rest hides training fields", "Mood is optional", "Review before save"),
    },
    {
        "nav": "Insights",
        "eyebrow": "Overview first, detail second",
        "title": "Go deeper only when you want to.",
        "copy": (
            "Home keeps the essentials compact. Insights separates Sleep & Mood, "
            "Training, Study, recent records, and factual previous-period comparisons "
            "once two complete seven-day periods exist."
        ),
        "visual": "insights",
        "accent": "sleep",
        "callouts": ("Exact values on hover", "Facts only", "Complete weeks compare"),
    },
    {
        "nav": "Backup",
        "eyebrow": "Private and portable",
        "title": "You’re ready. Your records stay with you.",
        "copy": (
            "Recovery Compass stores records in this browser/profile. Download one "
            "portable backup when you want a copy, then restore it in another browser "
            "or device when you want to move your history."
        ),
        "visual": "backup",
        "accent": "backup",
        "callouts": ("Stored in this browser", "No account required", "Backup moves your history"),
    },
)


def _quick_tour_title_html() -> str:
    """Render the dedicated first-launch title above the guided tour."""
    return f"""
        <header class="rc-tour-welcome" aria-label="Recovery Compass guided tour introduction">
            <div class="rc-tour-welcome-copy">
                <div class="rc-tour-welcome-eyebrow">Guided tour</div>
                <div class="rc-tour-welcome-title">Welcome to Recovery Compass.</div>
                <div class="rc-tour-welcome-subtitle">Four quick stops show you the same Home, Log, Insights, and Backup experience you are about to use. About 30 seconds. Skip anytime.</div>
            </div>
            <div class="rc-tour-welcome-mark" aria-hidden="true">
                <div class="rc-tour-welcome-orbit"><i></i><i></i><i></i><i></i><i></i><i></i><i></i><span>{BRAND_SVG}</span></div>
                <small>V1.0 QUICK START</small>
            </div>
        </header>
    """


def _tour_demo_records(start_date: str) -> list[dict[str, object]]:
    """Return a small synthetic week used only inside static tour previews."""
    dates = _period_dates(start_date)
    specs = {
        0: ("Rest", 0, 0, 7.5, 4, 2.0),
        2: ("Strength", 45, 6, 8.0, 4, 3.0),
        3: ("Rest", 0, 0, 7.0, 3, 1.5),
        5: ("Cardio", 35, 7, 7.8, 4, 2.0),
    }
    records = []
    for index, values in specs.items():
        workout_type, minutes, effort, sleep, mood, study = values
        records.append(
            {
                "date": dates[index].isoformat(),
                "workout_type": workout_type,
                "duration_minutes": minutes,
                "perceived_exertion": effort,
                "sleep_hours": sleep,
                "mood_rating": mood,
                "study_hours": study,
            }
        )
    return records


def _tour_ui_input(value: str, *, domain: str = "neutral") -> str:
    """Return a static miniature of the qualified Recovery Compass number input."""
    return (
        f'<div class="rc-tour-ui-input {escape(domain)}">'
        f'<span>{escape(value)}</span><b>−</b><b>+</b></div>'
    )


def _quick_tour_visual_html(visual: str) -> str:
    """Return a faithful miniature of the actual Recovery Compass destination."""
    demo_start = current["start_date"] if "current" in globals() else (date.today() - timedelta(days=6)).isoformat()
    demo_records = _tour_demo_records(demo_start)
    demo_label = _format_date_range(demo_start, _period_dates(demo_start)[-1].isoformat())

    if visual == "week":
        spark_days = [d.strftime("%a")[:1] for d in _period_dates(demo_start)]
        sleep_spark = [7.5, None, 8.0, 7.0, None, 7.8, None]
        training_spark = [0, None, 45, 0, None, 35, None]
        mood_spark = [4, None, 4, 3, None, 4, None]
        study_spark = [2.0, None, 3.0, 1.5, None, 2.0, None]
        return f"""
            <div class="rc-tour-faithful-screen rc-tour-faithful-home" aria-hidden="true">
                <div class="rc-tour-screen-label"><span>HOME</span><small>What you see after the tour</small></div>
                <div class="rc-home-hero rc-tour-home-hero">
                    <div class="rc-hero-content">
                        <div class="rc-hero-brand-mini">{_icon_svg('insights',16)} Your current week</div>
                        <div class="rc-home-title">See the week<br>clearly.</div>
                        <div class="rc-home-copy">A calm, factual picture of sleep, training, mood, and study.</div>
                        <div class="rc-home-meta">
                            <span class="rc-home-pill"><span class="rc-home-pill-dot"></span>{escape(demo_label)}</span>
                            <span class="rc-home-pill">4 of 7 days recorded</span>
                            <span class="rc-home-pill">Saved in this browser</span>
                        </div>
                    </div>
                    <div class="rc-compass-wrap">{_week_compass_html(demo_records, demo_start, 4)}</div>
                </div>
                <div class="rc-tour-mini-section-heading"><b>Four parts of your week</b><span>The same four colors continue throughout the app.</span></div>
                <div class="rc-domain-grid rc-tour-home-domains">
                    {_domain_card_html('sleep','moon','Sleep','7.6 hr','4 of 7 days recorded',sleep_spark,spark_days)}
                    {_domain_card_html('training','training','Training','40 min','2 workout days · 80 min total',training_spark,spark_days)}
                    {_domain_card_html('mood','mood','Mood','3.8 / 5','4 mood ratings',mood_spark,spark_days)}
                    {_domain_card_html('study','study','Study','2.1 hr','4 of 7 days recorded',study_spark,spark_days)}
                </div>
            </div>
        """

    if visual == "log":
        workout_choices = ''.join(
            f'<span class="{"active" if choice == "Strength" else ""}">{choice}</span>'
            for choice in ("Strength", "Cardio", "Sport", "Mobility", "Other")
        )
        mood_choices = ''.join(
            f'<span class="{"active" if choice == "4 Good" else ""}">{choice}</span>'
            for choice in ("Skip", "1 Very low", "2 Low", "3 Okay", "4 Good", "5 Great")
        )
        return f"""
            <div class="rc-tour-faithful-screen rc-tour-faithful-log" aria-hidden="true">
                <div class="rc-tour-screen-label"><span>LOG A DAY</span><small>The same three-step check-in you will use</small></div>
                <div class="rc-log-intro-pills">
                    <span class="rc-soft-pill">{_icon_svg('calendar',13)} About 1 minute</span>
                    <span class="rc-soft-pill">{_icon_svg('check',13)} 3 guided steps</span>
                </div>
                <div class="rc-stepper rc-tour-real-stepper">
                    <div class="rc-step complete"><div class="rc-step-bubble">✓</div><div class="rc-step-name">Choose the day</div><div class="rc-step-caption">Date and day type</div></div>
                    <div class="rc-step complete"><div class="rc-step-bubble">2</div><div class="rc-step-name">Add details</div><div class="rc-step-caption">Only what matters</div></div>
                    <div class="rc-step active"><div class="rc-step-bubble">3</div><div class="rc-step-name">Review & save</div><div class="rc-step-caption">Check before saving</div></div>
                </div>
                <div class="rc-tour-log-layout">
                    <div class="rc-tour-log-form">
                        <div class="rc-log-section-title"><span class="rc-log-step">1</span>Choose the day</div>
                        <div class="rc-tour-date-kind">
                            <div><small>Date</small><div class="rc-tour-date-box">{date.today().strftime('%Y/%m/%d')}</div></div>
                            <div><small>Did you work out?</small><div class="rc-tour-radio"><span>○ Rest day</span><b>● Workout day</b></div></div>
                        </div>
                        <div class="rc-log-divider"></div>
                        <div class="rc-log-section-title"><span class="rc-log-step">2</span>Add the details</div>
                        <div class="rc-domain-field-header rc-tour-training-head"><div class="rc-domain-field-icon training">{_icon_svg('training',15)}</div><div class="rc-domain-field-title">Training</div></div>
                        <small class="rc-tour-field-caption">Workout type</small>
                        <div class="rc-tour-choice-row training">{workout_choices}</div>
                        <div class="rc-tour-input-pair">
                            <div><small>Workout minutes</small>{_tour_ui_input('Example: 45', domain='training')}</div>
                            <div><small>How hard did it feel?</small>{_tour_ui_input('1 to 10', domain='training')}</div>
                        </div>
                        <div class="rc-log-subsection-title rc-tour-rest-title">The rest of your day</div>
                        <div class="rc-tour-daily-three">
                            <div><div class="rc-domain-field-header"><div class="rc-domain-field-icon sleep">{_icon_svg('moon',14)}</div><div class="rc-domain-field-title">Sleep</div></div><small>Previous night</small>{_tour_ui_input('Example: 7.5', domain='sleep')}</div>
                            <div><div class="rc-domain-field-header"><div class="rc-domain-field-icon mood">{_icon_svg('mood',14)}</div><div class="rc-domain-field-title">Mood</div></div><div class="rc-tour-mood-grid">{mood_choices}</div></div>
                            <div><div class="rc-domain-field-header"><div class="rc-domain-field-icon study">{_icon_svg('study',14)}</div><div class="rc-domain-field-title">Study</div></div>{_tour_ui_input('Example: 2.0', domain='study')}</div>
                        </div>
                    </div>
                    <div class="rc-live-preview ready rc-tour-live-preview">
                        <div class="rc-live-preview-kicker">Live review</div>
                        <div class="rc-live-preview-title">Today&apos;s entry</div>
                        <div class="rc-preview-row"><span class="rc-preview-icon calendar">{_icon_svg('calendar',15)}</span><div><div class="rc-preview-label">Date</div><div class="rc-preview-value">{date.today().strftime('%b %d, %Y')}</div></div></div>
                        <div class="rc-preview-row"><span class="rc-preview-icon training">{_icon_svg('training',15)}</span><div><div class="rc-preview-label">Day</div><div class="rc-preview-value">Strength · 45 min · effort 6/10</div></div></div>
                        <div class="rc-preview-row"><span class="rc-preview-icon sleep">{_icon_svg('moon',15)}</span><div><div class="rc-preview-label">Sleep</div><div class="rc-preview-value">7.5 hr</div></div></div>
                        <div class="rc-preview-row"><span class="rc-preview-icon mood">{_icon_svg('mood',15)}</span><div><div class="rc-preview-label">Mood</div><div class="rc-preview-value">4 — Good</div></div></div>
                        <div class="rc-preview-row"><span class="rc-preview-icon study">{_icon_svg('study',15)}</span><div><div class="rc-preview-label">Study</div><div class="rc-preview-value">2.0 hr</div></div></div>
                        <div class="rc-preview-ready">Ready to save</div>
                    </div>
                </div>
            </div>
        """

    if visual == "insights":
        return f"""
            <div class="rc-tour-faithful-screen rc-tour-faithful-insights" aria-hidden="true">
                <div class="rc-tour-screen-label"><span>INSIGHTS</span><small>The real overview structure, scaled down</small></div>
                <div class="rc-tour-real-tabs"><strong>Overview</strong><span>Sleep & Mood</span><span>Training</span><span>Study</span><span>Recent Records</span></div>
                <div class="rc-tour-insight-instrument">
                    <div class="rc-tour-mini-section-heading"><b>Your week, domain by domain</b><span>Values appear only where you recorded them.</span></div>
                    {_week_matrix_html(demo_records, demo_start)}
                </div>
                <div class="rc-insight-overview rc-tour-insight-cards">
                    <div class="rc-insight-card" style="--accent:var(--rc-training)"><div class="rc-insight-card-label">Workout days</div><div class="rc-insight-card-value">2</div><div class="rc-insight-card-note">Days with actual training</div></div>
                    <div class="rc-insight-card" style="--accent:var(--rc-brand)"><div class="rc-insight-card-label">Training</div><div class="rc-insight-card-value">80 min</div><div class="rc-insight-card-note">Total workout time</div></div>
                    <div class="rc-insight-card" style="--accent:#8A98AA"><div class="rc-insight-card-label">Avg exertion</div><div class="rc-insight-card-value">6.5 /10</div><div class="rc-insight-card-note">Workout days only</div></div>
                    <div class="rc-insight-card" style="--accent:var(--rc-mood)"><div class="rc-insight-card-label">Mood entries</div><div class="rc-insight-card-value">4</div><div class="rc-insight-card-note">Mood is optional</div></div>
                </div>
                <div class="rc-tour-real-comparison">{_icon_svg('info',15)} Previous-week comparison unlocks after two complete 7-of-7 periods.</div>
            </div>
        """

    return f"""
        <div class="rc-tour-faithful-screen rc-tour-faithful-backup" aria-hidden="true">
            <div class="rc-tour-screen-label"><span>DATA &amp; BACKUP</span><small>The same portability flow you will see in the app</small></div>
            <div class="rc-flow rc-tour-real-flow">
                <div class="rc-flow-node"><div class="rc-flow-icon">{_icon_svg('browser',24)}</div><div class="rc-flow-title">This browser</div><div class="rc-flow-copy">Your active Recovery Compass history lives here.</div></div>
                <div class="rc-flow-arrow">{_icon_svg('arrow',22)}</div>
                <div class="rc-flow-node"><div class="rc-flow-icon">{_icon_svg('file',24)}</div><div class="rc-flow-title">Backup file</div><div class="rc-flow-copy">A portable copy you download and keep yourself.</div></div>
                <div class="rc-flow-arrow">{_icon_svg('arrow',22)}</div>
                <div class="rc-flow-node"><div class="rc-flow-icon">{_icon_svg('device',24)}</div><div class="rc-flow-title">Another browser or device</div><div class="rc-flow-copy">Restore the backup there when you want to move your history.</div></div>
            </div>
            <div class="rc-tour-backup-heading"><small>BACKUP &amp; TRANSFER</small><b>Keep a portable copy</b><span>Download one file when you want a backup. Restore only when you want its records added here.</span></div>
            <div class="rc-tour-backup-tools">
                <div><div class="rc-data-tool-title">{_icon_svg('download',18)} Download a backup</div><div class="rc-data-tool-copy">Saves all current records into one portable CSV backup.</div><span class="rc-tour-primary-button">{_icon_svg('download',14)} Download backup</span></div>
                <div><div class="rc-data-tool-title">{_icon_svg('restore',18)} Restore a backup</div><div class="rc-data-tool-copy">Choose a Recovery Compass backup. The whole file is checked first.</div><span class="rc-tour-upload-box">{_icon_svg('file',14)} Upload</span><span class="rc-tour-disabled-button">{_icon_svg('restore',14)} Restore backup</span></div>
            </div>
            <div class="rc-transfer-note rc-tour-real-transfer-note"><span class="rc-transfer-note-dot"></span><div><strong>Nothing is uploaded to a Recovery Compass account.</strong> v1.0 has no account or cloud database.</div></div>
        </div>
    """


def _quick_tour_html(step: int) -> str:
    """Render the current stage of the dedicated first-launch product tour."""

    safe_step = max(0, min(int(step), QUICK_TOUR_STEP_COUNT - 1))
    stage = QUICK_TOUR_STAGES[safe_step]
    rail_parts = []
    for index, item in enumerate(QUICK_TOUR_STAGES):
        status_class = "done" if index < safe_step else "current" if index == safe_step else ""
        status_text = "Done" if index < safe_step else "Now" if index == safe_step else "Next"
        marker = _icon_svg("check", 13) if index < safe_step else str(index + 1)
        rail_parts.append(
            f'<div class="rc-tour-stage {status_class}">'
            f'<span>{marker}</span>'
            f'<div><b>{escape(item["nav"])}</b><small>{status_text}</small></div>'
            '</div>'
        )
    rail = "".join(rail_parts)
    callouts = "".join(
        f'<span>{_icon_svg("check",13)} {escape(callout)}</span>'
        for callout in stage["callouts"]
    )

    return f"""
        <section class="rc-guided-tour rc-guided-tour-v13 rc-guided-tour-v14 {stage['accent']}" role="region" aria-label="Recovery Compass guided quick tour">
            <div class="rc-tour-card-head"><span>Recovery Compass · Guided Tour</span><b>Step {safe_step + 1} of {QUICK_TOUR_STEP_COUNT}</b></div>
            <div class="rc-tour-stage-rail">{rail}</div>
            <div class="rc-tour-main-grid">
                <div class="rc-tour-message">
                    <div class="rc-tour-eyebrow">{escape(stage['eyebrow'])}</div>
                    <div class="rc-tour-title">{escape(stage['title'])}</div>
                    <div class="rc-tour-copy">{escape(stage['copy'])}</div>
                    <div class="rc-tour-callouts">{callouts}</div>
                </div>
                {_quick_tour_visual_html(stage['visual'])}
            </div>
        </section>
    """

def _empty_state(title: str, copy: str, icon: str = "info") -> None:
    """Render a deliberate, explanatory empty state."""
    st.html(
        f"""
        <div class="rc-empty-state">
            <div class="rc-empty-symbol">{_icon_svg(icon, 25)}</div>
            <div class="rc-empty-title">{escape(title)}</div>
            <div class="rc-empty-copy">{escape(copy)}</div>
        </div>
        """
    )


def _state_panel(
    title: str,
    copy: str,
    *,
    icon: str = "info",
    tone: str = "neutral",
) -> None:
    """Render one intentional product-state explanation without implying judgment."""
    safe_tone = tone if tone in {
        "neutral", "brand", "sleep", "training", "mood", "study", "warning"
    } else "neutral"
    st.html(
        f"""
        <div class="rc-state-panel {safe_tone}">
            <div class="rc-state-icon">{_icon_svg(icon, 20)}</div>
            <div class="rc-state-body">
                <div class="rc-state-title">{escape(title)}</div>
                <div class="rc-state-copy">{escape(copy)}</div>
            </div>
        </div>
        """
    )


def _current_period_rows(
    rows: list[dict[str, object]],
    start_date: str,
    end_date: str,
) -> list[dict[str, object]]:
    """Return chart rows inside the current analytics period."""
    return [row for row in rows if start_date <= row["date"] <= end_date]


def _period_dates(start_date: str) -> list[date]:
    """Return all seven dates in one Recovery Compass period."""
    start = date.fromisoformat(start_date)
    return [start + timedelta(days=offset) for offset in range(7)]


def _records_by_date(records: list[dict[str, object]]) -> dict[str, dict[str, object]]:
    return {str(record["date"]): record for record in records}


def _week_compass_html(
    records: list[dict[str, object]],
    start_date: str,
    days_recorded: int,
) -> str:
    """Build the signature seven-node week compass."""
    by_date = _records_by_date(records)
    nodes = []
    for index, period_date in enumerate(_period_dates(start_date)):
        iso = period_date.isoformat()
        record = by_date.get(iso)
        classes = ["rc-week-node"]
        if record is not None:
            classes.append("recorded")
            classes.append("rest" if record.get("workout_type") == "Rest" else "workout")
        if period_date == date.today():
            classes.append("today")
        angle = -90 + (index * 360 / 7)
        neg_angle = -angle
        nodes.append(
            f"""
            <div class="{' '.join(classes)}" style="--angle:{angle:.3f}deg;--neg-angle:{neg_angle:.3f}deg;">
                <div class="rc-week-node-day">{period_date.strftime('%a')}</div>
                <div class="rc-week-node-date">{period_date.day}</div>
                <span class="rc-week-node-type"></span>
            </div>
            """
        )
    return (
        f'<div class="rc-week-compass" role="img" aria-label="Week compass: {days_recorded} of 7 days recorded.">'
        f'{"".join(nodes)}'
        '<div class="rc-compass-core">'
        f'<div class="rc-compass-core-value">{days_recorded}/7</div>'
        '<div class="rc-compass-core-label">recorded</div>'
        '</div></div>'
    )


def _side_week_html(
    records: list[dict[str, object]],
    start_date: str,
    period_label: str,
    days_recorded: int,
) -> str:
    by_date = _records_by_date(records)
    days = []
    for period_date in _period_dates(start_date):
        record = by_date.get(period_date.isoformat())
        dot_classes = ["rc-side-dot"]
        if record is not None:
            dot_classes.append("recorded")
        if period_date == date.today():
            dot_classes.append("today")
        days.append(
            f'<div class="rc-side-day"><span class="rc-side-day-label">{period_date.strftime("%a")[:1]}</span><span class="{" ".join(dot_classes)}"></span></div>'
        )
    return f"""
        <div class="rc-side-week">
            <div class="rc-side-week-label">This week</div>
            <div class="rc-side-week-value">{days_recorded} of 7 days</div>
            <div class="rc-side-week-range">{escape(period_label)}</div>
            <div class="rc-side-days">{''.join(days)}</div>
        </div>
    """


def _sparkline_html(
    values: list[float | int | None],
    day_labels: list[str] | None = None,
) -> str:
    """Render a compact seven-day domain instrument once enough data exists.

    Height is encoded with CSS classes rather than inline styles because Streamlit's
    HTML sanitization can remove inline style attributes. Recorded zeroes remain
    distinct from missing days.
    """
    present = [float(value) for value in values if value is not None]
    if len(present) < 3:
        return ""

    nonzero = [value for value in present if value != 0]
    if nonzero:
        low, high = min(nonzero), max(nonzero)
        spread = high - low
    else:
        low = high = spread = 0

    labels = day_labels or [""] * len(values)
    columns = []

    for index, value in enumerate(values):
        label = labels[index] if index < len(labels) else ""

        if value is None:
            state = "missing"
            level_class = ""
            value_label = "Missing"
        else:
            numeric = float(value)
            value_label = _display_number(numeric)

            if numeric == 0:
                state = "zero"
                level_class = ""
            else:
                state = "active"
                if spread == 0:
                    level = 3
                else:
                    normalized = (numeric - low) / spread
                    level = 1 + min(4, int(round(normalized * 4)))
                level_class = f" level-{level}"

        columns.append(
            f'<span class="rc-spark-col {state}{level_class}" title="{escape(label)}: {escape(value_label)}">'
            f'<span class="rc-sparkbar"></span>'
            f'<span class="rc-spark-day">{escape(label)}</span>'
            '</span>'
        )

    return (
        '<div class="rc-sparkline" aria-label="Seven-day recorded pattern">'
        f'{"".join(columns)}'
        '</div>'
    )


def _domain_card_html(
    domain: str,
    icon: str,
    label: str,
    value: str,
    note: str,
    spark_values: list[float | int | None] | None = None,
    spark_days: list[str] | None = None,
) -> str:
    spark = _sparkline_html(spark_values or [], spark_days)
    return f"""
        <div class="rc-domain-card {escape(domain)}" aria-label="{escape(label)} summary">
            <div class="rc-domain-top">
                <div class="rc-domain-label">{escape(label)}</div>
                <div class="rc-domain-icon">{_icon_svg(icon)}</div>
            </div>
            <div class="rc-domain-value">{escape(value)}</div>
            <div class="rc-domain-note">{escape(note)}</div>
            {spark}
        </div>
    """



def _week_matrix_html(
    records: list[dict[str, object]],
    start_date: str,
) -> str:
    """Build a factual seven-day cross-domain overview without scores."""
    by_date = _records_by_date(records)
    dates = _period_dates(start_date)
    headers = ''.join(
        f'<div class="rc-matrix-day{" today" if d == date.today() else ""}">'
        f'<strong>{d.strftime("%a")}</strong><span>{d.day}</span></div>'
        for d in dates
    )

    domain_specs = [
        ("sleep", "Sleep", "moon", lambda r: f'{float(r.get("sleep_hours", 0)):.1f}h'),
        ("training", "Training", "training", lambda r: (
            "Rest" if r.get("workout_type") == "Rest" else f'{int(r.get("duration_minutes", 0))}m'
        )),
        ("mood", "Mood", "mood", lambda r: (
            "—" if r.get("mood_rating") is None else f'{int(r.get("mood_rating"))}/5'
        )),
        ("study", "Study", "study", lambda r: f'{float(r.get("study_hours", 0)):.1f}h'),
    ]
    rows = []
    for domain, label, icon, formatter in domain_specs:
        cells = []
        for d in dates:
            record = by_date.get(d.isoformat())
            if record is None:
                cells.append('<div class="rc-matrix-cell missing"><span>—</span></div>')
            else:
                value = formatter(record)
                cells.append(
                    f'<div class="rc-matrix-cell recorded {domain}"><span>{escape(value)}</span></div>'
                )
        rows.append(
            f'<div class="rc-matrix-label {domain}">{_icon_svg(icon, 17)}<span>{label}</span></div>'
            f'{"".join(cells)}'
        )
    return (
        '<div class="rc-week-matrix" role="table" aria-label="Seven-day overview of sleep, training, mood, and study. Missing days remain missing.">'
        '<div class="rc-matrix-corner"><span>7-day view</span></div>'
        f'{headers}{"".join(rows)}</div>'
        '<div class="rc-matrix-legend"><span class="recorded">Recorded</span>'
        '<span class="missing">Missing stays missing</span></div>'
    )

def _display_recent_records(records: list[dict[str, object]]) -> None:
    """Render the seven most recent records as a compact factual table."""
    recent_records = sorted(records, key=lambda record: record["date"], reverse=True)[:7]
    rows_html = []
    for record in recent_records:
        record_date = date.fromisoformat(str(record["date"])).strftime("%b %d, %Y")
        is_workout = record["workout_type"] != "Rest" and record["duration_minutes"] > 0
        exertion = str(record["perceived_exertion"]) if is_workout else "—"
        mood = str(record["mood_rating"]) if record["mood_rating"] is not None else "—"
        rows_html.append(
            f"""
            <tr>
                <td><strong>{escape(record_date)}</strong></td>
                <td>{escape(str(record['workout_type']))}</td>
                <td>{escape(str(record['duration_minutes']))}</td>
                <td class="{'rc-table-muted' if not is_workout else ''}">{escape(exertion)}</td>
                <td>{escape(str(record['sleep_hours']))}</td>
                <td class="{'rc-table-muted' if record['mood_rating'] is None else ''}">{escape(mood)}</td>
                <td>{escape(str(record['study_hours']))}</td>
            </tr>
            """
        )
    st.html(
        f"""
        <div class="rc-table-wrap">
            <table class="rc-table">
                <thead><tr><th>Date</th><th>Workout</th><th>Minutes</th><th>Exertion</th><th>Sleep</th><th>Mood</th><th>Study</th></tr></thead>
                <tbody>{''.join(rows_html)}</tbody>
            </table>
        </div>
        """
    )


def _footer_html() -> str:
    return """
        <div class="rc-footer">
            <div><strong>Recovery Compass</strong> · v1.0</div>
            <div>Your records stay in this browser · Calm, factual self-tracking</div>
        </div>
    """


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

    _state_panel(
        "Browser persistence is unavailable",
        (
            "Your current session can still work, but refreshing or closing the page "
            "may clear its records. Download a backup before leaving."
        ),
        icon="backup",
        tone="warning",
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
    """Render the V8 guided daily check-in without changing validation rules."""

    current_kind = st.session_state.get("recovery_compass_day_kind", "Rest day")
    is_current_rest = current_kind == "Rest day"
    current_sleep = st.session_state.get("recovery_compass_sleep")
    current_study = st.session_state.get("recovery_compass_study")
    current_duration = st.session_state.get("recovery_compass_duration")
    current_exertion = st.session_state.get("recovery_compass_exertion")
    details_ready = (
        current_sleep is not None
        and current_study is not None
        and (
            is_current_rest
            or (
                current_duration is not None
                and _valid_workout_exertion(current_exertion)
            )
        )
    )

    step_two_class = "complete" if details_ready else "active"
    step_three_class = "active" if details_ready else ""

    st.html(
        f"""
        <div class="rc-log-intro-pills">
            <span class="rc-soft-pill">{_icon_svg('calendar', 15)} About 1 minute</span>
            <span class="rc-soft-pill">{_icon_svg('check', 15)} 3 guided steps</span>
        </div>
        <div class="rc-stepper" aria-label="Daily check-in progress">
            <div class="rc-step complete"><div class="rc-step-bubble">✓</div><div class="rc-step-name">Choose the day</div><div class="rc-step-caption">Date and day type</div></div>
            <div class="rc-step {step_two_class}"><div class="rc-step-bubble">2</div><div class="rc-step-name">Add details</div><div class="rc-step-caption">Only what matters</div></div>
            <div class="rc-step {step_three_class}"><div class="rc-step-bubble">3</div><div class="rc-step-name">Review & save</div><div class="rc-step-caption">Check before saving</div></div>
        </div>
        """
    )

    form_column, preview_column = st.columns([1.55, .78], gap="large")

    with form_column:
        with st.container(border=True):
            st.html(
                """
                <div class="rc-log-section-title"><span class="rc-log-step">1</span>Choose the day</div>
                <div class="rc-log-hint">Leave the date on today unless you are catching up on an earlier day.</div>
                """
            )
            date_col, day_col = st.columns(2, gap="large")
            with date_col:
                st.html('<div class="rc-field-label">Date</div>')
                entry_date = st.date_input(
                    "Date",
                    value=date.today(),
                    max_value=date.today(),
                    help="Choose today or an earlier day you are catching up on.",
                    key="recovery_compass_entry_date",
                    label_visibility="collapsed",
                )
            with day_col:
                st.html('<div class="rc-field-label">Did you work out?</div>')
                day_kind = st.radio(
                    "Did you work out?",
                    options=["Rest day", "Workout day"],
                    horizontal=True,
                    help="Choose Workout day if you completed any planned training.",
                    key="recovery_compass_day_kind",
                    label_visibility="collapsed",
                )

            is_rest_day = day_kind == "Rest day"
            st.html('<div class="rc-log-divider"></div>')
            st.html(
                """
                <div class="rc-log-section-title"><span class="rc-log-step">2</span>Add the details</div>
                <div class="rc-log-hint">Each category keeps its own color so the form is easy to scan.</div>
                """
            )

            if is_rest_day:
                workout_type = WORKOUT_TYPES["rest"]
                duration_minutes = 0
                perceived_exertion = 0
                st.html(
                    f"""
                    <div class="rc-rest-note">
                        {_icon_svg('moon', 21)}
                        <div><strong>Rest day selected.</strong> Training fields are hidden because they do not apply. Recovery Compass will save workout minutes and exertion as 0 automatically.</div>
                    </div>
                    """
                )
            else:
                st.html(
                    f"""
                    <div class="rc-domain-field-header">
                        <div class="rc-domain-field-icon training">{_icon_svg('training', 17)}</div>
                        <div class="rc-domain-field-title">Training</div>
                    </div>
                    """
                )
                workout_options = [value for key, value in WORKOUT_TYPES.items() if key != "rest"]
                workout_choice_key = "recovery_compass_workout_type_choice_v10_0_8"
                if st.session_state.get(workout_choice_key) not in workout_options:
                    st.session_state[workout_choice_key] = workout_options[0]
                workout_type = st.session_state[workout_choice_key]

                st.html('<div class="rc-field-label">Workout type</div>')
                with st.container(key="rc_workout_choice_v10_0_8"):
                    workout_choice_columns = st.columns(len(workout_options), gap="small")
                    for choice_column, option in zip(workout_choice_columns, workout_options):
                        state = "active" if option == workout_type else "idle"
                        slug = option.lower().replace(" ", "_")
                        with choice_column:
                            st.button(
                                option,
                                width="stretch",
                                key=f"rc_workout_choice_{state}_{slug}_v10_0_8",
                                on_click=_set_ui_choice,
                                args=(workout_choice_key, option),
                            )

                workout_metrics_row = st.columns(2, gap="medium")
                with workout_metrics_row[0]:
                    st.html('<div class="rc-field-label">Workout minutes</div>')
                    duration_minutes = st.number_input(
                        "Workout minutes",
                        min_value=0,
                        max_value=300,
                        value=None,
                        step=1,
                        placeholder="Example: 45",
                        help="Total time spent training. Maximum: 300 minutes.",
                        key="recovery_compass_duration",
                        label_visibility="collapsed",
                    )
                with workout_metrics_row[1]:
                    st.html('<div class="rc-field-label">How hard did it feel?</div>')
                    perceived_exertion = st.number_input(
                        "How hard did it feel?",
                        value=None,
                        step=1,
                        placeholder="1 to 10",
                        help=(
                            "Workout-day perceived exertion uses 1–10: "
                            "1 means very light effort and 10 means maximum perceived effort. "
                            "Rest days are stored as 0 automatically."
                        ),
                        key="recovery_compass_exertion",
                        label_visibility="collapsed",
                    )

            st.html(
                """
                <div class="rc-log-subsection-title">The rest of your day</div>
                <div class="rc-log-subsection-copy">Sleep and study are required. Mood is optional and stays missing if you skip it.</div>
                <div class="rc-log-timing-note"><strong>Best time to log:</strong> near the end of the selected day, once your training and study are mostly finished. <strong>Sleep</strong> means the main sleep period that ended that morning.</div>
                """
            )
            # Give the optional Mood control enough horizontal room for a clean 3×2 choice grid.
            daily_row = st.columns([1.0, 1.45, 1.0], gap="medium")

            with daily_row[0]:
                st.html(
                    f'<div class="rc-domain-field-header"><div class="rc-domain-field-icon sleep">{_icon_svg("moon",17)}</div><div class="rc-domain-field-title">Sleep</div></div>'
                )
                st.html("<div class=\"rc-field-label\">Previous night\'s sleep</div>")
                sleep_hours = st.number_input(
                    "Sleep hours",
                    min_value=0.0,
                    max_value=16.0,
                    value=None,
                    step=0.1,
                    placeholder="Example: 7.5",
                    help="Hours slept during the main sleep period that ended on this date. For a Sep 4 entry, enter the sleep from Sep 3 night into Sep 4 morning.",
                    key="recovery_compass_sleep",
                    label_visibility="collapsed",
                )

            mood_options = [
                "Not recorded",
                "1 — Very low",
                "2 — Low",
                "3 — Okay",
                "4 — Good",
                "5 — Great",
            ]
            with daily_row[1]:
                st.html(
                    f'<div class="rc-domain-field-header"><div class="rc-domain-field-icon mood">{_icon_svg("mood",17)}</div><div class="rc-domain-field-title">Mood</div></div>'
                )
                st.html('<div class="rc-field-label">Mood (optional)</div>')
                mood_choice_key = "recovery_compass_mood_choice_v10_0_8"
                if st.session_state.get(mood_choice_key) not in mood_options:
                    st.session_state[mood_choice_key] = "Not recorded"
                mood_choice = st.session_state[mood_choice_key]

                mood_button_labels = [
                    ("Not recorded", "Skip"),
                    ("1 — Very low", "1 Very low"),
                    ("2 — Low", "2 Low"),
                    ("3 — Okay", "3 Okay"),
                    ("4 — Good", "4 Good"),
                    ("5 — Great", "5 Great"),
                ]
                with st.container(key="rc_mood_choice_v10_0_8"):
                    for row_start in (0, 3):
                        mood_columns = st.columns(3, gap="small")
                        for mood_column, (option, label) in zip(
                            mood_columns, mood_button_labels[row_start:row_start + 3]
                        ):
                            state = "active" if option == mood_choice else "idle"
                            slug = (
                                option.lower()
                                .replace(" — ", "_")
                                .replace(" ", "_")
                            )
                            with mood_column:
                                st.button(
                                    label,
                                    width="stretch",
                                    key=f"rc_mood_choice_{state}_{slug}_v10_0_8",
                                    on_click=_set_ui_choice,
                                    args=(mood_choice_key, option),
                                )

            with daily_row[2]:
                st.html(
                    f'<div class="rc-domain-field-header"><div class="rc-domain-field-icon study">{_icon_svg("study",17)}</div><div class="rc-domain-field-title">Study</div></div>'
                )
                st.html('<div class="rc-field-label">Study hours</div>')
                study_hours = st.number_input(
                    "Study hours",
                    min_value=0.0,
                    max_value=16.0,
                    value=None,
                    step=0.1,
                    placeholder="Example: 2.0",
                    help="Time spent studying or doing academic work.",
                    key="recovery_compass_study",
                    label_visibility="collapsed",
                )

            st.html('<div class="rc-log-divider"></div>')
            st.html(
                """
                <div class="rc-log-section-title"><span class="rc-log-step">3</span>Review and save</div>
                <div class="rc-log-hint">The preview beside the form updates as you enter the day. Recovery Compass validates everything again when you save.</div>
                """
            )
            submitted = st.button(
                "Save this day",
                type="primary",
                width="stretch",
                key="recovery_compass_save_entry",
                icon=":material/check_circle:",
            )

    mood_display = "Skipped" if mood_choice == "Not recorded" else mood_choice
    sleep_display = "—" if sleep_hours is None else f"{sleep_hours:g} hr"
    study_display = "—" if study_hours is None else f"{study_hours:g} hr"
    if is_rest_day:
        training_display = "Rest day"
    else:
        minutes_display = "—" if duration_minutes is None else str(duration_minutes)
        exertion_display = "—" if perceived_exertion is None else str(perceived_exertion)
        training_display = f"{workout_type} · {minutes_display} min · effort {exertion_display}/10"

    preview_ready = (
        sleep_hours is not None
        and study_hours is not None
        and (
            is_rest_day
            or (
                duration_minutes is not None
                and _valid_workout_exertion(perceived_exertion)
            )
        )
    )
    ready_copy = (
        "All required fields are present. Check the values once, then save."
        if preview_ready
        else "Complete the remaining required fields. Missing values stay visible as dashes."
    )
    preview_state = "ready" if preview_ready else "incomplete"
    preview_status = "Ready to save" if preview_ready else "Still filling this in"
    preview_status_icon = _icon_svg("check" if preview_ready else "info", 16)

    with preview_column:
        st.html(
            f"""
            <div class="rc-live-preview {preview_state}" role="status" aria-live="polite" aria-atomic="true">
                <div class="rc-live-preview-head">
                    <div>
                        <div class="rc-live-preview-kicker">Live review</div>
                        <div class="rc-live-preview-title">Today&apos;s entry</div>
                    </div>
                    <div class="rc-preview-status {preview_state}">{preview_status_icon}<span>{escape(preview_status)}</span></div>
                </div>

                <div class="rc-preview-row"><div class="rc-preview-icon calendar">{_icon_svg('calendar',18)}</div><div><div class="rc-preview-label">Date</div><div class="rc-preview-value">{escape(entry_date.strftime('%b %d, %Y'))}</div></div></div>
                <div class="rc-preview-row"><div class="rc-preview-icon training">{_icon_svg('training',18)}</div><div><div class="rc-preview-label">Day</div><div class="rc-preview-value">{escape(training_display)}</div></div></div>
                <div class="rc-preview-row"><div class="rc-preview-icon sleep">{_icon_svg('moon',18)}</div><div><div class="rc-preview-label">Sleep</div><div class="rc-preview-value">{escape(sleep_display)}</div></div></div>
                <div class="rc-preview-row"><div class="rc-preview-icon mood">{_icon_svg('mood',18)}</div><div><div class="rc-preview-label">Mood</div><div class="rc-preview-value">{escape(mood_display)}</div></div></div>
                <div class="rc-preview-row"><div class="rc-preview-icon study">{_icon_svg('study',18)}</div><div><div class="rc-preview-label">Study</div><div class="rc-preview-value">{escape(study_display)}</div></div></div>
                <div class="rc-preview-ready {preview_state}">{preview_status_icon}<span>{escape(ready_copy)}</span></div>
            </div>
            """
        )

    if not submitted:
        return

    mood_value = "" if mood_choice == "Not recorded" else mood_choice.split(" ", 1)[0]
    candidate_record = {
        "date": entry_date.isoformat(),
        "workout_type": workout_type,
        "duration_minutes": "" if duration_minutes is None else str(duration_minutes),
        "perceived_exertion": "" if perceived_exertion is None else str(perceived_exertion),
        "sleep_hours": "" if sleep_hours is None else str(sleep_hours),
        "mood_rating": mood_value,
        "study_hours": "" if study_hours is None else str(study_hours),
    }

    errors = validate_record(candidate_record)
    if errors:
        st.error("This day is not ready to save yet. Fix the items listed below; nothing has been saved.")
        for error in errors:
            st.markdown(f"- {error}")
        return

    try:
        normalized_record = normalize_record(candidate_record)
        with st.spinner("Saving your day…"):
            _save_session_record(normalized_record)
    except DuplicateDateError:
        st.error(
            "There is already a saved day for "
            f"{entry_date.strftime('%B %d, %Y')}. Recovery Compass keeps one entry per day."
        )
        return
    except StorageError as error:
        st.error("Recovery Compass could not save this day safely. Your existing browser data was not changed.")
        st.caption(f"Technical detail: {error}")
        return

    st.session_state["recovery_compass_saved_date"] = entry_date.isoformat()
    st.session_state[NAVIGATION_KEY] = "Home"
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


def _render_data_tools(records: list[dict[str, object]]) -> None:
    """Render the V8 visual backup and restore workflow."""
    imported_count = st.session_state.pop("recovery_compass_imported_count", None)
    if imported_count is not None:
        noun = "record" if imported_count == 1 else "records"
        st.success(f"Restored successfully. {imported_count} {noun} are now saved in this browser.")

    st.html(
        f"""
        <div class="rc-flow" aria-label="How Recovery Compass backups move your records">
            <div class="rc-flow-node">
                <div class="rc-flow-icon">{_icon_svg('browser',28)}</div>
                <div class="rc-flow-title">This browser</div>
                <div class="rc-flow-copy">Your active Recovery Compass history lives here.</div>
            </div>
            <div class="rc-flow-arrow">{_icon_svg('arrow',28)}</div>
            <div class="rc-flow-node">
                <div class="rc-flow-icon">{_icon_svg('file',28)}</div>
                <div class="rc-flow-title">Backup file</div>
                <div class="rc-flow-copy">A portable copy you download and keep yourself.</div>
            </div>
            <div class="rc-flow-arrow">{_icon_svg('arrow',28)}</div>
            <div class="rc-flow-node">
                <div class="rc-flow-icon">{_icon_svg('device',28)}</div>
                <div class="rc-flow-title">Another browser or device</div>
                <div class="rc-flow-copy">Restore the backup there when you want to move your history.</div>
            </div>
        </div>
        """
    )

    st.html(
        """
        <div class="rc-section-heading">
            <div>
                <div class="rc-section-kicker">Backup & transfer</div>
                <div class="rc-section-title">Keep a portable copy</div>
                <div class="rc-section-note">Download one file when you want a backup. Restore a Recovery Compass backup only when you want its records added to this browser.</div>
            </div>
        </div>
        """
    )

    with st.container(border=True):
        download_column, import_column = st.columns(2, gap="large")
        with download_column:
            st.html(
                f"""
                <div class="rc-data-tool-title">{_icon_svg('download',20)} Download a backup</div>
                <div class="rc-data-tool-copy">Saves all current Recovery Compass records into one portable CSV backup. Keep it somewhere you can find later.</div>
                """
            )
            if not records:
                _state_panel(
                    "No backup to download yet",
                    "Save your first day before creating a portable backup file.",
                    icon="backup",
                    tone="neutral",
                )
            else:
                try:
                    export_bytes = _build_export_bytes(records)
                except StorageError as error:
                    st.error("Recovery Compass could not prepare your backup.")
                    st.caption(f"Technical detail: {error}")
                else:
                    st.download_button(
                        "Download backup",
                        data=export_bytes,
                        file_name="recovery_compass_backup.csv",
                        mime="text/csv",
                        type="primary",
                        width="stretch",
                        icon=":material/download:",
                        key="rc_download_backup_v10",
                    )

        with import_column:
            st.html(
                f"""
                <div class="rc-data-tool-title">{_icon_svg('restore',20)} Restore a backup</div>
                <div class="rc-data-tool-copy">Choose a backup created by Recovery Compass. The whole file is validated before your current records change.</div>
                <div class="rc-upload-label">Choose a Recovery Compass backup</div>
                <div class="rc-upload-help">Nothing is restored until you press Restore backup.</div>
                """
            )
            uploaded_file = st.file_uploader(
                "Choose a Recovery Compass backup",
                type=["csv"],
                accept_multiple_files=False,
                key="recovery_compass_import_file",
                label_visibility="collapsed",
            )
            if uploaded_file is not None:
                st.caption("Backup selected. Recovery Compass will validate the whole file before restoring anything.")

            import_clicked = st.button(
                "Restore backup",
                type="secondary",
                width="stretch",
                disabled=uploaded_file is None,
                icon=":material/restore:",
            )
            if import_clicked and uploaded_file is not None:
                try:
                    with TemporaryDirectory() as temporary_directory:
                        import_path = Path(temporary_directory) / "recovery_compass_import.csv"
                        import_path.write_bytes(uploaded_file.getvalue())
                        with st.spinner("Checking this backup before anything changes…"):
                            count = _import_session_records(import_path)
                except DuplicateDateError as error:
                    st.error(
                        "This backup was not restored because at least one date already exists here. Your current records were not changed."
                    )
                    st.caption(f"Technical detail: {error}")
                except StorageError as error:
                    st.error(
                        "This backup could not be restored safely. Your current records were not changed."
                    )
                    st.caption(f"Technical detail: {error}")
                except OSError as error:
                    st.error(
                        "Recovery Compass could not read the selected backup. Your current records were not changed."
                    )
                    st.caption(f"Technical detail: {error}")
                else:
                    st.session_state["recovery_compass_imported_count"] = count
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
# V9 navigation + interaction shell
# ---------------------------------------------------------

NAVIGATION_KEY = "recovery_compass_navigation"
INSIGHT_VIEW_KEY = "recovery_compass_insight_view_v8"
NAVIGATION_OPTIONS = ["Home", "Log a Day", "Insights", "Data & Backup", "Help"]


def _navigate_to(page_name: str) -> None:
    """Move to one top-level destination."""
    st.session_state[NAVIGATION_KEY] = page_name


def _navigate_insight(view_name: str) -> None:
    """Open one Insights domain directly from Home."""
    st.session_state[INSIGHT_VIEW_KEY] = view_name
    st.session_state[NAVIGATION_KEY] = "Insights"


def _set_ui_choice(state_key: str, value: str) -> None:
    """Persist one Recovery Compass-owned button-group choice."""
    st.session_state[state_key] = value


def _set_quick_tour_step(step: int) -> None:
    """Move to one bounded step inside the optional quick tour."""
    st.session_state[QUICK_TOUR_STEP_KEY] = max(
        0,
        min(int(step), QUICK_TOUR_STEP_COUNT - 1),
    )
    st.session_state[QUICK_TOUR_ACTIVE_KEY] = True


def _finish_quick_tour() -> None:
    """Dismiss the tour and persist that this browser/profile has seen v1 onboarding."""
    st.session_state[QUICK_TOUR_SEEN_KEY] = True
    st.session_state[QUICK_TOUR_ACTIVE_KEY] = False
    st.session_state[QUICK_TOUR_STEP_KEY] = 0
    st.session_state[QUICK_TOUR_PENDING_WRITE_KEY] = True


def _start_quick_tour() -> None:
    """Replay the quick tour without clearing its persistent completion flag."""
    st.session_state[QUICK_TOUR_ACTIVE_KEY] = True
    st.session_state[QUICK_TOUR_STEP_KEY] = 0
    st.session_state[NAVIGATION_KEY] = "Home"


def _set_theme_from_widget(source_key: str) -> None:
    """Apply one Light/System/Dark choice and queue one browser persistence write."""

    selected_label = st.session_state.get(source_key)
    preference = THEME_CODES.get(selected_label)

    if preference not in THEME_PREFERENCES:
        return

    st.session_state[THEME_PREFERENCE_SESSION_KEY] = preference
    st.session_state[THEME_PENDING_WRITE_KEY] = preference


if NAVIGATION_KEY not in st.session_state:
    st.session_state[NAVIGATION_KEY] = "Home"
if INSIGHT_VIEW_KEY not in st.session_state:
    st.session_state[INSIGHT_VIEW_KEY] = "Overview"

active_page = st.session_state.get(NAVIGATION_KEY, "Home")
if active_page not in NAVIGATION_OPTIONS:
    active_page = "Home"
    st.session_state[NAVIGATION_KEY] = active_page

TODAY_ISO = date.today().isoformat()
today_logged = any(str(record.get("date")) == TODAY_ISO for record in records)

_theme_widget_label = THEME_LABELS[RC_THEME_PREFERENCE]
st.session_state[THEME_DESKTOP_WIDGET_KEY] = _theme_widget_label
st.session_state[THEME_MOBILE_WIDGET_KEY] = _theme_widget_label

nav_items = [
    ("Home", "Home", ":material/home:"),
    ("Log a Day", "Log a Day", ":material/check_circle:" if today_logged else ":material/edit_calendar:"),
    ("Insights", "Insights", ":material/insights:"),
    ("Data & Backup", "Data & Backup", ":material/cloud_download:"),
    ("Help", "Help", ":material/help_outline:"),
]

with st.sidebar:
    st.html(
        f"""
        <div class="rc-brand-lockup">
            <div class="rc-brand-row">
                <div class="rc-brand-mark">{BRAND_SVG}</div>
                <div>
                    <div class="rc-brand-name">Recovery Compass</div>
                    <div class="rc-brand-tagline">Your week, explained simply.</div>
                </div>
            </div>
        </div>
        <div class="rc-nav-kicker">Navigate</div>
        """
    )

    for page_name, label, icon in nav_items:
        st.button(
            label,
            key=f"nav_{page_name.lower().replace(' ', '_').replace('&', 'and')}_v9",
            type="primary" if active_page == page_name else "secondary",
            icon=icon,
            width="stretch",
            on_click=_navigate_to,
            args=(page_name,),
        )

    st.divider()
    st.html(_side_week_html(records, current["start_date"], period_label, days_recorded))

    st.html(
        """
        <div class="rc-appearance-heading">
            <span class="rc-appearance-title">Appearance</span>
            <span class="rc-appearance-copy">System follows this device.</span>
        </div>
        """
    )
    st.segmented_control(
        "Appearance",
        options=["Light", "System", "Dark"],
        key=THEME_DESKTOP_WIDGET_KEY,
        selection_mode="single",
        width="stretch",
        label_visibility="collapsed",
        on_change=_set_theme_from_widget,
        args=(THEME_DESKTOP_WIDGET_KEY,),
    )
    st.html(
        f"""
        <div class="rc-appearance-effective" role="status">
            Showing <strong>{escape(THEME_LABELS[RC_THEME_TYPE])}</strong>
            {"from your system preference" if RC_THEME_PREFERENCE == "system" else "by your choice"}.
        </div>
        """
    )

    st.html(
        """
        <div class="rc-side-storage">
            <span class="rc-side-storage-dot"></span><strong>Saved in this browser.</strong><br>
            Use Data & Backup before clearing browser data or moving devices.
        </div>
        """
    )

# Mobile interaction shell. CSS hides this above the narrow-layout breakpoint.
with st.container(key="rc_mobile_shell"):
    st.html(
        f"""
        <div class="rc-mobile-brand">
            <div class="rc-mobile-brand-mark">{BRAND_SVG}</div>
            <div>
                <div class="rc-mobile-brand-name">Recovery Compass</div>
                <div class="rc-mobile-brand-meta">{days_recorded}/7 recorded · {escape(period_label)}</div>
            </div>
        </div>
        """
    )

    with st.container(key="rc_mobile_nav", horizontal=True, gap="small"):
        for page_name, label, icon in nav_items:
            mobile_label = "Backup" if page_name == "Data & Backup" else ("Log" if page_name == "Log a Day" else label)
            st.button(
                mobile_label,
                key=f"mobile_nav_{page_name.lower().replace(' ', '_').replace('&', 'and')}_v9",
                type="primary" if active_page == page_name else "secondary",
                icon=icon,
                on_click=_navigate_to,
                args=(page_name,),
            )

    with st.container(key="rc_mobile_theme"):
        st.segmented_control(
            "Appearance",
            options=["Light", "System", "Dark"],
            key=THEME_MOBILE_WIDGET_KEY,
            selection_mode="single",
            width="stretch",
            label_visibility="collapsed",
            on_change=_set_theme_from_widget,
            args=(THEME_MOBILE_WIDGET_KEY,),
        )

st.html(
    '<a class="rc-skip-link" href="#rc-main-content">Skip to main content</a>'
    '<div id="rc-main-content" tabindex="-1"></div>'
)

QUICK_TOUR_ACTIVE = bool(
    st.session_state.get(QUICK_TOUR_ACTIVE_KEY, False)
)
if QUICK_TOUR_ACTIVE:
    # First-launch onboarding owns the main canvas. Keep the permanent shell
    # visible for orientation, but do not compete with the normal Home body.
    active_page = "Home"
    st.session_state[NAVIGATION_KEY] = "Home"

    _quick_tour_step = int(
        st.session_state.get(QUICK_TOUR_STEP_KEY, 0)
    )
    _quick_tour_step = max(
        0,
        min(_quick_tour_step, QUICK_TOUR_STEP_COUNT - 1),
    )

    st.html(_quick_tour_title_html())

    with st.container(key="rc_quick_tour_v2"):
        st.html(_quick_tour_html(_quick_tour_step))

        tour_skip_col, tour_back_col, tour_next_col = st.columns(
            [1.0, 1.0, 1.45],
            gap="small",
        )
        with tour_skip_col:
            st.button(
                "Skip tour",
                key=f"rc_quick_tour_skip_v2_{_quick_tour_step}",
                type="secondary",
                width="stretch",
                on_click=_finish_quick_tour,
            )
        with tour_back_col:
            st.button(
                "Back",
                key=f"rc_quick_tour_back_v2_{_quick_tour_step}",
                type="secondary",
                width="stretch",
                disabled=_quick_tour_step == 0,
                on_click=_set_quick_tour_step,
                args=(_quick_tour_step - 1,),
            )
        with tour_next_col:
            if _quick_tour_step < QUICK_TOUR_STEP_COUNT - 1:
                st.button(
                    "Next",
                    key=f"rc_quick_tour_next_v2_{_quick_tour_step}",
                    type="primary",
                    icon=":material/arrow_forward:",
                    width="stretch",
                    on_click=_set_quick_tour_step,
                    args=(_quick_tour_step + 1,),
                )
            else:
                st.button(
                    "Start using Recovery Compass",
                    key="rc_quick_tour_finish_v2",
                    type="primary",
                    icon=":material/check_circle:",
                    width="stretch",
                    on_click=_finish_quick_tour,
                )


# ---------------------------------------------------------
# Home — signature week dashboard
# ---------------------------------------------------------

if active_page == "Home" and not QUICK_TOUR_ACTIVE:
    just_saved_date = st.session_state.pop("recovery_compass_saved_date", None)
    if just_saved_date is not None:
        saved_label = date.fromisoformat(just_saved_date).strftime("%B %d, %Y")
        st.success(f"{saved_label} saved. Your week has been updated.", icon="✅")

    st.html(
        f"""
        <div class="rc-home-hero">
            <div class="rc-hero-content">
                <div class="rc-hero-brand-mini">{_icon_svg('insights',18)} Your current week</div>
                <div class="rc-home-title">See the week<br>clearly.</div>
                <div class="rc-home-copy">
                    Recovery Compass turns the days you record into a calm, factual picture of sleep, training,
                    mood, and study—without inventing a score or pretending missing days are data.
                </div>
                <div class="rc-home-meta">
                    <span class="rc-home-pill"><span class="rc-home-pill-dot"></span>{escape(period_label)}</span>
                    <span class="rc-home-pill">{days_recorded} of 7 days recorded</span>
                    <span class="rc-home-pill">Saved in this browser</span>
                </div>
            </div>
            <div class="rc-compass-wrap">
                {_week_compass_html(records, current['start_date'], days_recorded)}
            </div>
        </div>
        """
    )

    if not records and not QUICK_TOUR_ACTIVE:
        st.html(
            f"""
            <div class="rc-first-run" style="margin-top:1rem;">
                <div class="rc-first-illustration">{BRAND_SVG}</div>
                <div class="rc-first-text">
                    <div class="rc-first-title">Your first week starts here.</div>
                    <div class="rc-first-copy">Log one day. Recovery Compass builds the week only from what you actually record.</div>
                </div>
                <div class="rc-first-seven" aria-hidden="true"><i></i><i></i><i></i><i></i><i></i><i></i><i></i></div>
            </div>
            """
        )
        first_one, first_two = st.columns([1.2, 1], gap="medium")
        with first_one:
            st.button(
                "Log my first day",
                type="primary",
                icon=":material/edit_calendar:",
                width="stretch",
                on_click=_navigate_to,
                args=("Log a Day",),
                key="home_first_log_v8",
            )
        with first_two:
            st.button(
                "Restore a backup",
                icon=":material/restore:",
                width="stretch",
                on_click=_navigate_to,
                args=("Data & Backup",),
                key="home_first_backup_v8",
            )
    else:
        if today_logged:
            next_title = "Today is already recorded"
            next_copy = "Your week is current for today. Review the essentials below or record an earlier day if you are catching up."
            primary_label = "Log another day"
        else:
            next_title = "Today is not recorded yet"
            next_copy = "A normal check-in takes about a minute. You can also choose an earlier date if you are catching up."
            primary_label = "Log today"
        st.html(
            f"""
            <div class="rc-next-panel">
                <div class="rc-next-title">{escape(next_title)}</div>
                <div class="rc-next-copy">{escape(next_copy)}</div>
            </div>
            """
        )
        next_one, next_two = st.columns([1.3, 1], gap="medium")
        with next_one:
            st.button(
                primary_label,
                type="primary",
                icon=":material/edit_calendar:",
                width="stretch",
                on_click=_navigate_to,
                args=("Log a Day",),
                key="home_log_next_v8",
            )
        with next_two:
            st.button(
                "Explore the details",
                icon=":material/insights:",
                width="stretch",
                on_click=_navigate_to,
                args=("Insights",),
                key="home_insights_v8",
            )

        if days_recorded == 1:
            _state_panel(
                "One day recorded",
                (
                    "This is an early view of the week. Recovery Compass will not invent "
                    "a trend from one day, and unrecorded days stay missing."
                ),
                icon="info",
                tone="neutral",
            )
        elif days_recorded == 7:
            _state_panel(
                "Seven-day period complete",
                (
                    "All seven days in this period are recorded. Insights can now show "
                    "the full week without missing-day gaps."
                ),
                icon="check",
                tone="brand",
            )

        period_days = _period_dates(current["start_date"])
        by_date = _records_by_date(records)
        spark_days = [period_date.strftime("%a")[:1] for period_date in period_days]
        sleep_spark = []
        training_spark = []
        mood_spark = []
        study_spark = []
        for period_date in period_days:
            record = by_date.get(period_date.isoformat())
            if record is None:
                sleep_spark.append(None)
                training_spark.append(None)
                mood_spark.append(None)
                study_spark.append(None)
            else:
                sleep_spark.append(record.get("sleep_hours"))
                training_spark.append(record.get("duration_minutes"))
                mood_spark.append(record.get("mood_rating"))
                study_spark.append(record.get("study_hours"))

        sleep_value = f"{_display_number(average_sleep)} hr" if average_sleep is not None else "—"
        mood_value = f"{_display_number(average_mood)} / 5" if average_mood is not None else "No ratings"
        study_value = f"{_display_number(average_study)} hr" if average_study is not None else "—"
        mood_note = f"{mood_entries} mood rating{'' if mood_entries == 1 else 's'}" if mood_entries else "Mood is optional"
        average_workout_minutes = (
            training_minutes / workout_days
            if workout_days > 0
            else None
        )
        training_value = (
            f"{average_workout_minutes:g} min"
            if average_workout_minutes is not None
            else "—"
        )
        training_note = (
            "No workout days recorded"
            if workout_days == 0
            else (
                f"{workout_days} workout day" + ("" if workout_days == 1 else "s")
                + f" · {training_minutes} min total"
            )
        )

        st.html(
            """
            <div class="rc-section-heading">
                <div>
                    <div class="rc-section-kicker">At a glance</div>
                    <div class="rc-section-title">Four parts of your week</div>
                    <div class="rc-section-note">The same four colors follow you through Recovery Compass.</div>
                    <div class="rc-average-context"><span>Period averages</span><small>Calculated from recorded values. Training averages Workout days only.</small></div>
                </div>
            </div>
            """
        )
        st.html(
            f"""
            <div class="rc-domain-grid">
                {_domain_card_html('sleep','moon','Sleep',sleep_value,f'{days_recorded} of 7 days recorded',sleep_spark,spark_days)}
                {_domain_card_html('training','training','Training',training_value,training_note,training_spark,spark_days)}
                {_domain_card_html('mood','mood','Mood',mood_value,mood_note,mood_spark,spark_days)}
                {_domain_card_html('study','study','Study',study_value,f'{days_recorded} of 7 days recorded',study_spark,spark_days)}
            </div>
            """
        )

        drill_cols = st.columns(4, gap="small")
        drill_specs = [
            ("Sleep & Mood", ":material/bedtime:", "home_sleep_v8"),
            ("Training", ":material/fitness_center:", "home_training_v8"),
            ("Sleep & Mood", ":material/mood:", "home_mood_v8"),
            ("Study", ":material/menu_book:", "home_study_v8"),
        ]
        drill_labels = ["Explore sleep", "Explore training", "Explore mood", "Explore study"]
        for column, (view, icon, key), label in zip(drill_cols, drill_specs, drill_labels):
            with column:
                st.button(
                    label,
                    icon=icon,
                    width="stretch",
                    on_click=_navigate_insight,
                    args=(view,),
                    key=key,
                )

        feedback_statements = generate_feedback(metrics)
        feedback_items = "".join(f"<li>{escape(statement)}</li>" for statement in feedback_statements)
        st.html(
            f"""
            <div class="rc-section-heading">
                <div><div class="rc-section-kicker">Plain-language summary</div><div class="rc-section-title">What your data says</div><div class="rc-section-note">Factual observations only—no diagnosis, prediction, or recovery score.</div></div>
            </div>
            <div class="rc-summary-panel"><ul>{feedback_items}</ul></div>
            """
        )


# ---------------------------------------------------------
# Log a Day — guided, color-coded workflow
# ---------------------------------------------------------

elif active_page == "Log a Day":
    st.html(
        """
        <div class="rc-page-header">
            <div class="rc-page-eyebrow">Daily check-in</div>
            <div class="rc-page-title-large">Log one day</div>
            <div class="rc-page-subtitle">Record what happened. Irrelevant fields disappear automatically, and the live review shows exactly what will be saved.</div>
        </div>
        """
    )
    _render_daily_entry()


elif active_page == "Insights":
    st.html(
        f"""
        <div class="rc-page-header">
            <div class="rc-page-eyebrow">Insights</div>
            <div class="rc-page-title-large">Explore your week</div>
            <div class="rc-page-subtitle">Explore one focused view at a time. Every view uses the same seven-day period, and missing days stay missing.</div>
        </div>
        <div class="rc-domain-legend" aria-label="Recovery Compass domain colors">
            <span class="rc-domain-legend-label">Domains</span>
            <span class="rc-domain-legend-item sleep"><i></i>Sleep</span>
            <span class="rc-domain-legend-item training"><i></i>Training</span>
            <span class="rc-domain-legend-item mood"><i></i>Mood</span>
            <span class="rc-domain-legend-item study"><i></i>Study</span>
        </div>
        """
    )

    insight_options = ["Overview", "Sleep & Mood", "Training", "Study", "Recent Records"]
    insight_view = st.session_state.get(INSIGHT_VIEW_KEY, "Overview")
    if insight_view not in insight_options:
        insight_view = "Overview"
        st.session_state[INSIGHT_VIEW_KEY] = insight_view

    # V10.0.6 deliberately uses ordinary keyed Streamlit buttons instead of
    # st.segmented_control. The app's Light/System/Dark switch is independent
    # from Streamlit's native theme, and segmented_control repeatedly reintroduced
    # native dark styling into the custom Light surface. Buttons already have a
    # qualified, stable styling contract elsewhere in Recovery Compass.
    with st.container(key="rc_insight_tabs"):
        insight_columns = st.columns(len(insight_options), gap=None)
        for column, option in zip(insight_columns, insight_options):
            slug = (
                option.lower()
                .replace(" & ", "_")
                .replace(" ", "_")
            )
            state = "active" if option == insight_view else "idle"
            with column:
                st.button(
                    option,
                    width="stretch",
                    key=f"rc_insight_tab_{state}_{slug}",
                    on_click=_navigate_insight,
                    args=(option,),
                )

    period_start_date = date.fromisoformat(current["start_date"])
    period_dates = [
        period_start_date + timedelta(days=offset)
        for offset in range(7)
    ]
    date_labels = [
        period_date.strftime("%b %d")
        for period_date in period_dates
    ]

    if insight_view == "Overview":
        exertion_value = f"{_display_number(average_exertion)} / 10" if average_exertion is not None else "—"
        st.html(
            f"""
            <div class="rc-overview-instrument">
                <div class="rc-overview-instrument-head">
                    <div>
                        <div class="rc-section-kicker">Seven-day instrument</div>
                        <div class="rc-overview-instrument-title">Your week, domain by domain</div>
                    </div>
                    <div class="rc-overview-instrument-note">Values are shown only where you recorded them.</div>
                </div>
                {_week_matrix_html(records, current['start_date'])}
            </div>
            <div class="rc-insight-overview">
                <div class="rc-insight-card" style="--accent:{RC_TRAINING}"><div class="rc-insight-card-label">Workout days</div><div class="rc-insight-card-value">{workout_days}</div><div class="rc-insight-card-note">Days with actual training</div></div>
                <div class="rc-insight-card" style="--accent:{RC_BRAND}"><div class="rc-insight-card-label">Training</div><div class="rc-insight-card-value">{training_minutes} min</div><div class="rc-insight-card-note">Total workout time this period</div></div>
                <div class="rc-insight-card" style="--accent:#8A98AA"><div class="rc-insight-card-label">Avg exertion</div><div class="rc-insight-card-value">{escape(exertion_value)}</div><div class="rc-insight-card-note">Workout days only</div></div>
                <div class="rc-insight-card" style="--accent:{RC_MOOD}"><div class="rc-insight-card-label">Mood entries</div><div class="rc-insight-card-value">{mood_entries}</div><div class="rc-insight-card-note">Mood is optional</div></div>
            </div>
            """
        )

        previous_end_date = period_start_date - timedelta(days=1)
        previous_start_date = previous_end_date - timedelta(days=6)
        recorded_date_strings = {str(record.get("date")) for record in records}
        previous_period_dates = [
            previous_start_date + timedelta(days=offset)
            for offset in range(7)
        ]
        previous_days_recorded = sum(
            period_date.isoformat() in recorded_date_strings
            for period_date in previous_period_dates
        )
        current_range_label = _format_date_range(
            current["start_date"], current["end_date"]
        )
        previous_range_label = _format_date_range(
            previous_start_date.isoformat(), previous_end_date.isoformat()
        )
        missing_previous_dates = [
            period_date
            for period_date in previous_period_dates
            if period_date.isoformat() not in recorded_date_strings
        ]

        if metrics["comparison_available"]:
            _state_panel(
                "Previous week is comparison-ready",
                (
                    f"{current_range_label} and {previous_range_label} both contain all "
                    "seven recorded days. The factual comparison below uses only those two complete periods."
                ),
                icon="check",
                tone="brand",
            )

            previous = calculate_metrics(
                records,
                period_end=previous_end_date,
            )["current_period"]

            def _comparison_value(value, unit=""):
                if value is None:
                    return "No ratings" if unit == "/ 5" else "—"
                rendered = _display_number(value)
                return f"{rendered}{unit}" if unit.startswith(" /") else f"{rendered} {unit}".strip()

            previous_sleep = _comparison_value(previous["average_sleep_hours"], "hr")
            current_sleep = _comparison_value(current["average_sleep_hours"], "hr")
            previous_mood = _comparison_value(previous["average_mood_rating"], " / 5")
            current_mood = _comparison_value(current["average_mood_rating"], " / 5")
            previous_study = _comparison_value(previous["average_study_hours"], "hr")
            current_study = _comparison_value(current["average_study_hours"], "hr")

            st.html(
                f"""
                <section class="rc-week-comparison" aria-label="Previous and current seven-day period comparison">
                    <div class="rc-week-comparison-head">
                        <div>
                            <div class="rc-section-kicker">Two complete periods</div>
                            <div class="rc-week-comparison-title">Previous period vs current period</div>
                        </div>
                        <div class="rc-week-comparison-note">Facts only. Changes are not labeled good or bad.</div>
                    </div>
                    <div class="rc-week-comparison-periods">
                        <div><span>Previous</span>{escape(previous_range_label)}</div>
                        <div><span>Current</span>{escape(current_range_label)}</div>
                    </div>
                    <div class="rc-week-comparison-grid">
                        <article class="rc-week-compare-card sleep">
                            <div class="rc-week-compare-label">Sleep</div>
                            <div class="rc-week-compare-values">
                                <div><span>Previous</span><strong>{escape(previous_sleep)}</strong></div>
                                <div><span>Current</span><strong>{escape(current_sleep)}</strong></div>
                            </div>
                            <div class="rc-week-compare-caption">Average sleep across seven recorded days</div>
                        </article>
                        <article class="rc-week-compare-card training">
                            <div class="rc-week-compare-label">Training</div>
                            <div class="rc-week-compare-values">
                                <div><span>Previous</span><strong>{previous['total_training_minutes']} min</strong></div>
                                <div><span>Current</span><strong>{current['total_training_minutes']} min</strong></div>
                            </div>
                            <div class="rc-week-compare-caption">Workout days: {previous['workout_days']} previous · {current['workout_days']} current</div>
                        </article>
                        <article class="rc-week-compare-card mood">
                            <div class="rc-week-compare-label">Mood</div>
                            <div class="rc-week-compare-values">
                                <div><span>Previous</span><strong>{escape(previous_mood)}</strong></div>
                                <div><span>Current</span><strong>{escape(current_mood)}</strong></div>
                            </div>
                            <div class="rc-week-compare-caption">Optional ratings stay missing when none were recorded</div>
                        </article>
                        <article class="rc-week-compare-card study">
                            <div class="rc-week-compare-label">Study</div>
                            <div class="rc-week-compare-values">
                                <div><span>Previous</span><strong>{escape(previous_study)}</strong></div>
                                <div><span>Current</span><strong>{escape(current_study)}</strong></div>
                            </div>
                            <div class="rc-week-compare-caption">Average study time across seven recorded days</div>
                        </article>
                    </div>
                </section>
                """
            )
        else:
            missing_hint = ""
            if days_recorded == 7 and previous_days_recorded == 6 and len(missing_previous_dates) == 1:
                missing_hint = (
                    f" Record {missing_previous_dates[0].strftime('%b %d')} to complete the previous period."
                )
            _state_panel(
                "Previous-week comparison is locked",
                (
                    f"Current period {current_range_label}: {days_recorded} of 7 days. "
                    f"Previous period {previous_range_label}: {previous_days_recorded} of 7 days."
                    f"{missing_hint} Both periods must reach 7 of 7."
                ),
                icon="info",
                tone="neutral",
            )

    elif insight_view == "Sleep & Mood":
        # Patterns section
        # ---------------------------------------------------------

        st.html(
            """
            <div class="rc-section-heading">

                <div>
                    <div class="rc-section-kicker" style="color:var(--rc-sleep)!important">
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
                if sleep_rows and not mood_rows:
                    _state_panel(
                        "No mood ratings recorded",
                        (
                            "Mood is optional. Your recorded sleep still appears normally, "
                            "and missing mood is never treated as zero."
                        ),
                        icon="mood",
                        tone="mood",
                    )

                dark_chart_background = RC_CHART_BG
                dark_chart_grid = RC_CHART_GRID
                dark_chart_text = RC_CHART_TEXT
                dark_chart_domain = RC_CHART_DOMAIN

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
                                    titleColor=RC_SLEEP,
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
                            color=RC_SLEEP,
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
                            color=RC_SLEEP,
                            stroke=RC_CHART_BG,
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
                                color=RC_CHART_TITLE,
                                subtitleColor=RC_CHART_SUBTITLE,
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
                                    titleColor=RC_MOOD,
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
                            color=RC_MOOD,
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
                            color=RC_MOOD,
                            stroke=RC_CHART_BG,
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
                                color=RC_CHART_TITLE,
                                subtitleColor=RC_CHART_SUBTITLE,
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

    elif insight_view == "Training":
        # Training visualization
        # ---------------------------------------------------------

        st.html(
            """
            <div class="rc-section-heading">
                <div>
                    <div class="rc-section-kicker" style="color:var(--rc-training)!important">
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

            if days_recorded == 0:
                _empty_state(
                    "No training data yet",
                    (
                        "Log a day in this period to begin building "
                        "your Training timeline."
                    ),
                    icon="training",
                )

            elif workout_days == 0:
                _state_panel(
                    "No workout days recorded this week",
                    (
                        "Recorded Rest days remain Rest days. Training duration and exertion "
                        "will appear after you log a Workout day."
                    ),
                    icon="training",
                    tone="training",
                )

            else:
                dark_chart_background = RC_CHART_BG
                dark_chart_grid = RC_CHART_GRID
                dark_chart_text = RC_CHART_TEXT
                dark_chart_domain = RC_CHART_DOMAIN

                duration_chart = (
                    alt.Chart(
                        alt.Data(values=training_rows)
                    )
                    .mark_bar(
                        color=RC_TRAINING,
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
                                titleColor=RC_TRAINING,
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
                            color=RC_CHART_TITLE,
                            subtitleColor=RC_CHART_SUBTITLE,
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
                                title="Exertion (1–10)",
                                scale=alt.Scale(
                                    domain=[1, 10],
                                    padding=18,
                                ),
                                axis=alt.Axis(
                                    values=[1, 2, 4, 6, 8, 10],
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
                            stroke=RC_CHART_BG,
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
                                color=RC_CHART_TITLE,
                                subtitleColor=RC_CHART_SUBTITLE,
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

    elif insight_view == "Study":
        # Study visualization
        # ---------------------------------------------------------

        st.html(
            """
            <div class="rc-section-heading">
                <div>
                    <div class="rc-section-kicker" style="color:var(--rc-study)!important">
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
                dark_chart_background = RC_CHART_BG
                dark_chart_grid = RC_CHART_GRID
                dark_chart_text = RC_CHART_TEXT
                dark_chart_domain = RC_CHART_DOMAIN

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
                                titleColor=RC_STUDY,
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
                        color=RC_STUDY,
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
                        color=RC_STUDY,
                        stroke=RC_CHART_BG,
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
                            color=RC_CHART_TITLE,
                            subtitleColor=RC_CHART_SUBTITLE,
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

    elif insight_view == "Recent Records":
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


elif active_page == "Data & Backup":
    st.html(
        f"""
        <div class="rc-page-header">
            <div class="rc-page-eyebrow">Data & backup</div>
            <div class="rc-page-title-large">Keep your records safe</div>
            <div class="rc-page-subtitle">Your records stay in this browser. A backup is the portable copy you keep when you want protection or need to move your history.</div>
        </div>
        <div class="rc-storage-card rc-storage-card-compact">
            <strong>{_icon_svg('browser',20)} Saved locally in this browser</strong>
            <p>Refreshing or closing the tab should keep your records. Download a backup before clearing browser data or moving to another device.</p>
        </div>
        """
    )
    _render_data_tools(records)
    st.html(
        """
        <div class="rc-transfer-note">
            <span class="rc-transfer-note-dot"></span>
            <div><strong>Nothing is uploaded to a Recovery Compass account.</strong> v1.0 has no account or cloud database; your backup file is the transfer path.</div>
        </div>
        """
    )


elif active_page == "Help":
    st.html(
        f"""
        <div class="rc-page-header">
            <div class="rc-page-eyebrow">Help</div>
            <div class="rc-page-title-large">How Recovery Compass works</div>
            <div class="rc-page-subtitle">Plain-English guidance for recording a day, understanding each color-coded category, reading the week, and keeping your records safe.</div>
        </div>
        <div class="rc-help-grid">
            <div class="rc-help-card"><div class="rc-help-icon">{_icon_svg('log',20)}</div><div class="rc-help-card-title">1. Record</div><div class="rc-help-card-copy">Log one day at a time. Recovery Compass hides workout fields on Rest days and checks the entry before saving.</div></div>
            <div class="rc-help-card"><div class="rc-help-icon">{_icon_svg('insights',20)}</div><div class="rc-help-card-title">2. Review</div><div class="rc-help-card-copy">Home shows the essentials. Insights separates Sleep & Mood, Training, Study, and your recent records.</div></div>
            <div class="rc-help-card"><div class="rc-help-icon">{_icon_svg('backup',20)}</div><div class="rc-help-card-title">3. Back up</div><div class="rc-help-card-copy">Your data stays in this browser, so download a Recovery Compass backup when you want a portable copy.</div></div>
        </div>
        """
    )

    st.button(
        "Take the 30-second quick tour",
        key="help_replay_quick_tour_v1",
        type="secondary",
        icon=":material/play_circle:",
        on_click=_start_quick_tour,
    )

    with st.expander("Getting started", expanded=True):
        st.markdown(
            """
**Log a Day** is the only place you need for everyday recording. Choose the date, then choose **Rest day** or **Workout day**. Recovery Compass shows only the fields that matter for that day.

For the cleanest daily record, log **near the end of the selected day**, once your training and study are mostly finished. You can also catch up on an earlier date later.

**Sleep** means the main sleep period that **ended on the selected date**. For example, a **September 4** entry uses the sleep from the night of **September 3 into the morning of September 4**. **Study** is required and **Mood** is optional. If you choose **Rest day**, Recovery Compass automatically stores **0 workout minutes** and **0 perceived exertion**, so the record cannot contradict itself.

The live review panel shows what will be saved before you press **Save this day**.
            """
        )

    with st.expander("The colors and categories"):
        st.markdown(
            """
Recovery Compass uses the same category colors everywhere so you can scan the app faster:

- **Sleep — periwinkle/blue**
- **Training — cyan/azure**
- **Mood — amber/gold**
- **Study — sage/green**
- **General navigation and actions — teal**

Color never means that a value is medically “good” or “bad.” Labels and icons always remain present so color is not the only way information is communicated.
            """
        )

    with st.expander("Understanding the numbers"):
        st.markdown(
            """
**Coverage** — how many of the seven days in the current calendar period have a saved entry.

**Workout Days** — days with a non-Rest workout and more than zero training minutes.

**Training** — Home shows average workout duration across actual workout days. Training Insights also shows total workout minutes for the period.

**Average Sleep** — average of the sleep periods that ended on the recorded dates. On Home, the four domain cards use averages from the values actually recorded; Training averages Workout days only.

**Average Mood** — average of only the mood ratings you entered. Missing mood is never converted to zero.

**Average Study** — average study hours from recorded days in the current period.

**Average Exertion** — average perceived exertion from actual workout days only.

**Previous-week comparison** — becomes available only when both consecutive seven-day periods contain all seven recorded days.
            """
        )

    with st.expander("Charts and missing days"):
        st.markdown(
            """
Every Insights chart uses the same seven-day calendar period as Home.

**Sleep & Mood** use separate scales. Missing days appear as gaps.

**Training Duration** shows recorded workout minutes. Rest days remain at zero minutes; missing days remain missing.

**Perceived Exertion** uses a 1–10 whole-number scale on Workout days. Rest days are stored as 0 automatically and remain visually distinct from Workout-day exertion.

**Study Hours** leaves unrecorded days as gaps rather than pretending they were zero-hour study days.
            """
        )

    with st.expander("Your data, privacy, and backups"):
        st.markdown(
            """
Recovery Compass v1.0 stores records in **this browser/profile** using browser-local storage. There is no Recovery Compass account and no cloud database in v1.0.

Refreshing the page or closing and reopening the tab should keep your records. Clearing browser/site data can remove them.

Use **Data & Backup → Download backup** to create a portable copy. To move records, open Recovery Compass in another browser or device and use **Restore backup**. The entire backup is checked before your current records change.
            """
        )

    with st.expander("Editing or deleting a saved day"):
        st.markdown(
            """
Recovery Compass v1.0 intentionally keeps saved records **append-only**: one validated entry per calendar day. V9 evaluated edit and delete controls but does not add them because safe record mutation would change the qualified storage contract and require a separate round of destructive-action, backup, duplicate-date, and recovery testing.

If a saved day is wrong during the v1.0 release period, preserve a backup before changing the underlying data. Edit/delete remains a deliberate post-v1.0 feature decision rather than a hidden or partially tested control.
            """
        )

    with st.expander("What Recovery Compass does not do"):
        st.markdown(
            """
Recovery Compass reports deterministic facts from the data you enter. It does **not**:

- generate a medical or recovery score;
- diagnose health conditions;
- infer that one recorded behavior caused another;
- predict future health or performance;
- provide live AI coaching;
- replace professional medical guidance.

The goal of v1.0 is transparent self-tracking, not automated health judgment.
            """
        )


st.html(_footer_html())
