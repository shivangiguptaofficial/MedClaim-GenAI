-- ==============================================================================
-- File: sql/03_clinical_and_joins.sql
-- Description: Patient journey joins and continuity-of-care tracking across
--              the CMS Synthetic Medicare RIF beneficiary and claims views.
-- Project: MedClaim-GenAI
-- ==============================================================================

-- 1. Patient Demographics linked to Inpatient Hospital Costs
SELECT
    b.BENE_ID                          AS Patient_ID,
    b.SEX_IDENT_CD                     AS Gender,
    COUNT(i.CLM_ID)                    AS Total_Hospital_Admissions,
    ROUND(SUM(i.CLM_PMT_AMT), 2)       AS Total_Cost_Of_Care
FROM vw_clean_beneficiary b
INNER JOIN vw_clean_inpatient i
    ON b.BENE_ID = i.BENE_ID
GROUP BY b.BENE_ID, b.SEX_IDENT_CD
ORDER BY Total_Hospital_Admissions DESC
LIMIT 20;


-- 2. Continuity of Care: Patients moving from Inpatient to SNF (Nursing Home)
--    within 30 days of discharge
SELECT
    i.BENE_ID           AS Patient_ID,
    i.CLM_ID             AS Inpatient_Claim,
    i.CLM_THRU_DT         AS Hospital_Discharge_Date,
    s.CLM_ID             AS SNF_Claim,
    s.CLM_FROM_DT          AS SNF_Admission_Date
FROM vw_clean_inpatient i
INNER JOIN vw_clean_snf s
    ON i.BENE_ID = s.BENE_ID
WHERE
    s.CLM_FROM_DT >= i.CLM_THRU_DT
    -- Assumes ISO date formats (YYYY-MM-DD) for SQLite date functions
    AND s.CLM_FROM_DT <= date(i.CLM_THRU_DT, '+30 days')
LIMIT 50;


-- 3. High-Cost Provider Leakage: Total billed vs. paid variance by provider
--    across Inpatient, SNF, and HHA claim types (identifies underpayment risk)
SELECT
    PRVDR_NUM,
    'Inpatient'                                    AS Claim_Type,
    COUNT(CLM_ID)                                  AS Claim_Count,
    ROUND(SUM(CLM_TOT_CHRG_AMT), 2)                AS Total_Billed,
    ROUND(SUM(CLM_PMT_AMT), 2)                     AS Total_Paid,
    ROUND(SUM(CLM_TOT_CHRG_AMT) - SUM(CLM_PMT_AMT), 2) AS Revenue_Gap
FROM vw_clean_inpatient
GROUP BY PRVDR_NUM

UNION ALL

SELECT
    PRVDR_NUM,
    'SNF'                                           AS Claim_Type,
    COUNT(CLM_ID)                                   AS Claim_Count,
    ROUND(SUM(CLM_TOT_CHRG_AMT), 2)                 AS Total_Billed,
    ROUND(SUM(CLM_PMT_AMT), 2)                      AS Total_Paid,
    ROUND(SUM(CLM_TOT_CHRG_AMT) - SUM(CLM_PMT_AMT), 2) AS Revenue_Gap
FROM vw_clean_snf
GROUP BY PRVDR_NUM

ORDER BY Revenue_Gap DESC
LIMIT 25;


-- 4. Denied Claims Detail: Joins denial reason codes back to beneficiary
--    demographics for root-cause / equity analysis
SELECT
    c.BENE_ID,
    b.SEX_IDENT_CD                     AS Gender,
    b.AGE_AT_END_REF_YR                AS Age,
    c.CLM_ID,
    c.CLM_MDCR_NON_PMT_RSN_CD          AS Denial_Reason_Code,
    c.CLM_PMT_AMT                      AS Payment_Amount,
    c.CLM_FROM_DT                      AS Claim_Start_Date
FROM vw_clean_inpatient c
INNER JOIN vw_clean_beneficiary b
    ON c.BENE_ID = b.BENE_ID
WHERE
    c.CLM_MDCR_NON_PMT_RSN_CD IS NOT NULL
    AND TRIM(c.CLM_MDCR_NON_PMT_RSN_CD) <> ''
ORDER BY c.CLM_PMT_AMT DESC
LIMIT 50;

