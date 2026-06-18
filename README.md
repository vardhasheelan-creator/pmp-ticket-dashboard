# 📊 PMP Ticket Dashboard

A single-project ticket tracking dashboard built with Python and Streamlit, specifically built for PMP project ticket management and reporting.

> **Live demo:** [ticketdashboard.streamlit.app](https://ticketdashboard.streamlit.app)
>
> **Need multi-project support?** See [multi-project-ticket-dashboard](https://github.com/vardhasheelan-creator/multi-project-ticket-dashboard)

---

## 🔥 The problem it solves

Our PMP support team was spending hours every week manually compiling ticket reports from Excel files. This dashboard automates the entire reporting process — drop in the latest Excel export and get instant insights.

---

## ✨ Features

- **KPI cards** — Total, Open, Closed, In-Progress at a glance
- **Inflow vs closure rate** — % based progress tracking
- **L1/L2/L3 ownership breakdown** — who owns what
- **Category analysis** — ticket distribution by type
- **SLA tracking** — flags tickets breaching SLA thresholds
- **Open tickets tab** — full list with SLA status highlighting
- **Visual insights** — status pie chart + level breakdown bar chart
- **Date filters** — This Week / Last Week / This Month / This Year
- **CSV export** — download filtered data anytime
- **Dark themed UI**

---

## 🗂 Project structure

```
pmp-ticket-dashboard/
├── dashboard.py          # Main Streamlit app
├── requirements.txt      # Python dependencies
└── data/
    ├── tickets.xlsx              # All tickets data
    └── PMP_Open_Tickets.xlsx     # Open tickets with SLA info
```

---

## ⚙️ Setup

```bash
git clone https://github.com/vardhasheelan-creator/pmp-ticket-dashboard.git
cd pmp-ticket-dashboard
py -m venv venv
venv\Scripts\Activate.ps1       # Windows
# source venv/bin/activate      # Mac/Linux
pip install -r requirements.txt
```

Add your Excel files to the `data/` folder:
- `data/tickets.xlsx`
- `data/PMP_Open_Tickets.xlsx`

```bash
streamlit run dashboard.py
# Opens at http://localhost:8501
```

---

## 📋 Required Excel columns

| Column | Description |
|---|---|
| `Request Date` | Date ticket raised (DD-MM-YYYY) |
| `User Name` | Requester name |
| `User Email` | Requester email |
| `Query Description` | Ticket description |
| `Category` | Ticket category |
| `L1/L2/L3` | Support level assigned |
| `Status` | Open / Closed / In-Progress |
| `Workspace ID` | Unique ticket ID |

---

## 🛠 Tech stack

**Python 3.14 · Streamlit · Pandas · Matplotlib · openpyxl**

---

## 🔄 Upgrading to multi-project

This repo tracks one project only. For teams managing multiple projects across tools like Zoho, ServiceNow, or Jira, see the upgraded version:

👉 [multi-project-ticket-dashboard](https://github.com/vardhasheelan-creator/multi-project-ticket-dashboard)

---

## 👩‍💻 Built by

**Vardhasheela N** — [vardhasheelan.com](https://vardhasheelan.com) · Part of the Wenix AI portfolio.

> Want a custom dashboard for your team? [Get in touch →](https://vardhasheelan.com/#contact)
