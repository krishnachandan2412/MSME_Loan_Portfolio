# MSME Loan Portfolio – Credit Risk & Collections Dashboard

Interactive Streamlit dashboard to analyze an MSME loan portfolio.  
It focuses on NPAs, upcoming NPA risk, repayment behavior, collection effectiveness, and reasons for irregular payments.

## Features

- Upload your own **original MSME portfolio data** as a CSV file.
- Sidebar **row limit slider** to control how many rows are used in the analysis.
- Executive KPIs:
  - Total customers
  - Regular payer percentage
  - Current NPA %
  - Upcoming NPA %
  - Visit coverage %
  - Digital payment adoption %
  - Portfolio risk score (0–100)
- Portfolio composition by segment:
  - Healthy, Monitored, Upcoming NPA, Current NPA, Unclassified
- Risk zone distribution (Green / Yellow / Orange / Red).
- Profession-wise repayment behavior:
  - Salaried, Self-employed, Business
- DPD (Days Past Due) distribution and EMI vs loan amount.
- Legal notice coverage and collection visit coverage by segment.
- **Irregular payment reasons** chart (fraud / business stress / documentation issues etc.).
- Raw data view and export of the current dataset (CSV download).

## File Structure

```text
.
├─ msme.py                 # Streamlit dashboard (upload-only)
├─ generate_sample_data.py # Optional script to create synthetic MSME data
├─ data/                   # (Optional) Folder where you can store your own CSVs
└─ README.md
