-- ============================================================
-- MySQL Analytics Views
-- ============================================================

-- ============================
-- JUDGE ANALYTICS
-- ============================

-- Most active judges by case count
CREATE OR REPLACE VIEW v_judge_activity AS
SELECT
    j.judge_id,
    j.judge_name,
    COUNT(DISTINCT cj.case_id) AS total_cases,
    SUM(CASE WHEN c.verdict = 'Accepted' THEN 1 ELSE 0 END) AS accepted,
    SUM(CASE WHEN c.verdict = 'Rejected' THEN 1 ELSE 0 END) AS rejected,
    ROUND(AVG(c.word_count)) AS avg_judgment_length,
    MIN(c.judgment_date) AS first_case,
    MAX(c.judgment_date) AS last_case
FROM judges j
JOIN case_judges cj ON j.judge_id = cj.judge_id
JOIN cases c ON cj.case_id = c.case_id
GROUP BY j.judge_id, j.judge_name
ORDER BY total_cases DESC;


-- Most cited judges
CREATE OR REPLACE VIEW v_most_cited_judges AS
SELECT
    j.judge_id,
    j.judge_name,
    COUNT(DISTINCT ct.citation_id) AS citation_count,
    COUNT(DISTINCT cj.case_id) AS case_count
FROM judges j
JOIN case_judges cj ON j.judge_id = cj.judge_id
JOIN citations ct ON cj.case_id = ct.case_id
GROUP BY j.judge_id, j.judge_name
ORDER BY citation_count DESC;


-- ============================
-- LEGAL ANALYTICS
-- ============================

-- Most referenced acts
CREATE OR REPLACE VIEW v_act_analytics AS
SELECT
    a.act_id,
    a.act_name,
    COUNT(DISTINCT ca.case_id) AS case_count
FROM acts a
JOIN case_acts ca ON a.act_id = ca.act_id
GROUP BY a.act_id, a.act_name
ORDER BY case_count DESC;


-- Verdict distribution by case type
CREATE OR REPLACE VIEW v_verdict_distribution AS
SELECT
    verdict,
    case_type,
    COUNT(*) AS total
FROM cases
WHERE verdict IS NOT NULL AND verdict != ''
GROUP BY verdict, case_type
ORDER BY case_type, total DESC;


-- Case type distribution
CREATE OR REPLACE VIEW v_case_type_distribution AS
SELECT
    case_type,
    case_category,
    COUNT(*) AS total,
    ROUND(AVG(word_count)) AS avg_length,
    SUM(CASE WHEN verdict = 'Accepted' THEN 1 ELSE 0 END) AS accepted,
    SUM(CASE WHEN verdict = 'Rejected' THEN 1 ELSE 0 END) AS rejected
FROM cases
GROUP BY case_type, case_category
ORDER BY total DESC;


-- ============================
-- CITATION ANALYTICS
-- ============================

-- Most influential cases (most cited via case_citations)
CREATE OR REPLACE VIEW v_influential_cases AS
SELECT
    c.case_id,
    c.case_title,
    c.case_number,
    c.judgment_date,
    c.verdict,
    COUNT(cc.source_case_id) AS times_cited
FROM cases c
JOIN case_citations cc ON c.case_id = cc.target_case_id
GROUP BY c.case_id, c.case_title, c.case_number, c.judgment_date, c.verdict
ORDER BY times_cited DESC;


-- Citation type distribution
CREATE OR REPLACE VIEW v_citation_types AS
SELECT
    citation_type,
    COUNT(*) AS total,
    COUNT(DISTINCT case_id) AS unique_cases
FROM citations
GROUP BY citation_type
ORDER BY total DESC;


-- ============================
-- TIMELINE ANALYTICS
-- ============================

-- Cases per year
CREATE OR REPLACE VIEW v_cases_per_year AS
SELECT
    YEAR(judgment_date) AS `year`,
    COUNT(*) AS total_cases,
    SUM(CASE WHEN verdict = 'Accepted' THEN 1 ELSE 0 END) AS accepted,
    SUM(CASE WHEN verdict = 'Rejected' THEN 1 ELSE 0 END) AS rejected,
    ROUND(AVG(word_count)) AS avg_length
FROM cases
WHERE judgment_date IS NOT NULL
GROUP BY YEAR(judgment_date)
ORDER BY `year`;


-- Monthly trends
CREATE OR REPLACE VIEW v_monthly_trends AS
SELECT
    DATE_FORMAT(judgment_date, '%Y-%m-01') AS `month`,
    COUNT(*) AS total_cases,
    case_category
FROM cases
WHERE judgment_date IS NOT NULL
GROUP BY DATE_FORMAT(judgment_date, '%Y-%m-01'), case_category
ORDER BY `month`;


-- ============================
-- DASHBOARD SUMMARY
-- ============================

CREATE OR REPLACE VIEW v_dashboard_summary AS
SELECT
    (SELECT COUNT(*) FROM cases) AS total_cases,
    (SELECT COUNT(*) FROM judges) AS total_judges,
    (SELECT COUNT(*) FROM citations) AS total_citations,
    (SELECT COUNT(*) FROM acts) AS total_acts,
    (SELECT COUNT(*) FROM parties) AS total_parties,
    (SELECT COUNT(*) FROM courts) AS total_courts,
    (SELECT COUNT(*) FROM lawyers) AS total_lawyers,
    (SELECT SUM(CASE WHEN verdict = 'Accepted' THEN 1 ELSE 0 END) FROM cases) AS accepted_cases,
    (SELECT SUM(CASE WHEN verdict = 'Rejected' THEN 1 ELSE 0 END) FROM cases) AS rejected_cases;
