# MedClaim-GenAI: Intelligent Healthcare Claims & Revenue Cycle Analytics Engine

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

## 🏗️ 4-Tier System Architecture

| Tier Level | Component Name | Core Tech / Framework | Primary Function |
| :--- | :--- | :--- | :--- |
| **Tier 1** | Data Prep & Hygiene | Pandas, SQL Staging Views | Cleans raw CMS datasets, drops nulls, and handles corrupt payments. |
| **Tier 2** | Predictive ML Model | Scikit-Learn (Isolation Forest) | Performs unsupervised anomaly detection to flag high-risk fraudulent claims. |
| **Tier 3** | Business Intelligence | Power BI, DAX Measures | Provides executive RCM dashboards, financial metrics, and visual KPIs. |
| **Tier 4** | Generative AI Explainer | OpenAI API, LangChain | Automates root-cause summaries and drafts professional insurance appeal letters. |

---

## 📂 Repository Structure

```text
MedClaim-GenAI/
│
├── data/                       # Sample dataset schemas and CSV references
│
├── sql/                        # SQL cleaning, staging, and financial analytics queries
│   ├── 01_data_cleaning.sql    # Data hygiene & staging views
│   ├── 02_financial_analysis.sql # Provider billing, revenue leakage & denial metrics
│   └── 03_clinical_and_joins.sql # Patient journey & care continuity tracking
│
├── scripts/                    # Core Python logic and AI execution pipelines
│   ├── data_prep.py            # Tier 1: Automated data ingestion & cleaning
│   ├── isolation_forest.py     # Tier 2: Unsupervised ML anomaly & fraud detection
│   ├── genai_explainer.py      # Tier 4: LLM-powered root cause & appeal generator
│   └── visualize_claims.py     # Exploratory data visualization (Matplotlib/Seaborn)
│
├── dashboard/                  # Business Intelligence layout and calculation assets
│   ├── layout_config.json      # UI grid schema configuration
│   ├── layout_specs.md         # UI/UX design specifications guide
│   └── dax_measures.dax        # Core financial calculation formulas for Power BI
│
├── README.md                   # Comprehensive project documentation
└── requirements.txt            # Python package dependencies






