import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import matplotlib.pyplot as plt

# -------------------------------------------------
# PAGE CONFIG
# -------------------------------------------------
st.set_page_config(page_title="PMP Ticket Dashboard", layout="wide")

# -------------------------------------------------
# DATA SOURCES
# -------------------------------------------------
PMP_TICKETS_URL = "https://docs.google.com/spreadsheets/d/1DQRB35J42NJjWFGSxBQWWdHxpGBccKsUF29hrthKjBU/export?format=csv"
OPEN_TICKETS_URL = "https://docs.google.com/spreadsheets/d/1LQ2yzLJVaAfVNVQhkCuHNnEDbsdUIgdO_yS_4FMCKF4/export?format=csv"

# -------------------------------------------------
# LOAD DATA
# -------------------------------------------------
@st.cache_data(ttl=60)
def load_dashboard_data():
    df = pd.read_csv(PMP_TICKETS_URL)
    df["Request Date"] = pd.to_datetime(df["Request Date"], dayfirst=True, errors="coerce")
    df = df.dropna(subset=["Request Date"])
    df["Request Date"] = df["Request Date"].dt.normalize()
    return df

@st.cache_data(ttl=60)
def load_open_tickets():
    return pd.read_csv(OPEN_TICKETS_URL)

df = load_dashboard_data()
open_df = load_open_tickets()

# -------------------------------------------------
# FILTERS
# -------------------------------------------------
st.sidebar.title("📅 Filters")
view = st.sidebar.selectbox("Select View", ["This Week", "Last Week", "This Month", "This Year"])

today = datetime.today().date()

if view == "This Week":
    start = today - timedelta(days=today.weekday())
    end = start + timedelta(days=6)
elif view == "Last Week":
    start = today - timedelta(days=today.weekday() + 7)
    end = start + timedelta(days=6)
elif view == "This Month":
    start = today.replace(day=1)
    end = today
else:
    start = today.replace(month=1, day=1)
    end = today

filtered_df = df[
    (df["Request Date"].dt.date >= start) &
    (df["Request Date"].dt.date <= end)
]

# -------------------------------------------------
# HEADER
# -------------------------------------------------
st.title("📊 PMP Ticket Dashboard")
st.caption(f"Showing data from {start} to {end}")

tab_dashboard, tab_open, tab_charts = st.tabs(
    ["📊 Dashboard", "📌 Overall Open Tickets", "📈 Visual Insights"]
)

# =================================================
# DASHBOARD TAB
# =================================================
with tab_dashboard:

    # KPIs
    col1, col2, col3, col4 = st.columns(4)
    total = len(filtered_df)
    closed = (filtered_df["Status"] == "Closed").sum()
    open_ = (filtered_df["Status"] == "Open").sum()
    in_prog = (filtered_df["Status"] == "In-Progress").sum()

    col1.metric("Total Tickets", total)
    col2.metric("Open", open_)
    col3.metric("Closed", closed)
    col4.metric("In-Progress", in_prog)

    # -------------------------------------------------
    # INFLOW vs CLOSURE
    # -------------------------------------------------
    st.divider()
    st.subheader("📈 Inflow vs Closure (%)")

    if total > 0:
        closure_pct = int((closed / total) * 100)
        pending_pct = 100 - closure_pct
        st.progress(closure_pct / 100)
        c1, c2 = st.columns(2)
        c1.metric("Closure Rate", f"{closure_pct}%")
        c2.metric("Pending", f"{pending_pct}%")

    # -------------------------------------------------
    # OWNERSHIP BY LEVEL
    # -------------------------------------------------
    st.divider()
    st.subheader("🧑‍💼 Ticket Ownership by Level")

    ownership = (
        filtered_df
        .groupby(["L1/L2/L3", "Status"])
        .size()
        .unstack(fill_value=0)
        .reindex(["L1", "L2", "L3"])
        .fillna(0)
        .reset_index()
    )

    st.dataframe(ownership, hide_index=True, use_container_width=True)

    # -------------------------------------------------
    # PMP CATEGORIES – PERCENTAGE VIEW
    # -------------------------------------------------
    st.divider()
    st.subheader("📁 PMP Categories – Percentage View")

    cat = filtered_df.groupby("Category").size().reset_index(name="Tickets")
    cat["Percentage"] = ((cat["Tickets"] / total) * 100).round(0).astype(int).astype(str) + "%"

    # Status counts
    closed_map = filtered_df[filtered_df["Status"] == "Closed"].groupby("Category").size()
    inprog_map = filtered_df[filtered_df["Status"] == "In-Progress"].groupby("Category").size()

    cat["Status"] = cat["Category"].apply(
        lambda c: " · ".join(
            filter(None, [
                f"Closed={int(closed_map.get(c,0))}" if closed_map.get(c,0) > 0 else "",
                f"In-Progress={int(inprog_map.get(c,0))}" if inprog_map.get(c,0) > 0 else ""
            ])
        )
    )

    def level_breakdown(category, status):
        grp = filtered_df[
            (filtered_df["Category"] == category) &
            (filtered_df["Status"] == status)
        ].groupby("L1/L2/L3").size()
        return "-" if grp.empty else " · ".join([f"{k}={v}" for k,v in grp.items()])

    cat["In-Progress Levels"] = cat["Category"].apply(lambda x: level_breakdown(x, "In-Progress"))
    cat["Closed Levels"] = cat["Category"].apply(lambda x: level_breakdown(x, "Closed"))

    display_cat = cat[
        ["Category", "Tickets", "Percentage", "Status", "In-Progress Levels", "Closed Levels"]
    ]

    top = display_cat["Tickets"].max()

    def highlight_top(row):
        if row["Tickets"] == top:
            return ["background-color:#1f3d2b; color:#b7f5c6; font-weight:bold"] * len(row)
        return [""] * len(row)

    st.dataframe(
        display_cat.style.apply(highlight_top, axis=1),
        hide_index=True,
        use_container_width=True
    )

# =================================================
# OVERALL OPEN TICKETS (FULLY RESTORED)
# =================================================
with tab_open:

    st.subheader("📌 Overall Open Tickets")

    open_df.columns = open_df.columns.str.strip()
    open_df["Request Date"] = pd.to_datetime(open_df["Request Date"], dayfirst=True, errors="coerce")
    open_df = open_df.dropna(subset=["Request Date"])

    today_ts = pd.Timestamp.today().normalize()
    open_df["Pending Days"] = (today_ts - open_df["Request Date"]).dt.days

    SLA_DAYS = 1
    open_df["SLA Status"] = open_df["Pending Days"].apply(
        lambda x: "❌ Breached" if x > SLA_DAYS else "✅ Within SLA"
    )
    open_df["SLA Breach Days"] = open_df["Pending Days"].apply(lambda x: max(0, x - SLA_DAYS))

    open_df["Request Date"] = open_df["Request Date"].dt.strftime("%d-%m-%Y")

    preferred_cols = [
        "Request Date","User Name","User Email","Query Description",
        "Category","Level","Status","Workspace ID",
        "SLA Status","SLA Breach Days"
    ]
    display_df = open_df[[c for c in preferred_cols if c in open_df.columns]]

    show_breached = st.checkbox("Show only SLA breached tickets")

    if show_breached:
        display_df = display_df[display_df["SLA Status"] == "❌ Breached"]

    def highlight_sla(row):
        if row["SLA Status"] == "❌ Breached":
            return ["background-color:#7a1f1f; color:white"] * len(row)
        return [""] * len(row)

    st.dataframe(
        display_df.style.apply(highlight_sla, axis=1),
        hide_index=True,
        use_container_width=True
    )

# =================================================
# VISUAL INSIGHTS
# =================================================
with tab_charts:

    left, right = st.columns(2)

    status_counts = filtered_df["Status"].value_counts()
    if not status_counts.empty:
        fig1, ax1 = plt.subplots()
        ax1.pie(status_counts, labels=status_counts.index, autopct="%1.0f%%", startangle=90)
        ax1.set_title("Ticket Status Distribution")
        left.pyplot(fig1)

    level_status = (
        filtered_df
        .groupby(["L1/L2/L3", "Status"])
        .size()
        .unstack(fill_value=0)
        .reindex(["L1","L2","L3"])
        .fillna(0)
    )

    if not level_status.empty:
        fig2, ax2 = plt.subplots(figsize=(6,4))
        level_status.plot(kind="bar", ax=ax2)
        ax2.set_title("Ticket Status by Level")
        ax2.tick_params(axis="x", rotation=0)  # ✅ horizontal
        right.pyplot(fig2)

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
