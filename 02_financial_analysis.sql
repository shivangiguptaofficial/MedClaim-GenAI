-- =========================================================================
-- File: 02_financial_analysis.sql
-- Description: Financial metrics, provider billing, and denial analysis
-- Project: MedClaim-GenAI
-- =========================================================================

-- 1. Total Claim Payment Amount by Provider (Top 10 Highest Billing Hospitals)
SELECT 
    PRVDR_NUM AS Provider_ID,
    COUNT(CLM_ID) AS Total_Claims,
    ROUND(SUM(CLM_PMT_AMT), 2) AS Total_Payment_Received,
    ROUND(AVG(CLM_PMT_AMT), 2) AS Average_Payment_Per_Claim
FROM vw_clean_inpatient
GROUP BY PRVDR_NUM
ORDER BY Total_Payment_Received DESC
LIMIT 10;

-- 2. Non-Payment & Denial Analysis (Revenue Leakage)
SELECT 
    CLM_MDCR_NON_PMT_RSN_CD AS Denial_Reason_Code,
    COUNT(CLM_ID) AS Denied_Claims_Count,
    ROUND(SUM(CLM_PMT_AMT), 2) AS Revenue_At_Risk
FROM inpatient
WHERE CLM_MDCR_NON_PMT_RSN_CD IS NOT NULL 
  AND CLM_MDCR_NON_PMT_RSN_CD != ''
GROUP BY CLM_MDCR_NON_PMT_RSN_CD
ORDER BY Denied_Claims_Count DESC;

-- 3. Total Prescription Drug Event (PDE) Cost Overview
SELECT 
    COUNT(PDE_ID) AS Total_Prescriptions,
    ROUND(SUM(TOT_RX_CST_AMT), 2) AS Total_Drug_Cost
FROM pde
WHERE TOT_RX_CST_AMT > 0;
