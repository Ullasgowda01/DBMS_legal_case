-- ============================================================
-- MySQL Triggers
-- ============================================================

DELIMITER //

-- 1. Audit trigger — track judgment updates
DROP TRIGGER IF EXISTS trg_judgment_update//
CREATE TRIGGER trg_judgment_update
    AFTER UPDATE ON judgments
    FOR EACH ROW
BEGIN
    IF OLD.final_decision != NEW.final_decision THEN
        INSERT INTO audit_log (table_name, record_id, action, old_value, new_value)
        VALUES ('judgments', OLD.judgment_id, 'UPDATE', OLD.final_decision, NEW.final_decision);
    END IF;
END//

-- 2. Audit trigger — track judgment deletes
DROP TRIGGER IF EXISTS trg_judgment_delete//
CREATE TRIGGER trg_judgment_delete
    AFTER DELETE ON judgments
    FOR EACH ROW
BEGIN
    INSERT INTO audit_log (table_name, record_id, action, old_value)
    VALUES ('judgments', OLD.judgment_id, 'DELETE', OLD.final_decision);
END//

-- 3. Citation insert trigger — log citation additions
DROP TRIGGER IF EXISTS trg_citation_insert//
CREATE TRIGGER trg_citation_insert
    AFTER INSERT ON case_citations
    FOR EACH ROW
BEGIN
    UPDATE cases SET updated_at = CURRENT_TIMESTAMP
    WHERE case_id = NEW.source_case_id;
END//

-- 4. Case insert audit trigger
DROP TRIGGER IF EXISTS trg_case_insert//
CREATE TRIGGER trg_case_insert
    AFTER INSERT ON cases
    FOR EACH ROW
BEGIN
    INSERT INTO audit_log (table_name, record_id, action, new_value)
    VALUES ('cases', NEW.case_id, 'INSERT', NEW.case_title);
END//
-- 5. Self-citation prevention trigger
DROP TRIGGER IF EXISTS trg_no_self_cite//
CREATE TRIGGER trg_no_self_cite
    BEFORE INSERT ON case_citations
    FOR EACH ROW
BEGIN
    IF NEW.source_case_id = NEW.target_case_id THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Self-citation is not allowed';
    END IF;
END//

DELIMITER ;
