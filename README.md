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

## 📊 Dashboard & Visual Preview

Explore the multi-tier analytics outputs generated across the executive Power BI dashboard, Python exploratory data visualizations, and the automated GenAI pipeline:

| **Executive Power BI Widescreen Dashboard (1280x720)** | **Exploratory Data Analysis (Matplotlib / Seaborn)** |
| :---: | :---: |
| ![Dashboard Preview](./assets/dashboard_preview.png) | ![Visuals Preview](./assets/visuals_preview.png) |
| *Interactive RCM KPIs, Donut Denial Breakdown, & Top-10 Provider Leakage Analysis.* | *Automated programmatic plots tracking monthly claim trends and payment distributions.* |

| **GenAI Automated Appeal Generator (LangChain & OpenAI)** |
| :---: |
| ![GenAI Appeal Preview](./assets/genai_preview.png) |
| *Automated root-cause analysis and professional policy-appropriate insurance appeal drafts.* |

---


## 📈 Power BI & DAX Financial Engine

The dashboard utilizes a production-grade semantic data model driven by advanced DAX measures stored in `dashboard/dax_measures.dax`. Below are the core enterprise revenue cycle management (RCM) metrics implemented in the model:

| Metric Name | DAX Expression / Measure Reference | Business Purpose |
| :--- | :--- | :--- |
| **Total Billed Amount** | `SUM(Claims[CLM_BLD_AMT])` | Aggregates total submitted charges across all institutional claims. |
| **Revenue Gap** | `[Total_Billed_Amount] - [Total_Revenue_Collected]` | Surfaces underpayment leakage between billed amounts and actual cash collections. |
| **Revenue at Risk** | `CALCULATE(SUM(Claims[CLM_PWT_AMT]), Claims[CLM_MDCR_NON_PMT_RSN_CD] <> "" && ...)` | Quantifies the financial impact and exposure of denied or non-paid claims. |
| **Denial Rate Percentage** | `DIVIDE([Revenue_At_Risk], [Total_Billed_Amount], 0) * 100` | Tracks financial risk exposure relative to total billing volume. |
| **Provider Leakage Rank** | `RANKX(ALL(Claims[PRVDR_NUM]), CALCULATE([Revenue_At_Risk]), , DESC)` | Isolates top-10 high-loss institutional providers (`PRVDR_NUM`) for executive audit. |

### 🧮 Core Financial Equations

$$\text{Revenue\_Gap} = \text{Total\_Billed\_Amount} - \text{Total\_Revenue\_Collected}$$

$$\text{Denial\_Rate} = \frac{\text{Revenue\_At\_Risk}}{\text{Total\_Billed\_Amount}} \times 100$$

---

## 🚀 Step-by-Step Execution Guide

Follow these instructions to set up, run, and execute the complete analytics and AI pipeline locally:

### Step 1: Environment & Database Setup
1. Clone this repository to your local machine:
   ```bash
   git clone [https://github.com/shivangiguptaofficial/MedClaim-GenAI.git] cd MedClaim-GenAI
2. Configure your local environment variables:
   Create a `.env` file in the root directory for the GenAI appeal generator:
   ```env
   OPENAI_API_KEY=your_openai_api_key_here

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
* **`data_prep.py`**: Runs data preprocessing, cleaning pipelines, and standardizes raw datasets for modeling.
* **`isolation_forest.py`**: Executes unsupervised anomaly detection to isolate fraudulent claims and payment outliers.
* **`visualize_claims.py`**: Generates exploratory data visualizations (Matplotlib/Seaborn) for performance metrics.
* **`genai_explainer.py`**: Integrates with LLMs to process denial codes and draft automated insurance appeal documents.

---

## 📂 Repository Structure

The project files and directories are organized as follows:

* **`data/`**: Contains sample dataset schemas and CSV references for claims analysis.
* **`sql/`**: Houses SQL scripts for data staging, cleaning, and financial analytics:
  * **`01_data_cleaning.sql`**: Handles data hygiene, raw header cleaning, and staging views.
  * **`02_financial_analysis.sql`**: Computes provider billing aggregations, revenue leakage, and denial metrics.
  * **`03_clinical_and_joins.sql`**: Executes multi-table relational joins for patient journey and care continuity tracking.
* **`scripts/`**: Core Python automation, machine learning, and AI execution pipelines:
  * **`data_prep.py`**: Tier 1 data ingestion and cleaning pipeline.
  * **`isolation_forest.py`**: Tier 2 unsupervised anomaly detection model for fraud isolation.
  * **`visualize_claims.py`**: Generates exploratory data visualizations (Matplotlib/Seaborn).
  * **`genai_explainer.py`**: Tier 4 LLM-powered root cause and automated appeal letter generator.
* **`dashboard/`**: Business Intelligence layout assets and formulas:
  * **`layout_config.json`**: UI grid schema configuration.
  * **`layout_specs.md`**: UI/UX design specifications guide.
  * **`dax_measures.dax`**: Core financial calculation formulas for Power BI dashboards.
* **`requirements.txt`**: Lists all required Python package dependencies.
* **`README.md`**: Comprehensive documentation of the project.

---

## 💡 Key Analytics & Insights Covered

* **Revenue Leakage Identification:** Quantifies financial impact across specific Medicare non-payment reason codes (`CLM_MDCR_NON_PMT_RSN_CD`). 
* **Provider Risk Profiling:** Identifies top high-cost billing hospitals and medical outliers.
* **Continuity of Care Tracking:** Traces patient movement across acute care and post-acute settings within statutory 30-day windows.
* **Automated Appeal Documentation:** Accelerates back-office RCM processing by instantly drafting customized appeal justification packets for denied claims via GenAI.

---

## 👤 Author

Developed by **Shivangi Gupta** as part of an advanced Data Analytics & Business Intelligence portfolio.
