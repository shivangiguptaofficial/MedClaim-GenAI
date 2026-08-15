# =========================================================================
# Script: scripts/isolation_forest.py
# Description: Unsupervised anomaly detection using Scikit-Learn to flag 
#              fraudulent claims and high-risk payment denials.
# =========================================================================

import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

def detect_claim_anomalies(df):
    print("Initializing Isolation Forest anomaly detection model...")
    
    feature_cols = ['CLM_PMT_AMT']
    if 'TOT_RX_CST_AMT' in df.columns:
        feature_cols.append('TOT_RX_CST_AMT')
        
    model_data = df.dropna(subset=feature_cols).copy()
    if model_data.empty:
        print("Dataset contains insufficient feature rows for modeling.")
        return model_data
        
    X = model_data[feature_cols]
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    # Train Isolation Forest (contamination=0.03 flags top 3% anomalies)
    iso_model = IsolationForest(contamination=0.03, random_state=42)
    model_data['anomaly_score'] = iso_model.fit_predict(X_scaled)
    
    # Label anomalies
    model_data['RISK_CATEGORY'] = model_data['anomaly_score'].apply(
        lambda x: 'High Risk / Fraud Flag' if x == -1 else 'Normal Claim'
    )
    
    flagged_count = (model_data['RISK_CATEGORY'] == 'High Risk / Fraud Flag').sum()
    print(f"ML Processing Complete. Flagged {flagged_count} high-risk claims.")
    
    return model_data

if __name__ == "__main__":
    pass

