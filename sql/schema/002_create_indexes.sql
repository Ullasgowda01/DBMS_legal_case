-- ============================================================
-- Additional MySQL Indexes (beyond those in 001_create_tables.sql)
-- ============================================================
-- Note: Primary indexes (B-Tree, FULLTEXT) are defined inline in 001_create_tables.sql.
-- This file contains any supplementary indexes for query optimization.

-- Composite indexes for common query patterns
CREATE INDEX idx_cases_type_verdict ON cases (case_type, verdict);
CREATE INDEX idx_cases_date_verdict ON cases (judgment_date, verdict);
CREATE INDEX idx_cases_category_type ON cases (case_category, case_type);

-- Covering index for case listing queries
CREATE INDEX idx_cases_listing ON cases (case_id, case_type, verdict, judgment_date, word_count);

-- Index for lawyer analytics
CREATE INDEX idx_cl_case_lawyer ON case_lawyers (case_id, lawyer_id);

-- Index for act analytics
CREATE INDEX idx_ca_case_act ON case_acts (case_id, act_id);
