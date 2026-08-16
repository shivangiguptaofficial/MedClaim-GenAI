-- =====================================================================
-- Script: 01_data_cleaning.sql
-- Purpose: Data Hygiene, Staging Views, and SQLite Date Parsing Fix
-- =====================================================================

-- Drop existing views if they exist to allow clean recreation
DROP VIEW IF EXISTS vw_clean_inpatient;
DROP VIEW IF EXISTS vw_clean_snf;

-- 1. Cleaned Inpatient Claims View with ISO Date Conversion
CREATE VIEW vw_clean_inpatient AS
SELECT
    BENE_ID,
    CLM_ID,
    PRVDR_NUM,
    date(substr(CLM_FROM_DT,8,4)||'-'||
        CASE substr(CLM_FROM_DT,4,3)
            WHEN 'Jan' THEN '01' WHEN 'Feb' THEN '02' WHEN 'Mar' THEN '03'
            WHEN 'Apr' THEN '04' WHEN 'May' THEN '05' WHEN 'Jun' THEN '06'
            WHEN 'Jul' THEN '07' WHEN 'Aug' THEN '08' WHEN 'Sep' THEN '09'
            WHEN 'Oct' THEN '10' WHEN 'Nov' THEN '11' WHEN 'Dec' THEN '12'
        END||'-'||substr(CLM_FROM_DT,1,2)) AS CLM_FROM_DT,
    date(substr(CLM_THRU_DT,8,4)||'-'||
        CASE substr(CLM_THRU_DT,4,3)
            WHEN 'Jan' THEN '01' WHEN 'Feb' THEN '02' WHEN 'Mar' THEN '03'
            WHEN 'Apr' THEN '04' WHEN 'May' THEN '05' WHEN 'Jun' THEN '06'
            WHEN 'Jul' THEN '07' WHEN 'Aug' THEN '08' WHEN 'Sep' THEN '09'
            WHEN 'Oct' THEN '10' WHEN 'Nov' THEN '11' WHEN 'Dec' THEN '12'
        END||'-'||substr(CLM_THRU_DT,1,2)) AS CLM_THRU_DT,
    CLM_PMT_AMT,
    CLM_MDCR_NON_PMT_RSN_CD
FROM inpatient
WHERE CLM_ID IS NOT NULL
  AND CLM_FROM_DT IS NOT NULL
  AND CLM_PMT_AMT >= 0;

-- 2. Cleaned Skilled Nursing Facility (SNF) View with ISO Date Conversion
CREATE VIEW vw_clean_snf AS
SELECT
    BENE_ID,
    CLM_ID,
    PRVDR_NUM,
    date(substr(CLM_FROM_DT,8,4)||'-'||
        CASE substr(CLM_FROM_DT,4,3)
            WHEN 'Jan' THEN '01' WHEN 'Feb' THEN '02' WHEN 'Mar' THEN '03'
            WHEN 'Apr' THEN '04' WHEN 'May' THEN '05' WHEN 'Jun' THEN '06'
            WHEN 'Jul' THEN '07' WHEN 'Aug' THEN '08' WHEN 'Sep' THEN '09'
            WHEN 'Oct' THEN '10' WHEN 'Nov' THEN '11' WHEN 'Dec' THEN '12'
        END||'-'||substr(CLM_FROM_DT,1,2)) AS CLM_FROM_DT,
    date(substr(CLM_THRU_DT,8,4)||'-'||
        CASE substr(CLM_THRU_DT,4,3)
            WHEN 'Jan' THEN '01' WHEN 'Feb' THEN '02' WHEN 'Mar' THEN '03'
            WHEN 'Apr' THEN '04' WHEN 'May' THEN '05' WHEN 'Jun' THEN '06'
            WHEN 'Jul' THEN '07' WHEN 'Aug' THEN '08' WHEN 'Sep' THEN '09'
            WHEN 'Oct' THEN '10' WHEN 'Nov' THEN '11' WHEN 'Dec' THEN '12'
        END||'-'||substr(CLM_THRU_DT,1,2)) AS CLM_THRU_DT,
    CLM_PMT_AMT,
    CLM_MDCR_NON_PMT_RSN_CD
FROM snf
WHERE CLM_ID IS NOT NULL
  AND CLM_FROM_DT IS NOT NULL
  AND CLM_PMT_AMT >= 0;
