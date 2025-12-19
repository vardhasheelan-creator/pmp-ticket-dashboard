import pandas as pd
from datetime import date, timedelta

# ==================================================
# STEP 1: Load Excel
# ==================================================
print("🚀 Script started")

file_path = "data/tickets.xlsx"
df = pd.read_excel(file_path)

print("✅ Excel loaded successfully")
print("Rows:", df.shape[0])
print("Columns:", df.columns.tolist())

# ==================================================
# STEP 2: Fix Date Format (DD/MM/YYYY)
# ==================================================
df["Request Date"] = pd.to_datetime(
    df["Request Date"],
    dayfirst=True,
    errors="coerce"
)

df["Request_Date_Only"] = df["Request Date"].dt.date

# ==================================================
# STEP 3: Define Current Week (Mon → Sun)
# ==================================================
today = date.today()
start_of_week = today - timedelta(days=today.weekday())
end_of_week = start_of_week + timedelta(days=6)

weekly_df = df[
    (df["Request_Date_Only"] >= start_of_week) &
    (df["Request_Date_Only"] <= end_of_week)
]

print("\n📅 PMP WEEKLY REPORT")
print(f"From: {start_of_week} To: {end_of_week}")

# ==================================================
# STEP 4: TOP SUMMARY
# ==================================================
total_tickets = len(weekly_df)
open_tickets = (weekly_df["Status"] == "Open").sum()
closed_tickets = (weekly_df["Status"] == "Closed").sum()
in_progress_tickets = (weekly_df["Status"] == "In-Progress").sum()

print("\n🧾 TOP SUMMARY")
print(f"Total = {total_tickets}")
print(f"Open = {open_tickets}")
print(f"Closed = {closed_tickets}")
print(f"In Progress = {in_progress_tickets}")

# ==================================================
# STEP 5: LEVEL MOVEMENT SUMMARY (V2 UPGRADED)
# ==================================================
def count_level(level, status=None):
    temp = weekly_df[weekly_df["L1/L2/L3"] == level]
    if status:
        temp = temp[temp["Status"] == status]
    return len(temp)

print("\n🧑‍💼 LEVEL MOVEMENT SUMMARY")

for level in ["L1", "L2", "L3"]:
    closed_count = count_level(level, "Closed")
    open_count = count_level(level, "Open")
    in_progress_count = count_level(level, "In-Progress")

    print(f"\n{level} SUMMARY")
    print(f"Closed = {closed_count}")
    print(f"Open = {open_count}")
    print(f"In Progress = {in_progress_count}")

# ==================================================
# STEP 6: PMP CATEGORIES (CLOSED + IN PROGRESS)
# ==================================================
print("\n📂 PMP CATEGORIES")
print(f"Total tickets = {total_tickets}\n")

for category in weekly_df["Category"].dropna().unique():
    cat_df = weekly_df[weekly_df["Category"] == category]

    closed_df = cat_df[cat_df["Status"] == "Closed"]
    in_prog_df = cat_df[cat_df["Status"] == "In-Progress"]

    print("Category:", category)

    # Closed tickets by level
    if not closed_df.empty:
        l1_c = (closed_df["L1/L2/L3"] == "L1").sum()
        l2_c = (closed_df["L1/L2/L3"] == "L2").sum()
        l3_c = (closed_df["L1/L2/L3"] == "L3").sum()

        levels_closed = []
        if l1_c: levels_closed.append(f"L1 = {l1_c}")
        if l2_c: levels_closed.append(f"L2 = {l2_c}")
        if l3_c: levels_closed.append(f"L3 = {l3_c}")

        print(f"Closed = {len(closed_df)}")
        print("Closed Levels:", " / ".join(levels_closed))
    else:
        print("Closed = 0")

    # In-progress tickets by level
    if not in_prog_df.empty:
        l1_ip = (in_prog_df["L1/L2/L3"] == "L1").sum()
        l2_ip = (in_prog_df["L1/L2/L3"] == "L2").sum()
        l3_ip = (in_prog_df["L1/L2/L3"] == "L3").sum()

        levels_ip = []
        if l1_ip: levels_ip.append(f"L1 = {l1_ip}")
        if l2_ip: levels_ip.append(f"L2 = {l2_ip}")
        if l3_ip: levels_ip.append(f"L3 = {l3_ip}")

        print(f"In Progress = {len(in_prog_df)}")
        print("In-Progress Levels:", " / ".join(levels_ip))
    else:
        print("In Progress = 0")

    print("-" * 45)

# ==================================================
# STEP 7: WEEKLY RECORD PREVIEW
# ==================================================
print("\n🧪 WEEKLY RECORD PREVIEW")
if weekly_df.empty:
    print("No tickets this week")
else:
    print(
        weekly_df[
            ["Request Date", "Category", "Status", "L1/L2/L3"]
        ]
    )

input("\n✅ PMP Weekly Report V2 generated successfully. Press Enter to exit...")
