import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import matplotlib.pyplot as plt

# -------------------------------------------------
# PAGE CONFIG
# -------------------------------------------------
st.set_page_config(
    page_title="PMP Ticket Dashboard",
    layout="wide"
)

# -------------------------------------------------
# GOOGLE SHEET (LIVE SOURCE)
# -------------------------------------------------
GOOGLE_SHEET_CSV_URL = (
    "https://docs.google.com/spreadsheets/d/"
    "16IrnodH0VlT0mPNk9HahizoX3LTR7CwZzxd0rsXwTuw"
    "/export?format=csv"
)

# -------------------------------------------------
# LOAD DATA
# -------------------------------------------------
@st.cache_data(ttl=60)
def load_data():
    df = pd.read_csv(GOOGLE_SHEET_CSV_URL)

    # ✅ FINAL DATE PARSE (YYYY-MM-DD only)
    df["Request Date"] = pd.to_datetime(
        df["Request Date"],
        format="%Y-%m-%d",
        errors="coerce"
    )

    return df

df = load_data()

# -------------------------------------------------
# SIDEBAR FILTERS
# -------------------------------------------------
st.sidebar.title("📅 Filters")

view = st.sidebar.selectbox(
    "Select View",
    ["This Week", "Last Week", "This Month", "This Year"]
)

today = datetime.today().date()
weekday = today.weekday()  # Monday = 0

# Week ranges (NO ISO WEEKS — SAFE)
this_week_start = today - timedelta(days=weekday)
this_week_end = today

last_week_start = this_week_start - timedelta(days=7)
last_week_end = this_week_start - timedelta(days=1)

# -------------------------------------------------
# APPLY FILTERS (🔥 THIS IS THE FIX)
# -------------------------------------------------
if view == "This Month":
    filtered_df = df[
        (df["Request Date"].dt.year == today.year) &
        (df["Request Date"].dt.month == today.month)
    ]

elif view == "This Year":
    filtered_df = df[
        df["Request Date"].dt.year == today.year
    ]

elif view == "This Week":
    filtered_df = df[
        (df["Request Date"].dt.date >= this_week_start) &
        (df["Request Date"].dt.date <= this_week_end)
    ]

else:  # Last Week
    filtered_df = df[
        (df["Request Date"].dt.date >= last_week_start) &
        (df["Request Date"].dt.date <= last_week_end)
    ]

# -------------------------------------------------
# HEADER
# -------------------------------------------------
st.title("📊 PMP Automated Ticket Dashboard")

st.caption(
    f"Showing {view} data | Rows: {len(filtered_df)}"
)

# -------------------------------------------------
# METRICS
# -------------------------------------------------
c1, c2, c3, c4 = st.columns(4)

c1.metric("Total Tickets", len(filtered_df))
c2.metric("Open", (filtered_df["Status"] == "Open").sum())
c3.metric("Closed", (filtered_df["Status"] == "Closed").sum())
c4.metric("In-Progress", (filtered_df["Status"] == "In-Progress").sum())

# -------------------------------------------------
# TICKET OWNERSHIP
# -------------------------------------------------
st.divider()
st.subheader("🧑‍💼 Ticket Ownership by Level")

def closed_by(level):
    return len(
        filtered_df[
            (filtered_df["Status"] == "Closed") &
            (filtered_df["L1/L2/L3"] == level)
        ]
    )

l1, l2, l3 = st.columns(3)
l1.metric("Closed by L1", closed_by("L1"))
l2.metric("Closed by L2", closed_by("L2"))
l3.metric("Closed by L3", closed_by("L3"))

# -------------------------------------------------
# CATEGORY TABLE
# -------------------------------------------------
st.divider()
st.subheader("📁 PMP Categories")

if not filtered_df.empty:
    category_table = (
        filtered_df
        .groupby(["Category", "L1/L2/L3"])
        .size()
        .unstack(fill_value=0)
        .reset_index()
    )
    st.dataframe(category_table, use_container_width=True)
else:
    st.info("No category data available.")

# -------------------------------------------------
# CHARTS
# -------------------------------------------------
st.divider()
st.subheader("📊 Visual Insights")

col_left, col_right = st.columns(2)

# ---- PIE CHART ----
status_counts = filtered_df["Status"].value_counts()

if not status_counts.empty:
    fig1, ax1 = plt.subplots()
    ax1.pie(
        status_counts,
        labels=status_counts.index,
        autopct="%1.0f%%",
        startangle=90
    )
    ax1.set_title("Ticket Status Distribution")
    col_left.pyplot(fig1)
else:
    col_left.info("No status data.")

# ---- BAR CHART ----
level_status = (
    filtered_df
    .groupby(["L1/L2/L3", "Status"])
    .size()
    .unstack(fill_value=0)
)

level_status = level_status[level_status.sum(axis=1) > 0]

if not level_status.empty:
    fig2, ax2 = plt.subplots(figsize=(5, 3))
    level_status.plot(kind="bar", ax=ax2)
    ax2.set_title("Ticket Status by Level")
    ax2.set_xlabel("Level")
    ax2.set_ylabel("Count")
    ax2.tick_params(axis="x", rotation=0)
    col_right.pyplot(fig2, use_container_width=True)
else:
    col_right.info("No level/status data.")

# -------------------------------------------------
# DOWNLOAD
# -------------------------------------------------
st.divider()
st.download_button(
    "⬇️ Download Filtered Data (CSV)",
    filtered_df.to_csv(index=False),
    "pmp_filtered_report.csv",
    "text/csv"
)
