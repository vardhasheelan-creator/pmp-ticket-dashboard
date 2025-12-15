import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

# -----------------------------
# Page config
# -----------------------------
st.set_page_config(
    page_title="PMP Ticket Dashboard",
    layout="wide"
)

# -----------------------------
# Google Sheet Config
# -----------------------------
SHEET_ID = "16IrnodH0VlT0mPNk9HahizoX3LTR7CwZzxd0rsXwTuw"
SHEET_NAME = "Sheet1"

CSV_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={SHEET_NAME}"

# -----------------------------
# Load Data
# -----------------------------
@st.cache_data(ttl=300)
@st.cache_data
def load_data():
    SHEET_ID = "16IrnodH0VlT0mPNk9HahizoX3LTR7CwZzxd0rsXwTuw"
    SHEET_NAME = "Sheet1"

    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={SHEET_NAME}"
    df = pd.read_csv(url)

    # 🔒 Normalize column names (safe)
    df.columns = (
        df.columns
        .str.strip()
        .str.replace("\n", " ")
        .str.replace("  ", " ")
    )

    # ✅ Column mapping (only rename what we use)
    column_map = {
        "Request Date": "Request Date",
        "Category": "Category",
        "Status": "Status",
        "L1/L2/L3": "Level"
    }

    df = df.rename(columns=column_map)

    # 🧹 Drop completely empty columns
    df = df.dropna(axis=1, how="all")

    # 📅 Date parsing
    df["Request Date"] = pd.to_datetime(
        df["Request Date"],
        dayfirst=True,
        errors="coerce"
    )

    # 🧼 Normalize values
    df["Status"] = df["Status"].str.strip().str.title()
    df["Level"] = df["Level"].str.strip().str.upper()

    # 🧠 Fix common typos
    df["Level"] = df["Level"].replace({
        "L I": "L1",
        "L 1": "L1",
        "L2 ": "L2",
        "L3 ": "L3"
    })

    return df

# -----------------------------
# Sidebar Filters
# -----------------------------
st.sidebar.title("📅 Filters")

view = st.sidebar.selectbox(
    "Select View",
    ["This Week", "Last Week", "This Month", "This Year"]
)

today = datetime.today()

if view == "This Week":
    start_date = today - timedelta(days=today.weekday())
elif view == "Last Week":
    start_date = today - timedelta(days=today.weekday() + 7)
    end_date = start_date + timedelta(days=6)
elif view == "This Month":
    start_date = today.replace(day=1)
elif view == "This Year":
    start_date = today.replace(month=1, day=1)

if view != "Last Week":
    end_date = today

filtered_df = df[
    (df["Request Date"] >= start_date) &
    (df["Request Date"] <= end_date)
]

# -----------------------------
# Header
# -----------------------------
st.title("📊 PMP Automated Ticket Dashboard")
st.caption(f"Showing data from {start_date.date()} to {end_date.date()}")

# -----------------------------
# KPI Metrics
# -----------------------------
col1, col2, col3, col4 = st.columns(4)

total = len(filtered_df)
open_t = (filtered_df["Status"] == "Open").sum()
closed_t = (filtered_df["Status"] == "Closed").sum()
progress_t = (filtered_df["Status"] == "In-Progress").sum()

col1.metric("Total Tickets", total)
col2.metric("Open", open_t)
col3.metric("Closed", closed_t)
col4.metric("In-Progress", progress_t)

st.divider()

# -----------------------------
# Ownership Metrics
# -----------------------------
st.subheader("🧑‍💻 Ticket Ownership by Level")

l1_closed = len(filtered_df[(filtered_df["Status"] == "Closed") & (filtered_df["Level"] == "L1")])
l2_closed = len(filtered_df[(filtered_df["Status"] == "Closed") & (filtered_df["Level"] == "L2")])
l3_closed = len(filtered_df[(filtered_df["Status"] == "Closed") & (filtered_df["Level"] == "L3")])

c1, c2, c3 = st.columns(3)
c1.metric("Closed by L1", l1_closed)
c2.metric("Closed by L2", l2_closed)
c3.metric("Closed by L3", l3_closed)

st.divider()

# -----------------------------
# Category Table (L1 L2 L3 ORDER FIXED)
# -----------------------------
st.subheader("📁 PMP Categories")

category_table = (
    filtered_df
    .pivot_table(
        index="Category",
        columns="Level",
        values="ID",
        aggfunc="count",
        fill_value=0
    )
)

# FORCE ORDER
for col in ["L1", "L2", "L3"]:
    if col not in category_table.columns:
        category_table[col] = 0

category_table = category_table[["L1", "L2", "L3"]].reset_index()

st.dataframe(category_table, width="stretch")

# -----------------------------
# Charts
# -----------------------------
st.subheader("📊 Ticket Status by Level")

chart_df = (
    filtered_df
    .groupby(["Level", "Status"])
    .size()
    .unstack(fill_value=0)
    .reindex(["L1", "L2", "L3"])
)

if chart_df.sum().sum() > 0:
    fig, ax = plt.subplots()
    chart_df.plot(kind="bar", ax=ax)
    ax.set_xlabel("Level")
    ax.set_ylabel("Count")
    ax.set_xticklabels(ax.get_xticklabels(), rotation=0)
    st.pyplot(fig)
else:
    st.info("No data available to generate charts")

# -----------------------------
# Download
# -----------------------------
st.download_button(
    "⬇️ Download Filtered CSV",
    filtered_df.to_csv(index=False),
    "pmp_filtered_report.csv",
    "text/csv"
)
