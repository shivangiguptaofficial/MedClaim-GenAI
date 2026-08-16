-- ============================================================================
-- File: 02_financial_analysis.sql
-- Description: Financial metrics and provider billing analysis.
--              Reads exclusively from the Tier-1 vw_clean_* views defined in
--              01_data_cleaning.sql, so claim-grain double-counting, blank
--              provider keys, and unparsed dates are already handled before
--              any dollar amount is aggregated.
-- Project: MedClaim-GenAI
-- Prereq:  Run 01_data_cleaning.sql first (creates vw_clean_*).
-- ============================================================================

-- ----------------------------------------------------------------------------
-- 0. System-wide institutional provider claims view.
--    Unions the four institutional claim types that key on PRVDR_NUM
--    (Inpatient, SNF, HHA, Hospice). DME keys on CARR_NUM (supplier), not
--    PRVDR_NUM — see vw_clean_dme in 01_data_cleaning.sql — so it is kept
--    as its own view (Section 4 below) rather than unioned in here, since
--    mixing supplier IDs and facility IDs in one Provider_ID column would
--    silently blend two different identifier spaces.
--    Outpatient and Carrier claim files were not included in this data
--    delivery, so they are out of scope for this script; add them as their
--    own vw_clean_* view + UNION ALL branch here if/when those files land.
-- ----------------------------------------------------------------------------
DROP VIEW IF EXISTS vw_all_provider_claims;
CREATE VIEW vw_all_provider_claims AS
SELECT BENE_ID, CLM_ID, PRVDR_NUM, CLM_PMT_AMT, Line_Item_Count,
       'Inpatient' AS Claim_Type
FROM vw_clean_inpatient
UNION ALL
SELECT BENE_ID, CLM_ID, PRVDR_NUM, CLM_PMT_AMT, Line_Item_Count,
       'SNF' AS Claim_Type
FROM vw_clean_snf
UNION ALL
SELECT BENE_ID, CLM_ID, PRVDR_NUM, CLM_PMT_AMT, Line_Item_Count,
       'HHA' AS Claim_Type
FROM vw_clean_hha
UNION ALL
SELECT BENE_ID, CLM_ID, PRVDR_NUM, CLM_PMT_AMT, Line_Item_Count,
       'Hospice' AS Claim_Type
FROM vw_clean_hospice;

-- ----------------------------------------------------------------------------
-- 1. Top 10 Highest-Billing Institutional Providers
--    (Inpatient + SNF + HHA + Hospice — each claim counted exactly once,
--    since vw_clean_* is already one row per claim.)
--    NULL PRVDR_NUM claims are excluded — 2,841 of the raw inpatient lines
--    had a blank facility field, and vw_clean_inpatient already drops those
--    to NULL via NULLIF, so this filter is a belt-and-suspenders guard
--    against a bogus '' provider bucket, not new logic.
-- ----------------------------------------------------------------------------
SELECT
    PRVDR_NUM                                       AS Provider_ID,
    COUNT(DISTINCT CLM_ID)                          AS Total_Claims,
    ROUND(SUM(CLM_PMT_AMT), 2)                      AS Total_Payment_Received,
    ROUND(AVG(CLM_PMT_AMT), 2)                       AS Average_Payment_Per_Claim,
    ROUND(SUM(CLM_PMT_AMT) * 1.0 / COUNT(DISTINCT CLM_ID), 2) AS Payment_Per_Claim_Check
FROM vw_all_provider_claims
WHERE PRVDR_NUM IS NOT NULL
GROUP BY PRVDR_NUM
ORDER BY Total_Payment_Received DESC
LIMIT 10;

-- ----------------------------------------------------------------------------
-- 2. Total Payment by Claim Type
--    Sanity-check aggregate: total institutional dollars broken out by
--    care setting, so a provider-level view (#1) can be cross-checked
--    against a setting-level view.
-- ----------------------------------------------------------------------------
SELECT
    Claim_Type,
    COUNT(DISTINCT CLM_ID)                          AS Total_Claims,
    ROUND(SUM(CLM_PMT_AMT), 2)                      AS Total_Payment,
    ROUND(AVG(CLM_PMT_AMT), 2)                       AS Avg_Payment_Per_Claim,
    ROUND(AVG(Line_Item_Count), 2)                   AS Avg_Line_Items_Per_Claim
FROM vw_all_provider_claims
GROUP BY Claim_Type
ORDER BY Total_Payment DESC;

-- ----------------------------------------------------------------------------
-- 3. High-Complexity Claim Flag ("Top Billing Providers" proxy)
--    CLM_MDCR_NON_PMT_RSN_CD (the standard denial/non-payment reason code)
--    is populated on 0% of rows across every institutional claim type in
--    this synthetic release — confirmed on inpatient and hha directly, and
--    fixed as a permanently blank field for snf/hospice per the CMS User
--    Guide (Sections 6.2, 6.7, 6.8, 6.9). A denial-analysis query on that
--    column always returns zero rows on this dataset, so it's dropped
--    rather than shipped as dead code.
--    As a usable substitute revenue-risk signal, this flags claims with
--    unusually high line-item counts relative to their claim type's own
--    average — high line-item density is a standard, auditable proxy for
--    billing complexity/upcoding risk in claims analytics, and it's a
--    real, populated column rather than an always-empty one.
-- ----------------------------------------------------------------------------
SELECT
    Claim_Type,
    CLM_ID,
    PRVDR_NUM                                       AS Provider_ID,
    Line_Item_Count,
    ROUND(CLM_PMT_AMT, 2)                           AS Claim_Payment_Amount,
    'High Line-Item Complexity' AS Flag_Reason
FROM (
    SELECT *,
           AVG(Line_Item_Count) OVER (PARTITION BY Claim_Type) AS avg_lines_for_type
    FROM vw_all_provider_claims
    WHERE PRVDR_NUM IS NOT NULL
)
WHERE Line_Item_Count > avg_lines_for_type * 5
ORDER BY Line_Item_Count DESC
LIMIT 25;

-- ----------------------------------------------------------------------------
-- 4. Durable Medical Equipment (DME) — separate from institutional claims
--    since it keys on CARR_NUM (supplier), not PRVDR_NUM (facility).
-- ----------------------------------------------------------------------------
SELECT
    CARR_NUM                                        AS Supplier_ID,
    COUNT(DISTINCT CLM_ID)                          AS Total_Claims,
    ROUND(SUM(CLM_PMT_AMT), 2)                      AS Total_Payment_Received,
    ROUND(AVG(CLM_PMT_AMT), 2)                       AS Average_Payment_Per_Claim
FROM vw_clean_dme
WHERE CARR_NUM IS NOT NULL
GROUP BY CARR_NUM
ORDER BY Total_Payment_Received DESC
LIMIT 10;

-- ----------------------------------------------------------------------------
-- 5. Total Prescription Drug Event (PDE) Cost Overview
-- ----------------------------------------------------------------------------
SELECT
    COUNT(DISTINCT PDE_ID)                          AS Total_Prescriptions,
    COUNT(DISTINCT BENE_ID)                         AS Distinct_Beneficiaries,
    ROUND(SUM(TOT_RX_CST_AMT), 2)                   AS Total_Drug_Cost,
    ROUND(SUM(CVRD_D_PLAN_PD_AMT), 2)               AS Total_Plan_Paid,
    ROUND(SUM(PTNT_PAY_AMT), 2)                     AS Total_Patient_Paid,
    ROUND(AVG(TOT_RX_CST_AMT), 2)                   AS Avg_Cost_Per_Rx
FROM vw_clean_pde;

-- ----------------------------------------------------------------------------
-- 6. Top 10 Costliest Beneficiaries — Total Cost of Care Across All Claim
--    Types + PDE. Rolls institutional claims and drug events up to the
--    beneficiary level so total spend per patient is visible, since no
--    single claim view captures full cost of care on its own.
-- ----------------------------------------------------------------------------
SELECT
    BENE_ID,
    ROUND(SUM(Total_Cost), 2) AS Total_Cost_Of_Care,
    ROUND(SUM(CASE WHEN Source = 'Institutional' THEN Total_Cost ELSE 0 END), 2) AS Institutional_Cost,
    ROUND(SUM(CASE WHEN Source = 'DME' THEN Total_Cost ELSE 0 END), 2)          AS DME_Cost,
    ROUND(SUM(CASE WHEN Source = 'PDE' THEN Total_Cost ELSE 0 END), 2)          AS Drug_Cost
FROM (
    SELECT BENE_ID, CLM_PMT_AMT AS Total_Cost, 'Institutional' AS Source FROM vw_all_provider_claims
    UNION ALL
    SELECT BENE_ID, CLM_PMT_AMT, 'DME' FROM vw_clean_dme
    UNION ALL
    SELECT BENE_ID, TOT_RX_CST_AMT, 'PDE' FROM vw_clean_pde
)
GROUP BY BENE_ID
ORDER BY Total_Cost_Of_Care DESC
LIMIT 10;

-- ----------------------------------------------------------------------------
-- 7. Year-over-Year Institutional Spend Trend
--    Uses CLM_FROM_DT (already parsed to ISO date in the clean views) to
--    trend total payment by calendar year, 2015-2023 (the claims files'
--    covered period per the CMS User Guide Table 3-1). CLM_FROM_DT lives on
--    each individual vw_clean_* view, not on vw_all_provider_claims (which
--    drops it to keep the union's column list lean for Sections 1-3), so
--    it's re-unioned here rather than pulled in through a join — a join on
--    CLM_ID would re-introduce line-item duplication risk.
-- ----------------------------------------------------------------------------
SELECT
    strftime('%Y', CLM_FROM_DT)                     AS Claim_Year,
    Claim_Type,
    COUNT(DISTINCT CLM_ID)                          AS Total_Claims,
    ROUND(SUM(CLM_PMT_AMT), 2)                      AS Total_Payment
FROM (
    SELECT CLM_ID, CLM_FROM_DT, CLM_PMT_AMT, 'Inpatient' AS Claim_Type FROM vw_clean_inpatient
    UNION ALL
    SELECT CLM_ID, CLM_FROM_DT, CLM_PMT_AMT, 'SNF' FROM vw_clean_snf
    UNION ALL
    SELECT CLM_ID, CLM_FROM_DT, CLM_PMT_AMT, 'HHA' FROM vw_clean_hha
    UNION ALL
    SELECT CLM_ID, CLM_FROM_DT, CLM_PMT_AMT, 'Hospice' FROM vw_clean_hospice
    UNION ALL
    SELECT CLM_ID, CLM_FROM_DT, CLM_PMT_AMT, 'DME' FROM vw_clean_dme
)
GROUP BY Claim_Year, Claim_Type
ORDER BY Claim_Year, Claim_Type;
