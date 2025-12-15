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

    # 🔥 CRITICAL FIX: Clean + normalize dates
    df["Request Date"] = (
        pd.to_datetime(
            df["Request Date"]
            .astype(str)
            .str.strip(),
            dayfirst=True,
            errors="coerce"
        )
        .dt.date
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

if view == "This Week":
    start_date = today - timedelta(days=today.weekday())
    end_date = start_date + timedelta(days=6)

elif view == "Last Week":
    end_date = today - timedelta(days=today.weekday() + 1)
    start_date = end_date - timedelta(days=6)

elif view == "This Month":
    start_date = today.replace(day=1)
    end_date = today

else:  # This Year
    start_date = today.replace(month=1, day=1)
    end_date = today

filtered_df = df[
    (df["Request Date"] >= start_date) &
    (df["Request Date"] <= end_date)
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
    st.dataframe(category_table, width="stretch")
else:
    st.info("No category data available for this period.")

# -------------------------------------------------
# CHARTS (SAFE)
# -------------------------------------------------
st.divider()
st.subheader("📊 Visual Insights")

col_left, col_right = st.columns(2)

# ---- PIE CHART: Status Distribution ----
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
    col_left.info("No status data available for this period.")
# ---- BAR CHART: Level vs Status ----

# 🔧 Normalize Level values
filtered_df["L1/L2/L3"] = (
    filtered_df["L1/L2/L3"]
    .astype(str)
    .str.strip()
    .str.upper()
)

level_status = (
    filtered_df
    .groupby(["L1/L2/L3", "Status"])
    .size()
    .unstack(fill_value=0)
    .reindex(["L1", "L2", "L3"])  # enforce correct order
)

if (
    not level_status.empty
    and level_status.select_dtypes("number").sum().sum() > 0
):
    fig2, ax2 = plt.subplots()
    level_status.plot(kind="bar", ax=ax2)
    ax2.set_title("Ticket Status by Level")
    ax2.set_xlabel("Level")
    ax2.set_ylabel("Count")
    ax2.tick_params(axis="x", rotation=0)
    col_right.pyplot(fig2)
else:
    col_right.info("No level/status data available for chart.")


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
