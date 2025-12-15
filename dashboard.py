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
@st.cache_data(ttl=60)
def load_data():
    df = pd.read_csv(GOOGLE_SHEET_CSV_URL)

    # ✅ STRICT DATE PARSING (NO GUESSING)
    df["Request Date"] = pd.to_datetime(
        df["Request Date"].astype(str).str.strip(),
        format="%d/%m/%Y",
        errors="coerce"
    )

    # Clean text fields
    df["Category"] = (
        df["Category"]
        .astype(str)
        .str.strip()
        .str.rstrip(".")
        .str.title()
    )

    df["L1/L2/L3"] = df["L1/L2/L3"].astype(str).str.strip().str.upper()
    df["Status"] = df["Status"].astype(str).str.strip().str.title()

    return df.dropna(subset=["Request Date"])

df = load_data()

# -------------------------------------------------
# FILTERS
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
    (df["Request Date"].dt.date >= start_date) &
    (df["Request Date"].dt.date <= end_date)
]

# -------------------------------------------------
# HEADER
# -------------------------------------------------
st.title("📊 PMP Automated Ticket Dashboard")
st.caption(f"Showing data from {start_date} to {end_date}")

# -------------------------------------------------
# METRICS
# -------------------------------------------------
c1, c2, c3, c4 = st.columns(4)

c1.metric("Total Tickets", len(filtered_df))
c2.metric("Open", (filtered_df["Status"] == "Open").sum())
c3.metric("Closed", (filtered_df["Status"] == "Closed").sum())
c4.metric("In-Progress", (filtered_df["Status"] == "In-Progress").sum())

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

o1, o2, o3 = st.columns(3)
o1.metric("Closed by L1", closed_by("L1"))
o2.metric("Closed by L2", closed_by("L2"))
o3.metric("Closed by L3", closed_by("L3"))

# -------------------------------------------------
# CATEGORY TABLE
# -------------------------------------------------
st.divider()
st.subheader("📁 PMP Categories")

if not filtered_df.empty:
    cat_table = (
        filtered_df
        .groupby(["Category", "L1/L2/L3"])
        .size()
        .unstack(fill_value=0)
        .reset_index()
    )
    st.dataframe(cat_table, use_container_width=True)
else:
    st.info("No category data available.")

# -------------------------------------------------
# CHARTS
# -------------------------------------------------
st.divider()
st.subheader("📊 Visual Insights")

left, right = st.columns(2)

# Pie
status_counts = filtered_df["Status"].value_counts()
if not status_counts.empty:
    fig1, ax1 = plt.subplots()
    ax1.pie(status_counts, labels=status_counts.index, autopct="%1.0f%%")
    ax1.set_title("Ticket Status Distribution")
    left.pyplot(fig1)

# Bar
level_order = ["L1", "L2", "L3"]

level_status = (
    filtered_df
    .groupby(["L1/L2/L3", "Status"])
    .size()
    .unstack(fill_value=0)
    .reindex(level_order, fill_value=0)
)

level_status = level_status[level_status.sum(axis=1) > 0]

if not level_status.empty:
    fig2, ax2 = plt.subplots(figsize=(5, 3))
    level_status.plot(kind="bar", ax=ax2, width=0.55)
    ax2.set_title("Ticket Status by Level")
    ax2.legend(bbox_to_anchor=(1.02, 1), loc="upper left")
    right.pyplot(fig2, use_container_width=True)

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
