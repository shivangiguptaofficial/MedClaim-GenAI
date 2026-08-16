⁸# MedClaim-GenAI: Intelligent Healthcare Claims & Revenue Cycle Analytics Engine

![Python](https://img.shields.io/badge/Python-3.8%252B-blue.svg)
![SQL](https://img.shields.io/badge/SQL-SQLite%20%2F%20PostgreSQL-orange.svg)
![Machine Learning](https://img.shields.io/badge/ML-Scikit--Learn-green.svg)
![GenAI](https://img.shields.io/badge/GenAI-OpenAI%20%2F%20LangChain-purple.svg)
![Power BI](https://img.shields.io/badge/BI-Power%20BI%20%2F%20Tableau-yellow.svg)
![License](https://img.shields.io/badge/License-MIT-lightgrey.svg)

---

## 🚀 Project Overview

**MedClaim-GenAI** is an end-to-end, enterprise-grade healthcare data analysis and Revenue Cycle Management (RCM) framework designed to process, clean, audit, and model complex medical claims. Leveraging **CMS (Centers for Medicare & Medicaid Services) Synthetic Research Identifiable Files (RIF)**, this project demonstrates robust data engineering, multi-table relational joins, unsupervised machine learning for fraud detection, executive business intelligence dashboards, and Generative AI-assisted medical billing appeal automation.

Designed and developed by **Shivangi Gupta**, this portfolio project showcases a complete **4-Tier Data & AI Architecture** bridging raw administrative healthcare data to actionable financial intelligence.

---

## 📊 Data Source & Acknowledgement

The datasets and queries in this project are structured around standard healthcare administrative claims inspired by **CMS (Centers for Medicare & Medicaid Services) Synthetic Research Identifiable Files (RIF)**:
* **Inpatient Claims (`inpatient.csv`):** Hospitalization stays, provider IDs, payment amounts, and non-payment reason codes.
* **Skilled Nursing Facility (`snf.csv`):** Post-acute care tracking and transfer continuity.
* **Beneficiary Summary (`beneficiary_2023.csv`):** Patient demographics and longitudinal data.
* **Prescription Drug Events (`pde.csv`):** Pharmacy cost structures and medication volumes.

---

## 🏗️ 4-Tier System Architecture

| Tier Level | Component Name | Core Tech / Framework | Primary Function |
| :--- | :--- | :--- | :--- |
| **Tier 1** | Data Prep & Hygiene | Pandas, SQL Staging Views | Cleans raw CMS datasets, drops nulls, and handles corrupt payments. |
| **Tier 2** | Predictive ML Model | Scikit-Learn (Isolation Forest) | Performs unsupervised anomaly detection to flag high-risk fraudulent claims. |
| **Tier 3** | Business Intelligence | Power BI, DAX Measures | Provides executive RCM dashboards, financial metrics, and visual KPIs. |
| **Tier 4** | Generative AI Explainer | OpenAI API, LangChain | Automates root-cause summaries and drafts professional insurance appeal letters. |

---

## 🛠️ Tech Stack & Tools

This project leverages an industry-standard modern technology stack spanning across multiple data and AI domains:

| Domain Category | Core Technologies & Frameworks | Primary Application |
| :--- | :--- | :--- |
| **Database & Query** | SQL, SQLite, DB Browser for SQLite | Storing, querying, and managing relational healthcare datasets. |
| **Data Engineering** | Python, Pandas, NumPy, CSV Parser | Ingesting, cleaning, and formatting pipe-delimited raw claims data. |
| **Machine Learning** | Scikit-Learn (`Isolation Forest`, `StandardScaler`) | Unsupervised anomaly detection for fraud and payment outlier isolation. |
| **Generative AI** | OpenAI API (`gpt-3.5-turbo-instruct`), LangChain | Parsing denial codes and automating insurance appeal letter generation. |
| **Business Intelligence** | Power BI Desktop, DAX Measures, Tableau | Building executive RCM dashboards and financial performance KPIs. |
| **Domain Expertise** | Healthcare Insurance, RCM, Denial Management | Handling Medicare non-payment codes and tracking care continuity. |

---

## 🚀 Step-by-Step Execution Guide

Follow these instructions to set up, run, and execute the complete analytics and AI pipeline locally:

### Step 1: Environment & Database Setup
1. Clone this repository to your local machine:
   ```bash
   git clone [https://github.com/shivangiguptaofficial/MedClaim-GenAI.git](https://github.com/shivangiguptaofficial/MedClaim-GenAI.git)
   cd MedClaim-GenAI
2. Install the required Python dependencies:
   ```bash
   pip install -r requirements.txt
3. Open DB Browser for SQLite, create a new database file named `healthcare_claims.db`, and import your CMS synthetic CSV datasets using `|` (pipe) as the field separator.
### Step 2: Execute SQL Staging & Financial Queries
Run the analytical SQL scripts in the `sql/` directory sequentially using your database client:
* **`01_data_cleaning.sql`**: Cleans raw headers, drops null identifiers, and filters out negative payment anomalies.
* **`02_financial_analysis.sql`**: Aggregates top billing providers and calculates revenue leakage metrics based on denial codes.
* **`03_clinical_and_joins.sql`**: Executes multi-table relational joins to map longitudinal patient journeys across acute and post-acute settings.

### Step 3: Run Python ML & Generative AI Pipelines
Execute the core automation and machine learning scripts from your terminal or IDE:
```bash
# Run data preprocessing and cleaning pipeline
python scripts/data_prep.py

# Run unsupervised anomaly detection for fraudulent claim isolation
python scripts/isolation_forest.py

# Run GenAI script to process denials and draft appeal documents
python scripts/genai_explainer.py
