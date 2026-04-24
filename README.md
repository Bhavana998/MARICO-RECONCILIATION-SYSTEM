# 🧾 Marico Reconciliation System

## 📌 Overview
This project is a data reconciliation system designed to solve real-world challenges in FMCG companies where financial reconciliation across multiple channels is complex and time-consuming.

The system automates comparison of invoices, ledgers, and claims data to identify matched and unmatched records.

---

## 🎯 Problem Statement
In large-scale businesses:
- Reconciliation takes weeks or months
- Data exists in multiple formats
- Heavy manual Excel usage
- Frequent mismatches in:
  - Prices
  - Quantities
  - Claims

This leads to delayed financial closure and blocked working capital.

---
deployment link: https://bhavana998-marico-reconciliation-system-dashboard-qn3pnw.streamlit.app/

## 🚀 Solution
This project provides a prototype reconciliation engine that:
- Ingests financial datasets
- Cleans and standardizes data
- Matches records
- Detects mismatches
- Generates structured outputs
- Automates workflow using n8n

---

## 🧩 Features

### 🔄 Data Processing
- Load invoice, ledger, and claims data
- Normalize formats
- Handle missing values

### 🔍 Record Matching
- Rule-based matching using:
  - Invoice ID
  - Amount
  - Date

### ⚠️ Mismatch Detection
- Detect discrepancies
- Generate mismatch reports

### 🤖 Workflow Automation
- Integrated with n8n
- Reduces manual effort

---

## 📁 Project Structure

MARICO-RECONCILIATION-SYSTEM/
│
├── workflows/
│   └── reconciliation_workflow.json
│
├── data/
│   ├── sample_invoices.csv
│   ├── customer_ledger.csv
│   ├── claims_data.csv
│
├── scripts/
│   ├── preprocess.py
│   ├── match_records.py
│   ├── detect_mismatch.py
│
├── outputs/
│   ├── matched_results.csv
│   ├── mismatches.csv
│
├── app.py
├── requirements.txt
└── README.md

---

## ⚙️ How It Works

1. Load datasets  
2. Clean and standardize data  
3. Match records  
4. Detect mismatches  
5. Export results  
6. Trigger workflow (optional)  

---

## 🛠️ Tech Stack
- Python
- Pandas / NumPy
- n8n
- CSV data pipeline

---

## ▶️ Getting Started

### 1. Clone Repository
git clone https://github.com/Bhavana998/MARICO-RECONCILIATION-SYSTEM.git
cd MARICO-RECONCILIATION-SYSTEM

### 2. Install Dependencies
pip install -r requirements.txt

### 3. Run Application
python app.py

---

## 📊 Output
- Matched records  
- Unmatched records  
- Reconciliation results  

---

## 🧠 What This Project Demonstrates
- Financial reconciliation logic
- Data preprocessing
- Workflow automation
- Real-world problem solving

---

## ⚠️ Limitations
- Static/sample data
- Rule-based logic only
- No live ERP integration

---

## 🔮 Future Improvements
- ML-based mismatch detection
- LLM integration
- Dashboard visualization
- SAP integration

---

## ⭐ Why This Project Matters
Reconciliation is a critical financial process.  
This project shows how automation can reduce manual work and improve efficiency.

---

## 👩‍💻 Author
Bhavana
