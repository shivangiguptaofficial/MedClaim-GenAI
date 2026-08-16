"""
================================================================================
MedClaim-GenAI: Enterprise Healthcare Revenue Cycle Intelligence Platform
Author: Shivangi Gupta
Description: Unified Streamlit application that ties together the full
             MedClaim-GenAI stack:
               Tier 1  - SQLite / SQL staging & financial analytics views
               Tier 2  - Unsupervised ML (Isolation Forest) fraud/anomaly flags
               Tier 3  - Executive RCM KPI dashboard (Power BI-style, in-app)
               Tier 4  - GenAI (LangChain + OpenAI) root-cause & appeal writer

Run:
    streamlit run app.py

Expects (relative to this file):
    sql/01_data_cleaning.sql        -> creates vw_clean_* views
    sql/02_financial_analysis.sql   -> provider leakage / revenue queries
    sql/03_clinical_and_joins.sql   -> patient journey / continuity queries
    scripts/data_prep.py            -> data_prep.run_pipeline()
    scripts/isolation_forest.py     -> isolation_forest.load_claim_features / detect_claim_anomalies
    scripts/genai_explainer.py      -> genai_explainer.generate_appeal_documentation()
    healthcare_claims.db            -> SQLite DB built by data_prep.py + sql/01_data_cleaning.sql
================================================================================
"""

from __future__ import annotations

import os
import re
import sqlite3
import logging
import importlib.util
from pathlib import Path
from datetime import datetime

import pandas as pd
import numpy as np
import streamlit as st
from dotenv import load_dotenv

# --------------------------------------------------------------------------
# 0. Environment & Logging
# --------------------------------------------------------------------------
load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger("medclaim_app")

BASE_DIR = Path(__file__).resolve().parent
SQL_DIR = BASE_DIR / "sql"
SCRIPTS_DIR = BASE_DIR / "scripts"
DASHBOARD_EXPORT_DIR = BASE_DIR / "dashboard" / "exports"       # chart PNGs (visualize_claims.py)
FLAGGED_CLAIMS_PATH = BASE_DIR / "dashboard" / "flagged_claims_sample.csv"  # matches isolation_forest.py OUTPUT_PATH
DB_PATH = BASE_DIR / "healthcare_claims.db"

DASHBOARD_EXPORT_DIR.mkdir(parents=True, exist_ok=True)

SQL_FILES = {
    "01 · Data Cleaning & Hygiene (vw_clean_* views)": SQL_DIR / "01_data_cleaning.sql",
    "02 · Financial Analysis (provider leakage & revenue)": SQL_DIR / "02_financial_analysis.sql",
    "03 · Clinical & Continuity-of-Care Joins": SQL_DIR / "03_clinical_and_joins.sql",
}

# --------------------------------------------------------------------------
# 1. Page Configuration & Global Styling
# --------------------------------------------------------------------------
st.set_page_config(
    page_title="MedClaim-GenAI | Enterprise RCM Intelligence",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
        .stApp {
            background: linear-gradient(135deg, #1e1b4b 0%, #312e81 50%, #4c1d95 100%);
            color: #f1f5f9;
        }
        header, footer { visibility: hidden; }
        h1, h2, h3 { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; color: #f1f5f9; }

        div[data-testid="stMetric"] {
            background-color: rgba(255,255,255,0.06);
            border: 1px solid rgba(255,255,255,0.12);
            padding: 18px;
            border-radius: 14px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.25);
        }
        div[data-testid="stMetric"] label { color: #cbd5e1 !important; font-weight: 600; }
        div[data-testid="stMetricValue"] { color: #ffffff !important; }

        .stTextArea textarea, .stTextInput input, .stSelectbox div[data-baseweb="select"] {
            background-color: rgba(255,255,255,0.08) !important;
            color: #ffffff !important;
            border-radius: 10px !important;
            border: 1px solid rgba(255,255,255,0.18) !important;
        }

        .stButton button {
            background: linear-gradient(135deg, #7c3aed 0%, #6d28d9 100%) !important;
            color: white !important;
            border-radius: 10px !important;
            padding: 0.55rem 1.6rem !important;
            font-weight: 600 !important;
            border: 1px solid #8b5cf6 !important;
            box-shadow: 0 4px 12px rgba(124, 58, 237, 0.35);
            transition: all 0.2s ease;
        }
        .stButton button:hover {
            background: linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%) !important;
            transform: translateY(-1px);
        }

        section[data-testid="stSidebar"] {
            background-color: rgba(15, 12, 41, 0.85);
        }
        .badge {
            display: inline-block; padding: 2px 10px; border-radius: 999px;
            background: rgba(139,92,246,0.25); border: 1px solid #8b5cf6;
            font-size: 0.75rem; color: #ddd6fe; margin-right: 6px;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

# --------------------------------------------------------------------------
# 2. Database Helpers
# --------------------------------------------------------------------------
@st.cache_resource(show_spinner=False)
def get_db_connection(db_path: str = str(DB_PATH)) -> sqlite3.Connection | None:
    """Opens a cached, thread-safe SQLite connection to the analytics DB."""
    if not os.path.exists(db_path):
        return None
    return sqlite3.connect(db_path, check_same_thread=False)


def db_is_ready(conn: sqlite3.Connection | None) -> bool:
    """Checks that the Tier-1 vw_clean_* views have already been created."""
    if conn is None:
        return False
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT name FROM sqlite_master WHERE type='view' AND name LIKE 'vw_clean_%';"
        )
        return len(cur.fetchall()) > 0
    except sqlite3.Error:
        return False


def split_sql_statements(sql_text: str) -> list[str]:
    """Strips '--' comments and splits a multi-statement .sql file into
    individual executable statements on semicolon boundaries."""
    no_comments = re.sub(r"--.*", "", sql_text)
    statements = [s.strip() for s in no_comments.split(";")]
    return [s for s in statements if s]


def run_sql_file(conn: sqlite3.Connection, path: Path) -> list[tuple[str, pd.DataFrame | None]]:
    """Executes every statement in a .sql file sequentially.

    DDL (CREATE/DROP VIEW, etc.) is executed silently; SELECT statements
    are captured and returned as (label, DataFrame) pairs for display.
    """
    results: list[tuple[str, pd.DataFrame | None]] = []
    if not path.exists():
        st.error(f"SQL file not found: {path}")
        return results

    statements = split_sql_statements(path.read_text())
    cur = conn.cursor()
    select_count = 0

    for stmt in statements:
        upper = stmt.strip().upper()
        try:
            if upper.startswith("SELECT") or upper.startswith("WITH"):
                select_count += 1
                df = pd.read_sql_query(stmt, conn)
                # Best-effort label: first line of the query, trimmed
                label = f"Result {select_count}"
                results.append((label, df))
            else:
                cur.execute(stmt)
        except (sqlite3.Error, pd.errors.DatabaseError) as exc:
            results.append((f"Error in statement: {stmt[:60]}...", None))
            logger.error("SQL execution failed: %s", exc)

    conn.commit()
    return results


def query_scalar(conn: sqlite3.Connection, sql: str, default: float = 0.0) -> float:
    """Safely executes a scalar aggregate query, returning `default` on failure."""
    try:
        val = pd.read_sql_query(sql, conn).iloc[0, 0]
        return float(val) if val is not None else default
    except Exception as exc:  # noqa: BLE001
        logger.warning("Scalar query failed (%s): %s", sql[:60], exc)
        return default


# --------------------------------------------------------------------------
# 3. Dynamic Import of Project Scripts (scripts/*.py)
# --------------------------------------------------------------------------
def _load_module(module_name: str, file_path: Path):
    """Dynamically imports a project script so the app stays a single
    self-contained entry point without requiring package __init__ files."""
    if not file_path.exists():
        return None
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)  # type: ignore[union-attr]
        return module
    except Exception as exc:  # noqa: BLE001
        logger.error("Failed to import %s: %s", module_name, exc)
        return None


isolation_forest_mod = _load_module("isolation_forest", SCRIPTS_DIR / "isolation_forest.py")
genai_explainer_mod = _load_module("genai_explainer", SCRIPTS_DIR / "genai_explainer.py")

# --------------------------------------------------------------------------
# 4. Sidebar Navigation
# --------------------------------------------------------------------------
st.sidebar.markdown("### 🏥 MedClaim-GenAI Suite")
st.sidebar.caption("Enterprise Revenue Cycle Intelligence Platform")
st.sidebar.markdown("---")

navigation = st.sidebar.radio(
    "Select Module",
    (
        "📊  Executive RCM Dashboard",
        "🗄️  SQL Relational Analytics",
        "🤖  Unsupervised ML — Anomaly Detection",
        "✍️  GenAI Appeal Generator",
    ),
    label_visibility="collapsed",
)

st.sidebar.markdown("---")
st.sidebar.info(
    "**Architecture**\n\n"
    "Tier 1 · SQL Staging\n\n"
    "Tier 2 · ML Anomaly Isolation\n\n"
    "Tier 3 · BI / Executive KPIs\n\n"
    "Tier 4 · GenAI Appeal Drafting"
)

conn = get_db_connection()
db_ready = db_is_ready(conn)

if conn is None:
    st.sidebar.error("⚠️ `healthcare_claims.db` not found. Run `scripts/data_prep.py`.")
elif not db_ready:
    st.sidebar.warning("⚠️ DB found but `vw_clean_*` views are missing. Run `sql/01_data_cleaning.sql`.")
else:
    st.sidebar.success("✅ Database connected & views verified.")

# ==========================================================================
# MODULE 1 — EXECUTIVE RCM DASHBOARD
# ==========================================================================
if navigation.startswith("📊"):
    st.title("📊 Executive Revenue Cycle Management (RCM) Dashboard")
    st.markdown(
        "Real-time financial performance indicators derived from the CMS Synthetic "
        "Medicare RIF claims tables (Inpatient, SNF, HHA, Hospice, DME, PDE)."
    )

    if not db_ready:
        st.warning(
            "No cleaned data is available yet. Run the pipeline first:\n\n"
            "```bash\npython scripts/data_prep.py\n"
            "sqlite3 healthcare_claims.db < sql/01_data_cleaning.sql\n```"
        )
    else:
        # ---- Pull KPIs directly from the Tier-1 views --------------------
        total_billed = query_scalar(
            conn,
            """
            SELECT SUM(billed) FROM (
                SELECT CLM_PMT_AMT AS billed FROM vw_clean_inpatient
                UNION ALL SELECT CLM_PMT_AMT FROM vw_clean_snf
                UNION ALL SELECT CLM_PMT_AMT FROM vw_clean_hha
                UNION ALL SELECT CLM_PMT_AMT FROM vw_clean_hospice
            );
            """,
        )
        denied_claims = query_scalar(
            conn,
            """
            SELECT COUNT(*) FROM vw_clean_inpatient
            WHERE CLM_MDCR_NON_PMT_RSN_CD IS NOT NULL
              AND TRIM(CLM_MDCR_NON_PMT_RSN_CD) <> '';
            """,
        )
        total_claims = query_scalar(
            conn,
            """
            SELECT COUNT(*) FROM (
                SELECT CLM_ID FROM vw_clean_inpatient
                UNION ALL SELECT CLM_ID FROM vw_clean_snf
                UNION ALL SELECT CLM_ID FROM vw_clean_hha
                UNION ALL SELECT CLM_ID FROM vw_clean_hospice
            );
            """,
        )
        revenue_at_risk_denial = query_scalar(
            conn,
            """
            SELECT SUM(CLM_PMT_AMT) FROM vw_clean_inpatient
            WHERE CLM_MDCR_NON_PMT_RSN_CD IS NOT NULL
              AND TRIM(CLM_MDCR_NON_PMT_RSN_CD) <> '';
            """,
        )

        # ---- Known dataset caveat --------------------------------------
        # sql/02_financial_analysis.sql documents that CLM_MDCR_NON_PMT_RSN_CD
        # is populated on 0% of rows in this synthetic release, so the
        # denial-code-based "Revenue at Risk" measure is always ~0. We fall
        # back to the ML-flagged claims (Module 3) as a populated, working
        # proxy for exposure — the same substitution your own SQL script
        # uses ("High Line-Item Complexity" flag) when this field is empty.
        risk_source = "Denial Code (CLM_MDCR_NON_PMT_RSN_CD)"
        revenue_at_risk = revenue_at_risk_denial
        risk_claim_count = denied_claims

        if revenue_at_risk_denial == 0:
            if FLAGGED_CLAIMS_PATH.exists():
                try:
                    ml_flagged = pd.read_csv(FLAGGED_CLAIMS_PATH)
                    revenue_at_risk = float(ml_flagged["CLM_PMT_AMT"].sum())
                    risk_claim_count = len(ml_flagged)
                    risk_source = "ML Isolation Forest (High Risk / Fraud Flag)"
                except Exception as exc:  # noqa: BLE001
                    logger.warning("Could not read flagged claims CSV: %s", exc)
            else:
                proxy_df = pd.read_sql_query(
                    """
                    SELECT PRVDR_NUM, CLM_ID, Line_Item_Count, CLM_PMT_AMT FROM (
                        SELECT PRVDR_NUM, CLM_ID, Line_Item_Count, CLM_PMT_AMT FROM vw_clean_inpatient
                        UNION ALL
                        SELECT PRVDR_NUM, CLM_ID, Line_Item_Count, CLM_PMT_AMT FROM vw_clean_hha
                    );
                    """,
                    conn,
                )
                if not proxy_df.empty:
                    avg_lines = proxy_df["Line_Item_Count"].mean()
                    high_complexity = proxy_df[proxy_df["Line_Item_Count"] > avg_lines * 5]
                    revenue_at_risk = float(high_complexity["CLM_PMT_AMT"].sum())
                    risk_claim_count = len(high_complexity)
                    risk_source = "High Line-Item Complexity proxy (Line_Item_Count > 5x avg)"

        total_revenue_collected = max(total_billed - revenue_at_risk, 0.0)
        denial_rate = (revenue_at_risk / total_billed * 100) if total_billed else 0.0

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total Billed Amount", f"${total_billed:,.0f}")
        c2.metric("Total Revenue Collected", f"${total_revenue_collected:,.0f}")
        c3.metric("Revenue at Risk", f"${revenue_at_risk:,.0f}",
                   delta=f"{risk_claim_count:,.0f} claims", delta_color="inverse")
        c4.metric("Risk / Denial Rate", f"{denial_rate:.1f}%", delta_color="inverse")

        if revenue_at_risk_denial == 0:
            st.info(
                f"ℹ️ `CLM_MDCR_NON_PMT_RSN_CD` is unpopulated in this CMS synthetic sample "
                f"(a documented limitation — see `sql/02_financial_analysis.sql`), so "
                f"**Revenue at Risk** above is computed from **{risk_source}** instead. "
                "Run the Isolation Forest module for a more accurate, model-driven figure."
            )

        st.markdown("---")
        left, right = st.columns(2)

        with left:
            st.subheader("💡 Core Financial Formulas")
            st.code(
                "Revenue_At_Risk   = SUM(CLM_PMT_AMT) WHERE CLM_MDCR_NON_PMT_RSN_CD IS NOT NULL\n"
                "                    -- falls back to ML-flagged / high-complexity proxy\n"
                "                    -- when the denial code field is unpopulated\n"
                "Revenue_Gap       = Total_Billed_Amount - Total_Revenue_Collected\n"
                "Denial_Rate_Pct   = (Revenue_At_Risk / Total_Billed_Amount) * 100",
                language="text",
            )

        with right:
            st.subheader("🏆 Top Denial Reason Codes")
            top_denials = pd.read_sql_query(
                """
                SELECT CLM_MDCR_NON_PMT_RSN_CD AS Denial_Code, COUNT(*) AS Claims
                FROM vw_clean_inpatient
                WHERE CLM_MDCR_NON_PMT_RSN_CD IS NOT NULL
                  AND TRIM(CLM_MDCR_NON_PMT_RSN_CD) <> ''
                GROUP BY CLM_MDCR_NON_PMT_RSN_CD
                ORDER BY Claims DESC
                LIMIT 5;
                """,
                conn,
            )
            if top_denials.empty:
                st.caption("No denial reason codes populated in this dataset sample.")
            else:
                st.bar_chart(top_denials.set_index("Denial_Code"))

        st.markdown("---")
        st.subheader("🏥 Top 10 High-Cost Providers by Payment Volume")
        top_providers = pd.read_sql_query(
            """
            SELECT PRVDR_NUM AS Provider_ID, ROUND(SUM(CLM_PMT_AMT), 2) AS Total_Paid
            FROM vw_clean_inpatient
            WHERE PRVDR_NUM IS NOT NULL AND TRIM(PRVDR_NUM) <> ''
            GROUP BY PRVDR_NUM
            ORDER BY Total_Paid DESC
            LIMIT 10;
            """,
            conn,
        )
        st.bar_chart(top_providers.set_index("Provider_ID")) if not top_providers.empty else st.caption("No provider data available.")

# ==========================================================================
# MODULE 2 — SQL RELATIONAL ANALYTICS
# ==========================================================================
elif navigation.startswith("🗄️"):
    st.title("🗄️ SQL Relational Analytics")
    st.markdown("Execute and inspect the multi-table relational queries stored in `/sql`.")

    if conn is None:
        st.error("Database connection unavailable. Run `scripts/data_prep.py` first.")
    else:
        query_choice = st.selectbox("Choose Analytical Script", list(SQL_FILES.keys()))
        script_path = SQL_FILES[query_choice]

        with st.expander("📄 View raw SQL source"):
            st.code(script_path.read_text() if script_path.exists() else "File not found.", language="sql")

        if st.button("▶️ Run Script Against Database"):
            with st.spinner(f"Executing {script_path.name} ..."):
                outputs = run_sql_file(conn, script_path)
            if not outputs:
                st.info("Script ran with no SELECT statements to display (DDL/views only).")
            for label, df in outputs:
                st.markdown(f"**{label}**")
                if df is None:
                    st.error("This statement failed — see application logs for details.")
                elif df.empty:
                    st.caption("Query returned 0 rows.")
                else:
                    st.dataframe(df, use_container_width=True)
                    st.download_button(
                        f"⬇️ Download {label} (CSV)",
                        df.to_csv(index=False).encode("utf-8"),
                        file_name=f"{script_path.stem}_{label.replace(' ', '_')}.csv",
                        mime="text/csv",
                        key=f"dl_{script_path.stem}_{label}",
                    )
                st.markdown("---")

# ==========================================================================
# MODULE 3 — UNSUPERVISED ML (ISOLATION FOREST ANOMALY DETECTION)
# ==========================================================================
elif navigation.startswith("🤖"):
    st.title("🤖 Unsupervised ML — Claim Anomaly Detection")
    st.markdown(
        "Isolates billing outliers and potential fraud patterns using a Scikit-Learn "
        "**Isolation Forest** trained on claim-level payment amount, length-of-stay, "
        "line-item count, and provider payment deviation."
    )

    contamination_rate = st.slider(
        "Contamination Rate (expected outlier proportion)",
        min_value=0.01, max_value=0.25, value=0.03, step=0.01,
    )
    top_n_export = st.number_input("Top-N flagged claims to export", min_value=5, max_value=200, value=20, step=5)

    if isolation_forest_mod is None:
        st.error("`scripts/isolation_forest.py` could not be loaded. Verify the file exists and imports cleanly.")
    elif not db_ready:
        st.warning("Database views not found. Run `sql/01_data_cleaning.sql` before scoring claims.")
    else:
        if st.button("🚀 Run Isolation Forest Model"):
            with st.spinner("Loading claim features and scoring anomalies..."):
                try:
                    features_df = isolation_forest_mod.load_claim_features(DB_PATH)
                    if features_df.empty:
                        st.warning("No claim-level rows were returned for feature engineering.")
                    else:
                        scored_df = isolation_forest_mod.detect_claim_anomalies(
                            features_df,
                            feature_cols=isolation_forest_mod.FEATURE_COLS,
                            contamination=contamination_rate,
                            random_state=getattr(isolation_forest_mod, "RANDOM_STATE", 42),
                        )
                        flagged = (
                            scored_df[scored_df["RISK_CATEGORY"] == "High Risk / Fraud Flag"]
                            .sort_values("anomaly_severity", ascending=True)
                            .head(int(top_n_export))
                        )
                        st.session_state["flagged_claims"] = flagged
                        st.success(
                            f"Model complete — flagged {len(flagged):,} of {len(scored_df):,} claims "
                            f"({len(flagged) / max(len(scored_df), 1) * 100:.1f}%)."
                        )
                except Exception as exc:  # noqa: BLE001
                    st.error(f"Model execution failed: {exc}")
                    logger.exception("Isolation Forest run failed")

        flagged = st.session_state.get("flagged_claims")
        if flagged is not None and not flagged.empty:
            m1, m2, m3 = st.columns(3)
            m1.metric("Claims Flagged", f"{len(flagged):,}")
            m2.metric("Total Exposure ($)", f"${flagged['CLM_PMT_AMT'].sum():,.0f}")
            m3.metric("Avg Anomaly Score", f"{flagged['anomaly_score'].mean():.3f}")

            st.subheader("🚩 Flagged Claims")
            st.dataframe(flagged, use_container_width=True)

            st.subheader("📈 Anomaly Score Distribution")
            st.bar_chart(flagged.set_index("CLM_ID")["anomaly_score"])

            FLAGGED_CLAIMS_PATH.parent.mkdir(parents=True, exist_ok=True)
            flagged.to_csv(FLAGGED_CLAIMS_PATH, index=False)
            st.download_button(
                "⬇️ Download Flagged Claims (CSV)",
                flagged.to_csv(index=False).encode("utf-8"),
                file_name="flagged_claims_sample.csv",
                mime="text/csv",
            )
            st.caption(
                f"Also written to `{FLAGGED_CLAIMS_PATH.relative_to(BASE_DIR)}` — "
                "this is the same file the Power BI / Dashboard tier reads from."
            )

# ==========================================================================
# MODULE 4 — GENAI APPEAL GENERATOR
# ==========================================================================
elif navigation.startswith("✍️"):
    st.title("✍️ GenAI Automated Appeal Generator")
    st.markdown(
        "Powered by **LangChain + OpenAI**. Generates a root-cause analysis and a "
        "formal insurance appeal letter for a flagged or denied Medicare claim."
    )

    if genai_explainer_mod is None:
        st.error("`scripts/genai_explainer.py` could not be loaded.")
    elif not os.environ.get("OPENAI_API_KEY"):
        st.warning(
            "`OPENAI_API_KEY` is not set. Add it to a `.env` file in the project root:\n\n"
            "```\nOPENAI_API_KEY=sk-...\n```"
        )
    else:
        # Pre-fill from a claim flagged in Module 3, if available
        flagged = st.session_state.get("flagged_claims")
        default_row = flagged.iloc[0] if flagged is not None and not flagged.empty else None

        col1, col2 = st.columns(2)
        with col1:
            claim_id = st.text_input(
                "Claim ID",
                value=str(default_row["CLM_ID"]) if default_row is not None else "",
            )
            provider_id = st.text_input(
                "Provider ID",
                value=str(default_row["PRVDR_NUM"]) if default_row is not None and "PRVDR_NUM" in default_row else "",
            )
        with col2:
            billed_amount = st.number_input(
                "Billed / Payment Amount ($)",
                min_value=0.0,
                value=float(default_row["CLM_PMT_AMT"]) if default_row is not None else 0.0,
                step=100.0,
            )
            denial_code = st.text_input(
                "Denial Reason Code",
                value=str(default_row.get("RISK_CATEGORY", "")) if default_row is not None else "",
                placeholder="e.g., CO-16 · High Risk / Fraud Flag",
            )

        model_name = st.selectbox("Model", ["gpt-4o-mini", "gpt-4o", "gpt-4.1-mini"], index=0)
        temperature = st.slider("Creativity (temperature)", 0.0, 1.0, 0.3, 0.1)

        if st.button("📝 Generate Appeal Packet"):
            if not claim_id or not denial_code:
                st.warning("Please provide at least a Claim ID and Denial Reason Code.")
            else:
                with st.spinner("Invoking LangChain + OpenAI pipeline..."):
                    try:
                        output_text = genai_explainer_mod.generate_appeal_documentation(
                            claim_id=claim_id,
                            denial_code=denial_code,
                            billed_amount=billed_amount,
                            provider_id=provider_id or "UNKNOWN",
                            model_name=model_name,
                            temperature=temperature,
                        )
                        st.success("✅ Appeal packet generated successfully!")
                        st.markdown("#### 📄 Editable Output")
                        st.text_area("Generated Documentation", value=output_text, height=420)
                        st.download_button(
                            "⬇️ Download as .txt",
                            output_text.encode("utf-8"),
                            file_name=f"appeal_{claim_id}.txt",
                            mime="text/plain",
                        )
                    except Exception as exc:  # noqa: BLE001
                        st.error(f"Generation failed: {exc}")
                        logger.exception("GenAI appeal generation failed")

# --------------------------------------------------------------------------
# Footer
# --------------------------------------------------------------------------
st.markdown("---")
st.caption(
    f"MedClaim-GenAI · Built by Shivangi Gupta · "
    f"Session refreshed {datetime.now().strftime('%Y-%m-%d %H:%M')}"
)
