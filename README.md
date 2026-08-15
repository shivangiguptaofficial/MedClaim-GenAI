# MedClaim-GenAI: Intelligent Healthcare Claims & Revenue Cycle Analytics Engine

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![SQLite](https://img.shields.io/badge/Database-SQLite-lightgrey)
![SQL](https://img.shields.io/badge/SQL-Advanced%20Queries-orange)
![GenAI](https://img.shields.io/badge/GenAI-Workflow%20Assisted-green)

---

## 📌 Project Overview
**MedClaim-GenAI** is an end-to-end healthcare data analysis and revenue cycle management (RCM) project designed to process, clean, and analyze complex medical claims. Utilizing **CMS (Centers for Medicare & Medicaid Services) Synthetic Research Identifiable Files (RIF)**, this project demonstrates data engineering, data hygiene enforcement, advanced SQL querying, multi-table relational joins, and healthcare financial metrics evaluation, all optimized through Generative AI-assisted coding and documentation workflows.

---

## 📂 Data Source & Acknowledgement
The datasets used for developing and testing the queries in this project are derived from the official **CMS (Centers for Medicare & Medicaid Services) Synthetic Research Identifiable Files (RIF)**.

* **Datasets Covered:** 
  * Inpatient Claims (`inpatient.csv`)
  * Skilled Nursing Facility Claims (`snf.csv`)
  * Home Health Agency Claims (`hha.csv`)
  * Hospice Claims (`hospice.csv`)
  * Durable Medical Equipment Claims (`dme.csv`)
  * Prescription Drug Events (`pde.csv`)
* **Acknowledgement:** We acknowledge the Centers for Medicare & Medicaid Services (CMS) and the Chronic Conditions Data Warehouse (CCW) for providing open synthetic research files that enable realistic healthcare analytics modeling and data engineering practice without compromising patient privacy.
* **Access Reference:** Researchers and data analysts can explore and download similar synthetic datasets directly via the [CMS CCW Data Portal](https://www.ccwdata.org/).

---

## 🏗️ Repository Structure

📁 MedClaim-GenAI/
&nbsp;&nbsp;&nbsp;&nbsp;📁 sql/
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;📄 01_data_cleaning.sql (Staging tables & null/date filtering)
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;📄 02_financial_analysis.sql (Provider billing & revenue aggregations)
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;📄 03_clinical_and_joins.sql (Patient journey joins & procedure analytics)
&nbsp;&nbsp;&nbsp;&nbsp;📄 README.md (Project documentation)

---

## 🛠️ Tech Stack & Tools
* **Database & Query Management:** SQLite, DB Browser for SQLite
* **Querying Techniques:** Advanced SQL (CTEs, Subqueries, `INNER JOIN`, `GROUP BY`, `CAST`, Aggregations)
* **Data Processing & Pipeline:** Python (`pandas`), Pipe (`|`) Delimiter parsing for flat files
* **Domain Context:** Healthcare Insurance, Claims Processing, Revenue Cycle Management (RCM), Denial Management

---

## 🚀 Step-by-Step Execution Guide

### Step 1: Database Setup
* Open **DB Browser for SQLite**.
* Click **File > New Database** and save your database file as `healthcare_claims.db`.
* When prompted to create a table definition, click **Cancel**.

### Step 2: Data Ingestion (CSV to SQLite)
* Navigate to **File > Import > Table from CSV file...**.
* Select your dataset file (e.g., `inpatient.csv`, `snf.csv`).
* Configure import settings:
  * Check **"Column names in first line"**.
  * Change the **Field separator** from comma to Pipe (`|`).
* Click **OK** to complete the import table mapping.

### Step 3: Execute SQL Scripts
Open the **Execute SQL** tab in DB Browser, copy the code from the `sql/` folder files, and execute them in sequential order:
* **`01_data_cleaning.sql`**: Filters out invalid rows and establishes clean staging views.
* **`02_financial_analysis.sql`**: Generates provider-level financial metrics and non-payment loss impacts.
* **`03_clinical_and_joins.sql`**: Extracts high-frequency procedure utilization and multi-table patient continuum journeys.

---

## 📊 Key Analytics & Insights Covered
* **Data Hygiene & Staging:** Filtered out corrupt rows, missing claim identifiers (`CLM_ID`), and blank service dates to build robust analytical staging tables.
* **Provider Financial Performance:** Aggregated total billed amounts by provider number (`PRVDR_NUM`) to track high-cost billing entities and average claim sizes.
* **Continuity of Care:** Tracked patient (`BENE_ID`) pathways across care settings from Inpatient acute care hospitals to Skilled Nursing Facilities (SNF) via relational SQL joins.
* **Denial & Non-Payment Analysis:** Evaluated Medicare non-payment reason codes (`CLM_MDCR_NON_PMT_RSN_CD`) to quantify revenue leakage and denied claim volumes.
* **Procedure Utilization Analytics:** Analyzed high-frequency HCPCS procedure codes and mapped corresponding revenue charges.

---
*Developed as part of an advanced Data Analytics & Business Intelligence Portfolio.*


