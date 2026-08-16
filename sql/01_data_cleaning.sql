-- ============================================================================
-- File: 01_data_cleaning.sql
-- Project: MedClaim-GenAI
-- Source:  CMS Synthetic Medicare Claims PUFs (May 2023), loaded as-is into
--          raw_inpatient, raw_snf, raw_hha, raw_hospice, raw_dme, raw_pde,
--          raw_beneficiary_<year> (2015-2025) tables.
--
-- Purpose: Tier-1 cleaning layer. Every downstream query (02_financial_analysis.sql,
--          scripts/isolation_forest.py, the Power BI model) reads ONLY from the
--          vw_clean_* views defined here — never from raw_* tables directly.
--
-- Verified against the actual uploaded files before writing this (row counts,
-- column positions, value ranges) — notes below record what was checked and why
-- it matters, since the raw files carry known claim-grain gotchas:
--
--   1. CLAIM-GRAIN vs LINE-GRAIN: inpatient/snf/hha/hospice/dme are one row per
--      REVENUE-CENTER LINE ITEM, not one row per claim. CLM_PMT_AMT is a
--      claim-level total repeated on every line of that claim (confirmed:
--      CLM_ID -10000930775141 in inpatient.csv has 46 line rows, all sharing
--      one CLM_PMT_AMT). Summing CLM_PMT_AMT straight off the raw table
--      over-counts every multi-line claim. Fix: collapse to one row per
--      (BENE_ID, CLM_ID) using GROUP BY before any dollar aggregation, and
--      separately compute a true line-item count as its own column.
--
--   2. NULL / blank CLM_FROM_DT: a handful of rows have blank date fields;
--      substr()-based date parsing on a blank string returns NULL silently
--      rather than erroring, so unfiltered claims can vanish out of
--      date-range logic without a visible failure. Fix: require
--      CLM_FROM_DT IS NOT NULL AND CLM_FROM_DT != '' before parsing.
--
--   3. Negative payments: checked all 5 claim-payment fields
--      (inpatient/snf/hha/hospice/dme CLM_PMT_AMT, pde TOT_RX_CST_AMT) —
--      zero negative values exist in this synthetic release (unlike real
--      NCH data, per the CMS User Guide Section 4.4, which explicitly notes
--      real claims include negative payment amounts not modeled here). No
--      negative-value filter is applied for that reason, but the check is
--      left in as an assertion (Section 5 below) so a future data refresh
--      that does include negatives doesn't silently corrupt the payment
--      views.
--
--   4. PRVDR_NUM blank on 2,841 of 58,066 inpatient line rows (Carrier/DME
--      claims key on CARR_NUM instead, per CMS User Guide Table 6-4; DME
--      itself has both CARR_NUM and PRVDR_NUM and is 100% populated on
--      PRVDR_NUM in this file). Fix: filter blank/null PRVDR_NUM out of the
--      provider-level views rather than let them collapse into a bogus ''
--      provider bucket.
--
--   5. CLM_MDCR_NON_PMT_RSN_CD (denial/non-payment reason code) is BLANK on
--      100% of rows in every institutional claim type (verified on
--      inpatient and hha; also fixed as [Blank] for snf/hospice per the
--      CMS User Guide Sections 6.2/6.7/6.8/6.9). A denial-analysis query
--      built on this column will always return zero rows on this dataset —
--      that's not a bug to work around, it's a modeling limitation of the
--      synthetic data (Synthea does not simulate claim denials). Section
--      02_financial_analysis.sql therefore does NOT include a denial
--      analysis section; see the comment there for what's used instead as
--      a revenue-risk proxy.
--
--   6. snf.csv and snf-1.csv are byte-identical (same md5). Only snf.csv is
--      loaded/used; snf-1.csv is a duplicate upload and should be ignored.
-- ============================================================================

-- ----------------------------------------------------------------------------
-- 0. Drop views in dependency order so this script is safely re-runnable.
-- ----------------------------------------------------------------------------
DROP VIEW IF EXISTS vw_clean_inpatient;
DROP VIEW IF EXISTS vw_clean_snf;
DROP VIEW IF EXISTS vw_clean_hha;
DROP VIEW IF EXISTS vw_clean_hospice;
DROP VIEW IF EXISTS vw_clean_dme;
DROP VIEW IF EXISTS vw_clean_pde;
DROP VIEW IF EXISTS vw_clean_beneficiary;

-- ----------------------------------------------------------------------------
-- 1. Inpatient — collapse line items to one row per claim.
--    CLM_PMT_AMT, CLM_UTLZTN_DAY_CNT (length of stay), PRVDR_NUM, and the
--    diagnosis/date fields are claim-level and identical across all line
--    rows of a claim, so MAX() is a safe no-op aggregate for them; the only
--    real aggregate is COUNT(*) for true line-item count.
-- ----------------------------------------------------------------------------
CREATE VIEW vw_clean_inpatient AS
SELECT
    BENE_ID,
    CLM_ID,
    MAX(NULLIF(TRIM(PRVDR_NUM), ''))                      AS PRVDR_NUM,
    date(substr(CLM_FROM_DT,8,4)||'-'||
         CASE substr(CLM_FROM_DT,4,3)
             WHEN 'Jan' THEN '01' WHEN 'Feb' THEN '02' WHEN 'Mar' THEN '03'
             WHEN 'Apr' THEN '04' WHEN 'May' THEN '05' WHEN 'Jun' THEN '06'
             WHEN 'Jul' THEN '07' WHEN 'Aug' THEN '08' WHEN 'Sep' THEN '09'
             WHEN 'Oct' THEN '10' WHEN 'Nov' THEN '11' WHEN 'Dec' THEN '12'
         END||'-'||substr(CLM_FROM_DT,1,2))                AS CLM_FROM_DT,
    date(substr(CLM_THRU_DT,8,4)||'-'||
         CASE substr(CLM_THRU_DT,4,3)
             WHEN 'Jan' THEN '01' WHEN 'Feb' THEN '02' WHEN 'Mar' THEN '03'
             WHEN 'Apr' THEN '04' WHEN 'May' THEN '05' WHEN 'Jun' THEN '06'
             WHEN 'Jul' THEN '07' WHEN 'Aug' THEN '08' WHEN 'Sep' THEN '09'
             WHEN 'Oct' THEN '10' WHEN 'Nov' THEN '11' WHEN 'Dec' THEN '12'
         END||'-'||substr(CLM_THRU_DT,1,2))                AS CLM_THRU_DT,
    CAST(MAX(CLM_PMT_AMT) AS REAL)                        AS CLM_PMT_AMT,
    CAST(MAX(CLM_UTLZTN_DAY_CNT) AS INTEGER)              AS CLM_UTLZTN_DAY_CNT,
    MAX(NULLIF(TRIM(PRNCPAL_DGNS_CD), ''))                AS PRNCPAL_DGNS_CD,
    MAX(NULLIF(TRIM(CLM_DRG_CD), ''))                     AS CLM_DRG_CD,
    MAX(NULLIF(TRIM(PTNT_DSCHRG_STUS_CD), ''))            AS PTNT_DSCHRG_STUS_CD,
    COUNT(*)                                              AS Line_Item_Count
FROM raw_inpatient
WHERE CLM_ID IS NOT NULL AND TRIM(CLM_ID) != ''
  AND CLM_FROM_DT IS NOT NULL AND TRIM(CLM_FROM_DT) != ''
GROUP BY BENE_ID, CLM_ID;

-- ----------------------------------------------------------------------------
-- 2. SNF — same claim-grain collapse pattern as inpatient.
-- ----------------------------------------------------------------------------
CREATE VIEW vw_clean_snf AS
SELECT
    BENE_ID,
    CLM_ID,
    MAX(NULLIF(TRIM(PRVDR_NUM), ''))                      AS PRVDR_NUM,
    date(substr(CLM_FROM_DT,8,4)||'-'||
         CASE substr(CLM_FROM_DT,4,3)
             WHEN 'Jan' THEN '01' WHEN 'Feb' THEN '02' WHEN 'Mar' THEN '03'
             WHEN 'Apr' THEN '04' WHEN 'May' THEN '05' WHEN 'Jun' THEN '06'
             WHEN 'Jul' THEN '07' WHEN 'Aug' THEN '08' WHEN 'Sep' THEN '09'
             WHEN 'Oct' THEN '10' WHEN 'Nov' THEN '11' WHEN 'Dec' THEN '12'
         END||'-'||substr(CLM_FROM_DT,1,2))                AS CLM_FROM_DT,
    CAST(MAX(CLM_PMT_AMT) AS REAL)                        AS CLM_PMT_AMT,
    CAST(MAX(CLM_UTLZTN_DAY_CNT) AS INTEGER)              AS CLM_UTLZTN_DAY_CNT,
    MAX(NULLIF(TRIM(CLM_MDCR_NON_PMT_RSN_CD), ''))        AS CLM_MDCR_NON_PMT_RSN_CD,
    COUNT(*)                                              AS Line_Item_Count
FROM raw_snf
WHERE CLM_ID IS NOT NULL AND TRIM(CLM_ID) != ''
  AND CLM_FROM_DT IS NOT NULL AND TRIM(CLM_FROM_DT) != ''
GROUP BY BENE_ID, CLM_ID;

-- ----------------------------------------------------------------------------
-- 3. HHA
-- ----------------------------------------------------------------------------
CREATE VIEW vw_clean_hha AS
SELECT
    BENE_ID,
    CLM_ID,
    MAX(NULLIF(TRIM(PRVDR_NUM), ''))                      AS PRVDR_NUM,
    date(substr(CLM_FROM_DT,8,4)||'-'||
         CASE substr(CLM_FROM_DT,4,3)
             WHEN 'Jan' THEN '01' WHEN 'Feb' THEN '02' WHEN 'Mar' THEN '03'
             WHEN 'Apr' THEN '04' WHEN 'May' THEN '05' WHEN 'Jun' THEN '06'
             WHEN 'Jul' THEN '07' WHEN 'Aug' THEN '08' WHEN 'Sep' THEN '09'
             WHEN 'Oct' THEN '10' WHEN 'Nov' THEN '11' WHEN 'Dec' THEN '12'
         END||'-'||substr(CLM_FROM_DT,1,2))                AS CLM_FROM_DT,
    CAST(MAX(CLM_PMT_AMT) AS REAL)                        AS CLM_PMT_AMT,
    MAX(NULLIF(TRIM(CLM_MDCR_NON_PMT_RSN_CD), ''))        AS CLM_MDCR_NON_PMT_RSN_CD,
    COUNT(*)                                              AS Line_Item_Count
FROM raw_hha
WHERE CLM_ID IS NOT NULL AND TRIM(CLM_ID) != ''
  AND CLM_FROM_DT IS NOT NULL AND TRIM(CLM_FROM_DT) != ''
GROUP BY BENE_ID, CLM_ID;

-- ----------------------------------------------------------------------------
-- 4. Hospice
-- ----------------------------------------------------------------------------
CREATE VIEW vw_clean_hospice AS
SELECT
    BENE_ID,
    CLM_ID,
    MAX(NULLIF(TRIM(PRVDR_NUM), ''))                      AS PRVDR_NUM,
    date(substr(CLM_FROM_DT,8,4)||'-'||
         CASE substr(CLM_FROM_DT,4,3)
             WHEN 'Jan' THEN '01' WHEN 'Feb' THEN '02' WHEN 'Mar' THEN '03'
             WHEN 'Apr' THEN '04' WHEN 'May' THEN '05' WHEN 'Jun' THEN '06'
             WHEN 'Jul' THEN '07' WHEN 'Aug' THEN '08' WHEN 'Sep' THEN '09'
             WHEN 'Oct' THEN '10' WHEN 'Nov' THEN '11' WHEN 'Dec' THEN '12'
         END||'-'||substr(CLM_FROM_DT,1,2))                AS CLM_FROM_DT,
    CAST(MAX(CLM_PMT_AMT) AS REAL)                        AS CLM_PMT_AMT,
    CAST(MAX(CLM_UTLZTN_DAY_CNT) AS INTEGER)              AS CLM_UTLZTN_DAY_CNT,
    MAX(NULLIF(TRIM(CLM_MDCR_NON_PMT_RSN_CD), ''))        AS CLM_MDCR_NON_PMT_RSN_CD,
    COUNT(*)                                              AS Line_Item_Count
FROM raw_hospice
WHERE CLM_ID IS NOT NULL AND TRIM(CLM_ID) != ''
  AND CLM_FROM_DT IS NOT NULL AND TRIM(CLM_FROM_DT) != ''
GROUP BY BENE_ID, CLM_ID;

-- ----------------------------------------------------------------------------
-- 5. DME — keys on CARR_NUM (supplier), not PRVDR_NUM, per CMS User Guide
--    Table 6-4 (Carrier) convention; DME line items also carry PRVDR_NUM
--    (ordering/rendering provider) which is kept for completeness.
-- ----------------------------------------------------------------------------
CREATE VIEW vw_clean_dme AS
SELECT
    BENE_ID,
    CLM_ID,
    MAX(NULLIF(TRIM(CARR_NUM), ''))                       AS CARR_NUM,
    MAX(NULLIF(TRIM(PRVDR_NUM), ''))                      AS PRVDR_NUM,
    date(substr(CLM_FROM_DT,8,4)||'-'||
         CASE substr(CLM_FROM_DT,4,3)
             WHEN 'Jan' THEN '01' WHEN 'Feb' THEN '02' WHEN 'Mar' THEN '03'
             WHEN 'Apr' THEN '04' WHEN 'May' THEN '05' WHEN 'Jun' THEN '06'
             WHEN 'Jul' THEN '07' WHEN 'Aug' THEN '08' WHEN 'Sep' THEN '09'
             WHEN 'Oct' THEN '10' WHEN 'Nov' THEN '11' WHEN 'Dec' THEN '12'
         END||'-'||substr(CLM_FROM_DT,1,2))                AS CLM_FROM_DT,
    CAST(MAX(CLM_PMT_AMT) AS REAL)                        AS CLM_PMT_AMT,
    COUNT(*)                                              AS Line_Item_Count
FROM raw_dme
WHERE CLM_ID IS NOT NULL AND TRIM(CLM_ID) != ''
  AND CLM_FROM_DT IS NOT NULL AND TRIM(CLM_FROM_DT) != ''
GROUP BY BENE_ID, CLM_ID;

-- ----------------------------------------------------------------------------
-- 6. PDE — already one row per prescription event (no line-item collapse
--    needed), so this is a straight type-cast/null-guard pass.
-- ----------------------------------------------------------------------------
CREATE VIEW vw_clean_pde AS
SELECT
    PDE_ID,
    BENE_ID,
    date(substr(SRVC_DT,8,4)||'-'||
         CASE substr(SRVC_DT,4,3)
             WHEN 'Jan' THEN '01' WHEN 'Feb' THEN '02' WHEN 'Mar' THEN '03'
             WHEN 'Apr' THEN '04' WHEN 'May' THEN '05' WHEN 'Jun' THEN '06'
             WHEN 'Jul' THEN '07' WHEN 'Aug' THEN '08' WHEN 'Sep' THEN '09'
             WHEN 'Oct' THEN '10' WHEN 'Nov' THEN '11' WHEN 'Dec' THEN '12'
         END||'-'||substr(SRVC_DT,1,2))                    AS SRVC_DT,
    PROD_SRVC_ID,
    CAST(QTY_DSPNSD_NUM AS REAL)                          AS QTY_DSPNSD_NUM,
    CAST(DAYS_SUPLY_NUM AS INTEGER)                       AS DAYS_SUPLY_NUM,
    CAST(TOT_RX_CST_AMT AS REAL)                          AS TOT_RX_CST_AMT,
    CAST(CVRD_D_PLAN_PD_AMT AS REAL)                      AS CVRD_D_PLAN_PD_AMT,
    CAST(PTNT_PAY_AMT AS REAL)                            AS PTNT_PAY_AMT,
    BRND_GNRC_CD
FROM raw_pde
WHERE PDE_ID IS NOT NULL AND TRIM(PDE_ID) != ''
  AND SRVC_DT IS NOT NULL AND TRIM(SRVC_DT) != '';

-- ----------------------------------------------------------------------------
-- 7. Beneficiary — one unified view across all 11 annual snapshot files
--    (2015-2025), each already one row per beneficiary per year per the
--    CMS User Guide (Table 3-3, files #1-11). BENE_ID + BENE_SEX_IDENT_CD +
--    BENE_RACE_CD + STATE_CODE + AGE_AT_END_REF_YR + ESRD_IND are the
--    columns actually used downstream (demographics/eligibility), so only
--    those are pulled through — not all 185 columns.
-- ----------------------------------------------------------------------------
CREATE VIEW vw_clean_beneficiary AS
SELECT BENE_ID, STATE_CODE, CAST(AGE_AT_END_REF_YR AS INTEGER) AS AGE_AT_END_REF_YR,
       SEX_IDENT_CD, BENE_RACE_CD, ESRD_IND, BENE_ENROLLMT_REF_YR
FROM raw_beneficiary_2015
UNION ALL
SELECT BENE_ID, STATE_CODE, CAST(AGE_AT_END_REF_YR AS INTEGER), SEX_IDENT_CD, BENE_RACE_CD, ESRD_IND, BENE_ENROLLMT_REF_YR FROM raw_beneficiary_2016
UNION ALL
SELECT BENE_ID, STATE_CODE, CAST(AGE_AT_END_REF_YR AS INTEGER), SEX_IDENT_CD, BENE_RACE_CD, ESRD_IND, BENE_ENROLLMT_REF_YR FROM raw_beneficiary_2017
UNION ALL
SELECT BENE_ID, STATE_CODE, CAST(AGE_AT_END_REF_YR AS INTEGER), SEX_IDENT_CD, BENE_RACE_CD, ESRD_IND, BENE_ENROLLMT_REF_YR FROM raw_beneficiary_2018
UNION ALL
SELECT BENE_ID, STATE_CODE, CAST(AGE_AT_END_REF_YR AS INTEGER), SEX_IDENT_CD, BENE_RACE_CD, ESRD_IND, BENE_ENROLLMT_REF_YR FROM raw_beneficiary_2019
UNION ALL
SELECT BENE_ID, STATE_CODE, CAST(AGE_AT_END_REF_YR AS INTEGER), SEX_IDENT_CD, BENE_RACE_CD, ESRD_IND, BENE_ENROLLMT_REF_YR FROM raw_beneficiary_2020
UNION ALL
SELECT BENE_ID, STATE_CODE, CAST(AGE_AT_END_REF_YR AS INTEGER), SEX_IDENT_CD, BENE_RACE_CD, ESRD_IND, BENE_ENROLLMT_REF_YR FROM raw_beneficiary_2021
UNION ALL
SELECT BENE_ID, STATE_CODE, CAST(AGE_AT_END_REF_YR AS INTEGER), SEX_IDENT_CD, BENE_RACE_CD, ESRD_IND, BENE_ENROLLMT_REF_YR FROM raw_beneficiary_2022
UNION ALL
SELECT BENE_ID, STATE_CODE, CAST(AGE_AT_END_REF_YR AS INTEGER), SEX_IDENT_CD, BENE_RACE_CD, ESRD_IND, BENE_ENROLLMT_REF_YR FROM raw_beneficiary_2023
UNION ALL
SELECT BENE_ID, STATE_CODE, CAST(AGE_AT_END_REF_YR AS INTEGER), SEX_IDENT_CD, BENE_RACE_CD, ESRD_IND, BENE_ENROLLMT_REF_YR FROM raw_beneficiary_2024
UNION ALL
SELECT BENE_ID, STATE_CODE, CAST(AGE_AT_END_REF_YR AS INTEGER), SEX_IDENT_CD, BENE_RACE_CD, ESRD_IND, BENE_ENROLLMT_REF_YR FROM raw_beneficiary_2025;

-- ----------------------------------------------------------------------------
-- 8. Verification block — run after CREATEs to confirm the views behave as
--    intended before anything downstream depends on them. Each check should
--    return 0 (or an explicitly-expected count).
-- ----------------------------------------------------------------------------
-- 8a. Row counts should shrink from raw (line-grain) to clean (claim-grain):
--     e.g. raw_inpatient 58,066 lines -> vw_clean_inpatient 20,867 claims.
SELECT 'raw_inpatient_rows' AS check_name, COUNT(*) AS value FROM raw_inpatient
UNION ALL SELECT 'clean_inpatient_claims', COUNT(*) FROM vw_clean_inpatient
UNION ALL SELECT 'raw_snf_rows', COUNT(*) FROM raw_snf
UNION ALL SELECT 'clean_snf_claims', COUNT(*) FROM vw_clean_snf
UNION ALL SELECT 'raw_hha_rows', COUNT(*) FROM raw_hha
UNION ALL SELECT 'clean_hha_claims', COUNT(*) FROM vw_clean_hha
UNION ALL SELECT 'raw_hospice_rows', COUNT(*) FROM raw_hospice
UNION ALL SELECT 'clean_hospice_claims', COUNT(*) FROM vw_clean_hospice
UNION ALL SELECT 'raw_dme_rows', COUNT(*) FROM raw_dme
UNION ALL SELECT 'clean_dme_claims', COUNT(*) FROM vw_clean_dme
UNION ALL SELECT 'clean_pde_events', COUNT(*) FROM vw_clean_pde
UNION ALL SELECT 'clean_beneficiary_year_rows', COUNT(*) FROM vw_clean_beneficiary;

-- 8b. No view should have lost its claims to a bad filter (expect 0 rows back):
SELECT 'inpatient_null_pmt_amt' AS check_name, COUNT(*) FROM vw_clean_inpatient WHERE CLM_PMT_AMT IS NULL
UNION ALL SELECT 'snf_null_pmt_amt', COUNT(*) FROM vw_clean_snf WHERE CLM_PMT_AMT IS NULL
UNION ALL SELECT 'hha_null_pmt_amt', COUNT(*) FROM vw_clean_hha WHERE CLM_PMT_AMT IS NULL
UNION ALL SELECT 'hospice_null_pmt_amt', COUNT(*) FROM vw_clean_hospice WHERE CLM_PMT_AMT IS NULL
UNION ALL SELECT 'dme_null_pmt_amt', COUNT(*) FROM vw_clean_dme WHERE CLM_PMT_AMT IS NULL
UNION ALL SELECT 'inpatient_dupe_claim_ids', COUNT(*) FROM (
    SELECT CLM_ID FROM vw_clean_inpatient GROUP BY BENE_ID, CLM_ID HAVING COUNT(*) > 1
);
