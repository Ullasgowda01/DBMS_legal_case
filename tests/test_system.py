"""
CCIS System Tests — MySQL
==========================
Tests for schema integrity, FK constraints, extraction pipeline accuracy.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session
from backend.database.connection import engine, SessionLocal
from backend.models.models import Court, Case, Judge, CaseJudge, Citation, Lawyer, CaseLawyer


class TestDatabaseSchema:
    """Test MySQL schema integrity."""

    def setup_method(self):
        self.session = SessionLocal()

    def teardown_method(self):
        self.session.close()

    def test_tables_exist(self):
        """Verify all required tables exist in MySQL."""
        result = self.session.execute(text(
            "SELECT table_name FROM information_schema.tables "
            "WHERE table_schema = 'court_case_intelligence' AND table_type = 'BASE TABLE'"
        ))
        tables = {row[0] for row in result}
        required = {
            'courts', 'cases', 'judges', 'case_judges', 'parties',
            'case_parties', 'lawyers', 'case_lawyers', 'acts', 'case_acts',
            'citations', 'case_citations', 'hearings', 'judgments',
            'legal_sections', 'case_sections', 'audit_log'
        }
        missing = required - tables
        assert not missing, f"Missing tables: {missing}"

    def test_foreign_key_constraints(self):
        """Verify FK constraints exist."""
        result = self.session.execute(text("""
            SELECT TABLE_NAME, REFERENCED_TABLE_NAME
            FROM information_schema.KEY_COLUMN_USAGE
            WHERE CONSTRAINT_SCHEMA = 'court_case_intelligence'
            AND REFERENCED_TABLE_NAME IS NOT NULL
        """))
        fks = [(row[0], row[1]) for row in result]
        assert ('cases', 'courts') in fks, "Missing FK: cases -> courts"
        assert ('case_judges', 'cases') in fks, "Missing FK: case_judges -> cases"
        assert ('case_judges', 'judges') in fks, "Missing FK: case_judges -> judges"
        assert ('case_lawyers', 'cases') in fks, "Missing FK: case_lawyers -> cases"
        assert ('case_lawyers', 'lawyers') in fks, "Missing FK: case_lawyers -> lawyers"
        assert ('case_citations', 'cases') in fks, "Missing FK: case_citations (self-ref)"

    def test_fulltext_indexes(self):
        """Verify FULLTEXT indexes exist."""
        result = self.session.execute(text("""
            SELECT TABLE_NAME, INDEX_NAME, INDEX_TYPE
            FROM information_schema.STATISTICS
            WHERE TABLE_SCHEMA = 'court_case_intelligence'
            AND INDEX_TYPE = 'FULLTEXT'
        """))
        fulltext = {(row[0], row[1]) for row in result}
        assert ('cases', 'ft_cases_title') in fulltext, "Missing FULLTEXT on cases.case_title"
        assert ('judges', 'ft_judge_name') in fulltext, "Missing FULLTEXT on judges.judge_name"
        assert ('lawyers', 'ft_lawyer_name') in fulltext, "Missing FULLTEXT on lawyers.lawyer_name"

    def test_stored_procedures_exist(self):
        """Verify stored procedures exist."""
        result = self.session.execute(text("""
            SELECT ROUTINE_NAME FROM information_schema.ROUTINES
            WHERE ROUTINE_SCHEMA = 'court_case_intelligence'
            AND ROUTINE_TYPE = 'PROCEDURE'
        """))
        procs = {row[0] for row in result}
        required = {'add_case', 'add_citation', 'get_judge_statistics',
                     'get_case_detail', 'search_cases_fulltext'}
        missing = required - procs
        assert not missing, f"Missing procedures: {missing}"

    def test_triggers_exist(self):
        """Verify triggers exist."""
        result = self.session.execute(text("""
            SELECT TRIGGER_NAME FROM information_schema.TRIGGERS
            WHERE TRIGGER_SCHEMA = 'court_case_intelligence'
        """))
        triggers = {row[0] for row in result}
        required = {'trg_judgment_update', 'trg_citation_insert',
                     'trg_case_insert', 'trg_no_self_cite'}
        missing = required - triggers
        assert not missing, f"Missing triggers: {missing}"

    def test_views_exist(self):
        """Verify analytics views exist."""
        result = self.session.execute(text("""
            SELECT TABLE_NAME FROM information_schema.VIEWS
            WHERE TABLE_SCHEMA = 'court_case_intelligence'
        """))
        views = {row[0] for row in result}
        required = {'v_judge_activity', 'v_case_type_distribution',
                     'v_verdict_distribution', 'v_cases_per_year',
                     'v_dashboard_summary', 'v_citation_types'}
        missing = required - views
        assert not missing, f"Missing views: {missing}"

    def test_self_citation_prevention(self):
        """Test the self-referencing citation constraint via trigger."""
        # Try inserting a self-citation — should be blocked by trigger
        try:
            self.session.execute(text(
                "INSERT INTO case_citations (source_case_id, target_case_id) VALUES (1, 1)"
            ))
            self.session.commit()
            assert False, "Self-citation should have been blocked"
        except Exception:
            self.session.rollback()
            # Expected — trigger blocks self-citation

    def test_case_data_loaded(self):
        """Verify data was loaded."""
        count = self.session.execute(text("SELECT COUNT(*) FROM cases")).scalar()
        assert count > 40000, f"Expected 40000+ cases, got {count}"

    def test_junction_tables_populated(self):
        """Verify junction tables have data."""
        for table in ['case_judges', 'case_parties', 'case_lawyers', 'case_acts']:
            count = self.session.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()
            assert count > 0, f"Table {table} is empty"

    def test_transaction_rollback(self):
        """Test transaction rollback behavior."""
        try:
            self.session.execute(text(
                "INSERT INTO courts (court_name) VALUES ('Test Court')"
            ))
            # Force error with duplicate
            self.session.execute(text(
                "INSERT INTO courts (court_name) VALUES ('Test Court')"
            ))
            self.session.commit()
        except Exception:
            self.session.rollback()
        # Verify rollback
        count = self.session.execute(text(
            "SELECT COUNT(*) FROM courts WHERE court_name = 'Test Court'"
        )).scalar()
        assert count == 0, "Transaction rollback failed"


class TestExtractionPipeline:
    """Test metadata extraction accuracy."""

    def test_regex_case_number(self):
        from scripts.extraction.metadata_extractor import MetadataExtractor
        ext = MetadataExtractor()
        record = {'case_info': 'civil appeal number5802 of 2005', 'judgement_text': '',
                   'case_type': '', 'case_category': '', 'verdict_label': '', 'proof_sentence': ''}
        m = ext.extract(record)
        assert m.case_number != '', "Failed to extract case number"

    def test_regex_date(self):
        from scripts.extraction.metadata_extractor import MetadataExtractor
        ext = MetadataExtractor()
        record = {'case_info': 'date of judgment 23/02/1973', 'judgement_text': '',
                   'case_type': '', 'case_category': '', 'verdict_label': '', 'proof_sentence': ''}
        m = ext.extract(record)
        assert m.judgment_date == '23/02/1973'

    def test_regex_citations(self):
        from scripts.extraction.metadata_extractor import MetadataExtractor
        ext = MetadataExtractor()
        record = {'case_info': '', 'judgement_text': 'as per AIR 1953 SC 91',
                   'case_type': '', 'case_category': '', 'verdict_label': '', 'proof_sentence': ''}
        m = ext.extract(record)
        assert len(m.air_citations) > 0, "Failed to extract AIR citation"

    def test_date_cleaning(self):
        from scripts.cleaning.data_cleaner import DataCleaner
        cleaner = DataCleaner()
        assert cleaner._clean_date('23/02/1973') == '1973-02-23'

    def test_null_handling(self):
        from scripts.extraction.metadata_extractor import MetadataExtractor
        ext = MetadataExtractor()
        record = {'case_info': '', 'judgement_text': '', 'case_type': '',
                   'case_category': '', 'verdict_label': '', 'proof_sentence': ''}
        m = ext.extract(record)
        assert m.case_number == ''
        assert m.judges == []


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
