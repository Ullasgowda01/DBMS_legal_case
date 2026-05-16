# Court Case Intelligence System (CCIS)

A production-grade legal intelligence platform built on **MySQL 8.0**, **Python/FastAPI**, and **React**.

Processes 50,000 Indian Supreme Court judgments through a full ETL pipeline — extracting structured metadata from raw legal text, normalizing into a relational schema, and serving analytics through a REST API.

---

## Architecture

```
Raw Legal Data (CSV, 5.3M rows)
       ↓
Extraction Engine (regex + NLP parsing)
       ↓
Cleaning Pipeline (normalization, dedup)
       ↓
Structured CSV Layer (9 output files)
       ↓
MySQL 8.0 Database (17 tables, 3NF normalized)
       ↓
Analytics SQL Layer (views, procedures, triggers)
       ↓
FastAPI Backend (5 route modules, REST API)
       ↓
React Dashboard (analytics visualization)
```

---

## Database Design

### Schema — 3NF Normalized

**Core Tables:**
| Table | Description | Rows |
|-------|-------------|------|
| `courts` | Court entities | 1 |
| `cases` | Case records with metadata | 44,843 |
| `judges` | Judge profiles | 5,362 |
| `parties` | Legal parties | 36,546 |
| `lawyers` | Legal counsel | 2,577 |
| `acts` | Laws and statutes | 326,123 |
| `hearings` | Hearing records | — |
| `judgments` | Full judgment text | — |
| `citations` | AIR/SCC/SCR references | 28,111 |
| `legal_sections` | Section references | 14,950 |
| `audit_log` | Change tracking | — |

**Junction Tables (Many-to-Many):**
| Table | Relationship | Rows |
|-------|-------------|------|
| `case_judges` | Cases ↔ Judges | 57,790 |
| `case_parties` | Cases ↔ Parties | 55,801 |
| `case_lawyers` | Cases ↔ Lawyers | 6,747 |
| `case_acts` | Cases ↔ Acts | 554,779 |
| `case_citations` | Cases ↔ Cases (self-ref) | — |
| `case_sections` | Cases ↔ Sections | 419,951 |

### ER Diagram

```
courts ──1:N── cases ──M:N── judges       (via case_judges)
                  │
                  ├──M:N── parties        (via case_parties)
                  ├──M:N── lawyers        (via case_lawyers)
                  ├──M:N── acts           (via case_acts)
                  ├──M:N── legal_sections (via case_sections)
                  ├──1:N── citations
                  ├──1:1── judgments
                  ├──1:N── hearings
                  └──M:N── cases          (via case_citations — SELF-REFERENCING)
```

### Database Features

| Feature | Implementation |
|---------|---------------|
| **Primary Keys** | AUTO_INCREMENT on all entities |
| **Foreign Keys** | ON DELETE CASCADE/SET NULL with proper referential actions |
| **Indexes** | B-Tree on dates, types, IDs |
| **FULLTEXT Indexes** | On case_title, summary, judge_name, lawyer_name, act_name, citation_text, judgment_text |
| **Views** | 10 analytics views (v_judge_activity, v_cases_per_year, etc.) |
| **Stored Procedures** | add_case, add_citation, get_judge_statistics, get_case_detail, search_cases_fulltext |
| **Triggers** | Audit logging, citation tracking, self-citation prevention, case insert audit |
| **Transactions** | Full ACID via InnoDB |
| **Constraints** | UNIQUE, NOT NULL, CHECK (via trigger) |

---

## Project Structure

```
legal-case-intelligence/
├── backend/
│   ├── app/main.py              # FastAPI application
│   ├── database/connection.py   # MySQL connection (SQLAlchemy)
│   ├── models/models.py         # ORM models (17 tables)
│   ├── routes/
│   │   ├── cases.py             # Case CRUD + detail API
│   │   ├── judges.py            # Judge API
│   │   ├── citations.py         # Citation API
│   │   ├── analytics.py         # Dashboard + analytics API
│   │   └── search.py            # Full-text + advanced search
│   ├── services/                # Business logic layer
│   └── analytics/               # Analytics modules
├── scripts/
│   ├── extraction/
│   │   ├── csv_loader.py        # Memory-efficient CSV loader
│   │   └── metadata_extractor.py # Regex-based metadata extraction
│   ├── cleaning/
│   │   └── data_cleaner.py      # Date normalization, dedup
│   ├── transformation/
│   │   └── run_pipeline.py      # ETL orchestrator
│   └── loaders/
│       └── mysql_loader.py      # MySQL bulk data loader
├── sql/
│   ├── schema/001_create_tables.sql    # 17-table DDL
│   ├── schema/002_create_indexes.sql   # B-Tree + FULLTEXT indexes
│   ├── procedures/001_stored_procedures.sql
│   ├── triggers/001_triggers.sql
│   └── analytics/001_analytics_views.sql
├── frontend/
│   └── src/pages/               # Dashboard, CaseExplorer, etc.
├── extracted/                   # Pipeline output CSVs
├── tests/test_system.py         # 15 automated tests
├── requirements.txt
└── .env
```

---

## API Endpoints

### Cases
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/cases` | List cases (filter, sort, paginate) |
| GET | `/api/cases/{id}` | Case detail with judges, parties, lawyers, citations |
| POST | `/api/cases` | Create new case |

### Analytics
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/analytics/dashboard` | Summary statistics |
| GET | `/api/analytics/judges` | Top judges by case count |
| GET | `/api/analytics/acts` | Most referenced acts |
| GET | `/api/analytics/citations` | Citation type distribution |
| GET | `/api/analytics/verdicts` | Verdict distribution |
| GET | `/api/analytics/timeline` | Cases per year |
| GET | `/api/analytics/case-types` | Case type breakdown |
| GET | `/api/analytics/lawyers` | Top lawyers |

### Search
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/search?q=...` | Unified search (cases, judges, citations, acts) |
| GET | `/api/search/cases/advanced` | Multi-filter advanced search |

### Other
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/judges` | Judge listing |
| GET | `/api/judges/{id}` | Judge detail + analytics |
| GET | `/api/citations` | Citation listing |
| GET | `/api/citations/graph` | Citation graph data |

---

## Quick Start

### Prerequisites
- Python 3.10+
- MySQL 8.0+
- Node.js 18+

### Setup

```bash
# 1. Create virtual environment
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# 2. Start MySQL and create database
mysql -u root -e "CREATE DATABASE court_case_intelligence CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"

# 3. Apply schema
mysql -u root court_case_intelligence < sql/schema/001_create_tables.sql
mysql -u root court_case_intelligence < sql/procedures/001_stored_procedures.sql
mysql -u root court_case_intelligence < sql/triggers/001_triggers.sql
mysql -u root court_case_intelligence < sql/analytics/001_analytics_views.sql

# 4. Run extraction pipeline (requires dataset CSV)
PYTHONPATH=. python3 scripts/transformation/run_pipeline.py

# 5. Load data into MySQL
PYTHONPATH=. python3 scripts/loaders/mysql_loader.py

# 6. Start backend
PYTHONPATH=. uvicorn backend.app.main:app --reload --port 8000

# 7. Start frontend
cd frontend && npm install && npm run dev
```

### Run Tests
```bash
PYTHONPATH=. python3 -m pytest tests/test_system.py -v
```

---

## Technology Stack

| Component | Technology |
|-----------|-----------|
| Database | MySQL 8.0 (InnoDB) |
| Backend | Python 3.12, FastAPI, SQLAlchemy 2.0 |
| ORM Driver | PyMySQL |
| Frontend | React 19, Recharts, React Router |
| Build Tool | Vite |
| Testing | pytest |

---

## Test Results

```
tests/test_system.py::TestDatabaseSchema::test_tables_exist           PASSED
tests/test_system.py::TestDatabaseSchema::test_foreign_key_constraints PASSED
tests/test_system.py::TestDatabaseSchema::test_fulltext_indexes       PASSED
tests/test_system.py::TestDatabaseSchema::test_stored_procedures_exist PASSED
tests/test_system.py::TestDatabaseSchema::test_triggers_exist          PASSED
tests/test_system.py::TestDatabaseSchema::test_views_exist             PASSED
tests/test_system.py::TestDatabaseSchema::test_self_citation_prevention PASSED
tests/test_system.py::TestDatabaseSchema::test_case_data_loaded        PASSED
tests/test_system.py::TestDatabaseSchema::test_junction_tables_populated PASSED
tests/test_system.py::TestDatabaseSchema::test_transaction_rollback    PASSED
tests/test_system.py::TestExtractionPipeline::test_regex_case_number   PASSED
tests/test_system.py::TestExtractionPipeline::test_regex_date          PASSED
tests/test_system.py::TestExtractionPipeline::test_regex_citations     PASSED
tests/test_system.py::TestExtractionPipeline::test_date_cleaning       PASSED
tests/test_system.py::TestExtractionPipeline::test_null_handling       PASSED

15 passed in 0.57s
```
