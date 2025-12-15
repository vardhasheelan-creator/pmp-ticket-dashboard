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
# STEP 4: TOP SUMMARY (Matches Excel)
# ==================================================
total_tickets = len(weekly_df)
open_tickets = (weekly_df["Status"] == "Open").sum()
closed_tickets = (weekly_df["Status"] == "Closed").sum()

print("\n🧾 TOP SUMMARY")
print(f"Total = {total_tickets}")
print(f"Open = {open_tickets}")
print(f"Closed = {closed_tickets}")

# ==================================================
# STEP 5: LEVEL MOVEMENT SUMMARY
# ==================================================
def count_level(level, status=None):
    temp = weekly_df[weekly_df["L1/L2/L3"] == level]
    if status:
        temp = temp[temp["Status"] == status]
    return len(temp)

print("\n🧑‍💼 LEVEL MOVEMENT SUMMARY")

closed_l1 = count_level("L1", "Closed")
open_l1 = count_level("L1") - closed_l1

closed_l2 = count_level("L2", "Closed")
with_l2 = count_level("L2") - closed_l2

closed_l3 = count_level("L3", "Closed")
with_l3 = count_level("L3") - closed_l3
l3_in_progress = len(
    weekly_df[
        (weekly_df["L1/L2/L3"] == "L3") &
        (weekly_df["Status"] == "In-Progress")
    ]
)

print(f"Closed by L1 = {closed_l1}")
print(f"Open with L1 = {open_l1}")

print(f"With L2 = {with_l2}")
print(f"Closed by L2 = {closed_l2}")

print(f"With L3 = {with_l3}")
print(f"Closed by L3 = {closed_l3}")
print(f"With L3 in progress = {l3_in_progress}")

# ==================================================
# STEP 6: PMP CATEGORIES SECTION
# ==================================================
print("\n📂 PMP CATEGORIES")
print(f"Total tickets = {total_tickets}\n")

for category in weekly_df["Category"].dropna().unique():
    cat_df = weekly_df[weekly_df["Category"] == category]
    closed_df = cat_df[cat_df["Status"] == "Closed"]

    l1 = (closed_df["L1/L2/L3"] == "L1").sum()
    l2 = (closed_df["L1/L2/L3"] == "L2").sum()
    l3 = (closed_df["L1/L2/L3"] == "L3").sum()

    levels = []
    if l1: levels.append(f"L1 = {l1}")
    if l2: levels.append(f"L2 = {l2}")
    if l3: levels.append(f"L3 = {l3}")

    print("Category:", category)
    print("Closed =", len(closed_df))
    print("Levels:", " / ".join(levels))
    print("-" * 40)

# ==================================================
# STEP 7: WEEKLY RECORD PREVIEW (Validation)
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

input("\n✅ PMP Weekly Report generated successfully. Press Enter to exit...")
