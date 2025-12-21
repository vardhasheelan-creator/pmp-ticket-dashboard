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

    col1, col2, col3, col4 = st.columns(4)

    total_tickets = len(filtered_df)
    open_tickets = (filtered_df["Status"] == "Open").sum()
    closed_tickets = (filtered_df["Status"] == "Closed").sum()
    in_progress = (filtered_df["Status"] == "In-Progress").sum()

    col1.metric("Total Tickets", total_tickets)
    col2.metric("Open", open_tickets)
    col3.metric("Closed", closed_tickets)
    col4.metric("In-Progress", in_progress)

    # Inflow vs Closure
    st.divider()
    st.subheader("📈 Inflow vs Closure (%)")

    if total_tickets > 0:
        closure_pct = int((closed_tickets / total_tickets) * 100)
        pending_pct = 100 - closure_pct

        c1, c2 = st.columns(2)
        c1.metric("Closure Rate", f"{closure_pct}%")
        c2.metric("Pending", f"{pending_pct}%")
        st.progress(closure_pct / 100)

    # Ownership
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

    # =================================================
    # PMP CATEGORIES – ENHANCED VIEW
    # =================================================
    st.divider()
    st.subheader("📁 PMP Categories – Percentage View")

    if total_tickets > 0:

        # Base category aggregation
        cat = (
            filtered_df
            .groupby("Category")
            .size()
            .reset_index(name="Tickets")
        )

        # Percentage logic (unchanged)
        cat["ExactPct"] = (cat["Tickets"] / total_tickets) * 100
        cat["RoundedPct"] = cat["ExactPct"].astype(int)
        cat["Remainder"] = cat["ExactPct"] - cat["RoundedPct"]

        missing = 100 - cat["RoundedPct"].sum()
        if missing > 0:
            cat = cat.sort_values("Remainder", ascending=False)
            cat.iloc[:missing, cat.columns.get_loc("RoundedPct")] += 1

        cat["Percentage"] = cat["RoundedPct"].astype(str) + "%"

        # Status counts
        status_counts = (
            filtered_df
            .groupby(["Category", "Status"])
            .size()
            .unstack(fill_value=0)
            .reset_index()
        )

        cat = cat.merge(status_counts, on="Category", how="left")

        cat["Closed"] = cat.get("Closed", 0)
        cat["In-Progress"] = cat.get("In-Progress", 0)

        # Level breakdown text
        breakdown = []

        for category in cat["Category"]:
            temp = filtered_df[filtered_df["Category"] == category]
            parts = []

            for status in ["Closed", "In-Progress"]:
                sub = temp[temp["Status"] == status]
                if not sub.empty:
                    levels = sub["L1/L2/L3"].value_counts()
                    level_text = ", ".join(
                        [f"{lvl}={cnt}" for lvl, cnt in levels.items()]
                    )
                    parts.append(f"{status} → {level_text}")

            breakdown.append(" | ".join(parts) if parts else "—")

        cat["Level Breakdown"] = breakdown

        final_cat = cat[
            ["Category", "Tickets", "Percentage", "Closed", "In-Progress", "Level Breakdown"]
        ]

        top_tickets = final_cat["Tickets"].max()

        def highlight_top(row):
            if row["Tickets"] == top_tickets:
                return ["background-color:#1f3d2b; color:#b7f5c6; font-weight:bold"] * len(row)
            return [""] * len(row)

        st.dataframe(
            final_cat.style.apply(highlight_top, axis=1),
            hide_index=True
        )

# =================================================
# OTHER TABS (UNCHANGED)
# =================================================
with tab_open:
    st.subheader("📌 Overall Open Tickets")
    if open_df.empty:
        st.success("✅ No open tickets available.")
    else:
        st.dataframe(open_df, use_container_width=True, hide_index=True)

with tab_charts:
    left, right = st.columns(2)
    status_counts = filtered_df["Status"].value_counts()
    if not status_counts.empty:
        fig1, ax1 = plt.subplots()
        ax1.pie(status_counts, labels=status_counts.index, autopct="%1.0f%%")
        left.pyplot(fig1)
