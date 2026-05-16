"""
MySQL Database Loader
======================
Loads extracted CSV data into MySQL database.
Uses SQLAlchemy bulk operations for performance.
"""

import csv
import os
import sys
import logging
import re
from pathlib import Path
from datetime import datetime
from typing import Optional

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from sqlalchemy import text
from backend.database.connection import engine, SessionLocal, Base
from backend.models.models import (
    Court, Case, Judge, CaseJudge, Party, CaseParty,
    Lawyer, CaseLawyer, Act, CaseAct, LegalSection,
    CaseSection, Citation, Judgment
)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

DATA_DIR = PROJECT_ROOT / 'extracted' / 'clean_csv'


def load_courts(session):
    """Insert default court."""
    court = session.query(Court).filter(Court.court_name == 'Supreme Court of India').first()
    if not court:
        court = Court(court_name='Supreme Court of India', court_level='supreme', country='India')
        session.add(court)
        session.commit()
        logger.info(f"Created court: {court.court_name} (ID: {court.court_id})")
    return court.court_id


def load_cases(session, court_id):
    """Load cases into MySQL. Returns csv_id -> db_id map."""
    csv_path = DATA_DIR / 'cases.csv'
    if not csv_path.exists():
        logger.error(f"File not found: {csv_path}")
        return {}

    # Disable FK checks and triggers for bulk load
    session.execute(text("SET FOREIGN_KEY_CHECKS = 0"))
    session.execute(text("SET @DISABLE_TRIGGERS = 1"))

    id_map = {}
    count = 0
    batch = []

    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
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
                case_type=row.get('case_type', '')[:100],
                case_category=row.get('case_category', '')[:50],
                verdict=row.get('verdict', '')[:50],
                bench_strength=int(row.get('bench_strength', 0) or 0),
                bench_type=row.get('bench_type', '')[:50],
                word_count=int(row.get('word_count', 0) or 0),
                summary=(row.get('judgment_summary', '') or '')[:60000],
                file_name=row.get('file_name', '')[:255],
            )
            batch.append((int(row.get('case_id', 0)), case))

            if len(batch) >= 2000:
                for _, c in batch:
                    session.add(c)
                session.flush()
                for csv_id, c in batch:
                    id_map[csv_id] = c.case_id
                count += len(batch)
                batch = []
                if count % 10000 == 0:
                    logger.info(f"  Cases: {count}")

        if batch:
            for _, c in batch:
                session.add(c)
            session.flush()
            for csv_id, c in batch:
                id_map[csv_id] = c.case_id
            count += len(batch)

    session.commit()
    session.execute(text("SET FOREIGN_KEY_CHECKS = 1"))
    logger.info(f"✓ Loaded {count} cases")
    return id_map


def load_judges(session):
    """Load judges. Returns csv_id -> db_id map."""
    csv_path = DATA_DIR / 'judges.csv'
    if not csv_path.exists():
        return {}

    id_map = {}
    skipped = 0
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = row['judge_name'][:250].strip()
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
    logger.info(f"✓ Loaded {len(id_map)} judges (skipped {skipped} invalid)")
    return id_map


def load_case_judges(session, case_map, judge_map):
    """Load case-judge junction table."""
    csv_path = DATA_DIR / 'case_judges.csv'
    if not csv_path.exists():
        return

    count = 0
    seen = set()
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            db_case = case_map.get(int(row['case_id']))
            db_judge = judge_map.get(int(row['judge_id']))
            if db_case and db_judge:
                key = (db_case, db_judge)
                if key not in seen:
                    seen.add(key)
                    session.add(CaseJudge(case_id=db_case, judge_id=db_judge, role='bench'))
                    count += 1
            if count % 5000 == 0 and count > 0:
                session.flush()

    session.commit()
    logger.info(f"✓ Loaded {count} case-judge links")


def load_parties(session):
    """Load parties. Returns csv_id -> db_id map."""
    csv_path = DATA_DIR / 'parties.csv'
    if not csv_path.exists():
        return {}

    id_map = {}
    count = 0
    batch = []
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            party = Party(party_name=row['party_name'][:500])
            batch.append((int(row['party_id']), party))
            if len(batch) >= 2000:
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
    logger.info(f"✓ Loaded {count} parties")
    return id_map


def load_case_parties(session, case_map, party_map):
    """Load case-party junction table with dedup."""
    csv_path = DATA_DIR / 'case_parties.csv'
    if not csv_path.exists():
        return

    count = 0
    seen = set()
    batch = []
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            db_case = case_map.get(int(row['case_id']))
            db_party = party_map.get(int(row['party_id']))
            role = row.get('role', 'unknown')[:50]
            if db_case and db_party:
                key = (db_case, db_party, role)
                if key not in seen:
                    seen.add(key)
                    batch.append(CaseParty(case_id=db_case, party_id=db_party, role=role))
                    count += 1
            if len(batch) >= 2000:
                session.add_all(batch)
                session.flush()
                batch = []

        if batch:
            session.add_all(batch)
            session.flush()

    session.commit()
    logger.info(f"✓ Loaded {count} case-party links")


def load_lawyers_from_text(session, case_map):
    """Extract lawyers from case_info text and load them."""
    cases_path = DATA_DIR / 'cases.csv'
    if not cases_path.exists():
        return

    lawyer_re = re.compile(
        r'(?:(?:sr\.\s*)?adv(?:ocate)?\.?|counsel)\s*[:\-]?\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,3})',
        re.IGNORECASE
    )

    lawyer_map = {}
    link_count = 0
    seen_links = set()

    # Read raw case_info from the original data to find lawyer names
    raw_csv = PROJECT_ROOT / 'raw_data' / 'csv' / 'case_files_total.csv'
    if not raw_csv.exists():
        raw_csv = Path('/Users/ullasgowda/Desktop/DBMS_project_claude/case_files_total.csv')

    if raw_csv.exists():
        with open(raw_csv, 'r', encoding='ascii', errors='replace') as f:
            reader = csv.DictReader(f)
            case_idx = 0
            for i, row in enumerate(reader):
                if i >= 50000:
                    break
                case_info = row.get('case_info', '')
                if not case_info:
                    continue

                case_idx += 1
                db_case_id = case_map.get(case_idx)
                if not db_case_id:
                    continue

                matches = lawyer_re.findall(case_info[:2000])
                for name in matches[:5]:
                    name = name.strip()[:250]
                    if len(name) < 3 or len(name) > 200:
                        continue

                    if name not in lawyer_map:
                        existing = session.query(Lawyer).filter(Lawyer.lawyer_name == name).first()
                        if existing:
                            lawyer_map[name] = existing.lawyer_id
                        else:
                            lawyer = Lawyer(lawyer_name=name, designation='Advocate')
                            session.add(lawyer)
                            session.flush()
                            lawyer_map[name] = lawyer.lawyer_id

                    key = (db_case_id, lawyer_map[name])
                    if key not in seen_links:
                        seen_links.add(key)
                        session.add(CaseLawyer(
                            case_id=db_case_id,
                            lawyer_id=lawyer_map[name],
                            role='counsel'
                        ))
                        link_count += 1

                if link_count % 5000 == 0 and link_count > 0:
                    session.flush()

    session.commit()
    logger.info(f"✓ Loaded {len(lawyer_map)} lawyers and {link_count} case-lawyer links")


def load_citations(session, case_map):
    """Load citations."""
    csv_path = DATA_DIR / 'citations.csv'
    if not csv_path.exists():
        return

    count = 0
    batch = []
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            db_case = case_map.get(int(row['case_id']))
            if db_case:
                batch.append(Citation(
                    citation_text=row['citation_text'][:255],
                    citation_type=row.get('citation_type', '')[:20],
                    case_id=db_case,
                ))
            if len(batch) >= 2000:
                session.add_all(batch)
                session.flush()
                count += len(batch)
                batch = []

        if batch:
            session.add_all(batch)
            session.flush()
            count += len(batch)

    session.commit()
    logger.info(f"✓ Loaded {count} citations")


def load_acts(session):
    """Load acts. Returns name -> db_id map."""
    csv_path = DATA_DIR / 'acts.csv'
    if not csv_path.exists():
        return {}

    act_map = {}
    count = 0
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = row['act_name'][:490].strip()
            if not name or len(name) < 3:
                continue
            if name not in act_map:
                existing = session.query(Act).filter(Act.act_name == name).first()
                if existing:
                    act_map[name] = existing.act_id
                else:
                    act = Act(act_name=name)
                    session.add(act)
                    session.flush()
                    act_map[name] = act.act_id
                    count += 1

            if count % 10000 == 0 and count > 0 and count not in [10000]:
                pass  # Just counting

    session.commit()
    logger.info(f"✓ Loaded {len(act_map)} unique acts")
    return act_map


def load_case_acts(session, case_map, act_map):
    """Load case-act junction using case_acts.csv."""
    csv_path = DATA_DIR / 'case_acts.csv'
    if not csv_path.exists():
        return

    # Build act_id -> name map from CSV
    acts_csv = DATA_DIR / 'acts.csv'
    csv_act_id_to_name = {}
    if acts_csv.exists():
        with open(acts_csv, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                csv_act_id_to_name[int(row['act_id'])] = row['act_name'][:490].strip()

    count = 0
    seen = set()
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            db_case = case_map.get(int(row['case_id']))
            act_name = csv_act_id_to_name.get(int(row['act_id']), row.get('act_name', ''))
            db_act = act_map.get(act_name)

            if db_case and db_act:
                key = (db_case, db_act)
                if key not in seen:
                    seen.add(key)
                    session.add(CaseAct(case_id=db_case, act_id=db_act))
                    count += 1

            if count % 10000 == 0 and count > 0:
                session.flush()
                if count % 50000 == 0:
                    logger.info(f"  Case-acts: {count}")

    session.commit()
    logger.info(f"✓ Loaded {count} case-act links")


def load_sections(session, case_map):
    """Load sections and case-section links."""
    csv_path = DATA_DIR / 'case_sections.csv'
    if not csv_path.exists():
        return

    section_map = {}
    count = 0
    seen = set()

    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            sec_name = row.get('section_name', '')[:250]
            db_case = case_map.get(int(row['case_id']))

            if sec_name and db_case:
                if sec_name not in section_map:
                    existing = session.query(LegalSection).filter(
                        LegalSection.section_name == sec_name,
                        LegalSection.act_id.is_(None)
                    ).first()
                    if existing:
                        section_map[sec_name] = existing.section_id
                    else:
                        ls = LegalSection(section_name=sec_name)
                        session.add(ls)
                        session.flush()
                        section_map[sec_name] = ls.section_id

                sec_id = section_map[sec_name]
                key = (db_case, sec_id)
                if key not in seen:
                    seen.add(key)
                    session.add(CaseSection(case_id=db_case, section_id=sec_id))
                    count += 1

            if count % 10000 == 0 and count > 0:
                session.flush()
                if count % 50000 == 0:
                    logger.info(f"  Case-sections: {count}")

    session.commit()
    logger.info(f"✓ Loaded {len(section_map)} sections, {count} case-section links")


def run_mysql_loader():
    """Run the complete MySQL data loading pipeline."""
    logger.info("=" * 60)
    logger.info("CCIS MySQL Data Loader")
    logger.info("=" * 60)

    session = SessionLocal()
    try:
        court_id = load_courts(session)
        case_map = load_cases(session, court_id)
        judge_map = load_judges(session)
        load_case_judges(session, case_map, judge_map)
        party_map = load_parties(session)
        load_case_parties(session, case_map, party_map)
        load_lawyers_from_text(session, case_map)
        load_citations(session, case_map)
        act_map = load_acts(session)
        load_case_acts(session, case_map, act_map)
        load_sections(session, case_map)

        # Print summary
        logger.info("=" * 60)
        logger.info("LOADING COMPLETE — Summary:")
        for tbl in ['courts', 'cases', 'judges', 'case_judges', 'parties',
                     'case_parties', 'lawyers', 'case_lawyers', 'acts',
                     'case_acts', 'citations', 'legal_sections', 'case_sections']:
            cnt = session.execute(text(f"SELECT COUNT(*) FROM {tbl}")).scalar()
            logger.info(f"  {tbl:20s}: {cnt:>10,}")
        logger.info("=" * 60)

    except Exception as e:
        session.rollback()
        logger.error(f"Loading failed: {e}")
        raise
    finally:
        session.close()


if __name__ == '__main__':
    run_mysql_loader()
