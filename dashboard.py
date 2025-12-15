import streamlit as st
import pandas as pd
from datetime import datetime
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
# LOAD DATA (NO DATE GUESSING)
# -------------------------------------------------
@st.cache_data(ttl=60)
def load_data():
    df = pd.read_csv(GOOGLE_SHEET_CSV_URL)

    # STRICT ISO parsing
    df["Request Date"] = pd.to_datetime(
        df["Request Date"],
        format="%Y-%m-%d",
        errors="coerce"
    )

    # Drop bad dates
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

today = datetime.today()

# -------------------------------------------------
# DATE FILTERING (YEAR + MONTH SAFE)
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
    week = today.isocalendar().week
    filtered_df = df[
        (df["Request Date"].dt.year == today.year) &
        (df["Request Date"].dt.isocalendar().week == week)
    ]

else:  # Last Week
    week = today.isocalendar().week - 1
    filtered_df = df[
        (df["Request Date"].dt.year == today.year) &
        (df["Request Date"].dt.isocalendar().week == week)
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
# OWNERSHIP
# -------------------------------------------------
st.divider()
st.subheader("🧑‍💼 Ticket Ownership by Level")

def closed_by(level):
    return filtered_df[
        (filtered_df["Status"] == "Closed") &
        (filtered_df["L1/L2/L3"] == level)
    ].shape[0]

l1, l2, l3 = st.columns(3)
l1.metric("Closed by L1", closed_by("L1"))
l2.metric("Closed by L2", closed_by("L2"))
l3.metric("Closed by L3", closed_by("L3"))

# -------------------------------------------------
# CATEGORY TABLE
# -------------------------------------------------
st.divider()
st.subheader("📁 PMP Categories")

category_table = (
    filtered_df
    .groupby("Category")
    .size()
    .reset_index(name="Tickets")
)

st.dataframe(category_table, use_container_width=True)

# -------------------------------------------------
# CHARTS
# -------------------------------------------------
st.divider()
st.subheader("📊 Visual Insights")

col1, col2 = st.columns(2)

# Pie
status_counts = filtered_df["Status"].value_counts()
fig1, ax1 = plt.subplots()
ax1.pie(status_counts, labels=status_counts.index, autopct="%1.0f%%")
ax1.set_title("Ticket Status Distribution")
col1.pyplot(fig1)

# Bar
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
col2.pyplot(fig2)

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
