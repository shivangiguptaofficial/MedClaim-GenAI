# ==============================================================================
# Script: scripts/data_prep.py
# Project: MedClaim-GenAI
# Description: Ingests raw pipe-delimited CMS Synthetic RIF claims data,
#              handles nulls, standardizes types/dates, filters corrupt
#              payment records, and writes cleaned Parquet/CSV outputs for
#              downstream SQL, visualization, and GenAI modules.
#
# Source: CMS Synthetic Medicare Enrollment, FFS Claims, and PDE Data
#         (User Guide, May 2023) — pipe "|" delimited RIF format.
# ==============================================================================

import os
import logging
import pandas as pd

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger("data_prep")

# ------------------------------------------------------------------------
# Config
# ------------------------------------------------------------------------
RAW_DATA_DIR = "../data/raw"
CLEAN_DATA_DIR = "../data/clean"

# CMS RIF claim files are pipe-delimited; beneficiary + flagged sample are
# handled separately below since they use different delimiters/schemas.
CLAIM_FILES = {
    "inpatient": "inpatient.csv",
    "snf": "snf.csv",
    "hha": "hha.csv",
    "hospice": "hospice.csv",
    "dme": "dme.csv",
    "outpatient": "outpatient.csv",
    "carrier": "carrier.csv",
}

# Columns that represent dollar amounts across the RIF claim files.
# Not every file has every column — script checks existence before casting.
AMOUNT_COLUMNS = [
    "CLM_PMT_AMT",          # Actual Medicare payment (revenue collected)
    "CLM_TOT_CHRG_AMT",     # Total billed/submitted charge amount
    "NCH_PRMRY_PYR_CLM_PD_AMT",
]

# Columns that represent dates in CCYY-MM-DD or DD-MMM-YYYY across RIF files.
DATE_COLUMNS = [
    "CLM_FROM_DT", "CLM_THRU_DT", "CLM_ADMSN_DT",
    "NCH_BENE_DSCHRG_DT", "NCH_WKLY_PROC_DT", "FI_CLM_PROC_DT",
]


def _read_pipe_delimited(file_path: str) -> pd.DataFrame:
    """Reads a pipe-delimited CMS RIF file with safe dtype handling."""
    df = pd.read_csv(
        file_path,
        sep="|",
        low_memory=False,
        dtype=str,          # read everything as string first; cast explicitly after
        na_values=["", " ", "NA", "NULL"],
    )
    df.columns = df.columns.str.strip().str.upper()
    return df


def clean_claims_data(file_path: str) -> pd.DataFrame | None:
    """
    Loads and cleans a single CMS RIF claims file.

    Cleaning steps:
      1. Validate file exists.
      2. Read as pipe-delimited, normalize column headers.
      3. Drop rows missing the primary claim identifier (CLM_ID).
      4. Cast known amount columns to numeric; negative/NaN payments -> 0
         (CMS synthetic data does not model negative payments; real BFD
         data can, so this filter is intentionally explicit and logged).
      5. Parse known date columns to datetime (coerce invalid -> NaT).
      6. Deduplicate exact-duplicate claim lines.

    Returns a cleaned DataFrame, or None if the file could not be found.
    """
    logger.info(f"Loading dataset from {file_path} ...")

    if not os.path.exists(file_path):
        logger.error(f"File not found: {file_path}")
        return None

    df = _read_pipe_delimited(file_path)
    raw_rows = len(df)

    # --- Drop rows missing the crucial claim identifier ---
    if "CLM_ID" in df.columns:
        before = len(df)
        df = df.dropna(subset=["CLM_ID"])
        logger.info(f"Dropped {before - len(df)} rows missing CLM_ID.")

    # --- Clean payment / charge amounts ---
    for col in AMOUNT_COLUMNS:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
            negative_count = (df[col] < 0).sum()
            if negative_count > 0:
                logger.warning(f"{col}: {negative_count} negative values found; clipped to 0.")
            df[col] = df[col].clip(lower=0)

    # --- Parse date columns ---
    for col in DATE_COLUMNS:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")

    # --- Deduplicate exact repeated line items ---
    before = len(df)
    df = df.drop_duplicates()
    if before - len(df) > 0:
        logger.info(f"Removed {before - len(df)} exact duplicate rows.")

    logger.info(f"Cleaning complete for {os.path.basename(file_path)}: "
                f"{raw_rows} -> {len(df)} rows, {df.shape[1]} columns.")
    return df


def clean_beneficiary_file(file_path: str, ref_year: int) -> pd.DataFrame | None:
    """
    Loads and cleans a single-year beneficiary summary file
    (beneficiary_YYYY.csv), tagging each row with its reference year
    so multi-year files can be safely concatenated later.
    """
    df = clean_claims_data(file_path)
    if df is None:
        return None

    if "BENE_BIRTH_DT" in df.columns:
        df["BENE_BIRTH_DT"] = pd.to_datetime(df["BENE_BIRTH_DT"], errors="coerce")
    if "BENE_DEATH_DT" in df.columns:
        df["BENE_DEATH_DT"] = pd.to_datetime(df["BENE_DEATH_DT"], errors="coerce")

    df["REF_YEAR"] = ref_year
    return df


def clean_flagged_claims(file_path: str) -> pd.DataFrame | None:
    """
    Loads the pre-scored anomaly/fraud-flag sample (comma-delimited,
    distinct schema from the RIF claim files: includes anomaly_score,
    anomaly_severity, RISK_CATEGORY).
    """
    logger.info(f"Loading flagged claims sample from {file_path} ...")
    if not os.path.exists(file_path):
        logger.error(f"File not found: {file_path}")
        return None

    df = pd.read_csv(file_path, low_memory=False)
    df.columns = df.columns.str.strip().str.upper()

    for col in ["CLM_FROM_DT", "CLM_THRU_DT"]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")

    if "CLM_PMT_AMT" in df.columns:
        df["CLM_PMT_AMT"] = pd.to_numeric(df["CLM_PMT_AMT"], errors="coerce").fillna(0)

    logger.info(f"Flagged claims loaded: {len(df)} rows.")
    return df


def run_pipeline(raw_dir: str = RAW_DATA_DIR, out_dir: str = CLEAN_DATA_DIR) -> None:
    """Runs the full cleaning pipeline across all claim types and beneficiary years."""
    os.makedirs(out_dir, exist_ok=True)

    # 1. Claim files
    for key, filename in CLAIM_FILES.items():
        path = os.path.join(raw_dir, filename)
        df = clean_claims_data(path)
        if df is not None:
            out_path = os.path.join(out_dir, f"clean_{key}.csv")
            df.to_csv(out_path, index=False)
            logger.info(f"Saved -> {out_path}")

    # 2. Beneficiary files (2015-2025), tagged with REF_YEAR and concatenated
    bene_frames = []
    for year in range(2015, 2026):
        path = os.path.join(raw_dir, f"beneficiary_{year}.csv")
        if os.path.exists(path):
            df = clean_beneficiary_file(path, ref_year=year)
            if df is not None:
                bene_frames.append(df)

    if bene_frames:
        all_bene = pd.concat(bene_frames, ignore_index=True)
        out_path = os.path.join(out_dir, "clean_beneficiary_all_years.csv")
        all_bene.to_csv(out_path, index=False)
        logger.info(f"Saved combined beneficiary file -> {out_path} "
                    f"({len(all_bene)} total rows across {len(bene_frames)} years)")

    # 3. Flagged / anomaly sample
    flagged_path = os.path.join(raw_dir, "flagged_claims_sample.csv")
    flagged_df = clean_flagged_claims(flagged_path)
    if flagged_df is not None:
        out_path = os.path.join(out_dir, "clean_flagged_claims.csv")
        flagged_df.to_csv(out_path, index=False)
        logger.info(f"Saved -> {out_path}")


if __name__ == "__main__":
    run_pipeline()
