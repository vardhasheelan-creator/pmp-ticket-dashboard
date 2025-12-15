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

    # Ensure date parsing is correct
    df["Request Date"] = pd.to_datetime(
        df["Request Date"],
        dayfirst=True,
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

today = datetime.today()

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
st.caption(
    f"Showing data from {start_date.date()} to {end_date.date()}"
)

# -------------------------------------------------
# METRICS
# -------------------------------------------------
col1, col2, col3, col4 = st.columns(4)

col1.metric("Total Tickets", len(filtered_df))
col2.metric("Open", len(filtered_df[filtered_df["Status"] == "Open"]))
col3.metric("Closed", len(filtered_df[filtered_df["Status"] == "Closed"]))
col4.metric("In-Progress", len(filtered_df[filtered_df["Status"] == "In-Progress"]))

# -------------------------------------------------
# TICKET OWNERSHIP
# -------------------------------------------------
st.divider()
st.subheader("🧑‍💼 Ticket Ownership by Level")

l1_closed = len(filtered_df[
    (filtered_df["Status"] == "Closed") &
    (filtered_df["L1/L2/L3"] == "L1")
])

l2_closed = len(filtered_df[
    (filtered_df["Status"] == "Closed") &
    (filtered_df["L1/L2/L3"] == "L2")
])

l3_closed = len(filtered_df[
    (filtered_df["Status"] == "Closed") &
    (filtered_df["L1/L2/L3"] == "L3")
])

c1, c2, c3 = st.columns(3)
c1.metric("Closed by L1", l1_closed)
c2.metric("Closed by L2", l2_closed)
c3.metric("Closed by L3", l3_closed)

# -------------------------------------------------
# CATEGORY SUMMARY TABLE
# -------------------------------------------------
st.divider()
st.subheader("📁 PMP Categories")

category_table = (
    filtered_df
    .groupby(["Category", "L1/L2/L3"])
    .size()
    .unstack(fill_value=0)
    .reset_index()
)

st.dataframe(category_table, width="stretch")

# -------------------------------------------------
# CHARTS
# -------------------------------------------------
st.divider()
st.subheader("📊 Visual Insights")

col_left, col_right = st.columns(2)

# Pie chart – Status distribution
status_counts = filtered_df["Status"].value_counts()

fig1, ax1 = plt.subplots()
ax1.pie(
    status_counts,
    labels=status_counts.index,
    autopct="%1.0f%%",
    startangle=90
)
ax1.set_title("Ticket Status Distribution")
col_left.pyplot(fig1)

# Bar chart – Level vs Status
level_status = (
    filtered_df
    .groupby(["L1/L2/L3", "Status"])
    .size()
    .unstack(fill_value=0)
)

fig2, ax2 = plt.subplots()
level_status.plot(kind="bar", ax=ax2)
ax2.set_title("Ticket Status by Level")
ax2.set_xlabel("Level")
ax2.set_ylabel("Count")
ax2.tick_params(axis="x", rotation=0)
col_right.pyplot(fig2)

# -------------------------------------------------
# DOWNLOAD
# -------------------------------------------------
st.divider()
st.download_button(
    label="⬇️ Download Filtered Data (CSV)",
    data=filtered_df.to_csv(index=False),
    file_name="pmp_filtered_report.csv",
    mime="text/csv"
)
