
# HR Insights Suite

### 📊 Overview
This dashboard provides strategic HR insights using interactive visuals and KPIs for the BSES team. It is designed for offline, on-premise use only — no internet or external server is required.

---

### ✅ Key Features
- Executive Dashboard with KPIs like Headcount, New Joins, Attrition, and CTC
- Detailed reports on Joiners, Exits, Promotions, Diversity, Pay Trends, and more
- Interactive filters for Company, Business Unit, Zone, Band, and Employment Type
- Works entirely offline with Excel files as input

---

### 🗂️ Folder Structure

| Folder/File          | Description |
|----------------------|-------------|
| `main.py`            | Launch file for the dashboard |
| `data/`              | Store all input Excel files here |
| `reports/`           | Individual report files (e.g., Joiners Snapshot, Pay Metrics) |
| `utils/`             | Shared styling, charts, and KPI logic |
| `static/`            | CSS, logo, and other UI assets |
| `config.py`          | Central constants like financial year, today’s date |
| `requirements.txt`   | Python dependencies (optional) |

---

### 🖥️ System Requirements

- Python 3.9 or above
- Streamlit (tested on v1.31+)
- Plotly, Pandas, openpyxl

---

### 🚀 How to Run

1. Copy this folder to your PC (e.g., `D:\BSES\Dashboard`)
2. Open Command Prompt (CMD)
3. Run the following command:

```
cd "D:\BSES\Dashboard" && streamlit run main.py
```

4. The dashboard will open automatically in your browser.

---

### 📁 Data Setup

- Place all Excel files in the `data/` folder.
- Ensure correct file names if any are pre-configured (e.g., `employee_data.xlsx`, etc.)
- No internet is required — all processing is local.

---

### ⚙️ Customization

- To change logo/style: update files in `static/`
- To edit filters: modify `main.py` and `data_handler.py`
- To add new reports: place new `.py` files in `reports/`

---

### 👨‍💻 Support

For updates or troubleshooting, please contact the developer or project lead.

---
