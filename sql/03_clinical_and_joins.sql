-- =========================================================================
-- File: 03_clinical_and_joins.sql
-- Description: Patient journey joins and continuity of care tracking
-- Project: MedClaim-GenAI
-- =========================================================================

-- 1. Patient Demographics linked to Inpatient Hospital Costs
SELECT 
    b.BENE_ID AS Patient_ID,
    b.BENE_SEX_IDENT_CD AS Gender,
    COUNT(i.CLM_ID) AS Total_Hospital_Admissions,
    ROUND(SUM(i.CLM_PMT_AMT), 2) AS Total_Cost_Of_Care
FROM vw_clean_beneficiary b
INNER JOIN vw_clean_inpatient i 
    ON b.BENE_ID = i.BENE_ID
GROUP BY b.BENE_ID, b.BENE_SEX_IDENT_CD
ORDER BY Total_Hospital_Admissions DESC
LIMIT 20;

-- 2. Continuity of Care: Patients moving from Inpatient to SNF (Nursing Home) within 30 Days
SELECT 
    i.BENE_ID AS Patient_ID,
    i.CLM_ID AS Inpatient_Claim,
    i.CLM_THRU_DT AS Hospital_Discharge_Date,
    s.CLM_ID AS SNF_Claim,
    s.CLM_FROM_DT AS SNF_Admission_Date
FROM vw_clean_inpatient i
INNER JOIN vw_clean_snf s 
    ON i.BENE_ID = s.BENE_ID
WHERE 
    s.CLM_FROM_DT >= i.CLM_THRU_DT 
    -- Assuming Date formats are standard YYYY-MM-DD for SQLite Date functions
    AND s.CLM_FROM_DT <= date(i.CLM_THRU_DT, '+30 days') 
LIMIT 50;
