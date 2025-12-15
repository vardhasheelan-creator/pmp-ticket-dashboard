import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from datetime import date, timedelta

# --------------------------------------------------
# Page config
# --------------------------------------------------
st.set_page_config(
    page_title="PMP Automated Ticket Dashboard",
    layout="wide"
)

st.title("📊 PMP Automated Ticket Dashboard")

# --------------------------------------------------
# Load data
# --------------------------------------------------
@st.cache_data
def load_data():
    df = pd.read_excel("data/tickets.xlsx")
    df["Request Date"] = pd.to_datetime(
        df["Request Date"], dayfirst=True, errors="coerce"
    )
    df["Request_Date_Only"] = df["Request Date"].dt.date
    return df

df = load_data()

# --------------------------------------------------
# Sidebar filters
# --------------------------------------------------
st.sidebar.header("📅 Filters")

filter_type = st.sidebar.selectbox(
    "Select View",
    ["This Week", "Last Week", "This Month", "This Year"]
)

today = date.today()

if filter_type == "This Week":
    start_date = today - timedelta(days=today.weekday())
    end_date = start_date + timedelta(days=6)

elif filter_type == "Last Week":
    end_date = today - timedelta(days=today.weekday() + 1)
    start_date = end_date - timedelta(days=6)

elif filter_type == "This Month":
    start_date = today.replace(day=1)
    end_date = today

else:  # This Year
    start_date = today.replace(month=1, day=1)
    end_date = today

filtered_df = df[
    (df["Request_Date_Only"] >= start_date) &
    (df["Request_Date_Only"] <= end_date)
]

st.subheader(f"Showing data from {start_date} to {end_date}")

# --------------------------------------------------
# TOP KPI CARDS
# --------------------------------------------------
k1, k2, k3, k4 = st.columns(4)

k1.metric("Total Tickets", len(filtered_df))
k2.metric("Open", (filtered_df["Status"] == "Open").sum())
k3.metric("Closed", (filtered_df["Status"] == "Closed").sum())
k4.metric("In-Progress", (filtered_df["Status"] == "In-Progress").sum())

st.divider()

# --------------------------------------------------
# LEVEL-WISE KPI LOGIC
# --------------------------------------------------
def level_status_count(level, status):
    return len(
        filtered_df[
            (filtered_df["L1/L2/L3"] == level) &
            (filtered_df["Status"] == status)
        ]
    )

st.subheader("🧑‍💼 Ticket Ownership by Level")

l1, l2, l3 = st.columns(3)
l1.metric("Closed by L1", level_status_count("L1", "Closed"))
l2.metric("Closed by L2", level_status_count("L2", "Closed"))
l3.metric("Closed by L3", level_status_count("L3", "Closed"))

i1, i2, i3 = st.columns(3)
i1.metric("In-Progress with L1", level_status_count("L1", "In-Progress"))
i2.metric("In-Progress with L2", level_status_count("L2", "In-Progress"))
i3.metric("In-Progress with L3", level_status_count("L3", "In-Progress"))

st.divider()

# --------------------------------------------------
# LEVEL vs STATUS TABLE
# --------------------------------------------------
st.subheader("📋 Level vs Status Breakdown")

if filtered_df.empty:
    st.info("No tickets available for selected period")
else:
    level_status_table = (
        filtered_df
        .groupby(["L1/L2/L3", "Status"])
        .size()
        .unstack(fill_value=0)
        .reset_index()
    )

    st.dataframe(level_status_table, use_container_width=True)

st.divider()

# --------------------------------------------------
# PMP CATEGORY TABLE (CLOSED TICKETS)
# --------------------------------------------------
st.subheader("📂 PMP Categories (Closed Tickets)")

if filtered_df.empty:
    st.info("No closed tickets in selected period")
else:
    category_table = (
        filtered_df[filtered_df["Status"] == "Closed"]
        .groupby(["Category", "L1/L2/L3"])
        .size()
        .unstack(fill_value=0)
        .reset_index()
    )

    st.dataframe(category_table, use_container_width=True)

# --------------------------------------------------
# DOWNLOAD CSV
# --------------------------------------------------
st.divider()
st.subheader("⬇️ Download Data")

csv = filtered_df.to_csv(index=False).encode("utf-8")

st.download_button(
    label="Download filtered data as CSV",
    data=csv,
    file_name="pmp_filtered_tickets.csv",
    mime="text/csv"
)

# --------------------------------------------------
# CHARTS SECTION (NO FORMAT CHANGES ABOVE)
# --------------------------------------------------
st.divider()
st.subheader("📊 Visual Insights")

if not filtered_df.empty:

    col1, col2 = st.columns(2)

    # -------------------------------
    # PIE CHART: Closed tickets by Level
    # -------------------------------
    closed_by_level = (
        filtered_df[filtered_df["Status"] == "Closed"]
        .groupby("L1/L2/L3")
        .size()
        .reset_index(name="Count")
    )

    if not closed_by_level.empty:
        fig1, ax1 = plt.subplots(figsize=(5, 5))
        ax1.pie(
            closed_by_level["Count"],
            labels=closed_by_level["L1/L2/L3"],
            autopct="%1.0f%%",
            startangle=90
        )
        ax1.set_title("Closed Tickets by Level")
        col1.pyplot(fig1)
    else:
        col1.info("No closed tickets to display")

    # -------------------------------
    # BAR CHART: Status by Level (Horizontal labels)
    # -------------------------------
    status_by_level = (
        filtered_df
        .groupby(["L1/L2/L3", "Status"])
        .size()
        .unstack(fill_value=0)
    )

    fig2, ax2 = plt.subplots(figsize=(6, 4))
    status_by_level.plot(kind="bar", ax=ax2)

    ax2.set_xlabel("Level")
    ax2.set_ylabel("Ticket Count")
    ax2.tick_params(axis="x", rotation=0)  # 👈 FIXED
    ax2.legend(title="Status")

    col2.pyplot(fig2)

else:
    st.info("No data available to generate charts")
