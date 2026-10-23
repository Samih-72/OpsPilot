from pathlib import Path
import html
import json
from datetime import datetime
import altair as alt
import pandas as pd
import streamlit as st

# The chatbot imports the Groq client at import time. If the key or a data file
# is missing, keep the rest of the app usable and show the reason on the chat page.
try:
    from main import handle_customer_query
    CHATBOT_ERROR = None
except Exception as exc:  # noqa: BLE001
    handle_customer_query = None
    CHATBOT_ERROR = "{}: {}".format(type(exc).__name__, exc)

from daily_briefing import get_daily_business_briefing

# --------------------------------------------------
# PAGE CONFIGURATION
# --------------------------------------------------
st.set_page_config(
    page_title="OpsPilot",
    page_icon="🧭",
    layout="wide",
    initial_sidebar_state="expanded",
)

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
DATA_FILES = [
    "customers.csv",
    "products.csv",
    "orders.csv",
    "order_items.csv",
    "payments.csv",
    "shipments.csv",
    "returns.csv",
    "marketing_campaigns.csv",
    "customer_reviews.csv",
]
PAGES = ["Dashboard", "Daily Briefing", "AI Assistant", "Data Explorer","Upload Data"]

INK = "#171A33"
CANVAS = "#F4F5F9"
LINE = "#E4E6EF"
MUTED = "#6B7090"
INDIGO = "#4B4FD8"
MARIGOLD = "#F2A33A"
TEAL = "#1F9D8A"
CORAL = "#E5484D"
SLATE = "#9AA0BC"

esc = html.escape

# --------------------------------------------------
# STYLING — PRESERVED
# --------------------------------------------------
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,600;9..144,700&family=Manrope:wght@400;500;600;700;800&display=swap');
    .stApp, .stMarkdown, .stMarkdown p, .stButton button, input,
    textarea, label, [data-testid="stCaptionContainer"],
    [data-testid="stChatMessage"] {
        font-family: 'Manrope', sans-serif;
    }
    .stApp { background: #F4F5F9; color: #171A33; }
    header[data-testid="stHeader"] { background: transparent; }
    #MainMenu, footer { visibility: hidden; }
    .block-container {
        padding-top: 2.2rem;
        padding-bottom: 4rem;
        max-width: 1280px;
    }
    [data-testid="stSidebar"] {
        background: #171A33;
        border-right: none;
    }
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] [data-testid="stCaptionContainer"] {
        color: #C9CCE6;
    }
    [data-testid="stSidebar"] hr {
        border-color: rgba(255,255,255,.08);
    }
    .brand {
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 6px 4px 18px;
    }
    .brand-mark {
        width: 38px;
        height: 38px;
        border-radius: 11px;
        background: #F2A33A;
        display: flex;
        align-items: center;
        justify-content: center;
        font-family: 'Fraunces', serif;
        font-weight: 700;
        font-size: 20px;
        color: #171A33;
    }
    .brand-name {
        font-family: 'Fraunces', serif;
        font-weight: 700;
        font-size: 21px;
        color: #fff;
        line-height: 1.1;
    }
    .brand-sub {
        font-size: 11px;
        color: #8F94B8;
        letter-spacing: .12em;
        text-transform: uppercase;
        margin-top: 3px;
    }

    /* ---------- page headings ---------- */
    .page-title {
        font-family: 'Fraunces', serif;
        font-weight: 700;
        font-size: 34px;
        line-height: 1.15;
        color: #171A33;
        margin: 0;
    }
    .page-sub { color: #6B7090; font-size: 15px; margin: 6px 0 22px; }
    .section-title {
        font-family: 'Fraunces', serif;
        font-weight: 700;
        font-size: 22px;
        color: #171A33;
        margin: 30px 0 4px;
    }
    .section-sub { color: #6B7090; font-size: 13.5px; margin-bottom: 14px; }

    /* ---------- briefing summary ---------- */
    .summary-card {
        background: #171A33;
        color: #E9EAF7;
        border-radius: 18px;
        padding: 22px 26px;
        font-size: 16px;
        line-height: 1.65;
        margin-bottom: 6px;
    }
    .summary-meta { color: #8F94B8; font-size: 12px; margin-top: 10px; }

    /* ---------- KPI cards ---------- */
    .kpi-card {
        background: #FFFFFF;
        border: 1px solid #E4E6EF;
        border-radius: 16px;
        padding: 16px 18px;
        min-height: 138px;
        margin-bottom: 14px;
        box-shadow: 0 1px 2px rgba(23, 26, 51, .04);
    }
    .kpi-label {
        color: #6B7090;
        font-size: 11.5px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: .06em;
    }
    .kpi-value {
        font-family: 'Fraunces', serif;
        font-weight: 700;
        font-size: 30px;
        color: #171A33;
        margin: 6px 0 4px;
        line-height: 1.1;
    }
    .kpi-delta {
        display: inline-block;
        font-size: 11.5px;
        font-weight: 700;
        padding: 2px 9px;
        border-radius: 99px;
        margin-bottom: 5px;
    }
    .kpi-delta.good { background: #E3F5F1; color: #1F9D8A; }
    .kpi-delta.bad { background: #FDECEC; color: #E5484D; }
    .kpi-delta.neutral { background: #EEF0F7; color: #6B7090; }
    .kpi-note { color: #6B7090; font-size: 12px; line-height: 1.45; }

    /* ---------- problems and actions ---------- */
    .problem-card {
        background: #FFFFFF;
        border: 1px solid #E4E6EF;
        border-left: 5px solid #F2A33A;
        border-radius: 14px;
        padding: 16px 20px;
        margin-bottom: 12px;
        box-shadow: 0 1px 2px rgba(23, 26, 51, .04);
    }
    .problem-card.high { border-left-color: #E5484D; }
    .problem-head { display: flex; align-items: center; gap: 12px; margin-bottom: 10px; }
    .problem-rank {
        width: 28px;
        height: 28px;
        border-radius: 8px;
        background: #171A33;
        color: #fff;
        font-weight: 800;
        font-size: 13px;
        display: flex;
        align-items: center;
        justify-content: center;
        flex-shrink: 0;
    }
    .problem-title { font-weight: 700; font-size: 16px; color: #171A33; flex: 1; }
    .sev {
        font-size: 11px;
        font-weight: 800;
        text-transform: uppercase;
        letter-spacing: .06em;
        padding: 3px 10px;
        border-radius: 99px;
    }
    .sev.high { background: #FDECEC; color: #E5484D; }
    .sev.medium { background: #FEF3E2; color: #B9740F; }
    .problem-row {
        display: flex;
        gap: 10px;
        align-items: flex-start;
        font-size: 14px;
        line-height: 1.55;
        color: #2B2F52;
        margin-top: 7px;
    }
    .tag {
        flex-shrink: 0;
        min-width: 138px;
        text-align: center;
        font-size: 11px;
        font-weight: 800;
        padding: 3px 8px;
        border-radius: 8px;
        text-transform: uppercase;
        letter-spacing: .04em;
    }
    .tag.confirmed { background: #E3F5F1; color: #187A6B; }
    .tag.possible { background: #FEF3E2; color: #B9740F; }
    .tag.reco { background: #ECECFB; color: #4B4FD8; }
    .action-item {
        display: flex;
        gap: 14px;
        align-items: flex-start;
        background: #FFFFFF;
        border: 1px solid #E4E6EF;
        border-radius: 14px;
        padding: 14px 18px;
        margin-bottom: 10px;
        font-size: 14.5px;
        line-height: 1.5;
        color: #2B2F52;
    }
    .action-num {
        width: 26px;
        height: 26px;
        border-radius: 50%;
        background: #F2A33A;
        color: #171A33;
        font-weight: 800;
        font-size: 13px;
        display: flex;
        align-items: center;
        justify-content: center;
        flex-shrink: 0;
    }
    .action-area { color: #6B7090; font-size: 12px; margin-top: 2px; }
    .chart-title { font-weight: 700; font-size: 14.5px; color: #171A33; margin: 4px 0 0; }
    .chart-sub { color: #6B7090; font-size: 12px; margin-bottom: 6px; }

    @media (max-width: 760px) {
        .page-title { font-size: 27px; }
        .problem-row { flex-direction: column; gap: 4px; }
        .tag { min-width: 0; align-self: flex-start; }
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# --------------------------------------------------
# SMALL HELPERS
# --------------------------------------------------
def stretch(fn, *args, **kwargs):
    """Call a Streamlit element full-width on both old and new Streamlit versions."""
    try:
        return fn(*args, width="stretch", **kwargs)
    except TypeError:
        return fn(*args, use_container_width=True, **kwargs)


@st.cache_data(show_spinner=False)
def load_csv(name):
    """Load one CSV from the data folder. Returns None if it is missing or unreadable."""
    path = DATA_DIR / name
    if not path.exists():
        return None
    try:
        return pd.read_csv(path)
    except Exception:  # noqa: BLE001
        return None


def find_col(df, *names):
    if df is None:
        return None
    lookup = {str(c).strip().lower(): c for c in df.columns}
    for name in names:
        if name.lower() in lookup:
            return lookup[name.lower()]
    return None


def page_header(title, subtitle):
    st.markdown(
        '<div class="page-title">{}</div><div class="page-sub">{}</div>'.format(esc(title), esc(subtitle)),
        unsafe_allow_html=True,
    )


def section_header(title, subtitle=""):
    markup = '<div class="section-title">{}</div>'.format(esc(title))
    if subtitle:
        markup += '<div class="section-sub">{}</div>'.format(esc(subtitle))
    st.markdown(markup, unsafe_allow_html=True)


def kpi_card(label, value, note="", delta=None, tone="neutral"):
    delta_html = ""
    if delta:
        delta_html = '<div><span class="kpi-delta {}">{}</span></div>'.format(esc(tone), esc(delta))
    return (
        '<div class="kpi-card"><div class="kpi-label">{}</div><div class="kpi-value">{}</div>{}'
        '<div class="kpi-note">{}</div></div>'
    ).format(esc(label), esc(str(value)), delta_html, esc(note))


def kpi_row(cards):
    columns = st.columns(len(cards))
    for column, card in zip(columns, cards):
        with column:
            st.markdown(kpi_card(**card), unsafe_allow_html=True)


# --------------------------------------------------
# CHART BUILDERS
# --------------------------------------------------
def line_chart(df, x, y, color, y_title):
    base = alt.Chart(df).encode(
        x=alt.X("{}:T".format(x), title=None),
        y=alt.Y("{}:Q".format(y), title=y_title),
        tooltip=list(df.columns),
    )
    return (base.mark_area(color=color, opacity=0.12) + base.mark_line(color=color)).properties(height=240)


def hbar_chart(df, cat, val, color, val_title, rule=None):
    base = alt.Chart(df).mark_bar(color=color, cornerRadiusEnd=4).encode(
        y=alt.Y("{}:N".format(cat), sort="-x", title=None, axis=alt.Axis(labelLimit=220)),
        x=alt.X("{}:Q".format(val), title=val_title),
        tooltip=list(df.columns),
    )
    chart = base
    if rule is not None:
        marker = alt.Chart(pd.DataFrame({"x": [rule]})).mark_rule(
            color=CORAL, strokeDash=[5, 4]
        ).encode(x="x:Q")
        chart = base + marker
    return chart.properties(height=max(170, 34 * len(df) + 50))


def bar_chart(df, x, y, color, y_title):
    return (
        alt.Chart(df)
        .mark_bar(color=color, cornerRadiusTopLeft=4, cornerRadiusTopRight=4)
        .encode(
            x=alt.X("{}:T".format(x), title=None),
            y=alt.Y("{}:Q".format(y), title=y_title),
            tooltip=list(df.columns),
        )
        .properties(height=240)
    )


def chart_tile(title, subtitle, chart):
    st.markdown(
        '<div class="chart-title">{}</div><div class="chart-sub">{}</div>'.format(esc(title), esc(subtitle)),
        unsafe_allow_html=True,
    )
    stretch(st.altair_chart, chart)


# --------------------------------------------------
# SIDEBAR
# --------------------------------------------------
def render_sidebar():
    with st.sidebar:
        st.markdown(
            '<div class="brand"><div class="brand-mark">O</div><div>'
            '<div class="brand-name">OpsPilot</div>'
            '<div class="brand-sub">Business operations</div></div></div>',
            unsafe_allow_html=True,
        )
        page = st.radio("Navigate", PAGES, label_visibility="collapsed")
        st.divider()
        found = [f for f in DATA_FILES if (DATA_DIR / f).exists()]
        missing = [f for f in DATA_FILES if f not in found]
        st.caption("Data files found: {}/{}".format(len(found), len(DATA_FILES)))
        if missing:
            st.caption("Missing: " + ", ".join(missing))
    return page


# --------------------------------------------------
# DASHBOARD
# --------------------------------------------------
def render_dashboard():
    page_header("Dashboard", "A live view of your customers, orders and payments.")
    uploaded_data= st.session_state.get("uploaded_data",{})
    customers = uploaded_data.get("customers.csv")
    orders = uploaded_data.get("orders.csv")
    payments = uploaded_data.get("payments.csv")

    cards = [
        dict(label="Customers", value="{:,}".format(len(customers)) if customers is not None else "N/A",
             note="Rows in customers.csv" if customers is not None else "customers.csv not found"),
        dict(label="Orders", value="{:,}".format(len(orders)) if orders is not None else "N/A",
             note="Rows in orders.csv" if orders is not None else "orders.csv not found"),
    ]
    status_col = find_col(payments, "payment_status")
    amount_col = find_col(payments, "amount_paid")
    if payments is not None and status_col is not None and amount_col is not None:
        status = payments[status_col].fillna("").astype(str).str.strip().str.lower()
        amounts = pd.to_numeric(payments[amount_col], errors="coerce").fillna(0)
        cards.append(dict(label="Gross collections", value="\u20b9{:,.0f}".format(amounts[status == "success"].sum()),
                          note="Successful payments, all dates. Refunds not subtracted."))
        cards.append(dict(label="Payment success rate", value="{:.1f}%".format((status == "success").mean() * 100),
                          note="{:,} payment records".format(len(payments))))
    else:
        cards.append(dict(label="Gross collections", value="N/A", note="payments.csv columns not found"))
        cards.append(dict(label="Payment success rate", value="N/A", note="payments.csv columns not found"))
    kpi_row(cards)

    # Latest-day snapshot (uses the original get_daily_business_briefing helper)
    section_header("Latest day snapshot", "From the most recent date in your order, payment and shipment files.")
    try:
        
        uploaded_data = st.session_state.get("uploaded_data", {})
        orders_df = uploaded_data.get("orders.csv")
        snap = get_daily_business_briefing(orders_df=orders_df)

        kpi_row([
            dict(label="Orders", value="{:,}".format(snap["orders"]["orders"]),
                 note="{} | {:+,} vs previous day".format(snap["orders"]["report_date"], snap["orders"]["change"])),
            dict(label="Gross collections", value="\u20b9{:,.0f}".format(snap["collections"]["successful_collections"]),
                 note="{} | {:+,.0f} vs previous day".format(
                     snap["collections"]["report_date"], snap["collections"]["change"])),
            dict(label="Recorded refunds", value="\u20b9{:,.0f}".format(snap["refunds"]["refunds"]),
                 note="{} | shown separately".format(snap["refunds"]["report_date"])),
            dict(label="Shipments delayed", value="{:.1f}%".format(snap["shipping"]["delay_rate_pct"]),
                 note="{} | {:,} of {:,} shipments".format(
                     snap["shipping"]["report_date"], snap["shipping"]["delayed_shipments"],
                     snap["shipping"]["total_shipments"])),
        ])
    except Exception as exc:  # noqa: BLE001
        st.caption("Latest-day snapshot unavailable ({}: {}).".format(type(exc).__name__, exc))

    section_header("Orders and payments")
    left, right = st.columns(2)
    with left:
        date_col = find_col(orders, "order_date")
        if date_col is not None:
            dates = pd.to_datetime(orders[date_col], errors="coerce").dropna()
            if not dates.empty:
                monthly = dates.dt.to_period("M").dt.to_timestamp().value_counts().sort_index()
                chart_tile("Orders per month", "Count of orders by order date",
                           bar_chart(pd.DataFrame({"month": monthly.index, "orders": monthly.values}),
                                     "month", "orders", INDIGO, "Orders"))
            else:
                st.info("No valid order dates found.")
        else:
            st.info("orders.csv has no order_date column.")
    with right:
        if payments is not None and status_col is not None:
            counts = payments[status_col].fillna("Unknown").astype(str).str.strip().value_counts()
            chart_tile("Payments by status", "Count of payment records",
                       hbar_chart(pd.DataFrame({"status": counts.index, "payments": counts.values}),
                                  "status", "payments", TEAL, "Payment records"))
        else:
            st.info("Payment status data is not available.")


# ============================================================
# BRIEFING CALCULATIONS  (added for OpsPilot)
# (Moved here from daily_briefing.py so that file stays untouched.)
# ============================================================
try:
    from analytics import get_payment_overview
except Exception:  # analytics.py missing or unreadable
    get_payment_overview = None

BRIEFING_DATA_DIR = DATA_DIR

BRIEFING_FILES = [
    "customers.csv",
    "products.csv",
    "orders.csv",
    "order_items.csv",
    "payments.csv",
    "shipments.csv",
    "returns.csv",
    "marketing_campaigns.csv",
    "customer_reviews.csv",
]

# Investigation thresholds. These are starting points for deciding what to
# look at first. They are NOT industry benchmarks.
THRESHOLDS = {
    "payment_failure_pct": 5.0,
    "method_failure_pct": 6.0,
    "wow_drop_pct": 15.0,
    "delay_pct": 10.0,
    "carrier_delay_pct": 15.0,
    "return_pct": 10.0,
    "reason_share_pct": 30.0,
    "low_rating_share_pct": 20.0,
    "avg_rating": 3.5,
    "refund_pct": 5.0,
}

KPI_DEFS = [
    ("orders", "Orders - last 7 days"),
    ("collections", "Gross collections - last 7 days"),
    ("refunds", "Recorded refunds - last 7 days"),
    ("pay_success", "Payment success rate"),
    ("delay", "Shipment delay rate"),
    ("returns", "Return rate"),
    ("rating", "Average review rating"),
    ("customers", "Customers"),
]


# ---------- small helpers ----------



def _read(name, uploaded_data=None):
    # Use this visitor's uploaded CSV when available.
    if uploaded_data is not None and name in uploaded_data:
        return uploaded_data[name].copy()

    # Otherwise, retain the existing local-file fallback.
    path = BRIEFING_DATA_DIR / name
    if not path.exists():
        return None

    try:
        return pd.read_csv(path)
    except Exception:
        return None



def _find(df, *names):
    """Return the real column name matching any candidate (case-insensitive)."""
    if df is None:
        return None
    lookup = {str(c).strip().lower(): c for c in df.columns}
    for name in names:
        if name.lower() in lookup:
            return lookup[name.lower()]
    return None


def _num(series):
    return pd.to_numeric(series, errors="coerce")


def _dt(series):
    return pd.to_datetime(series, errors="coerce").dt.normalize()


def _flag(series):
    numbers = _num(series)
    if numbers.notna().any():
        return numbers
    words = {
        "true": 1, "yes": 1, "y": 1, "delayed": 1,
        "false": 0, "no": 0, "n": 0, "on time": 0,
    }
    return series.astype(str).str.strip().str.lower().map(words)


def _mask(df, date_col, end, days, offset=0):
    """Rows whose date falls in the `days`-day window ending `offset` days before `end`."""
    dates = _dt(df[date_col])
    stop = end - pd.Timedelta(days=offset)
    start = stop - pd.Timedelta(days=days - 1)
    return (dates >= start) & (dates <= stop)


def _last_days(end, n):
    return pd.date_range(end - pd.Timedelta(days=n - 1), end)


def _pct_change(current, previous):
    if not previous:
        return None
    return (current - previous) / previous * 100


def _fmt_delta(change):
    if change is None:
        return None
    return "{:+.1f}% vs previous 7 days".format(change)


def _tone(change, up_is_good=True):
    if change is None or abs(change) < 0.05:
        return "neutral"
    return "good" if (change > 0) == up_is_good else "bad"


def _money(value):
    return "\u20b9{:,.0f}".format(value)


def _gap(ctx, message):
    ctx["limitations"].append(message)


def _set_kpi(ctx, key, value, note="", delta=None, tone="neutral"):
    ctx["kpis"][key].update(value=value, note=note, delta=delta, tone=tone)


def _add_problem(ctx, area, title, ratio, finding, possible, action):
    ctx["problems"].append({
        "area": area,
        "title": title,
        "ratio": float(ratio),
        "severity": "High" if ratio >= 1.5 else "Medium",
        "finding": finding,
        "possible": possible,
        "action": action,
    })



def _new_ctx(uploaded_data=None):
    return {
        "df": {
            name: _read(name, uploaded_data)
            for name in BRIEFING_FILES
        },
        "end": None,
        "kpis": {
            key: {
                "label": label,
                "value": "N/A",
                "note": "Data unavailable",
                "delta": None,
                "tone": "neutral",
            }
            for key, label in KPI_DEFS
        },
        "problems": [],
        "charts": {},
        "limitations": [],
        "facts": {},
    }



def _safe(section, ctx, label):
    try:
        section(ctx)
    except Exception as exc:
        _gap(ctx, "{} could not be analyzed ({}: {}).".format(label, type(exc).__name__, exc))


# ---------- sections ----------

def _section_dates(ctx):
    candidates = []
    for name, column in (("orders.csv", "order_date"), ("payments.csv", "payment_date")):
        df = ctx["df"][name]
        col = _find(df, column)
        if col is not None:
            dates = _dt(df[col]).dropna()
            if not dates.empty:
                candidates.append(dates.max())
    ctx["end"] = max(candidates) if candidates else None


def _section_orders(ctx):
    df, end, T = ctx["df"]["orders.csv"], ctx["end"], THRESHOLDS
    if df is None:
        _gap(ctx, "orders.csv was not found, so order trends are unavailable.")
        return
    dc = _find(df, "order_date")
    if dc is None or end is None:
        _gap(ctx, "orders.csv has no usable order_date column, so order trends are unavailable.")
        return
    cur = int(_mask(df, dc, end, 7).sum())
    prev = int(_mask(df, dc, end, 7, 7).sum())
    change = _pct_change(cur, prev)
    _set_kpi(ctx, "orders", "{:,}".format(cur), "Previous 7 days: {:,}".format(prev),
             _fmt_delta(change), _tone(change))
    ctx["facts"].update(orders_cur=cur, orders_prev=prev, orders_change=change)

    days = _last_days(end, 30)
    counts = _dt(df[dc]).value_counts().reindex(days, fill_value=0)
    ctx["charts"]["orders_trend"] = pd.DataFrame(
        {"date": days, "orders": counts.values.astype(int)}
    )

    if prev >= 10 and change is not None and change <= -T["wow_drop_pct"]:
        _add_problem(
            ctx, "Orders", "Orders dropped versus the previous 7 days",
            abs(change) / T["wow_drop_pct"],
            "Orders fell {:.1f}% ({:,} vs {:,}) in the 7 days ending {:%d %b %Y}.".format(
                abs(change), cur, prev, end),
            "Could reflect seasonality, a pause in marketing, stock-outs or site issues. "
            "The data alone cannot confirm which.",
            "Compare this week's traffic sources, campaigns and stock availability with last week's.",
        )


def _section_payments(ctx):
    df, end, T = ctx["df"]["payments.csv"], ctx["end"], THRESHOLDS
    if df is None:
        _gap(ctx, "payments.csv was not found, so payment metrics are unavailable.")
        return
    sc = _find(df, "payment_status")
    ac = _find(df, "amount_paid")
    dc = _find(df, "payment_date")
    rc = _find(df, "refund_amount")
    mc = _find(df, "payment_method")
    if sc is None:
        _gap(ctx, "payments.csv has no payment_status column, so payment metrics are unavailable.")
        return

    status = df[sc].fillna("").astype(str).str.strip().str.lower()
    ok = status == "success"
    failed = status == "failed"
    total, n_ok, n_fail = len(df), int(ok.sum()), int(failed.sum())
    success_rate = n_ok / total * 100 if total else 0.0
    fail_rate = n_fail / total * 100 if total else 0.0

    _set_kpi(ctx, "pay_success", "{:.1f}%".format(success_rate),
             "{:,} failed of {:,} payment records".format(n_fail, total))
    ctx["facts"].update(pay_success=success_rate)

    if total >= 30 and fail_rate >= T["payment_failure_pct"]:
        _add_problem(
            ctx, "Payments", "Payment failure rate is elevated",
            fail_rate / T["payment_failure_pct"],
            "{:.1f}% of payment records ({:,} of {:,}) are marked Failed.".format(
                fail_rate, n_fail, total),
            "The data has no failure reasons, so the cause is unknown. Gateway errors, "
            "card declines or checkout friction are all possible.",
            "Review failed payments by method and date, and ask your payment gateway for decline/error codes.",
        )

    # Failure rate by payment method
    if mc is not None:
        methods = df[mc].fillna("Unknown").astype(str).str.strip()
        grouped = (
            pd.DataFrame({"method": methods, "failed": failed})
            .groupby("method")
            .agg(attempts=("failed", "size"), failed=("failed", "sum"))
        )
        grouped["failure_rate"] = (grouped["failed"] / grouped["attempts"] * 100).round(2)
        grouped = grouped.reset_index()
        ctx["charts"]["payment_methods"] = (
            grouped[grouped["attempts"] >= 10]
            .sort_values("failure_rate", ascending=False).head(8)
        )
        flagged = grouped[
            (grouped["attempts"] >= 20) & (grouped["failed"] >= 5)
            & (grouped["failure_rate"] >= T["method_failure_pct"])
        ].sort_values("failure_rate", ascending=False)
        if not flagged.empty:
            worst = flagged.iloc[0]
            _add_problem(
                ctx, "Payments", "{} has the highest payment failure rate".format(worst["method"]),
                worst["failure_rate"] / T["method_failure_pct"],
                "{} payments are marked Failed {:.1f}% of the time ({:,} of {:,} records).".format(
                    worst["method"], worst["failure_rate"], int(worst["failed"]), int(worst["attempts"])),
                "Rates use all records, not confirmed checkout attempts, and no failure reasons "
                "are recorded. A provider or integration issue is possible.",
                "Test the {} checkout flow end to end and check with that provider for errors.".format(worst["method"]),
            )
    else:
        _gap(ctx, "payments.csv has no payment_method column, so failure rates by method are unavailable.")

    if ac is None:
        _gap(ctx, "payments.csv has no amount_paid column, so collections are unavailable.")
        return
    amount = _num(df[ac]).fillna(0)
    refund = _num(df[rc]).fillna(0) if rc is not None else None

    if dc is not None and end is not None:
        cur_mask, prev_mask = _mask(df, dc, end, 7), _mask(df, dc, end, 7, 7)
        cur = float(amount[ok & cur_mask].sum())
        prev = float(amount[ok & prev_mask].sum())
        change = _pct_change(cur, prev)
        _set_kpi(ctx, "collections", _money(cur),
                 "Successful payments only. Refunds not subtracted. Previous 7 days: {}".format(_money(prev)),
                 _fmt_delta(change), _tone(change))
        ctx["facts"].update(coll_cur=cur, coll_prev=prev, coll_change=change)

        days = _last_days(end, 30)
        daily = amount[ok].groupby(_dt(df[dc])[ok]).sum().reindex(days, fill_value=0)
        ctx["charts"]["collections_trend"] = pd.DataFrame(
            {"date": days, "collections": daily.values.astype(float)}
        )

        if prev > 0 and change is not None and change <= -T["wow_drop_pct"]:
            _add_problem(
                ctx, "Collections", "Gross collections dropped versus the previous 7 days",
                abs(change) / T["wow_drop_pct"],
                "Gross successful collections fell {:.1f}% ({} vs {}) in the 7 days ending {:%d %b %Y}.".format(
                    abs(change), _money(cur), _money(prev), end),
                "Could follow lower order volume, more failed payments, or smaller baskets. "
                "The data does not confirm which.",
                "Check whether the drop matches fewer orders or more failed payments in the same window.",
            )

        if refund is not None:
            r_cur, r_prev = float(refund[cur_mask].sum()), float(refund[prev_mask].sum())
            r_change = _pct_change(r_cur, r_prev)
            _set_kpi(ctx, "refunds", _money(r_cur),
                     "Shown separately, not netted from collections. Previous 7 days: {}".format(_money(r_prev)),
                     _fmt_delta(r_change), _tone(r_change, up_is_good=False))
        else:
            _gap(ctx, "payments.csv has no refund_amount column, so refunds are unavailable.")
    else:
        _gap(ctx, "payments.csv has no usable payment_date column, so recent collections are unavailable.")

    # All-time gross vs refunds (reuses analytics.get_payment_overview when possible)
    gross_all, refunds_all = float(amount[ok].sum()), (float(refund.sum()) if refund is not None else None)
    if get_payment_overview is not None:
        try:
            overview = get_payment_overview()
            gross_all = overview["gross_successful_collections"]
            refunds_all = overview["total_recorded_refunds"]
        except Exception:
            pass
    ctx["facts"].update(gross_all=gross_all, refunds_all=refunds_all)
    if refunds_all is not None and gross_all > 0:
        pct = refunds_all / gross_all * 100
        if pct >= T["refund_pct"]:
            _add_problem(
                ctx, "Refunds", "Recorded refunds are a notable share of gross collections",
                pct / T["refund_pct"],
                "Recorded refunds total {} across all dates, about {:.1f}% of gross successful collections ({}).".format(
                    _money(refunds_all), pct, _money(gross_all)),
                "Refunds may relate to payments from earlier periods, so this ratio is indicative only. "
                "It is not a measure of profit or net revenue.",
                "Review refund reasons and approvals, and compare against the return reasons below.",
            )


def _section_shipments(ctx):
    df, end, T = ctx["df"]["shipments.csv"], ctx["end"], THRESHOLDS
    if df is None:
        _gap(ctx, "shipments.csv was not found, so shipment delays are unavailable.")
        return
    fc = _find(df, "delayed_flag")
    dc = _find(df, "dispatch_date", "shipped_date")
    cc = _find(df, "carrier", "courier", "shipping_partner", "shipping_carrier", "delivery_partner")
    if fc is None:
        _gap(ctx, "shipments.csv has no delayed_flag column, so delay rates are unavailable.")
        return
    flag = _flag(df[fc])
    use = flag.notna()
    scope = "all dates"
    if dc is not None and end is not None:
        recent = use & _mask(df, dc, end, 30)
        if recent.sum() > 0:
            use, scope = recent, "last 30 days"
    total = int(use.sum())
    if total == 0:
        _gap(ctx, "shipments.csv has no usable delay data.")
        return
    delayed = int((flag[use] == 1).sum())
    rate = delayed / total * 100
    _set_kpi(ctx, "delay", "{:.1f}%".format(rate),
             "{:,} of {:,} shipments delayed ({})".format(delayed, total, scope))
    ctx["facts"].update(delay_rate=rate)

    if cc is not None:
        sub = pd.DataFrame({
            "carrier": df.loc[use, cc].fillna("Unknown").astype(str).str.strip(),
            "delayed": flag[use] == 1,
        })
        grouped = sub.groupby("carrier").agg(shipments=("delayed", "size"), delayed=("delayed", "sum"))
        grouped["delay_rate"] = (grouped["delayed"] / grouped["shipments"] * 100).round(2)
        grouped = grouped.reset_index()
        ctx["charts"]["carrier_delays"] = (
            grouped[grouped["shipments"] >= 10].sort_values("delay_rate", ascending=False).head(8)
        )
        flagged = grouped[(grouped["shipments"] >= 10) & (grouped["delay_rate"] >= T["carrier_delay_pct"])]
        if not flagged.empty:
            worst = flagged.sort_values("delay_rate", ascending=False).iloc[0]
            _add_problem(
                ctx, "Shipping", "{} has a high shipment delay rate".format(worst["carrier"]),
                worst["delay_rate"] / T["carrier_delay_pct"],
                "{:.1f}% of {} shipments are flagged delayed ({:,} of {:,}, {}).".format(
                    worst["delay_rate"], worst["carrier"], int(worst["delayed"]), int(worst["shipments"]), scope),
                "Could be a carrier capacity problem, a regional issue or slow dispatch. "
                "The data does not say which.",
                "Ask {} about delayed lanes and consider shifting volume to a faster carrier.".format(worst["carrier"]),
            )

    if total >= 20 and rate >= T["delay_pct"]:
        _add_problem(
            ctx, "Shipping", "Shipment delay rate is elevated",
            rate / T["delay_pct"],
            "{:.1f}% of shipments ({:,} of {:,}, {}) are flagged as delayed.".format(rate, delayed, total, scope),
            "Delays may come from dispatch backlog, carrier performance or location. "
            "The data only flags delays, not their causes.",
            "Check whether delays start at dispatch or in transit, and review the worst carriers and locations.",
        )


def _section_returns(ctx):
    returns, orders, T = ctx["df"]["returns.csv"], ctx["df"]["orders.csv"], THRESHOLDS
    if returns is None:
        _gap(ctx, "returns.csv was not found, so return metrics are unavailable.")
        return
    if orders is None:
        _gap(ctx, "orders.csv is needed to calculate a return rate and was not found.")
        return
    r_oid, o_oid = _find(returns, "order_id"), _find(orders, "order_id")
    returned = returns[r_oid].nunique() if r_oid is not None else len(returns)
    orders_total = orders[o_oid].nunique() if o_oid is not None else len(orders)
    if orders_total == 0:
        _gap(ctx, "orders.csv is empty, so a return rate cannot be calculated.")
        return
    rate = returned / orders_total * 100
    _set_kpi(ctx, "returns", "{:.1f}%".format(rate),
             "{:,} returned of {:,} orders (all dates)".format(returned, orders_total))
    ctx["facts"].update(return_rate=rate)
    if r_oid is None or o_oid is None:
        _gap(ctx, "returns.csv or orders.csv has no order_id column, so return rate counts rows, not unique orders.")

    reason_col = _find(returns, "return_reason", "reason", "return_issue", "issue")
    top_reason, top_share = None, 0.0
    if reason_col is not None:
        reasons = returns[reason_col].fillna("Unknown").astype(str).str.strip().value_counts()
        ctx["charts"]["return_reasons"] = pd.DataFrame(
            {"reason": reasons.index[:8], "count": reasons.values[:8].astype(int)}
        )
        if len(returns) >= 10:
            top_reason, top_share = reasons.index[0], reasons.iloc[0] / len(returns) * 100
    else:
        _gap(ctx, "returns.csv has no return reason column, so common return issues are unavailable.")

    if returned >= 10 and rate >= T["return_pct"]:
        _add_problem(
            ctx, "Returns", "Return rate is elevated",
            rate / T["return_pct"],
            "{:.1f}% of orders ({:,} of {:,}) have a return record.".format(rate, returned, orders_total),
            "Could relate to product quality, listing accuracy or fit, or a specific category. "
            "Check the reasons and categories to narrow this down.",
            "Break returns down by product, category and reason, and fix the biggest contributor first.",
        )
    if top_reason is not None and top_share >= T["reason_share_pct"]:
        _add_problem(
            ctx, "Returns", "One return reason dominates: {}".format(top_reason),
            top_share / T["reason_share_pct"],
            "{:.0f}% of return records ({:,} of {:,}) list \"{}\" as the reason.".format(
                top_share, int(round(top_share / 100 * len(returns))), len(returns), top_reason),
            "A single dominant reason often points to one fixable cause such as descriptions, sizing or packaging.",
            "Review the products behind \"{}\" returns and update listings, sizing or packaging.".format(top_reason),
        )


def _section_reviews(ctx):
    df, products, end, T = ctx["df"]["customer_reviews.csv"], ctx["df"]["products.csv"], ctx["end"], THRESHOLDS
    if df is None:
        _gap(ctx, "customer_reviews.csv was not found, so feedback patterns are unavailable.")
        return
    rc = _find(df, "rating", "review_rating", "stars", "review_score", "score")
    if rc is None:
        _gap(ctx, "customer_reviews.csv has no rating column, so feedback patterns are unavailable.")
        return
    ratings = _num(df[rc])
    valid = ratings.notna()
    n = int(valid.sum())
    if n == 0:
        _gap(ctx, "customer_reviews.csv has no numeric ratings.")
        return
    avg = float(ratings[valid].mean())
    scale_ok = float(ratings[valid].max()) <= 5
    low_share = float((ratings[valid] <= 2).mean() * 100) if scale_ok else None
    if not scale_ok:
        _gap(ctx, "Ratings go above 5, so the share of low ratings was not calculated.")

    note = "{:,} reviews".format(n)
    dc = _find(df, "review_date", "date", "created_at")
    if dc is not None:
        rdates = _dt(df[dc])
        rend = rdates.max()
        if pd.notna(rend):
            cur = ratings[valid & _mask(df, dc, rend, 30)]
            prev = ratings[valid & _mask(df, dc, rend, 30, 30)]
            if len(cur) >= 5 and len(prev) >= 5:
                note += " | last 30 days {:+.2f} vs prior 30".format(cur.mean() - prev.mean())
    _set_kpi(ctx, "rating", "{:.2f}{}".format(avg, " / 5" if scale_ok else ""), note)
    ctx["facts"].update(avg_rating=avg)

    pid = _find(df, "product_id")
    ppid = _find(products, "product_id")
    if pid is not None and ppid is not None:
        name_col = _find(products, "product_name", "name", "title") or ppid
        frame = pd.DataFrame({"pid": df[pid].astype(str), "rating": ratings})
        grouped = frame.dropna().groupby("pid")["rating"].agg(["mean", "count"])
        grouped = grouped[grouped["count"] >= 5]
        if not grouped.empty:
            names = products.drop_duplicates(ppid).set_index(products[ppid].astype(str))[name_col].astype(str)
            low = grouped.sort_values("mean").head(8).reset_index()
            low["product"] = low["pid"].map(names).fillna(low["pid"])
            low = low.rename(columns={"mean": "avg_rating", "count": "reviews"})
            low["avg_rating"] = low["avg_rating"].round(2)
            ctx["charts"]["low_rated_products"] = low[["product", "avg_rating", "reviews"]]
            ctx["facts"]["lowest_product"] = (low.iloc[0]["product"], float(low.iloc[0]["avg_rating"]))

    if n >= 20 and ((low_share is not None and low_share >= T["low_rating_share_pct"]) or avg < T["avg_rating"]):
        ratio = max(T["avg_rating"] / avg if avg else 0,
                    (low_share or 0) / T["low_rating_share_pct"])
        finding = "Average rating is {:.2f} across {:,} reviews".format(avg, n)
        if low_share is not None:
            finding += "; {:.0f}% of reviews are 1-2 stars".format(low_share)
        finding += "."
        lowest = ctx["facts"].get("lowest_product")
        if lowest:
            finding += " Lowest-rated product with 5+ reviews: {} ({:.2f}).".format(lowest[0], lowest[1])
        _add_problem(
            ctx, "Feedback", "Customer ratings are weak", ratio, finding,
            "Ratings alone do not show why customers are unhappy. Review text, delivery experience and "
            "product quality are all possible factors.",
            "Read the lowest-rated reviews, group them by product, and follow up on recurring complaints.",
        )


def _section_catalog(ctx):
    items, products = ctx["df"]["order_items.csv"], ctx["df"]["products.csv"]
    if items is None or products is None:
        _gap(ctx, "order_items.csv and products.csv are both needed for product and category performance.")
        return
    ipid, ppid = _find(items, "product_id"), _find(products, "product_id")
    if ipid is None or ppid is None:
        _gap(ctx, "product_id is missing from order_items.csv or products.csv, so product performance is unavailable.")
        return
    qc = _find(items, "quantity", "qty")
    units = _num(items[qc]).fillna(0) if qc is not None else pd.Series(1, index=items.index)
    if qc is None:
        _gap(ctx, "order_items.csv has no quantity column, so each row counts as one unit.")
    by_pid = pd.DataFrame({"pid": items[ipid].astype(str), "units": units}).groupby("pid")["units"].sum()

    catc = _find(products, "category", "product_category")
    name_col = _find(products, "product_name", "name", "title")
    prod = products.copy()
    prod[ppid] = prod[ppid].astype(str)
    prod = prod.drop_duplicates(ppid).set_index(ppid)

    if catc is not None:
        cats = pd.Series(
            [prod[catc].get(p, "Unknown") for p in by_pid.index], index=by_pid.index
        ).fillna("Unknown")
        by_cat = by_pid.groupby(cats).sum().sort_values(ascending=False)
        ctx["charts"]["category_units"] = pd.DataFrame(
            {"category": by_cat.index[:8], "units": by_cat.values[:8].astype(int)}
        )
        if by_cat.sum() > 0:
            ctx["facts"]["top_category"] = (by_cat.index[0], float(by_cat.iloc[0] / by_cat.sum() * 100))
    else:
        _gap(ctx, "products.csv has no category column, so category performance is unavailable.")
    if name_col is not None:
        top = by_pid.sort_values(ascending=False).head(5)
        ctx["facts"]["top_products"] = [(str(prod[name_col].get(p, p)), int(u)) for p, u in top.items()]


def _section_marketing(ctx):
    df = ctx["df"]["marketing_campaigns.csv"]
    if df is None:
        _gap(ctx, "marketing_campaigns.csv was not found, so campaign performance is unavailable.")
        return
    name_c = _find(df, "campaign_name", "campaign", "name")
    spend_c = _find(df, "spend", "budget", "cost", "amount_spent", "ad_spend")
    rev_c = _find(df, "revenue", "revenue_generated", "sales", "revenue_attributed")
    conv_c = _find(df, "conversions", "orders", "orders_generated", "purchases")
    if name_c is None or spend_c is None or (rev_c is None and conv_c is None):
        _gap(ctx, "marketing_campaigns.csv does not have the campaign name, spend and results columns needed "
                  "to compare campaigns.")
        return
    spend = _num(df[spend_c])
    if rev_c is not None:
        result = _num(df[rev_c])
        frame = pd.DataFrame({"campaign": df[name_c].astype(str), "spend": spend, "result": result})
        frame = frame[(frame["spend"] > 0) & frame["result"].notna()]
        frame["ratio"] = (frame["result"] / frame["spend"]).round(2)
        ctx["facts"]["marketing_metric"] = "Reported revenue per \u20b91 of spend"
    else:
        result = _num(df[conv_c])
        frame = pd.DataFrame({"campaign": df[name_c].astype(str), "spend": spend, "result": result})
        frame = frame[(frame["result"] > 0) & frame["spend"].notna()]
        frame["ratio"] = (frame["spend"] / frame["result"]).round(2)
        ctx["facts"]["marketing_metric"] = "Spend per conversion (\u20b9, lower is better)"
    if frame.empty:
        _gap(ctx, "marketing_campaigns.csv has no rows with usable spend and results.")
        return
    ascending = rev_c is None
    ctx["charts"]["campaigns"] = frame.sort_values("ratio", ascending=ascending).head(8)[
        ["campaign", "spend", "result", "ratio"]
    ]
    _gap(ctx, "Campaign figures are as recorded in marketing_campaigns.csv. Attribution to orders is not verified.")


def _section_customers(ctx):
    df = ctx["df"]["customers.csv"]
    if df is None:
        _gap(ctx, "customers.csv was not found, so customer counts are unavailable.")
        return
    total = len(df)
    sc = _find(df, "customer_status")
    note = "All customers on record"
    if sc is not None:
        active = int(df[sc].fillna("").astype(str).str.strip().str.lower().eq("active").sum())
        note = "{:,} marked Active".format(active)
    _set_kpi(ctx, "customers", "{:,}".format(total), note)


# ---------- assembly ----------

def _build_summary(ctx, problems):
    f, end = ctx["facts"], ctx["end"]
    parts = []
    if "orders_cur" in f:
        sentence = "In the 7 days ending {:%d %b %Y}, the store recorded {:,} orders".format(end, f["orders_cur"])
        if f.get("orders_change") is not None:
            sentence += " ({:+.1f}% vs the previous 7 days)".format(f["orders_change"])
        if "coll_cur" in f:
            sentence += " and {} in gross successful payment collections".format(_money(f["coll_cur"]))
            if f.get("coll_change") is not None:
                sentence += " ({:+.1f}%)".format(f["coll_change"])
            sentence += "; refunds are reported separately"
        parts.append(sentence + ".")
    elif "coll_cur" in f:
        parts.append("In the 7 days ending {:%d %b %Y}, gross successful payment collections were {}.".format(
            end, _money(f["coll_cur"])))
    else:
        parts.append("There is not enough dated order or payment data to summarize recent performance.")
    if "pay_success" in f:
        parts.append("The payment success rate across all records is {:.1f}%.".format(f["pay_success"]))
    if problems:
        parts.append("{} item{} crossed {} investigation threshold{}; the highest priority is: {}.".format(
            len(problems), "" if len(problems) == 1 else "s",
            "its" if len(problems) == 1 else "their", "" if len(problems) == 1 else "s",
            problems[0]["title"].rstrip(".")))
    else:
        parts.append("No monitored metric crossed its investigation threshold.")
    return " ".join(parts)


def build_daily_briefing(uploaded_data=None):
    """Calculate the Daily Business Briefing from the CSV files in data/."""
    ctx = _new_ctx(uploaded_data=uploaded_data)
    for section, label in (
        (_section_dates, "Date range"),
        (_section_orders, "Orders"),
        (_section_payments, "Payments"),
        (_section_shipments, "Shipments"),
        (_section_returns, "Returns"),
        (_section_reviews, "Customer reviews"),
        (_section_catalog, "Product performance"),
        (_section_marketing, "Marketing"),
        (_section_customers, "Customers"),
    ):
        _safe(section, ctx, label)

    problems = sorted(ctx["problems"], key=lambda p: p["ratio"], reverse=True)
    for rank, problem in enumerate(problems, start=1):
        problem["rank"] = rank

    actions, seen = [], set()
    for problem in problems:
        if problem["action"] not in seen:
            seen.add(problem["action"])
            actions.append({"priority": len(actions) + 1, "action": problem["action"], "area": problem["area"]})
        if len(actions) == 5:
            break
    if not problems:
        actions.append({
            "priority": 1, "area": "General",
            "action": "No threshold was crossed. Keep checking this briefing regularly and watch the trend charts.",
        })
    if ctx["limitations"]:
        actions.append({
            "priority": len(actions) + 1, "area": "Data",
            "action": "Fill the data gaps listed under Data notes so more of the briefing can be calculated.",
        })

    notes = list(ctx["limitations"])
    if ctx["end"] is not None:
        notes.append(
            "Windows end at the latest date found in the data ({:%d %b %Y}), not today's date. "
            "Problem thresholds are investigation starting points, not industry benchmarks.".format(ctx["end"])
        )

    return {
        "generated_at": datetime.now().strftime("%d %b %Y, %H:%M"),
        "data_through": ctx["end"].strftime("%d %b %Y") if ctx["end"] is not None else None,
        "summary": _build_summary(ctx, problems),
        "kpis": [ctx["kpis"][key] for key, _ in KPI_DEFS],
        "problems": problems,
        "actions": actions,
        "charts": ctx["charts"],
        "marketing_metric": ctx["facts"].get("marketing_metric"),
        "limitations": notes,
        "thresholds": THRESHOLDS,
    }


# --------------------------------------------------
# DAILY BUSINESS BRIEFING
# --------------------------------------------------
def get_briefing():
    uploaded_data = st.session_state.get("uploaded_data", {})
    return build_daily_briefing(uploaded_data=uploaded_data)

def problem_card(problem):
    severity = problem["severity"].lower()
    return (
        '<div class="problem-card {sev}"><div class="problem-head">'
        '<div class="problem-rank">{rank}</div><div class="problem-title">{title}</div>'
        '<span class="sev {sev}">{severity}</span></div>'
        '<div class="problem-row"><span class="tag confirmed">Confirmed finding</span><span>{finding}</span></div>'
        '<div class="problem-row"><span class="tag possible">Possible explanation</span><span>{possible}</span></div>'
        '<div class="problem-row"><span class="tag reco">Recommendation</span><span>{action}</span></div></div>'
    ).format(
        sev=esc(severity), rank=problem["rank"], title=esc(problem["title"]),
        severity=esc(problem["severity"]), finding=esc(problem["finding"]),
        possible=esc(problem["possible"]), action=esc(problem["action"]),
    )


def render_briefing():
    left, right = st.columns([5, 1])
    with left:
        page_header("Daily Business Briefing", "How the business is doing, what to investigate first, and what to do next.")
    with right:
        st.write("")
        if st.button("↻ Refresh", key="refresh_briefing"):
            st.cache_data.clear()
            st.rerun()

    try:
        briefing = get_briefing()
    except Exception as exc:  # noqa: BLE001
        st.error("The briefing could not be calculated: {}: {}".format(type(exc).__name__, exc))
        return

    through = briefing["data_through"] or "no dated data found"
    st.markdown(
        '<div class="summary-card">{}<div class="summary-meta">Generated {} | Data through {}</div></div>'.format(
            esc(briefing["summary"]), esc(briefing["generated_at"]), esc(through)),
        unsafe_allow_html=True,
    )

    section_header("Key metrics", "Gross collections and refunds are shown separately. Neither is net revenue or profit.")
    kpis = [dict(label=k["label"], value=k["value"], note=k["note"], delta=k["delta"], tone=k["tone"])
            for k in briefing["kpis"]]
    kpi_row(kpis[:4])
    kpi_row(kpis[4:])

    section_header("Problems to Investigate",
                   "Ranked by how far each metric is above its investigation threshold. "
                   "Findings are calculated from your data; explanations are possibilities only.")
    if briefing["problems"]:
        for problem in briefing["problems"]:
            st.markdown(problem_card(problem), unsafe_allow_html=True)
    else:
        st.success("No monitored metric crossed its investigation threshold in the available data.")

    section_header("Recommended Actions", "Practical next steps, in priority order.")
    for action in briefing["actions"]:
        st.markdown(
            '<div class="action-item"><div class="action-num">{}</div><div>{}<div class="action-area">{}</div></div></div>'.format(
                action["priority"], esc(action["action"]), esc(action["area"])),
            unsafe_allow_html=True,
        )

    charts = briefing["charts"]
    tiles = []
    if "orders_trend" in charts:
        tiles.append(("Daily orders", "Last 30 days of data",
                      line_chart(charts["orders_trend"], "date", "orders", INDIGO, "Orders")))
    if "collections_trend" in charts:
        tiles.append(("Daily gross collections", "Successful payments only, last 30 days of data",
                      line_chart(charts["collections_trend"], "date", "collections", TEAL, "\u20b9 collected")))
    if "payment_methods" in charts and not charts["payment_methods"].empty:
        tiles.append(("Payment failure rate by method", "Dashed line = 6% investigation threshold",
                      hbar_chart(charts["payment_methods"], "method", "failure_rate", CORAL, "Failure rate (%)", rule=6)))
    if "carrier_delays" in charts and not charts["carrier_delays"].empty:
        tiles.append(("Shipment delay rate by carrier", "Dashed line = 15% investigation threshold",
                      hbar_chart(charts["carrier_delays"], "carrier", "delay_rate", CORAL, "Delayed (%)", rule=15)))
    if "return_reasons" in charts and not charts["return_reasons"].empty:
        tiles.append(("Common return reasons", "Number of return records by reason",
                      hbar_chart(charts["return_reasons"], "reason", "count", MARIGOLD, "Returns")))
    if "category_units" in charts and not charts["category_units"].empty:
        tiles.append(("Units sold by category", "From order items joined to products",
                      hbar_chart(charts["category_units"], "category", "units", INDIGO, "Units")))
    if "low_rated_products" in charts and not charts["low_rated_products"].empty:
        tiles.append(("Lowest-rated products", "Products with 5 or more reviews",
                      hbar_chart(charts["low_rated_products"], "product", "avg_rating", SLATE, "Average rating")))
    if "campaigns" in charts and not charts["campaigns"].empty:
        tiles.append(("Marketing campaigns", briefing.get("marketing_metric") or "Campaign comparison",
                      hbar_chart(charts["campaigns"], "campaign", "ratio", TEAL, "Value")))

    if tiles:
        section_header("Trends and comparisons")
        for i in range(0, len(tiles), 2):
            columns = st.columns(2)
            for column, tile in zip(columns, tiles[i:i + 2]):
                with column:
                    chart_tile(*tile)

    with st.expander("Data notes and limitations"):
        if briefing["limitations"]:
            for note in briefing["limitations"]:
                st.markdown("- " + note)
        else:
            st.markdown("No data gaps were detected.")
        st.caption("Investigation thresholds used:")
        st.code(json.dumps(briefing["thresholds"], indent=2), language="json")


# --------------------------------------------------
# AI ASSISTANT
# --------------------------------------------------
def render_assistant():
    page_header("AI Assistant", "Ask about orders, customers, payments, policies, or public market research.")

    if handle_customer_query is None:
        st.error("The assistant could not be loaded. Check your .env keys and data files.")
        st.code(CHATBOT_ERROR)
        return

    if "messages" not in st.session_state:
        st.session_state.messages = []

    if st.session_state.messages and st.button("Clear conversation", key="clear_chat"):
        st.session_state.messages = []
        st.rerun()

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if message.get("activity"):
                with st.expander("What the assistant did"):
                    for step in message["activity"]:
                        st.markdown("- " + step)

    prompt = st.chat_input("Ask OpsPilot anything about your business...")
    if prompt:
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    result = handle_customer_query(prompt)
                    answer, activity = result["answer"], result.get("activity", [])
                except Exception as exc:  # noqa: BLE001
                    answer = "Sorry, something went wrong while answering: {}: {}".format(type(exc).__name__, exc)
                    activity = []
            st.markdown(answer)
            if activity:
                with st.expander("What the assistant did"):
                    for step in activity:
                        st.markdown("- " + step)
        st.session_state.messages.append({"role": "assistant", "content": answer, "activity": activity})


# --------------------------------------------------
# DATA EXPLORER
# --------------------------------------------------
def render_explorer():
    page_header("Data Explorer", "Browse and search the raw CSV files behind OpsPilot.")
    available = [f for f in DATA_FILES if (DATA_DIR / f).exists()]
    if not available:
        st.warning("No CSV files were found in the data folder: {}".format(DATA_DIR))
        return

    choice = st.selectbox("Dataset", available)
    df = load_csv(choice)
    if df is None:
        st.error("{} could not be read.".format(choice))
        return

    kpi_row([
        dict(label="Rows", value="{:,}".format(len(df)), note=choice),
        dict(label="Columns", value="{:,}".format(df.shape[1]), note="Fields in this file"),
        dict(label="Missing cells", value="{:,}".format(int(df.isna().sum().sum())), note="Empty values across all columns"),
    ])

    query = st.text_input("Search all columns", placeholder="Type to filter rows...")
    view = df
    if query:
        matches = df.astype(str).apply(lambda col: col.str.contains(query, case=False, na=False, regex=False))
        view = df[matches.any(axis=1)]
    st.caption("Showing {:,} of {:,} rows".format(len(view), len(df)))
    stretch(st.dataframe, view)

    st.download_button("Download shown rows as CSV", view.to_csv(index=False).encode("utf-8"),
                       file_name="filtered_" + choice, mime="text/csv")
    with st.expander("Column types"):
        st.dataframe(pd.DataFrame({"column": df.columns, "type": [str(t) for t in df.dtypes]}), hide_index=True)

# --------------------------------------------------
# UPLOAD DATA
# --------------------------------------------------

def render_upload_data():
    page_header(
        "Upload Data",
        "Upload your own e-commerce CSV files for private session-based analysis."
    )

    st.info(
        "For this first version, upload files using the expected dataset "
        "filenames. Your uploads stay in this browser session and do not "
        "overwrite the sample CSV files in the data folder."
    )

    # Each visitor's uploaded DataFrames live in their own session state.
    if "uploaded_data" not in st.session_state:
        st.session_state["uploaded_data"] = {}

    uploaded_files = st.file_uploader(
        "Choose CSV files",
        type=["csv"],
        accept_multiple_files=True,
        help=(
            "Use filenames such as orders.csv, payments.csv, "
            "customers.csv and products.csv."
        ),
        key="ops_upload_files",
    )

    if uploaded_files:
        valid_uploads = {}
        errors = []

        for uploaded_file in uploaded_files:
            filename = uploaded_file.name

            # Accept only datasets recognized by the current project.
            if filename not in DATA_FILES:
                errors.append(
                    "{}: unsupported filename.".format(filename)
                )
                continue

            try:
                df = pd.read_csv(uploaded_file)

                if df.empty:
                    errors.append(
                        "{}: the file has no data rows.".format(filename)
                    )
                    continue

                if len(df.columns) == 0:
                    errors.append(
                        "{}: no columns were found.".format(filename)
                    )
                    continue

                if df.columns.duplicated().any():
                    errors.append(
                        "{}: duplicate column names were found.".format(
                            filename
                        )
                    )
                    continue

                # Basic validation passed; keep the DataFrame in this session.
                valid_uploads[filename] = df

            except Exception as exc:
                errors.append(
                    "{}: could not read CSV ({}).".format(
                        filename, type(exc).__name__
                    )
                )

        if valid_uploads:
            st.session_state["uploaded_data"].update(valid_uploads)
            st.success(
                "Validated and loaded {} file(s) into this session.".format(
                    len(valid_uploads)
                )
            )

        for error in errors:
            st.error(error)

    session_data = st.session_state["uploaded_data"]

    st.subheader("Your uploaded datasets")

    if not session_data:
        st.caption("No valid files uploaded yet.")
        return

    summary = pd.DataFrame([
        {
            "Dataset": name,
            "Rows": len(df),
            "Columns": len(df.columns),
            "Missing cells": int(df.isna().sum().sum()),
        }
        for name, df in sorted(session_data.items())
    ])

    st.dataframe(summary, hide_index=True, use_container_width=True)

    selected_file = st.selectbox(
        "Preview an uploaded dataset",
        list(sorted(session_data.keys())),
    )

    st.dataframe(
        session_data[selected_file].head(20),
        hide_index=True,
        use_container_width=True,
    )

    if st.button("Clear my uploaded data"):
        st.session_state["uploaded_data"] = {}
        st.rerun()


# --------------------------------------------------
# ROUTER
# --------------------------------------------------
selected_page = render_sidebar()

if selected_page == "Dashboard":
    render_dashboard()
elif selected_page == "Daily Briefing":
    render_briefing()
elif selected_page == "AI Assistant":
    render_assistant()
elif selected_page == "Data Explorer":
    render_explorer()
elif selected_page == "Upload Data":
    render_upload_data()