"""
Load remaining data: case_parties, citations, acts, sections
(Run after initial load hit duplicate key error)
"""
import csv
import sys
import logging
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from sqlalchemy import text
from backend.database.connection import engine, SessionLocal
from backend.models.models import (
    Case, Party, CaseParty, Citation, Act, LegalSection, CaseSection
)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

DATA_DIR = PROJECT_ROOT / 'extracted' / 'clean_csv'


def main():
    session = SessionLocal()

    try:
        # Build case_id map: csv_case_id -> db_case_id
        # Since we loaded sequentially, csv IDs 1..N map to db IDs 1..N
        case_count = session.execute(text("SELECT COUNT(*) FROM cases")).scalar()
        logger.info(f"Cases in DB: {case_count}")
        case_map = {i: i for i in range(1, case_count + 1)}

        # Build party map
        party_map = {}
        parties = session.execute(text("SELECT party_id FROM parties")).fetchall()
        for p in parties:
            party_map[p[0]] = p[0]
        logger.info(f"Parties in DB: {len(party_map)}")

        # Load case_parties with dedup
        csv_path = DATA_DIR / 'case_parties.csv'
        if csv_path.exists():
            count = 0
            seen = set()
            # Load existing
            existing = session.execute(text("SELECT case_id, party_id, role FROM case_parties")).fetchall()
            for e in existing:
                seen.add((e[0], e[1], e[2]))
            logger.info(f"Existing case_parties: {len(seen)}")

            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                batch = []
                for row in reader:
                    db_case_id = case_map.get(int(row['case_id']))
                    db_party_id = party_map.get(int(row['party_id']))
                    role = row.get('role', 'unknown')[:50]

                    if db_case_id and db_party_id:
                        key = (db_case_id, db_party_id, role)
                        if key not in seen:
                            seen.add(key)
                            batch.append(CaseParty(case_id=db_case_id, party_id=db_party_id, role=role))
                            count += 1

                    if len(batch) >= 1000:
                        session.add_all(batch)
                        session.flush()
                        batch = []
                        if count % 5000 == 0:
                            logger.info(f"  Loaded {count} case-party links...")

                if batch:
                    session.add_all(batch)
                    session.flush()

            session.commit()
            logger.info(f"Loaded {count} case-party links.")

        # Load citations
        csv_path = DATA_DIR / 'citations.csv'
        if csv_path.exists():
            count = 0
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                batch = []
                for row in reader:
                    db_case_id = case_map.get(int(row['case_id']))
                    if db_case_id:
                        batch.append(Citation(
                            citation_text=row['citation_text'][:255],
                            citation_type=row.get('citation_type', '')[:20],
                            case_id=db_case_id,
                        ))

                    if len(batch) >= 1000:
                        session.add_all(batch)
                        session.flush()
                        count += len(batch)
                        batch = []
                        if count % 5000 == 0:
                            logger.info(f"  Loaded {count} citations...")

                if batch:
                    session.add_all(batch)
                    session.flush()
                    count += len(batch)

            session.commit()
            logger.info(f"Loaded {count} citations.")

        # Load acts
        acts_path = DATA_DIR / 'acts.csv'
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

        # Load sections and case-section links
        sections_path = DATA_DIR / 'case_sections.csv'
        if sections_path.exists():
            section_map = {}
            cs_count = 0
            seen_cs = set()

            with open(sections_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    sec_name = row.get('section_name', '')[:250]
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
                                ls = LegalSection(section_name=sec_name)
                                session.add(ls)
                                session.flush()
                                section_map[sec_name] = ls.section_id

                        sec_id = section_map[sec_name]
                        key = (db_case_id, sec_id)
                        if key not in seen_cs:
                            seen_cs.add(key)
                            session.add(CaseSection(case_id=db_case_id, section_id=sec_id))
                            cs_count += 1

                    if cs_count % 10000 == 0 and cs_count > 0:
                        session.flush()
                        if cs_count % 50000 == 0:
                            logger.info(f"  Loaded {cs_count} case-section links...")

            session.commit()
            logger.info(f"Loaded {len(section_map)} sections and {cs_count} case-section links.")

        logger.info("=== Remaining data loaded successfully ===")
    except Exception as e:
        session.rollback()
        logger.error(f"Error: {e}")
        raise
    finally:
        session.close()


if __name__ == '__main__':
    main()
