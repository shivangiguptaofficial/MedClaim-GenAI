-- ============================================================================
-- File: 01_data_cleaning.sql
-- Description: Tier 1 data hygiene layer for MedClaim-GenAI.
--
--   Every raw CMS RIF claim file is stored at LINE-ITEM grain (one row per
--   revenue-center line, not per claim), and claim-level dollar fields like
--   CLM_PMT_AMT are repeated on every line of the same claim. Summing them
--   directly overcounts payments for any multi-line claim. Every view below
--   collapses to CLAIM grain via GROUP BY BENE_ID, CLM_ID and uses MAX() on
--   fields that are constant per claim (safe, since they don't vary across
--   lines) while COUNT(*) captures the true line-item count as a feature.
--
--   Raw dates arrive as text in 'DD-Mon-YYYY' format (e.g. '25-Mar-2015'),
--   which SQLite's date() function cannot parse or compare correctly as
--   text. Every date field is rebuilt into ISO 8601 'YYYY-MM-DD' so date()
--   arithmetic and chronological sorting/joins behave correctly downstream.
--
-- Project: MedClaim-GenAI
-- ============================================================================

-- ----------------------------------------------------------------------------
-- 1. Cleaned Inpatient Claims (claim grain, one row per CLM_ID)
-- ----------------------------------------------------------------------------
DROP VIEW IF EXISTS vw_clean_inpatient;
CREATE VIEW vw_clean_inpatient AS
SELECT
    BENE_ID,
    CLM_ID,
    MAX(PRVDR_NUM) AS PRVDR_NUM,
    MAX(date(
        substr(CLM_FROM_DT, 8, 4) || '-' ||
        CASE substr(CLM_FROM_DT, 4, 3)
            WHEN 'Jan' THEN '01' WHEN 'Feb' THEN '02' WHEN 'Mar' THEN '03'
            WHEN 'Apr' THEN '04' WHEN 'May' THEN '05' WHEN 'Jun' THEN '06'
            WHEN 'Jul' THEN '07' WHEN 'Aug' THEN '08' WHEN 'Sep' THEN '09'
            WHEN 'Oct' THEN '10' WHEN 'Nov' THEN '11' WHEN 'Dec' THEN '12'
        END || '-' || substr(CLM_FROM_DT, 1, 2)
    )) AS CLM_FROM_DT,
    MAX(date(
        substr(CLM_THRU_DT, 8, 4) || '-' ||
        CASE substr(CLM_THRU_DT, 4, 3)
            WHEN 'Jan' THEN '01' WHEN 'Feb' THEN '02' WHEN 'Mar' THEN '03'
            WHEN 'Apr' THEN '04' WHEN 'May' THEN '05' WHEN 'Jun' THEN '06'
            WHEN 'Jul' THEN '07' WHEN 'Aug' THEN '08' WHEN 'Sep' THEN '09'
            WHEN 'Oct' THEN '10' WHEN 'Nov' THEN '11' WHEN 'Dec' THEN '12'
        END || '-' || substr(CLM_THRU_DT, 1, 2)
    )) AS CLM_THRU_DT,
    MAX(CLM_UTLZTN_DAY_CNT) AS CLM_UTLZTN_DAY_CNT,   -- length of stay
    MAX(CLM_PMT_AMT) AS CLM_PMT_AMT,
    MAX(CLM_MDCR_NON_PMT_RSN_CD) AS CLM_MDCR_NON_PMT_RSN_CD,
    MAX(PRNCPAL_DGNS_CD) AS PRNCPAL_DGNS_CD,
    COUNT(*) AS Line_Item_Count
FROM inpatient
WHERE CLM_ID IS NOT NULL
  AND CLM_FROM_DT IS NOT NULL
  AND CLM_PMT_AMT >= 0
GROUP BY BENE_ID, CLM_ID;

-- ----------------------------------------------------------------------------
-- 2. Cleaned Beneficiary table (2023 snapshot)
--    NOTE: this is a single-year snapshot. If you want longitudinal
--    enrollment across 2015-2023, replace this with a UNION ALL across all
--    beneficiary_YYYY tables, tagged with a Reference_Year column.
-- ----------------------------------------------------------------------------
DROP VIEW IF EXISTS vw_clean_beneficiary;
CREATE VIEW vw_clean_beneficiary AS
SELECT
    BENE_ID,
    BENE_BIRTH_DT,
    BENE_DEATH_DT,
    BENE_SEX_IDENT_CD
FROM beneficiary_2023
WHERE BENE_ID IS NOT NULL;

-- ----------------------------------------------------------------------------
-- 3. Cleaned Skilled Nursing Facility (SNF) claims (claim grain)
-- ----------------------------------------------------------------------------
DROP VIEW IF EXISTS vw_clean_snf;
CREATE VIEW vw_clean_snf AS
SELECT
    BENE_ID,
    CLM_ID,
    MAX(PRVDR_NUM) AS PRVDR_NUM,
    MAX(date(
        substr(CLM_FROM_DT, 8, 4) || '-' ||
        CASE substr(CLM_FROM_DT, 4, 3)
            WHEN 'Jan' THEN '01' WHEN 'Feb' THEN '02' WHEN 'Mar' THEN '03'
            WHEN 'Apr' THEN '04' WHEN 'May' THEN '05' WHEN 'Jun' THEN '06'
            WHEN 'Jul' THEN '07' WHEN 'Aug' THEN '08' WHEN 'Sep' THEN '09'
            WHEN 'Oct' THEN '10' WHEN 'Nov' THEN '11' WHEN 'Dec' THEN '12'
        END || '-' || substr(CLM_FROM_DT, 1, 2)
    )) AS CLM_FROM_DT,
    MAX(date(
        substr(CLM_THRU_DT, 8, 4) || '-' ||
        CASE substr(CLM_THRU_DT, 4, 3)
            WHEN 'Jan' THEN '01' WHEN 'Feb' THEN '02' WHEN 'Mar' THEN '03'
            WHEN 'Apr' THEN '04' WHEN 'May' THEN '05' WHEN 'Jun' THEN '06'
            WHEN 'Jul' THEN '07' WHEN 'Aug' THEN '08' WHEN 'Sep' THEN '09'
            WHEN 'Oct' THEN '10' WHEN 'Nov' THEN '11' WHEN 'Dec' THEN '12'
        END || '-' || substr(CLM_THRU_DT, 1, 2)
    )) AS CLM_THRU_DT,
    MAX(CLM_UTLZTN_DAY_CNT) AS CLM_UTLZTN_DAY_CNT,
    MAX(CLM_PMT_AMT) AS CLM_PMT_AMT,
    MAX(CLM_MDCR_NON_PMT_RSN_CD) AS CLM_MDCR_NON_PMT_RSN_CD,
    COUNT(*) AS Line_Item_Count
FROM snf
WHERE CLM_ID IS NOT NULL
  AND CLM_FROM_DT IS NOT NULL
  AND CLM_PMT_AMT >= 0
GROUP BY BENE_ID, CLM_ID;

-- ----------------------------------------------------------------------------
-- 4. Cleaned Home Health Agency (HHA) claims (claim grain)
--    HHA has no CLM_UTLZTN_DAY_CNT; CLM_HHA_TOT_VISIT_CNT is its
--    utilization equivalent (visit count instead of length of stay).
-- ----------------------------------------------------------------------------
DROP VIEW IF EXISTS vw_clean_hha;
CREATE VIEW vw_clean_hha AS
SELECT
    BENE_ID,
    CLM_ID,
    MAX(PRVDR_NUM) AS PRVDR_NUM,
    MAX(CLM_PMT_AMT) AS CLM_PMT_AMT,
    MAX(CLM_MDCR_NON_PMT_RSN_CD) AS CLM_MDCR_NON_PMT_RSN_CD,
    MAX(CLM_HHA_TOT_VISIT_CNT) AS CLM_HHA_TOT_VISIT_CNT,
    COUNT(*) AS Line_Item_Count
FROM hha
WHERE CLM_ID IS NOT NULL
  AND CLM_PMT_AMT >= 0
GROUP BY BENE_ID, CLM_ID;

-- ----------------------------------------------------------------------------
-- 5. Cleaned Hospice claims (claim grain)
-- ----------------------------------------------------------------------------
DROP VIEW IF EXISTS vw_clean_hospice;
CREATE VIEW vw_clean_hospice AS
SELECT
    BENE_ID,
    CLM_ID,
    MAX(PRVDR_NUM) AS PRVDR_NUM,
    MAX(CLM_PMT_AMT) AS CLM_PMT_AMT,
    MAX(CLM_MDCR_NON_PMT_RSN_CD) AS CLM_MDCR_NON_PMT_RSN_CD,
    MAX(CLM_UTLZTN_DAY_CNT) AS CLM_UTLZTN_DAY_CNT,
    COUNT(*) AS Line_Item_Count
FROM hospice
WHERE CLM_ID IS NOT NULL
  AND CLM_PMT_AMT >= 0
GROUP BY BENE_ID, CLM_ID;

-- ----------------------------------------------------------------------------
-- 6. Cleaned Prescription Drug Event (PDE) claims
--    PDE is already one row per event, no line-item dedup needed.
-- ----------------------------------------------------------------------------
DROP VIEW IF EXISTS vw_clean_pde;
CREATE VIEW vw_clean_pde AS
SELECT
    PDE_ID,
    BENE_ID,
    SRVC_DT,
    TOT_RX_CST_AMT,
    PTNT_PAY_AMT
FROM pde
WHERE PDE_ID IS NOT NULL
  AND BENE_ID IS NOT NULL
  AND TOT_RX_CST_AMT >= 0;

-- ============================================================================
-- Sanity check — run this after creating the views above.
-- If any view returns 0 rows, its WHERE clause is too strict for the
-- underlying table and needs loosening before building anything on top of it.
-- ============================================================================
SELECT 'vw_clean_inpatient'   AS view_name, COUNT(*) AS row_count FROM vw_clean_inpatient
UNION ALL
SELECT 'vw_clean_beneficiary', COUNT(*) FROM vw_clean_beneficiary
UNION ALL
SELECT 'vw_clean_snf',         COUNT(*) FROM vw_clean_snf
UNION ALL
SELECT 'vw_clean_hha',         COUNT(*) FROM vw_clean_hha
UNION ALL
SELECT 'vw_clean_hospice',     COUNT(*) FROM vw_clean_hospice
UNION ALL
SELECT 'vw_clean_pde',         COUNT(*) FROM vw_clean_pde;

