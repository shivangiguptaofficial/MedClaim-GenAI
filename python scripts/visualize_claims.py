# =========================================================================
# Script: scripts/visualize_claims.py
# Description: Generates production-ready data visualization charts (Python / 
#              Matplotlib / Seaborn) for healthcare claims and denial trends.
# =========================================================================

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

def generate_visualizations(file_path, output_dir="../dashboard"):
    print(f"Loading data from {file_path} for visualization...")
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}. Please check the path.")
        return
        
    df = pd.read_csv(file_path, sep='|', low_memory=False)
    df.columns = df.columns.str.strip().str.upper()
    
    os.makedirs(output_dir, exist_ok=True)
    sns.set_theme(style="whitegrid")
    
    # 1. Denial Reason Breakdown Chart
    if 'CLM_MDCR_NON_PMT_RSN_CD' in df.columns:
        plt.figure(figsize=(10, 6))
        denials = df[df['CLM_MDCR_NON_PMT_RSN_CD'].notnull() & (df['CLM_MDCR_NON_PMT_RSN_CD'] != '')]
        if not denials.empty:
            top_denials = denials['CLM_MDCR_NON_PMT_RSN_CD'].value_counts().head(5)
            sns.barplot(x=top_denials.index, y=top_denials.values, palette="Reds_r")
            plt.title("Top Medicare Non-Payment Denial Reasons", fontsize=14, fontweight='bold')
            plt.xlabel("Denial Reason Code", fontsize=12)
            plt.ylabel("Frequency of Denied Claims", fontsize=12)
            plt.tight_layout()
            plt.savefig(os.path.join(output_dir, "denial_breakdown.png"), dpi=300)
            plt.close()
            print("Successfully generated: denial_breakdown.png")

    # 2. Top High-Cost Providers Chart
    if 'PRVDR_NUM' in df.columns and 'CLM_PMT_AMT' in df.columns:
        plt.figure(figsize=(12, 6))
        df['CLM_PMT_AMT'] = pd.to_numeric(df['CLM_PMT_AMT'], errors='coerce').fillna(0)
        provider_costs = df.groupby('PRVDR_NUM')['CLM_PMT_AMT'].sum().reset_index()
        top_providers = provider_costs.sort_values(by='CLM_PMT_AMT', ascending=False).head(10)
        
        sns.barplot(data=top_providers, x='PRVDR_NUM', y='CLM_PMT_AMT', palette="Blues_r")
        plt.title("Top 10 High-Cost Billing Providers by Payment Volume", fontsize=14, fontweight='bold')
        plt.xlabel("Provider Number", fontsize=12)
        plt.ylabel("Total Payment Amount ($)", fontsize=12)
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, "top_providers_leakage.png"), dpi=300)
        plt.close()
        print("Successfully generated: top_providers_leakage.png")

if __name__ == "__main__":
    # Example execution call:
    # generate_visualizations("../data/inpatient.csv")
    pass
