#!/usr/bin/env python3
# ============================================================================
# Script: scripts/isolation_forest.py
# Project: MedClaim-GenAI
#
# Description:
#   Unsupervised anomaly detection on Inpatient claims using Isolation
#   Forest. Reads claim-grain records from the vw_clean_inpatient view
#   (sql/01_data_cleaning.sql, run first) and engineers a multi-feature
#   set — a single dollar-amount feature is functionally equivalent to a
#   payment percentile cutoff and doesn't need a model, so this adds:
#
#     - CLM_PMT_AMT                claim payment amount
#     - CLM_UTLZTN_DAY_CNT         length of stay
#     - Line_Item_Count            billing complexity
#     - Provider_Payment_Deviation claim's payment vs. that specific
#                                  provider's own average — flags claims
#                                  that are unusual *for that provider*,
#                                  not just unusual overall
#
# Data notes (checked against the actual loaded database before writing
# this, not assumed):
#
#   - vw_clean_inpatient has 20,867 claim-grain rows. Of those, 910 claims
#     (4.4%) carry a NULL PRVDR_NUM — the facility field is blank on the
#     source rows (see 01_data_cleaning.sql, note #4). A groupby("PRVDR_NUM")
#     silently excludes NaN keys in pandas, so those 910 claims would get a
#     NaN Provider_Payment_Deviation and then vanish through dropna() with
#     no record that it happened. This version routes them to their own
#     "UNKNOWN_PROVIDER" bucket instead, so every claim stays in scope and
#     the row-count drop is logged explicitly if it ever occurs for a new
#     reason.
#
#   - 1,919 of 4,876 distinct providers (39%) appear exactly once in the
#     data. A single-claim provider's "deviation from its own average" is
#     mathematically always 0 — not because that claim is typical, but
#     because there's nothing to compare it to. Left as-is, Isolation
#     Forest would read every one of those 1,919 claims as maximally
#     normal on that feature, which is the opposite of the right prior for
#     a provider with no track record. This version computes deviation
#     only from providers with >= MIN_CLAIMS_FOR_BASELINE claims, and adds
#     a separate Low_Provider_History flag (rather than baking a fabricated
#     0 into the model input) so this information reaches the output
#     instead of being silently absorbed into "Normal Claim."
# ============================================================================

import logging
import sqlite3
import sys
from pathlib import Path

import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

# ----------------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------------
SCRIPT_DIR = Path(__file__).resolve().parent
DB_PATH = SCRIPT_DIR.parent / "healthcare_claims.db"
OUTPUT_PATH = SCRIPT_DIR.parent / "dashboard" / "flagged_claims_sample.csv"

FEATURE_COLS = [
    "CLM_PMT_AMT",
    "CLM_UTLZTN_DAY_CNT",
    "Line_Item_Count",
    "Provider_Payment_Deviation",
]

# A provider needs at least this many claims before its own average is a
# meaningful baseline (see data note above). Below this, deviation is left
# NULL rather than fabricated as 0, and the claim is instead marked via
# Low_Provider_History for downstream review.
MIN_CLAIMS_FOR_BASELINE = 3

CONTAMINATION = 0.03  # expected fraction of claims to flag as anomalous
RANDOM_STATE = 42
TOP_N_FOR_SAMPLE_EXPORT = 20

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("isolation_forest")


# ----------------------------------------------------------------------------
# Data loading and feature engineering
# ----------------------------------------------------------------------------
def load_claim_features(db_path: Path = DB_PATH) -> pd.DataFrame:
    """Pull claim-level inpatient records and engineer the feature set."""
    if not db_path.exists():
        log.error(
            "Database not found at %s. Run sql/01_data_cleaning.sql against "
            "healthcare_claims.db first.",
            db_path,
        )
        return pd.DataFrame()

    log.info("Connecting to %s and loading vw_clean_inpatient...", db_path)
    conn = sqlite3.connect(str(db_path))
    try:
        df = pd.read_sql_query("SELECT * FROM vw_clean_inpatient", conn)
    except (sqlite3.OperationalError, pd.errors.DatabaseError) as exc:
        log.error(
            "Could not read vw_clean_inpatient (%s). Has "
            "sql/01_data_cleaning.sql been run against this database?",
            exc,
        )
        return pd.DataFrame()
    finally:
        conn.close()

    if df.empty:
        log.warning("vw_clean_inpatient returned 0 rows.")
        return df

    n_loaded = len(df)
    log.info("Loaded %d claim-grain rows from vw_clean_inpatient.", n_loaded)

    # --- Provider key hygiene -----------------------------------------
    # NULL/blank PRVDR_NUM claims are routed to an explicit sentinel group
    # rather than silently dropped by pandas' NaN-key groupby behavior.
    n_missing_provider = df["PRVDR_NUM"].isna().sum()
    if n_missing_provider:
        log.warning(
            "%d of %d claims (%.1f%%) have a missing PRVDR_NUM; grouping "
            "them under 'UNKNOWN_PROVIDER' so they stay in the dataset "
            "instead of being dropped.",
            n_missing_provider,
            n_loaded,
            100 * n_missing_provider / n_loaded,
        )
    df["PRVDR_NUM"] = df["PRVDR_NUM"].fillna("UNKNOWN_PROVIDER")

    # --- Provider-relative baseline ------------------------------------
    # How far this claim's payment sits from that provider's own average,
    # so the model can flag a claim that looks normal system-wide but is
    # an outlier for its specific provider. Computed only from providers
    # with enough claims (MIN_CLAIMS_FOR_BASELINE) to make "the provider's
    # own average" a meaningful number rather than a single data point
    # restated as its own baseline.
    provider_claim_counts = df.groupby("PRVDR_NUM")["CLM_ID"].transform("count")
    df["Low_Provider_History"] = provider_claim_counts < MIN_CLAIMS_FOR_BASELINE

    n_low_history = df["Low_Provider_History"].sum()
    log.info(
        "%d of %d claims (%.1f%%) belong to a provider with fewer than %d "
        "claims on file; their Provider_Payment_Deviation is left null "
        "rather than fabricated as 0, and they're flagged via "
        "Low_Provider_History for separate review.",
        n_low_history,
        n_loaded,
        100 * n_low_history / n_loaded,
        MIN_CLAIMS_FOR_BASELINE,
    )

    eligible_mask = ~df["Low_Provider_History"]
    provider_avg = (
        df.loc[eligible_mask]
        .groupby("PRVDR_NUM")["CLM_PMT_AMT"]
        .transform("mean")
    )
    df["Provider_Payment_Deviation"] = pd.NA
    df.loc[eligible_mask, "Provider_Payment_Deviation"] = (
        df.loc[eligible_mask, "CLM_PMT_AMT"] - provider_avg
    )

    # --- Type coercion and null handling --------------------------------
    df[FEATURE_COLS] = df[FEATURE_COLS].apply(pd.to_numeric, errors="coerce")

    n_before_dropna = len(df)
    df = df.dropna(subset=FEATURE_COLS)
    n_after_dropna = len(df)
    n_dropped = n_before_dropna - n_after_dropna
    if n_dropped:
        log.info(
            "Dropped %d of %d claims (%.1f%%) that are missing a required "
            "feature after coercion — expected to be exactly the "
            "Low_Provider_History claims (%d), since those are the only "
            "rows with a null Provider_Payment_Deviation by design.",
            n_dropped,
            n_before_dropna,
            100 * n_dropped / n_before_dropna,
            n_low_history,
        )

    log.info(
        "%d claim-level rows with %d features ready for modeling.",
        len(df),
        len(FEATURE_COLS),
    )
    return df


# ----------------------------------------------------------------------------
# Modeling
# ----------------------------------------------------------------------------
def detect_claim_anomalies(
    df: pd.DataFrame,
    feature_cols: list[str] = FEATURE_COLS,
    contamination: float = CONTAMINATION,
    random_state: int = RANDOM_STATE,
) -> pd.DataFrame:
    """Fit Isolation Forest on the engineered feature set and label claims."""
    if df.empty:
        log.warning("Dataset contains insufficient feature rows for modeling.")
        return df

    log.info("Initializing Isolation Forest on features: %s", feature_cols)

    X = df[feature_cols]
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    iso_model = IsolationForest(
        contamination=contamination,
        random_state=random_state,
        n_jobs=-1,
    )
    df = df.copy()
    df["anomaly_score"] = iso_model.fit_predict(X_scaled)
    # decision_function: lower (more negative) = more anomalous. Kept
    # alongside the binary label so results can be ranked, not just
    # bucketed — a claim just past the -1/1 boundary and the single most
    # extreme claim in the dataset otherwise look identical downstream.
    df["anomaly_severity"] = iso_model.decision_function(X_scaled)
    df["RISK_CATEGORY"] = df["anomaly_score"].map(
        {-1: "High Risk / Fraud Flag", 1: "Normal Claim"}
    )

    flagged_count = (df["RISK_CATEGORY"] == "High Risk / Fraud Flag").sum()
    pct = flagged_count / len(df) if len(df) else 0
    log.info(
        "Model complete. Flagged %d of %d claims (%.1f%%).",
        flagged_count,
        len(df),
        100 * pct,
    )

    return df


# ----------------------------------------------------------------------------
# Entry point
# ----------------------------------------------------------------------------
def main() -> int:
    claims_df = load_claim_features()
    if claims_df.empty:
        log.error("No data to model. Exiting without writing output.")
        return 1

    result = detect_claim_anomalies(claims_df)
    if result.empty:
        log.error("Modeling produced no results. Exiting without writing output.")
        return 1

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    flagged = result[result["RISK_CATEGORY"] == "High Risk / Fraud Flag"]
    sample = flagged.sort_values("anomaly_severity", ascending=True).head(
        TOP_N_FOR_SAMPLE_EXPORT
    )
    if sample.empty:
        log.warning(
            "No claims were flagged as high risk at contamination=%.2f; "
            "writing an empty (header-only) sample file.",
            CONTAMINATION,
        )
        sample = flagged  # empty, but preserves the correct columns

    sample.to_csv(OUTPUT_PATH, index=False)
    log.info(
        "Wrote %d most-severe flagged claims to %s", len(sample), OUTPUT_PATH
    )

    # Full result set alongside the curated sample, so the dashboard can
    # show either the top-20 highlight or the complete scored population.
    full_output_path = OUTPUT_PATH.with_name("flagged_claims_full.csv")
    result.to_csv(full_output_path, index=False)
    log.info("Wrote full scored dataset (%d claims) to %s", len(result), full_output_path)

    return 0


if __name__ == "__main__":
    sys.exit(main())


