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
# GOOGLE SHEETS
# -------------------------------------------------
PMP_TICKETS_URL = (
    "https://docs.google.com/spreadsheets/d/"
    "1DQRB35J42NJjWFGSxBQWWdHxpGBccKsUF29hrthKjBU"
    "/export?format=csv"
)

OPEN_TICKETS_URL = (
    "https://docs.google.com/spreadsheets/d/"
    "1LQ2yzLJVaAfVNVQhkCuHNnEDbsdUIgdO_yS_4FMCKF4"
    "/export?format=csv"
)

# -------------------------------------------------
# LOAD MAIN DASHBOARD DATA
# -------------------------------------------------
@st.cache_data(ttl=60)
def load_dashboard_data():
    df = pd.read_csv(PMP_TICKETS_URL)

    df["Request Date"] = pd.to_datetime(
        df["Request Date"].astype(str).str.strip(),
        dayfirst=True,
        errors="coerce"
    )

    df = df.dropna(subset=["Request Date"])

    current_year = datetime.today().year
    df = df[df["Request Date"].dt.year == current_year]

    df["Request Date"] = df["Request Date"].dt.normalize()
    return df

# -------------------------------------------------
# LOAD OPEN TICKETS DATA
# -------------------------------------------------
@st.cache_data(ttl=60)
def load_open_tickets():
    try:
        return pd.read_csv(OPEN_TICKETS_URL)
    except Exception:
        return pd.DataFrame()

df = load_dashboard_data()
open_df = load_open_tickets()

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
    iso = today.isocalendar()
    start_date = datetime.strptime(
        f"{iso.year}-W{iso.week - 1}-1", "%G-W%V-%u"
    ).date()
    end_date = start_date + timedelta(days=6)

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
st.title("📊 PMP Ticket Dashboard")
st.caption(f"Showing data from {start_date} to {end_date}")

# -------------------------------------------------
# TABS
# -------------------------------------------------
tab_dashboard, tab_open, tab_charts = st.tabs(
    ["📊 Dashboard", "📌 Overall Open Tickets", "📈 Visual Insights"]
)

# =================================================
# DASHBOARD TAB
# =================================================
with tab_dashboard:

    # -------------------------------
    # TOP KPIs
    # -------------------------------
    col1, col2, col3, col4 = st.columns(4)

    total_tickets = len(filtered_df)
    open_tickets = (filtered_df["Status"] == "Open").sum()
    closed_tickets = (filtered_df["Status"] == "Closed").sum()
    in_progress = (filtered_df["Status"] == "In-Progress").sum()

    col1.metric("Total Tickets", total_tickets)
    col2.metric("Open", open_tickets)
    col3.metric("Closed", closed_tickets)
    col4.metric("In-Progress", in_progress)

    # -------------------------------
    # INFLOW vs CLOSURE (RESTORED)
    # -------------------------------
    st.divider()
    st.subheader("📈 Inflow vs Closure (%)")

    if total_tickets > 0:
        closure_pct = int((closed_tickets / total_tickets) * 100)
        pending_pct = 100 - closure_pct

        c1, c2 = st.columns(2)
        c1.metric("Closure Rate", f"{closure_pct}%")
        c2.metric("Pending", f"{pending_pct}%")

        st.progress(closure_pct / 100)
    else:
        st.info("No tickets available for the selected period.")

    # -------------------------------
    # OWNERSHIP BY LEVEL
    # -------------------------------
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

    st.dataframe(ownership, hide_index=True)

# -------------------------------
# CATEGORY PERCENTAGE VIEW – INLINE CHIPS + DETAIL DRAWER
# -------------------------------
st.divider()
st.subheader("📁 PMP Categories – Percentage View")

if total_tickets > 0:

    # Base category counts
    cat = filtered_df.groupby("Category").size().reset_index(name="Tickets")
    cat["ExactPct"] = (cat["Tickets"] / total_tickets) * 100
    cat["Percentage"] = cat["ExactPct"].round(0).astype(int).astype(str) + "%"

    # Status counts
    closed_map = (
        filtered_df[filtered_df["Status"] == "Closed"]
        .groupby("Category")
        .size()
    )

    inprog_map = (
        filtered_df[filtered_df["Status"] == "In-Progress"]
        .groupby("Category")
        .size()
    )

    cat["Closed"] = cat["Category"].map(closed_map).fillna(0).astype(int)
    cat["In-Progress"] = cat["Category"].map(inprog_map).fillna(0).astype(int)

    # Status Snapshot (chips-style text)
    def status_snapshot(row):
        parts = []
        if row["Closed"] > 0:
            parts.append(f"🟢 Closed={row['Closed']}")
        if row["In-Progress"] > 0:
            parts.append(f"🟠 In-Prog={row['In-Progress']}")
        return " · ".join(parts) if parts else "-"

    cat["Status Snapshot"] = cat.apply(status_snapshot, axis=1)

    # Owner Snapshot (L1/L2/L3 counts)
    def owner_snapshot(category):
        sub = filtered_df[filtered_df["Category"] == category]
        grp = sub.groupby("L1/L2/L3").size()
        return " · ".join([f"{lvl}({cnt})" for lvl, cnt in grp.items()])

    cat["Owner Snapshot"] = cat["Category"].apply(owner_snapshot)

    display_cat = cat[
        ["Category", "Tickets", "Percentage", "Status Snapshot", "Owner Snapshot"]
    ]

    # Highlight top category
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

    # -------------------------------
    # SINGLE DETAIL DRAWER
    # -------------------------------
    st.markdown("### 🔎 Category-wise Detailed Breakdown")

    selected_category = st.selectbox(
        "Select category to view details",
        display_cat["Category"].tolist()
    )

    detail_df = filtered_df[filtered_df["Category"] == selected_category]

    st.markdown(f"#### 📂 {selected_category} — Detailed View")

    for status in ["Closed", "In-Progress"]:
        grp = (
            detail_df[detail_df["Status"] == status]
            .groupby("L1/L2/L3")
            .size()
        )

        if not grp.empty:
            st.markdown(f"**{status}:**")
            for lvl, cnt in grp.items():
                st.write(f"• {lvl} = {cnt}")

else:
    st.info("No category data available.")

# =================================================
# OVERALL OPEN TICKETS TAB
# =================================================
with tab_open:

    st.subheader("📌 Overall Open Tickets")

    if open_df.empty:
        st.success("✅ No open tickets available.")
    else:
        open_df.columns = open_df.columns.str.strip()

        open_df["Request Date"] = pd.to_datetime(
            open_df["Request Date"],
            dayfirst=True,
            errors="coerce"
        )

        open_df = open_df.dropna(subset=["Request Date"])

        today_ts = pd.Timestamp.today().normalize()
        open_df["Pending Days"] = (today_ts - open_df["Request Date"]).dt.days

        SLA_DAYS = 1
        open_df["SLA Status"] = open_df["Pending Days"].apply(
            lambda x: "❌ Breached" if x > SLA_DAYS else "✅ Within SLA"
        )
        open_df["SLA Breach Days"] = open_df["Pending Days"].apply(
            lambda x: max(0, x - SLA_DAYS)
        )

        open_df["Request Date"] = open_df["Request Date"].dt.strftime("%d-%m-%Y")

        if "Comments" in open_df.columns:
            open_df = open_df.drop(columns=["Comments"])

        preferred_columns = [
            "Request Date",
            "User Name",
            "User Email",
            "Query Description",
            "Category",
            "Level",
            "Status",
            "Workspace ID",
            "SLA Status",
            "SLA Breach Days"
        ]

        display_columns = [c for c in preferred_columns if c in open_df.columns]
        display_df = open_df[display_columns].copy()

        show_breached = st.checkbox("Show only SLA breached tickets")

        if show_breached:
            display_df = display_df[display_df["SLA Status"] == "❌ Breached"]

        def highlight_sla(row):
            if row["SLA Status"] == "❌ Breached":
                return ["background-color: #7a1f1f; color: white"] * len(row)
            return [""] * len(row)

        st.dataframe(
            display_df.style.apply(highlight_sla, axis=1),
            use_container_width=True,
            hide_index=True
        )

# =================================================
# VISUAL INSIGHTS TAB
# =================================================
with tab_charts:

    left, right = st.columns(2)

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

    level_status = (
        filtered_df
        .groupby(["L1/L2/L3", "Status"])
        .size()
        .unstack(fill_value=0)
        .reindex(["L1", "L2", "L3"])
        .fillna(0)
    )

    if not level_status.empty:
        fig2, ax2 = plt.subplots(figsize=(6, 4))
        level_status.plot(kind="bar", ax=ax2)
        ax2.set_title("Ticket Status by Level")
        ax2.tick_params(axis="x", rotation=0)
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
