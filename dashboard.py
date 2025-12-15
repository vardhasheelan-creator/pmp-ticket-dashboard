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
# LOAD DATA (AUTO REFRESH EVERY 60s)
# -------------------------------------------------
@st.cache_data(ttl=60)
def load_data():
    df = pd.read_csv(GOOGLE_SHEET_CSV_URL)

    # Parse dates safely
    df["Request Date"] = pd.to_datetime(
        df["Request Date"].astype(str).str.strip(),
        dayfirst=True,
        errors="coerce"
    )

    # 🔒 HARD FILTER: ONLY 2025 DATA
    df = df[df["Request Date"].dt.year == 2025]

    # Convert to date (after filtering)
    df["Request Date"] = df["Request Date"].dt.date

    return df

# -------------------------------------------------
# SIDEBAR FILTERS
# -------------------------------------------------
st.sidebar.title("📅 Filters")

view = st.sidebar.selectbox(
    "Select View",
    ["This Week", "Last Week", "This Month", "This Year"]
)

today = datetime.today().date()

# Compute date ranges
if view == "This Week":
    start_date = today - timedelta(days=today.weekday())
    end_date = start_date + timedelta(days=6)

elif view == "Last Week":
    today_iso = today.isocalendar()
    last_week_num = today_iso.week - 1
    year = today_iso.year

    # Compute start and end of last week
    start_date = datetime.strptime(f"{year}-W{last_week_num}-1", "%G-W%V-%u").date()
    end_date = datetime.strptime(f"{year}-W{last_week_num}-7", "%G-W%V-%u").date()

elif view == "This Month":
    start_date = today.replace(day=1)
    end_date = today

elif view == "This Year":
    start_date = today.replace(month=1, day=1)
    end_date = today

# Apply filter ensuring only CURRENT YEAR DATA is included
filtered_df = df[
    (pd.to_datetime(df["Request Date"]).dt.date >= start_date) &
    (pd.to_datetime(df["Request Date"]).dt.date <= end_date) &
    (pd.to_datetime(df["Request Date"]).dt.year == today.year)
]

# -------------------------------------------------
# HEADER
# -------------------------------------------------
st.title("📊 PMP Automated Ticket Dashboard")
st.caption(f"Showing data from {start_date} to {end_date}")

# -------------------------------------------------
# METRICS
# -------------------------------------------------
col1, col2, col3, col4 = st.columns(4)

col1.metric("Total Tickets", len(filtered_df))
col2.metric("Open", (filtered_df["Status"] == "Open").sum())
col3.metric("Closed", (filtered_df["Status"] == "Closed").sum())
col4.metric("In-Progress", (filtered_df["Status"] == "In-Progress").sum())

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

c1, c2, c3 = st.columns(3)
c1.metric("Closed by L1", closed_by("L1"))
c2.metric("Closed by L2", closed_by("L2"))
c3.metric("Closed by L3", closed_by("L3"))

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
    st.info("No category data available for this period.")

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
    col_left.info("No status data available.")

# ---- BAR CHART ----
level_order = ["L1", "L2", "L3"]

level_status = (
    filtered_df
    .groupby(["L1/L2/L3", "Status"])
    .size()
    .unstack(fill_value=0)
    .reindex(level_order, fill_value=0)
)

# Remove rows with zero total
level_status = level_status[level_status.sum(axis=1) > 0]

if not level_status.empty:
    fig2, ax2 = plt.subplots(figsize=(5, 3))

    level_status.plot(
        kind="bar",
        ax=ax2,
        width=0.5
    )

    ax2.set_title("Ticket Status by Level", fontsize=11)
    ax2.set_xlabel("Level")
    ax2.set_ylabel("Count")
    ax2.tick_params(axis="x", rotation=0)

    ax2.legend(
        title="Status",
        bbox_to_anchor=(1.02, 1),
        loc="upper left"
    )

    col_right.pyplot(fig2, use_container_width=True)
else:
    col_right.info("No level/status data available.")

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
