"""
Time Dashboard - a live, filterable view of where the week goes.

Data sources (pick in the sidebar):
  1. Google Calendar  - live, via a service account (see README to set up)
  2. Upload CSV       - columns: Week Start, Week End, Category, Hours
  3. Sample week      - bundled Jul 27-31 data, so it works with zero setup

Categorization rules live in categories.py - edit there to refine buckets.
"""
import datetime as dt
from datetime import timedelta

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from categories import COLORS, classify, color_for

st.set_page_config(page_title="Time Dashboard", page_icon="⏱️", layout="wide")

TZ = st.secrets.get("timezone", "Asia/Dubai") if hasattr(st, "secrets") else "Asia/Dubai"


# ----------------------------------------------------------------------
# Data loading
# ----------------------------------------------------------------------
def week_label(d: dt.date) -> str:
    monday = d - timedelta(days=d.weekday())
    friday = monday + timedelta(days=4)
    return f"{monday:%b %d} \u2013 {friday:%d}"


def week_monday(d: dt.date) -> dt.date:
    return d - timedelta(days=d.weekday())


@st.cache_resource(show_spinner=False)
def calendar_service():
    from google.oauth2 import service_account
    from googleapiclient.discovery import build
    info = dict(st.secrets["gcp_service_account"])
    creds = service_account.Credentials.from_service_account_info(
        info, scopes=["https://www.googleapis.com/auth/calendar.readonly"]
    )
    return build("calendar", "v3", credentials=creds, cache_discovery=False)


@st.cache_data(ttl=1800, show_spinner="Reading your calendar\u2026")
def load_from_calendar(cal_id: str, start: dt.date, end: dt.date) -> pd.DataFrame:
    svc = calendar_service()
    tmin = dt.datetime.combine(start, dt.time.min).isoformat() + "Z"
    tmax = dt.datetime.combine(end, dt.time.max).isoformat() + "Z"
    items, page = [], None
    while True:
        resp = svc.events().list(
            calendarId=cal_id, timeMin=tmin, timeMax=tmax,
            singleEvents=True, orderBy="startTime",
            pageToken=page, maxResults=2500,
        ).execute()
        items += resp.get("items", [])
        page = resp.get("nextPageToken")
        if not page:
            break

    rows = []
    for ev in items:
        start_o = ev.get("start", {})
        end_o = ev.get("end", {})
        if "dateTime" not in start_o:          # skip all-day events
            continue
        # skip events the user declined
        declined = any(
            a.get("email") == cal_id and a.get("responseStatus") == "declined"
            for a in ev.get("attendees", [])
        )
        if declined:
            continue
        s = pd.to_datetime(start_o["dateTime"])
        e = pd.to_datetime(end_o["dateTime"])
        hrs = (e - s).total_seconds() / 3600
        if hrs <= 0:
            continue
        d = s.date()
        rows.append({
            "date": d,
            "week_monday": week_monday(d),
            "week": week_label(d),
            "category": classify(ev.get("summary", "")),
            "hours": hrs,
        })
    return pd.DataFrame(rows)


def load_from_csv(file) -> pd.DataFrame:
    raw = pd.read_csv(file)
    raw.columns = [c.strip().lower() for c in raw.columns]
    ws = pd.to_datetime(raw["week start"]).dt.date
    return pd.DataFrame({
        "date": ws,
        "week_monday": ws.map(week_monday),
        "week": ws.map(week_label),
        "category": raw["category"].astype(str),
        "hours": pd.to_numeric(raw["hours"], errors="coerce").fillna(0),
    })


def sample_frame() -> pd.DataFrame:
    data = [
        ("Admin, Email & Misc", 9.92), ("Inventory / Forecasting", 6.75),
        ("Break / Lunch", 6.5), ("Refurbishment", 4.5), ("Ciao / Delivery Ops", 4.0),
        ("Tech / Systems", 3.75), ("Recurring Syncs", 2.58), ("Hiring & SOP", 2.08),
        ("1:1s & Catchups", 2.0), ("Shipa Transition", 0.92),
        ("Order Management", 0.5), ("Supplier Syncs", 0.33),
    ]
    ws = dt.date(2026, 7, 27)
    return pd.DataFrame([{
        "date": ws, "week_monday": ws, "week": week_label(ws),
        "category": c, "hours": h,
    } for c, h in data])


# ----------------------------------------------------------------------
# Sidebar - source + filters
# ----------------------------------------------------------------------
st.sidebar.title("⏱️  Time Dashboard")
source = st.sidebar.radio(
    "Data source",
    ["Google Calendar", "Upload CSV", "Sample week"],
    index=2,
    help="Calendar is live once secrets are configured (see README).",
)

df = pd.DataFrame()
if source == "Google Calendar":
    has_creds = hasattr(st, "secrets") and "gcp_service_account" in st.secrets
    if not has_creds:
        st.sidebar.warning("Calendar not configured yet. Add service-account "
                           "secrets (see README) or use Sample / CSV.")
    else:
        cal_id = st.sidebar.text_input(
            "Calendar ID",
            value=st.secrets.get("default_calendar_id", ""),
        )
        today = dt.date.today()
        default_start = today - timedelta(days=28)
        start, end = st.sidebar.date_input(
            "Date range", value=(default_start, today),
        )
        if cal_id:
            try:
                df = load_from_calendar(cal_id, start, end)
            except Exception as exc:
                st.sidebar.error(f"Couldn't read calendar: {exc}")

elif source == "Upload CSV":
    up = st.sidebar.file_uploader("Tracking CSV", type=["csv"])
    if up:
        df = load_from_csv(up)
    else:
        st.sidebar.info("Upload a CSV with: Week Start, Week End, Category, Hours")

else:
    df = sample_frame()

excl_break = st.sidebar.checkbox("Exclude breaks & lunch", value=False)

st.sidebar.markdown("---")
st.sidebar.caption("Categories & colours are defined in **categories.py**. "
                   "Edit that file to refine buckets, then redeploy.")

# ----------------------------------------------------------------------
# Guard
# ----------------------------------------------------------------------
if df.empty:
    st.title("Time Dashboard")
    st.info("Pick a data source in the sidebar to get started. "
            "**Sample week** works with no setup.")
    st.stop()

if excl_break:
    df = df[df["category"] != "Break / Lunch"]

# aggregate to (week, category)
agg = (df.groupby(["week_monday", "week", "category"], as_index=False)["hours"]
         .sum().sort_values("week_monday"))

weeks = agg.drop_duplicates("week_monday").sort_values("week_monday")
week_options = list(weeks["week"])
latest = week_options[-1]

# ----------------------------------------------------------------------
# Header + week picker
# ----------------------------------------------------------------------
left, right = st.columns([3, 1])
left.title("Time Dashboard")
left.caption("Where the week actually goes \u00b7 " + source)
focus_week = right.selectbox("Week in focus", week_options,
                             index=len(week_options) - 1)

cur = agg[agg["week"] == focus_week].sort_values("hours", ascending=False)
total = cur["hours"].sum()
work = cur[cur["category"] != "Break / Lunch"]["hours"].sum()
top = cur.iloc[0]

# previous week (for deltas)
mondays = list(weeks["week_monday"])
cur_monday = weeks[weeks["week"] == focus_week]["week_monday"].iloc[0]
prev = None
if mondays.index(cur_monday) > 0:
    pm = mondays[mondays.index(cur_monday) - 1]
    prev = agg[agg["week_monday"] == pm].set_index("category")["hours"].to_dict()

# ----------------------------------------------------------------------
# KPI row
# ----------------------------------------------------------------------
k1, k2, k3, k4 = st.columns(4)
k1.metric("Total tracked", f"{total:.1f} hrs")
k2.metric("Work hours", f"{work:.1f} hrs", help="Excludes breaks & lunch")
top_delta = None
if prev is not None:
    d = top["hours"] - prev.get(top["category"], 0)
    top_delta = f"{d:+.1f} vs last wk"
k3.metric("Biggest focus", top["category"], top_delta)
k4.metric("Share of top", f"{top['hours']/total*100:.0f}%")

# ----------------------------------------------------------------------
# Week-at-a-glance spine
# ----------------------------------------------------------------------
st.markdown("##### Week at a glance")
seg = "".join(
    f'<span title="{r.category}: {r.hours:.1f} hrs" '
    f'style="width:{r.hours/total*100:.4f}%;background:{color_for(r.category)};'
    f'display:block;height:100%"></span>'
    for r in cur.itertuples()
)
st.markdown(
    f'<div style="display:flex;height:30px;border-radius:8px;overflow:hidden;'
    f'border:1px solid #e3eaef">{seg}</div>', unsafe_allow_html=True)

# ----------------------------------------------------------------------
# Donut + bar
# ----------------------------------------------------------------------
c1, c2 = st.columns(2)
with c1:
    st.markdown("##### Share of time")
    fig = px.pie(cur, values="hours", names="category", hole=0.58,
                 color="category", color_discrete_map=COLORS)
    fig.update_traces(textposition="none",
                      hovertemplate="%{label}: %{value:.1f} hrs (%{percent})")
    fig.update_layout(showlegend=False, margin=dict(t=6, b=6, l=6, r=6), height=300)
    st.plotly_chart(fig, use_container_width=True)
with c2:
    st.markdown("##### Hours by focus area")
    fig = px.bar(cur.sort_values("hours"), x="hours", y="category",
                 orientation="h", color="category", color_discrete_map=COLORS)
    fig.update_traces(hovertemplate="%{y}: %{x:.1f} hrs<extra></extra>")
    fig.update_layout(showlegend=False, margin=dict(t=6, b=6, l=6, r=6),
                      height=300, xaxis_title=None, yaxis_title=None)
    st.plotly_chart(fig, use_container_width=True)

# ----------------------------------------------------------------------
# Week-on-week trend (only meaningful with 2+ weeks)
# ----------------------------------------------------------------------
if len(week_options) > 1:
    st.markdown("##### Week-on-week trend")
    trend = agg.copy()
    fig = px.bar(trend, x="week", y="hours", color="category",
                 color_discrete_map=COLORS, barmode="stack",
                 category_orders={"week": week_options})
    fig.update_layout(height=360, xaxis_title=None, yaxis_title="Hours",
                      legend_title=None, margin=dict(t=10, b=10))
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Only one week loaded - the week-on-week trend appears once a "
            "second week is in range. Widen the date range or add another week.")

# ----------------------------------------------------------------------
# Breakdown table
# ----------------------------------------------------------------------
st.markdown("##### Breakdown \u00b7 " + focus_week)
tbl = cur.copy()
tbl["share"] = (tbl["hours"] / total * 100).round(1).astype(str) + "%"
if prev is not None:
    tbl["vs last wk"] = tbl.apply(
        lambda r: "new" if r.category not in prev
        else f"{r.hours - prev[r.category]:+.1f}", axis=1)
tbl["hours"] = tbl["hours"].round(2)
show_cols = ["category", "hours", "share"] + (["vs last wk"] if prev is not None else [])
st.dataframe(tbl[show_cols], use_container_width=True, hide_index=True)
