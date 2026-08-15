-- =========================================================================
-- File: 01_data_cleaning.sql
-- Description: Clean raw claim tables by filtering nulls and invalid dates
-- Project: MedClaim-GenAI
-- =========================================================================

-- 1. Create a cleaned version of the Inpatient Claims table
CREATE VIEW vw_clean_inpatient AS
SELECT 
    BENE_ID,
    CLM_ID,
    PRVDR_NUM,
    CLM_FROM_DT,
    CLM_THRU_DT,
    CLM_PMT_AMT,
    CLM_MDCR_NON_PMT_RSN_CD
FROM inpatient
WHERE CLM_ID IS NOT NULL 
  AND CLM_FROM_DT IS NOT NULL
  AND CLM_PMT_AMT >= 0;

-- 2. Create a cleaned version of the Beneficiary table (using 2023 as base)
CREATE VIEW vw_clean_beneficiary AS
SELECT 
    BENE_ID,
    BENE_BIRTH_DT,
    BENE_DEATH_DT,
    BENE_SEX_IDENT_CD
FROM beneficiary_2023 
WHERE BENE_ID IS NOT NULL;

-- 3. Clean Skilled Nursing Facility (SNF) Data
CREATE VIEW vw_clean_snf AS
SELECT 
    BENE_ID,
    CLM_ID,
    PRVDR_NUM,
    CLM_FROM_DT,
    CLM_PMT_AMT
FROM snf
WHERE CLM_ID IS NOT NULL;
