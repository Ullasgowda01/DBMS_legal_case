-- ============================================================
-- MySQL Stored Procedures
-- ============================================================

DELIMITER //

-- add_case: Insert new case with court resolution
DROP PROCEDURE IF EXISTS add_case//
CREATE PROCEDURE add_case(
    IN p_case_number VARCHAR(100),
    IN p_case_title VARCHAR(500),
    IN p_court_name VARCHAR(255),
    IN p_judgment_date DATE,
    IN p_case_type VARCHAR(100),
    IN p_case_category VARCHAR(50),
    IN p_verdict VARCHAR(50),
    IN p_summary TEXT,
    OUT p_case_id INT
)
BEGIN
    DECLARE v_court_id INT;

    -- Get or create court
    SELECT court_id INTO v_court_id FROM courts WHERE court_name = p_court_name LIMIT 1;
    IF v_court_id IS NULL THEN
        INSERT INTO courts (court_name) VALUES (p_court_name);
        SET v_court_id = LAST_INSERT_ID();
    END IF;

    -- Insert case
    INSERT INTO cases (case_number, case_title, court_id, judgment_date,
                       case_type, case_category, verdict, summary)
    VALUES (p_case_number, p_case_title, v_court_id, p_judgment_date,
            p_case_type, p_case_category, p_verdict, p_summary);

    SET p_case_id = LAST_INSERT_ID();
END//


-- add_citation: Insert citation relationship between cases
DROP PROCEDURE IF EXISTS add_citation//
CREATE PROCEDURE add_citation(
    IN p_source_case_id INT,
    IN p_target_case_id INT,
    IN p_strength INT
)
BEGIN
    INSERT INTO case_citations (source_case_id, target_case_id, citation_strength)
    VALUES (p_source_case_id, p_target_case_id, p_strength)
    ON DUPLICATE KEY UPDATE citation_strength = citation_strength + p_strength;
END//


-- get_judge_statistics: Comprehensive judge analytics
DROP PROCEDURE IF EXISTS get_judge_statistics//
CREATE PROCEDURE get_judge_statistics(IN p_judge_id INT)
BEGIN
    SELECT
        j.judge_id,
        j.judge_name,
        COUNT(DISTINCT cj.case_id) AS total_cases,
        ROUND(AVG(c.word_count), 0) AS avg_word_count,
        COUNT(DISTINCT ct.citation_id) AS total_citations,
        SUM(CASE WHEN c.verdict = 'Accepted' THEN 1 ELSE 0 END) AS accepted_cases,
        SUM(CASE WHEN c.verdict = 'Rejected' THEN 1 ELSE 0 END) AS rejected_cases,
        ROUND(
            SUM(CASE WHEN c.verdict = 'Accepted' THEN 1 ELSE 0 END) /
            NULLIF(COUNT(DISTINCT cj.case_id), 0) * 100, 2
        ) AS acceptance_rate
    FROM judges j
    JOIN case_judges cj ON j.judge_id = cj.judge_id
    JOIN cases c ON cj.case_id = c.case_id
    LEFT JOIN citations ct ON c.case_id = ct.case_id
    WHERE (p_judge_id IS NULL OR j.judge_id = p_judge_id)
    GROUP BY j.judge_id, j.judge_name
    ORDER BY total_cases DESC;
END//


-- get_case_detail: Full case information with all relationships
DROP PROCEDURE IF EXISTS get_case_detail//
CREATE PROCEDURE get_case_detail(IN p_case_id INT)
BEGIN
    SELECT
        c.case_id,
        c.case_number,
        c.case_title,
        co.court_name,
        c.judgment_date,
        c.case_type,
        c.case_category,
        c.verdict,
        c.summary,
        GROUP_CONCAT(DISTINCT j.judge_name SEPARATOR ', ') AS judges,
        GROUP_CONCAT(DISTINCT a.act_name SEPARATOR ', ') AS acts,
        GROUP_CONCAT(DISTINCT ct.citation_text SEPARATOR ', ') AS citations
    FROM cases c
    LEFT JOIN courts co ON c.court_id = co.court_id
    LEFT JOIN case_judges cj ON c.case_id = cj.case_id
    LEFT JOIN judges j ON cj.judge_id = j.judge_id
    LEFT JOIN case_acts ca ON c.case_id = ca.case_id
    LEFT JOIN acts a ON ca.act_id = a.act_id
    LEFT JOIN citations ct ON c.case_id = ct.case_id
    WHERE c.case_id = p_case_id
    GROUP BY c.case_id, c.case_number, c.case_title, co.court_name,
             c.judgment_date, c.case_type, c.case_category, c.verdict, c.summary;
END//


-- search_cases_fulltext: Full-text search across cases
DROP PROCEDURE IF EXISTS search_cases_fulltext//
CREATE PROCEDURE search_cases_fulltext(IN p_query VARCHAR(255), IN p_limit INT)
BEGIN
    SELECT
        c.case_id,
        c.case_title,
        c.case_number,
        c.case_type,
        c.verdict,
        c.judgment_date,
        MATCH(c.case_title) AGAINST(p_query IN NATURAL LANGUAGE MODE) AS relevance
    FROM cases c
    WHERE MATCH(c.case_title) AGAINST(p_query IN NATURAL LANGUAGE MODE)
       OR MATCH(c.summary) AGAINST(p_query IN NATURAL LANGUAGE MODE)
    ORDER BY relevance DESC
    LIMIT p_limit;
END//

DELIMITER ;
