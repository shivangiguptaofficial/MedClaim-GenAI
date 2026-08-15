# =========================================================================
# Script: data_prep.py
# Description: Ingests raw pipe-delimited claims data, handles null values,
#              filters negative/corrupt payments, and structures datasets.
# =========================================================================

import pandas as pd
import os

def clean_claims_data(file_path):
    print(f"Loading dataset from {file_path}...")
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return None
        
    # Read pipe-delimited files typical of CMS claims datasets
    df = pd.read_csv(file_path, sep='|', low_memory=False)
    
    # Standardize column header whitespace and case
    df.columns = df.columns.str.strip().str.upper()
    
    # Data Hygiene: Drop rows with missing crucial identifiers
    if 'CLM_ID' in df.columns:
        df = df.dropna(subset=['CLM_ID'])
        
    # Clean payment amounts (convert to numeric and filter valid records)
    if 'CLM_PMT_AMT' in df.columns:
        df['CLM_PMT_AMT'] = pd.to_numeric(df['CLM_PMT_AMT'], errors='coerce').fillna(0)
        df = df[df['CLM_PMT_AMT'] >= 0]
        
    print(f"Cleaning complete. Output shape: {df.shape}")
    return df

if __name__ == "__main__":
    # Example usage
    # df_inpatient = clean_claims_data("../data/inpatient.csv")
    pass
