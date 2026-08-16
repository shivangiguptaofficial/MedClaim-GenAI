# ==============================================================================
# Script: scripts/visualize_claims.py
# Project: MedClaim-GenAI
# Description: Generates production-ready data visualizations (Matplotlib /
#              Seaborn) for healthcare claims denial trends, provider cost
#              leakage, and payment distributions from CMS Synthetic RIF data.
# ==============================================================================

import os
import logging
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger("visualize_claims")

sns.set_theme(style="whitegrid")


def _load(file_path: str) -> pd.DataFrame | None:
    if not os.path.exists(file_path):
        logger.error(f"File not found: {file_path}. Please check the path.")
        return None
    df = pd.read_csv(file_path, sep="|", low_memory=False)
    df.columns = df.columns.str.strip().str.upper()
    return df


def plot_denial_breakdown(df: pd.DataFrame, output_dir: str) -> None:
    """Top 5 Medicare non-payment denial reason codes by claim volume."""
    if "CLM_MDCR_NON_PMT_RSN_CD" not in df.columns:
        logger.warning("CLM_MDCR_NON_PMT_RSN_CD not present; skipping denial chart.")
        return

    denials = df[df["CLM_MDCR_NON_PMT_RSN_CD"].notnull() &
                 (df["CLM_MDCR_NON_PMT_RSN_CD"].astype(str).str.strip() != "")]
    if denials.empty:
        logger.info("No denied claims found in this file; skipping denial chart.")
        return

    top_denials = denials["CLM_MDCR_NON_PMT_RSN_CD"].value_counts().head(5)

    plt.figure(figsize=(10, 6))
    sns.barplot(x=top_denials.index.astype(str), y=top_denials.values, hue=top_denials.index.astype(str), palette="Reds_r", legend=False)
    plt.title("Top Medicare Non-Payment Denial Reasons", fontsize=14, fontweight="bold")
    plt.xlabel("Denial Reason Code", fontsize=12)
    plt.ylabel("Frequency of Denied Claims", fontsize=12)
    plt.tight_layout()
    out_path = os.path.join(output_dir, "denial_breakdown.png")
    plt.savefig(out_path, dpi=300)
    plt.close()
    logger.info(f"Successfully generated: {out_path}")


def plot_top_providers(df: pd.DataFrame, output_dir: str) -> None:
    """Top 10 providers by total Medicare payment volume (cost leakage view)."""
    if not {"PRVDR_NUM", "CLM_PMT_AMT"}.issubset(df.columns):
        logger.warning("PRVDR_NUM / CLM_PMT_AMT not present; skipping provider chart.")
        return

    df = df.copy()
    df["CLM_PMT_AMT"] = pd.to_numeric(df["CLM_PMT_AMT"], errors="coerce").fillna(0)
    provider_costs = df.groupby("PRVDR_NUM")["CLM_PMT_AMT"].sum().reset_index()
    top_providers = provider_costs.sort_values(by="CLM_PMT_AMT", ascending=False).head(10)

    plt.figure(figsize=(12, 6))
    sns.barplot(data=top_providers, x="PRVDR_NUM", y="CLM_PMT_AMT", hue="PRVDR_NUM", palette="Blues_r", legend=False)
    plt.title("Top 10 High-Cost Billing Providers by Payment Volume", fontsize=14, fontweight="bold")
    plt.xlabel("Provider Number", fontsize=12)
    plt.ylabel("Total Payment Amount ($)", fontsize=12)
    plt.xticks(rotation=45)
    plt.tight_layout()
    out_path = os.path.join(output_dir, "top_providers_leakage.png")
    plt.savefig(out_path, dpi=300)
    plt.close()
    logger.info(f"Successfully generated: {out_path}")


def plot_payment_distribution(df: pd.DataFrame, output_dir: str, claim_type: str = "Claims") -> None:
    """Distribution of claim payment amounts (identifies long-tail high-cost claims)."""
    if "CLM_PMT_AMT" not in df.columns:
        logger.warning("CLM_PMT_AMT not present; skipping payment distribution chart.")
        return

    amounts = pd.to_numeric(df["CLM_PMT_AMT"], errors="coerce").fillna(0)
    amounts = amounts[amounts > 0]
    if amounts.empty:
        logger.info("No positive payment amounts found; skipping chart.")
        return

    plt.figure(figsize=(10, 6))
    sns.histplot(amounts, bins=40, color="#1F4E78", kde=True)
    plt.title(f"{claim_type} Payment Amount Distribution", fontsize=14, fontweight="bold")
    plt.xlabel("Claim Payment Amount ($)", fontsize=12)
    plt.ylabel("Number of Claims", fontsize=12)
    plt.tight_layout()
    out_path = os.path.join(output_dir, "payment_distribution.png")
    plt.savefig(out_path, dpi=300)
    plt.close()
    logger.info(f"Successfully generated: {out_path}")


def plot_monthly_claim_trend(df: pd.DataFrame, output_dir: str) -> None:
    """Monthly claim volume trend line, used to sanity-check seasonality/coverage."""
    if "CLM_FROM_DT" not in df.columns:
        logger.warning("CLM_FROM_DT not present; skipping monthly trend chart.")
        return

    df = df.copy()
    df["CLM_FROM_DT"] = pd.to_datetime(df["CLM_FROM_DT"], errors="coerce")
    monthly = (
        df.dropna(subset=["CLM_FROM_DT"])
          .set_index("CLM_FROM_DT")
          .resample("MS")
          .size()
    )
    if monthly.empty:
        logger.info("No valid claim dates found; skipping monthly trend chart.")
        return

    plt.figure(figsize=(12, 6))
    monthly.plot(color="#1F4E78", linewidth=2)
    plt.title("Monthly Claim Volume Trend", fontsize=14, fontweight="bold")
    plt.xlabel("Month", fontsize=12)
    plt.ylabel("Number of Claims", fontsize=12)
    plt.tight_layout()
    out_path = os.path.join(output_dir, "monthly_claim_trend.png")
    plt.savefig(out_path, dpi=300)
    plt.close()
    logger.info(f"Successfully generated: {out_path}")


def generate_visualizations(file_path: str, output_dir: str = "../dashboard/exports", claim_type: str = "Claims") -> None:
    """Loads a cleaned claims file and generates the full standard chart set."""
    logger.info(f"Loading data from {file_path} for visualization...")
    df = _load(file_path)
    if df is None:
        return

    os.makedirs(output_dir, exist_ok=True)

    plot_denial_breakdown(df, output_dir)
    plot_top_providers(df, output_dir)
    plot_payment_distribution(df, output_dir, claim_type=claim_type)
    plot_monthly_claim_trend(df, output_dir)


if __name__ == "__main__":
    # Example usage:
    # generate_visualizations("../data/raw/inpatient.csv", claim_type="Inpatient")
    pass

