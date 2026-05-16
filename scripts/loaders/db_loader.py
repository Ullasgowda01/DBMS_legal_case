"""
Database Loader
================
Loads extracted CSV data into PostgreSQL database.
Uses SQLAlchemy for type-safe insertions with relationship management.
"""

import csv
import os
import sys
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from backend.database.connection import engine, SessionLocal, Base
from backend.models.models import (
    Court, Case, Judge, CaseJudge, Party, CaseParty,
    Act, LegalSection, CaseSection, Citation, Judgment
)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

DATA_DIR = PROJECT_ROOT / 'extracted' / 'clean_csv'


def create_tables():
    """Create all database tables."""
    Base.metadata.create_all(bind=engine)
    logger.info("All tables created successfully.")


def load_courts(session: Session):
    """Load courts (default: Supreme Court of India)."""
    court = session.query(Court).filter(Court.court_name == 'Supreme Court of India').first()
    if not court:
        court = Court(
            court_name='Supreme Court of India',
            court_level='supreme',
            state=None,
            country='India'
        )
        session.add(court)
        session.commit()
        logger.info(f"Created court: {court.court_name} (ID: {court.court_id})")
    return court.court_id


def load_cases(session: Session, court_id: int) -> dict:
    """Load cases from CSV and return ID mapping."""
    csv_path = DATA_DIR / 'cases.csv'
    if not csv_path.exists():
        logger.error(f"File not found: {csv_path}")
        return {}

    id_map = {}  # csv_case_id -> db_case_id
    count = 0

    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        batch = []
        for row in reader:
            jdate = None
            if row.get('judgment_date'):
                try:
                    jdate = datetime.strptime(row['judgment_date'], '%Y-%m-%d').date()
                except ValueError:
                    pass

            case = Case(
                case_number=row.get('case_number', '')[:100],
                case_title=row.get('case_title', '')[:500],
                court_id=court_id,
                judgment_date=jdate,
                case_type=row.get('case_type', ''),
                case_category=row.get('case_category', ''),
                verdict=row.get('verdict', ''),
                bench_strength=int(row.get('bench_strength', 0) or 0),
                bench_type=row.get('bench_type', ''),
                word_count=int(row.get('word_count', 0) or 0),
                summary=row.get('judgment_summary', '')[:2000] if row.get('judgment_summary') else None,
                file_name=row.get('file_name', ''),
            )
            batch.append(case)
            csv_id = int(row.get('case_id', 0))

            if len(batch) >= 1000:
                session.add_all(batch)
                session.flush()
                for c in batch:
                    old_id = csv_id - len(batch) + batch.index(c) + 1
                    id_map[old_id] = c.case_id
                count += len(batch)
                batch = []
                logger.info(f"  Loaded {count} cases...")

        if batch:
            session.add_all(batch)
            session.flush()
            for c in batch:
                old_id = csv_id - len(batch) + batch.index(c) + 1
                id_map[old_id] = c.case_id
            count += len(batch)

    session.commit()
    logger.info(f"Loaded {count} cases total.")
    return id_map


def load_judges(session: Session) -> dict:
    """Load judges and return ID mapping."""
    csv_path = DATA_DIR / 'judges.csv'
    if not csv_path.exists():
        return {}

    id_map = {}
    skipped = 0
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = row['judge_name'][:250].strip()
            # Skip invalid judge names (too long, contain garbage)
            if not name or len(name) > 200 or len(name.split()) > 8:
                skipped += 1
                continue
            existing = session.query(Judge).filter(Judge.judge_name == name).first()
            if existing:
                id_map[int(row['judge_id'])] = existing.judge_id
            else:
                judge = Judge(judge_name=name)
                session.add(judge)
                session.flush()
                id_map[int(row['judge_id'])] = judge.judge_id

    session.commit()
    logger.info(f"Loaded {len(id_map)} judges (skipped {skipped} invalid).")
    return id_map


def load_case_judges(session: Session, case_map: dict, judge_map: dict):
    """Load case-judge relationships."""
    csv_path = DATA_DIR / 'case_judges.csv'
    if not csv_path.exists():
        return

    count = 0
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            csv_case_id = int(row['case_id'])
            csv_judge_id = int(row['judge_id'])

            db_case_id = case_map.get(csv_case_id)
            db_judge_id = judge_map.get(csv_judge_id)

            if db_case_id and db_judge_id:
                exists = session.query(CaseJudge).filter(
                    CaseJudge.case_id == db_case_id,
                    CaseJudge.judge_id == db_judge_id
                ).first()
                if not exists:
                    cj = CaseJudge(case_id=db_case_id, judge_id=db_judge_id, role='bench')
                    session.add(cj)
                    count += 1

            if count % 5000 == 0 and count > 0:
                session.flush()
                logger.info(f"  Loaded {count} case-judge links...")

    session.commit()
    logger.info(f"Loaded {count} case-judge links.")


def load_parties(session: Session) -> dict:
    """Load parties."""
    csv_path = DATA_DIR / 'parties.csv'
    if not csv_path.exists():
        return {}

    id_map = {}
    count = 0
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        batch = []
        for row in reader:
            party = Party(party_name=row['party_name'][:500])
            batch.append((int(row['party_id']), party))
            if len(batch) >= 1000:
                for _, p in batch:
                    session.add(p)
                session.flush()
                for old_id, p in batch:
                    id_map[old_id] = p.party_id
                count += len(batch)
                batch = []

        if batch:
            for _, p in batch:
                session.add(p)
            session.flush()
            for old_id, p in batch:
                id_map[old_id] = p.party_id
            count += len(batch)

    session.commit()
    logger.info(f"Loaded {count} parties.")
    return id_map


def load_case_parties(session: Session, case_map: dict, party_map: dict):
    """Load case-party relationships."""
    csv_path = DATA_DIR / 'case_parties.csv'
    if not csv_path.exists():
        return

    count = 0
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            db_case_id = case_map.get(int(row['case_id']))
            db_party_id = party_map.get(int(row['party_id']))
            role = row.get('role', 'unknown')

            if db_case_id and db_party_id:
                exists = session.query(CaseParty).filter(
                    CaseParty.case_id == db_case_id,
                    CaseParty.party_id == db_party_id,
                    CaseParty.role == role
                ).first()
                if not exists:
                    cp = CaseParty(case_id=db_case_id, party_id=db_party_id, role=role)
                    session.add(cp)
                    count += 1

            if count % 5000 == 0 and count > 0:
                session.flush()

    session.commit()
    logger.info(f"Loaded {count} case-party links.")


def load_citations(session: Session, case_map: dict):
    """Load citations."""
    csv_path = DATA_DIR / 'citations.csv'
    if not csv_path.exists():
        return

    count = 0
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        batch = []
        for row in reader:
            db_case_id = case_map.get(int(row['case_id']))
            if db_case_id:
                cit = Citation(
                    citation_text=row['citation_text'][:255],
                    citation_type=row.get('citation_type', ''),
                    case_id=db_case_id,
                )
                batch.append(cit)

            if len(batch) >= 1000:
                session.add_all(batch)
                session.flush()
                count += len(batch)
                batch = []
                logger.info(f"  Loaded {count} citations...")

        if batch:
            session.add_all(batch)
            session.flush()
            count += len(batch)

    session.commit()
    logger.info(f"Loaded {count} citations.")


def load_acts_and_sections(session: Session, case_map: dict):
    """Load acts, sections, and case-section links."""
    acts_path = DATA_DIR / 'acts.csv'
    sections_path = DATA_DIR / 'case_sections.csv'

    act_map = {}
    if acts_path.exists():
        with open(acts_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                act_name = row['act_name'][:490].strip()
                if not act_name or len(act_name) < 3:
                    continue
                existing = session.query(Act).filter(Act.act_name == act_name).first()
                if existing:
                    act_map[act_name] = existing.act_id
                else:
                    act = Act(act_name=act_name)
                    session.add(act)
                    session.flush()
                    act_map[act_name] = act.act_id
        session.commit()
        logger.info(f"Loaded {len(act_map)} acts.")

    # Load sections from case_sections
    if sections_path.exists():
        section_map = {}
        count = 0
        with open(sections_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                sec_name = row.get('section_name', '')
                db_case_id = case_map.get(int(row['case_id']))

                if sec_name and db_case_id:
                    if sec_name not in section_map:
                        existing = session.query(LegalSection).filter(
                            LegalSection.section_name == sec_name,
                            LegalSection.act_id.is_(None)
                        ).first()
                        if existing:
                            section_map[sec_name] = existing.section_id
                        else:
                            ls = LegalSection(section_name=sec_name[:250])
                            session.add(ls)
                            session.flush()
                            section_map[sec_name] = ls.section_id

                    sec_id = section_map[sec_name]
                    exists = session.query(CaseSection).filter(
                        CaseSection.case_id == db_case_id,
                        CaseSection.section_id == sec_id
                    ).first()
                    if not exists:
                        cs = CaseSection(case_id=db_case_id, section_id=sec_id)
                        session.add(cs)
                        count += 1

                if count % 5000 == 0 and count > 0:
                    session.flush()

        session.commit()
        logger.info(f"Loaded {len(section_map)} sections and {count} case-section links.")


def run_loader():
    """Run the full data loading pipeline."""
    logger.info("=== Database Loader Starting ===")

    # Create tables
    create_tables()

    session = SessionLocal()
    try:
        # Load in order
        court_id = load_courts(session)
        case_map = load_cases(session, court_id)
        judge_map = load_judges(session)
        load_case_judges(session, case_map, judge_map)
        party_map = load_parties(session)
        load_case_parties(session, case_map, party_map)
        load_citations(session, case_map)
        load_acts_and_sections(session, case_map)

        logger.info("=== Database Loading Complete ===")
    except Exception as e:
        session.rollback()
        logger.error(f"Loading failed: {e}")
        raise
    finally:
        session.close()


if __name__ == '__main__':
    run_loader()
