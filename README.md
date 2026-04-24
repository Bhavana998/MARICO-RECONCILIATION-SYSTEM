**Marico Reconciliation System**

📌 What This Project Does

This project implements a practical reconciliation pipeline for FMCG use cases (like Marico) focusing on:

Matching customer and company records

Detecting mismatches

Structuring claims data

Automating basic reconciliation workflows

link : https://bhavana998-marico-reconciliation-system-dashboard-qn3pnw.streamlit.app/


⚠️ This repository primarily demonstrates implementation (code + workflow) rather than a full enterprise deployment.


🧩 What I Have Built

✅ Core Capabilities Implemented

Data ingestion from sample inputs (invoices, ledger data, claims)

Data cleaning and normalization

Basic reconciliation logic (matching records)

Mismatch identification

Workflow automation using n8n

JSON-based workflow export for reproducibility


⚙️ Focus of the Project

Reduce manual reconciliation effort

Structure unorganized financial data

Demonstrate automation using workflows


📁 Project Structure

MARICO-RECONCILIATION-SYSTEM/
│
├── workflows/
│   ├── reconciliation_workflow.json   # n8n workflow for automation
│
├── data/
│   ├── sample_invoices.csv           # Sample invoice data
│   ├── customer_ledger.csv          # Customer records
│   ├── claims_data.csv              # Claims / deductions
│
├── scripts/
│   ├── preprocess.py                # Data cleaning & normalization
│   ├── match_records.py             # Matching logic
│   ├── detect_mismatch.py           # Mismatch identification
│
├── outputs/
│   ├── matched_results.csv          # Successfully matched records
│   ├── mismatches.csv               # Identified discrepancies
│
├── app.py                           # Main execution script
├── requirements.txt                 # Dependencies
└── README.md                        # Project documentation



🔄 How It Works

1. Load invoice, ledger, and claims data


2. Preprocess and standardize formats


3. Match records using logic (invoice ID, amount, etc.)


4. Identify mismatches


5. Export results


6. (Optional) Trigger n8n workflow for automation


🚀 How to Run

1. Clone Repository

git clone https://github.com/Bhavana998/MARICO-RECONCILIATION-SYSTEM.git
cd MARICO-RECONCILIATION-SYSTEM

2. Install Dependencies

pip install -r requirements.txt

3. Run Project

python app.py

📊 Output

The system generates:

Matched records

Mismatch reports

Structured reconciliation results


🧠 What This Project Demonstrates

Understanding of reconciliation problems in FMCG

Data processing and cleaning

Basic financial matching logic

Real-world problem modeling


⚠️ Limitations

Uses sample/static data

Rule-based matching (no advanced ML yet)

Not integrated with live ERP systems


🔮 Future Improvements

Add ML-based mismatch classification

Integrate LLM for claim reasoning

Real-time dashboard

ERP (SAP) integration


📌 Note

This project is designed as a practical prototype to demonstrate reconciliation automation concepts and workflow design.


⭐ Why This Project Matters

Reconciliation is a major bottleneck in FMCG companies. This project shows how:

Manual work can be reduced

Data can be structured

Automation can improve efficiency


👩‍💻 Author

Bhavana




