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
# GOOGLE SHEET
# -------------------------------------------------
GOOGLE_SHEET_CSV_URL = (
    "https://docs.google.com/spreadsheets/d/"
    "16IrnodH0VlT0mPNk9HahizoX3LTR7CwZzxd0rsXwTuw"
    "/export?format=csv"
)

# -------------------------------------------------
# LOAD DATA
# -------------------------------------------------
@st.cache_data(ttl=30)
def load_data():
    df = pd.read_csv(GOOGLE_SHEET_CSV_URL)

    df["Request Date"] = pd.to_datetime(
        df["Request Date"].astype(str).str.strip(),
        dayfirst=True,
        errors="coerce"
    )

    df = df.dropna(subset=["Request Date"])

    # 🔥 HARD YEAR + MONTH COLUMNS
    df["YEAR"] = df["Request Date"].dt.year
    df["MONTH"] = df["Request Date"].dt.month
    df["DATE"] = df["Request Date"].dt.date

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

today = datetime.today()
current_year = today.year
current_month = today.month

# -------------------------------------------------
# FILTER LOGIC (FIXED)
# -------------------------------------------------
if view == "This Week":
    start_date = today.date() - timedelta(days=today.weekday())
    end_date = today.date()

    filtered_df = df[
        (df["DATE"] >= start_date) &
        (df["DATE"] <= end_date)
    ]

elif view == "Last Week":
    end_date = today.date() - timedelta(days=today.weekday() + 1)
    start_date = end_date - timedelta(days=6)

    filtered_df = df[
        (df["DATE"] >= start_date) &
        (df["DATE"] <= end_date)
    ]

elif view == "This Month":
    # 🔥 BULLETPROOF FIX
    filtered_df = df[
        (df["YEAR"] == current_year) &
        (df["MONTH"] == current_month)
    ]

else:  # This Year
    filtered_df = df[df["YEAR"] == current_year]

# -------------------------------------------------
# HEADER
# -------------------------------------------------
st.title("📊 PMP Automated Ticket Dashboard")
st.caption(
    f"Showing data for {view} | Year: {current_year}"
)

# -------------------------------------------------
# METRICS
# -------------------------------------------------
col1, col2, col3, col4 = st.columns(4)

col1.metric("Total Tickets", len(filtered_df))
col2.metric("Open", (filtered_df["Status"] == "Open").sum())
col3.metric("Closed", (filtered_df["Status"] == "Closed").sum())
col4.metric("In-Progress", (filtered_df["Status"] == "In-Progress").sum())

# -------------------------------------------------
# OWNERSHIP
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
    st.info("No data available")

# -------------------------------------------------
# CHARTS
# -------------------------------------------------
st.divider()
st.subheader("📊 Visual Insights")

col_left, col_right = st.columns(2)

# PIE
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

# BAR
level_status = (
    filtered_df
    .groupby(["L1/L2/L3", "Status"])
    .size()
    .unstack(fill_value=0)
)

level_status = level_status[level_status.sum(axis=1) > 0]

if not level_status.empty:
    fig2, ax2 = plt.subplots(figsize=(5, 3))
    level_status.plot(kind="bar", ax=ax2, width=0.5)

    ax2.set_title("Ticket Status by Level")
    ax2.set_xlabel("Level")
    ax2.set_ylabel("Count")
    ax2.tick_params(axis="x", rotation=0)

    ax2.legend(
        title="Status",
        bbox_to_anchor=(1.02, 1),
        loc="upper left"
    )

    col_right.pyplot(fig2, use_container_width=True)

# -------------------------------------------------
# DOWNLOAD
# -------------------------------------------------
st.divider()
st.download_button(
    "⬇️ Download Filtered Data",
    filtered_df.to_csv(index=False),
    "pmp_filtered_report.csv",
    "text/csv"
)
