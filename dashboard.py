import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import matplotlib.pyplot as plt

# -------------------- PAGE CONFIG --------------------
st.set_page_config(
    page_title="PMP Automated Ticket Dashboard",
    layout="wide"
)

# -------------------- LOAD DATA --------------------
@st.cache_data(ttl=300)
def load_data():
    SHEET_ID = "16IrnodH0VlT0mPNk9HahizoX3LTR7CwZzxd0rsXwTuw"
    SHEET_NAME = "Sheet1"
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={SHEET_NAME}"

    df = pd.read_csv(url)

    df.columns = [
        "ID",
        "Request Date",
        "Name",
        "Email",
        "Description",
        "Category",
        "Status",
        "Level"
    ]

    df["Request Date"] = pd.to_datetime(
        df["Request Date"],
        dayfirst=True,
        errors="coerce"
    )

    df["Status"] = df["Status"].str.strip()
    df["Level"] = df["Level"].str.strip().str.upper()
    df["Category"] = df["Category"].str.strip()

    return df.dropna(subset=["Request Date"])


# -------------------- LOAD DF (CRITICAL) --------------------
df = load_data()

if df.empty:
    st.warning("No data available.")
    st.stop()

# -------------------- SIDEBAR FILTER --------------------
st.sidebar.title("📅 Filters")

view = st.sidebar.selectbox(
    "Select View",
    ["This Week", "Last Week", "This Month", "This Year", "All Time"]
)

today = datetime.today().date()

if view == "This Week":
    start_date = today - timedelta(days=today.weekday())
    end_date = start_date + timedelta(days=6)
elif view == "Last Week":
    start_date = today - timedelta(days=today.weekday() + 7)
    end_date = start_date + timedelta(days=6)
elif view == "This Month":
    start_date = today.replace(day=1)
    end_date = today
elif view == "This Year":
    start_date = today.replace(month=1, day=1)
    end_date = today
else:
    start_date = df["Request Date"].min().date()
    end_date = df["Request Date"].max().date()

# -------------------- FILTER DATA --------------------
filtered_df = df[
    (df["Request Date"].dt.date >= start_date) &
    (df["Request Date"].dt.date <= end_date)
]

# -------------------- HEADER --------------------
st.title("📊 PMP Automated Ticket Dashboard")
st.caption(f"Showing data from **{start_date}** to **{end_date}**")

# -------------------- METRICS --------------------
total = len(filtered_df)
open_cnt = len(filtered_df[filtered_df["Status"] == "Open"])
closed_cnt = len(filtered_df[filtered_df["Status"] == "Closed"])
inprog_cnt = len(filtered_df[filtered_df["Status"] == "In-Progress"])

c1, c2, c3, c4 = st.columns(4)
c1.metric("Total Tickets", total)
c2.metric("Open", open_cnt)
c3.metric("Closed", closed_cnt)
c4.metric("In-Progress", inprog_cnt)

# -------------------- OWNERSHIP BY LEVEL --------------------
st.divider()
st.subheader("👤 Ticket Ownership by Level")

def count_level(status, level):
    return len(
        filtered_df[
            (filtered_df["Status"] == status) &
            (filtered_df["Level"] == level)
        ]
    )

l1_closed = count_level("Closed", "L1")
l2_closed = count_level("Closed", "L2")
l3_closed = count_level("Closed", "L3")

oc1, oc2, oc3 = st.columns(3)
oc1.metric("Closed by L1", l1_closed)
oc2.metric("Closed by L2", l2_closed)
oc3.metric("Closed by L3", l3_closed)

# -------------------- CATEGORY TABLE --------------------
st.divider()
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
    .reset_index()
)

for col in ["L1", "L2", "L3"]:
    if col not in category_table.columns:
        category_table[col] = 0

category_table = category_table[["Category", "L1", "L2", "L3"]]

st.dataframe(category_table, width="stretch")

# -------------------- CHARTS --------------------
st.divider()
st.subheader("📊 Ticket Status by Level")

if not filtered_df.empty:
    level_status = (
        filtered_df
        .groupby(["Level", "Status"])
        .size()
        .unstack(fill_value=0)
        .reindex(["L1", "L2", "L3"], fill_value=0)
    )

    fig, ax = plt.subplots(figsize=(8, 4))
    level_status.plot(kind="bar", ax=ax)
    ax.set_xlabel("Level")
    ax.set_ylabel("Count")
    ax.set_xticklabels(ax.get_xticklabels(), rotation=0)
    ax.legend(title="Status")

    st.pyplot(fig)
else:
    st.info("No data available for charts")

# -------------------- DATA PREVIEW --------------------
st.divider()
st.subheader("🧾 Weekly Record Preview")

preview_cols = ["Request Date", "Category", "Status", "Level"]
st.dataframe(
    filtered_df[preview_cols].sort_values("Request Date"),
    width="stretch"
)

# -------------------- DOWNLOAD --------------------
st.download_button(
    "⬇️ Download CSV",
    filtered_df.to_csv(index=False),
    file_name="pmp_ticket_report.csv",
    mime="text/csv"
)
