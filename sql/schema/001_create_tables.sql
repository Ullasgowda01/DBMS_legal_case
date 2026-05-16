-- ============================================================
-- Court Case Intelligence System (CCIS) — MySQL 8.0 Schema
-- Normalized to 3NF with proper FK, indexes, constraints
-- ============================================================

SET FOREIGN_KEY_CHECKS = 0;

-- ============================================================
-- TABLE: courts
-- ============================================================
DROP TABLE IF EXISTS courts;
CREATE TABLE courts (
    court_id    INT AUTO_INCREMENT PRIMARY KEY,
    court_name  VARCHAR(255) NOT NULL,
    court_level VARCHAR(50)  COMMENT 'supreme, high, district, tribunal',
    state       VARCHAR(100),
    country     VARCHAR(100) DEFAULT 'India',
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uq_court_name (court_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- TABLE: cases
-- ============================================================
DROP TABLE IF EXISTS cases;
CREATE TABLE cases (
    case_id         INT AUTO_INCREMENT PRIMARY KEY,
    case_number     VARCHAR(100),
    case_title      VARCHAR(500),
    court_id        INT,
    judgment_date   DATE,
    case_type       VARCHAR(100),
    case_category   VARCHAR(50),
    verdict         VARCHAR(50),
    bench_strength  INT,
    bench_type      VARCHAR(50),
    word_count      INT,
    summary         TEXT,
    raw_text        LONGTEXT,
    file_name       VARCHAR(255),
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_cases_court FOREIGN KEY (court_id) REFERENCES courts(court_id)
        ON DELETE SET NULL ON UPDATE CASCADE,
    INDEX idx_cases_date (judgment_date),
    INDEX idx_cases_type (case_type),
    INDEX idx_cases_category (case_category),
    INDEX idx_cases_verdict (verdict),
    INDEX idx_cases_court (court_id),
    INDEX idx_cases_number (case_number),
    FULLTEXT INDEX ft_cases_title (case_title),
    FULLTEXT INDEX ft_cases_summary (summary)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- TABLE: judges
-- ============================================================
DROP TABLE IF EXISTS judges;
CREATE TABLE judges (
    judge_id    INT AUTO_INCREMENT PRIMARY KEY,
    judge_name  VARCHAR(255) NOT NULL,
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uq_judge_name (judge_name),
    FULLTEXT INDEX ft_judge_name (judge_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- TABLE: case_judges (many-to-many junction)
-- ============================================================
DROP TABLE IF EXISTS case_judges;
CREATE TABLE case_judges (
    case_id     INT NOT NULL,
    judge_id    INT NOT NULL,
    role        VARCHAR(50) DEFAULT 'bench',
    PRIMARY KEY (case_id, judge_id),
    CONSTRAINT fk_cj_case FOREIGN KEY (case_id) REFERENCES cases(case_id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_cj_judge FOREIGN KEY (judge_id) REFERENCES judges(judge_id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    INDEX idx_cj_judge (judge_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- TABLE: parties
-- ============================================================
DROP TABLE IF EXISTS parties;
CREATE TABLE parties (
    party_id    INT AUTO_INCREMENT PRIMARY KEY,
    party_name  VARCHAR(500) NOT NULL,
    party_type  VARCHAR(50) COMMENT 'individual, organization, government',
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FULLTEXT INDEX ft_party_name (party_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- TABLE: case_parties (many-to-many junction)
-- ============================================================
DROP TABLE IF EXISTS case_parties;
CREATE TABLE case_parties (
    case_id     INT NOT NULL,
    party_id    INT NOT NULL,
    role        VARCHAR(50) NOT NULL COMMENT 'petitioner, respondent, appellant, defendant',
    PRIMARY KEY (case_id, party_id, role),
    CONSTRAINT fk_cp_case FOREIGN KEY (case_id) REFERENCES cases(case_id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_cp_party FOREIGN KEY (party_id) REFERENCES parties(party_id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    INDEX idx_cp_party (party_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- TABLE: lawyers
-- ============================================================
DROP TABLE IF EXISTS lawyers;
CREATE TABLE lawyers (
    lawyer_id   INT AUTO_INCREMENT PRIMARY KEY,
    lawyer_name VARCHAR(255) NOT NULL,
    designation VARCHAR(100) COMMENT 'Senior Advocate, Advocate, AG, SG',
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uq_lawyer_name (lawyer_name),
    FULLTEXT INDEX ft_lawyer_name (lawyer_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- TABLE: case_lawyers (many-to-many junction)
-- ============================================================
DROP TABLE IF EXISTS case_lawyers;
CREATE TABLE case_lawyers (
    case_id     INT NOT NULL,
    lawyer_id   INT NOT NULL,
    role        VARCHAR(50) DEFAULT 'counsel' COMMENT 'counsel, senior_counsel, amicus_curiae',
    side        VARCHAR(50) COMMENT 'petitioner, respondent',
    PRIMARY KEY (case_id, lawyer_id),
    CONSTRAINT fk_cl_case FOREIGN KEY (case_id) REFERENCES cases(case_id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_cl_lawyer FOREIGN KEY (lawyer_id) REFERENCES lawyers(lawyer_id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    INDEX idx_cl_lawyer (lawyer_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- TABLE: acts
-- ============================================================
DROP TABLE IF EXISTS acts;
CREATE TABLE acts (
    act_id      INT AUTO_INCREMENT PRIMARY KEY,
    act_name    VARCHAR(500) NOT NULL,
    act_year    INT,
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uq_act_name (act_name),
    FULLTEXT INDEX ft_act_name (act_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- TABLE: case_acts (many-to-many junction)
-- ============================================================
DROP TABLE IF EXISTS case_acts;
CREATE TABLE case_acts (
    case_id     INT NOT NULL,
    act_id      INT NOT NULL,
    section_ref VARCHAR(255) COMMENT 'Section/Article reference',
    PRIMARY KEY (case_id, act_id),
    CONSTRAINT fk_ca_case FOREIGN KEY (case_id) REFERENCES cases(case_id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_ca_act FOREIGN KEY (act_id) REFERENCES acts(act_id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    INDEX idx_ca_act (act_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- TABLE: citations (direct citation references)
-- ============================================================
DROP TABLE IF EXISTS citations;
CREATE TABLE citations (
    citation_id     INT AUTO_INCREMENT PRIMARY KEY,
    citation_text   VARCHAR(255) NOT NULL,
    citation_type   VARCHAR(20) COMMENT 'AIR, SCC, SCR, ILR',
    case_id         INT,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_cit_case FOREIGN KEY (case_id) REFERENCES cases(case_id)
        ON DELETE SET NULL ON UPDATE CASCADE,
    INDEX idx_cit_case (case_id),
    INDEX idx_cit_type (citation_type),
    FULLTEXT INDEX ft_citation_text (citation_text)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- TABLE: case_citations (SELF-REFERENCING many-to-many)
-- This is the citation graph — one of the most important features
-- ============================================================
DROP TABLE IF EXISTS case_citations;
CREATE TABLE case_citations (
    id                  INT AUTO_INCREMENT PRIMARY KEY,
    source_case_id      INT NOT NULL COMMENT 'The case that cites',
    target_case_id      INT NOT NULL COMMENT 'The case being cited',
    citation_strength   INT DEFAULT 1,
    CONSTRAINT fk_cc_source FOREIGN KEY (source_case_id) REFERENCES cases(case_id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_cc_target FOREIGN KEY (target_case_id) REFERENCES cases(case_id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    UNIQUE KEY uq_case_citation (source_case_id, target_case_id),
    INDEX idx_cc_source (source_case_id),
    INDEX idx_cc_target (target_case_id)
    -- Note: self-citation prevention enforced via BEFORE INSERT trigger
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- TABLE: hearings
-- ============================================================
DROP TABLE IF EXISTS hearings;
CREATE TABLE hearings (
    hearing_id      INT AUTO_INCREMENT PRIMARY KEY,
    case_id         INT NOT NULL,
    hearing_date    DATE,
    hearing_type    VARCHAR(100),
    notes           TEXT,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_h_case FOREIGN KEY (case_id) REFERENCES cases(case_id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    INDEX idx_h_case (case_id),
    INDEX idx_h_date (hearing_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- TABLE: judgments (detailed judgment text)
-- ============================================================
DROP TABLE IF EXISTS judgments;
CREATE TABLE judgments (
    judgment_id     INT AUTO_INCREMENT PRIMARY KEY,
    case_id         INT NOT NULL,
    judgment_text   LONGTEXT,
    final_decision  VARCHAR(100),
    word_count      INT,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_jm_case FOREIGN KEY (case_id) REFERENCES cases(case_id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    INDEX idx_jm_case (case_id),
    FULLTEXT INDEX ft_judgment_text (judgment_text)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- TABLE: legal_sections (normalized section references)
-- ============================================================
DROP TABLE IF EXISTS legal_sections;
CREATE TABLE legal_sections (
    section_id      INT AUTO_INCREMENT PRIMARY KEY,
    act_id          INT,
    section_name    VARCHAR(255) NOT NULL,
    description     TEXT,
    CONSTRAINT fk_ls_act FOREIGN KEY (act_id) REFERENCES acts(act_id)
        ON DELETE SET NULL ON UPDATE CASCADE,
    UNIQUE KEY uq_section (act_id, section_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- TABLE: case_sections (many-to-many junction)
-- ============================================================
DROP TABLE IF EXISTS case_sections;
CREATE TABLE case_sections (
    case_id     INT NOT NULL,
    section_id  INT NOT NULL,
    PRIMARY KEY (case_id, section_id),
    CONSTRAINT fk_csec_case FOREIGN KEY (case_id) REFERENCES cases(case_id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_csec_section FOREIGN KEY (section_id) REFERENCES legal_sections(section_id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    INDEX idx_csec_section (section_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- TABLE: audit_log (for triggers)
-- ============================================================
DROP TABLE IF EXISTS audit_log;
CREATE TABLE audit_log (
    audit_id        INT AUTO_INCREMENT PRIMARY KEY,
    table_name      VARCHAR(100),
    record_id       INT,
    action          VARCHAR(20),
    old_value       TEXT,
    new_value       TEXT,
    changed_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    changed_by      VARCHAR(100) DEFAULT (CURRENT_USER())
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

SET FOREIGN_KEY_CHECKS = 1;
