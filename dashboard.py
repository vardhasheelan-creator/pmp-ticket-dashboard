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
# LOAD DATA (SAFE DATE PARSING)
# -------------------------------------------------
@st.cache_data(ttl=60)
def load_data():
    df = pd.read_csv(GOOGLE_SHEET_CSV_URL)

    # 🔑 CRITICAL FIX: let pandas auto-detect format
    df["Request Date"] = pd.to_datetime(
        df["Request Date"],
        errors="coerce",
        infer_datetime_format=True
    ).dt.date

    # drop rows where date is invalid
    df = df.dropna(subset=["Request Date"])

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
    end_date = today

elif view == "Last Week":
    end_date = today - timedelta(days=today.weekday() + 1)
    start_date = end_date - timedelta(days=6)

elif view == "This Month":
    start_date = today.replace(day=1)
    end_date = today

else:
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
st.caption(
    f"Showing data from {start_date} to {end_date} | Rows: {len(filtered_df)}"
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

x1, x2, x3 = st.columns(3)
x1.metric("Closed by L1", closed_by("L1"))
x2.metric("Closed by L2", closed_by("L2"))
x3.metric("Closed by L3", closed_by("L3"))

# -------------------------------------------------
# CATEGORY TABLE
# -------------------------------------------------
st.divider()
st.subheader("📁 PMP Categories")

if not filtered_df.empty:
    category_table = (
        filtered_df
        .groupby(["Category"])
        .size()
        .reset_index(name="Tickets")
        .sort_values("Tickets", ascending=False)
    )
    st.dataframe(category_table, use_container_width=True)
else:
    st.info("No category data available for this period.")

# -------------------------------------------------
# CHARTS
# -------------------------------------------------
st.divider()
st.subheader("📊 Visual Insights")

left, right = st.columns(2)

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
    left.pyplot(fig1)
else:
    left.info("No status data available.")

# ---- BAR CHART ----
level_status = (
    filtered_df
    .groupby(["L1/L2/L3"])
    .size()
    .reindex(["L1", "L2", "L3"], fill_value=0)
)

if level_status.sum() > 0:
    fig2, ax2 = plt.subplots()
    level_status.plot(kind="bar", ax=ax2)
    ax2.set_title("Tickets by Support Level")
    ax2.set_xlabel("Level")
    ax2.set_ylabel("Tickets")
    ax2.tick_params(axis="x", rotation=0)
    right.pyplot(fig2)
else:
    right.info("No level data available.")

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
