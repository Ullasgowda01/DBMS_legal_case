"""
Main Extraction Pipeline
=========================
Orchestrates: CSV loading → metadata extraction → cleaning → CSV output.
Processes the raw legal dataset into normalized, structured CSV files.
"""

import csv
import json
import os
import sys
import logging
from pathlib import Path
from dataclasses import asdict
from datetime import datetime
from collections import defaultdict

# Add parent dirs to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from extraction.csv_loader import CSVLoader
from extraction.metadata_extractor import MetadataExtractor, CaseMetadata
from cleaning.data_cleaner import DataCleaner

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(Path(__file__).parent.parent.parent / 'extracted' / 'logs' / 'pipeline.log')
    ]
)
logger = logging.getLogger(__name__)

BASE = Path(__file__).parent.parent.parent
OUTPUT_DIR = BASE / 'extracted' / 'clean_csv'
REPORT_DIR = BASE / 'extracted' / 'reports'
LOG_DIR = BASE / 'extracted' / 'logs'


def ensure_dirs():
    for d in [OUTPUT_DIR, REPORT_DIR, LOG_DIR]:
        d.mkdir(parents=True, exist_ok=True)


def run_pipeline(csv_path: str, sample_size: int = 50000):
    """Run the full extraction pipeline."""
    ensure_dirs()
    logger.info(f"=== Legal Case Extraction Pipeline ===")
    logger.info(f"Source: {csv_path}")
    logger.info(f"Sample size: {sample_size}")

    loader = CSVLoader(csv_path, sample_size=sample_size)
    extractor = MetadataExtractor()
    cleaner = DataCleaner()

    # Collect all data for output
    cases = []
    all_judges = set()
    all_acts = set()
    all_citations = []
    all_parties = []
    case_judge_links = []
    case_act_links = []
    case_section_links = []
    case_citation_links = []
    case_party_links = []

    case_id = 0
    judge_map = {}  # name -> id
    act_map = {}    # name -> id
    party_map = {}  # name -> id

    for batch_num, batch in enumerate(loader.load_batch(batch_size=1000)):
        logger.info(f"Processing batch {batch_num + 1} ({len(batch)} records)...")

        for record in batch:
            # Extract metadata
            metadata = extractor.extract(record)
            meta_dict = asdict(metadata)

            # Clean
            cleaned = cleaner.clean_record(meta_dict)
            if cleaned is None:
                continue

            case_id += 1

            # Build case record
            case_record = {
                'case_id': case_id,
                'case_number': cleaned['case_number'],
                'case_title': cleaned['case_title'],
                'court_name': cleaned['court_name'],
                'judgment_date': cleaned['judgment_date'],
                'case_type': cleaned['case_type'],
                'case_category': cleaned['case_category'],
                'verdict': cleaned['verdict'],
                'bench_strength': cleaned['bench_strength'],
                'bench_type': cleaned['bench_type'],
                'word_count': cleaned['word_count'],
                'judgment_summary': cleaned['judgment_summary'][:500] if cleaned['judgment_summary'] else '',
                'file_name': record.get('file_name', ''),
            }
            cases.append(case_record)

            # Judges
            for judge_name in cleaned['judges']:
                if judge_name not in judge_map:
                    judge_map[judge_name] = len(judge_map) + 1
                case_judge_links.append({
                    'case_id': case_id,
                    'judge_id': judge_map[judge_name],
                    'judge_name': judge_name,
                })

            # Acts
            for act_name in cleaned['acts_cited']:
                if act_name not in act_map:
                    act_map[act_name] = len(act_map) + 1
                case_act_links.append({
                    'case_id': case_id,
                    'act_id': act_map[act_name],
                    'act_name': act_name,
                })

            # Sections
            for sec in cleaned['sections_cited']:
                case_section_links.append({
                    'case_id': case_id,
                    'section_name': sec,
                })

            # Citations
            for ctype, clist in [('AIR', cleaned['air_citations']),
                                  ('SCC', cleaned['scc_citations']),
                                  ('SCR', cleaned['scr_citations'])]:
                for cit in clist:
                    all_citations.append({
                        'case_id': case_id,
                        'citation_text': cit,
                        'citation_type': ctype,
                    })

            # Parties
            for pname in cleaned['petitioners']:
                if pname not in party_map:
                    party_map[pname] = len(party_map) + 1
                case_party_links.append({
                    'case_id': case_id,
                    'party_id': party_map[pname],
                    'party_name': pname,
                    'role': 'petitioner',
                })
            for rname in cleaned['respondents']:
                if rname not in party_map:
                    party_map[rname] = len(party_map) + 1
                case_party_links.append({
                    'case_id': case_id,
                    'party_id': party_map[rname],
                    'party_name': rname,
                    'role': 'respondent',
                })

            # Articles
            for art in cleaned['articles_cited']:
                case_section_links.append({
                    'case_id': case_id,
                    'section_name': art,
                })

    # === Write output CSVs ===
    logger.info("Writing output files...")

    _write_csv(OUTPUT_DIR / 'cases.csv', cases,
               ['case_id', 'case_number', 'case_title', 'court_name', 'judgment_date',
                'case_type', 'case_category', 'verdict', 'bench_strength', 'bench_type',
                'word_count', 'judgment_summary', 'file_name'])

    judges_list = [{'judge_id': v, 'judge_name': k} for k, v in judge_map.items()]
    _write_csv(OUTPUT_DIR / 'judges.csv', judges_list, ['judge_id', 'judge_name'])

    _write_csv(OUTPUT_DIR / 'case_judges.csv', case_judge_links,
               ['case_id', 'judge_id', 'judge_name'])

    acts_list = [{'act_id': v, 'act_name': k} for k, v in act_map.items()]
    _write_csv(OUTPUT_DIR / 'acts.csv', acts_list, ['act_id', 'act_name'])

    _write_csv(OUTPUT_DIR / 'case_acts.csv', case_act_links,
               ['case_id', 'act_id', 'act_name'])

    _write_csv(OUTPUT_DIR / 'citations.csv', all_citations,
               ['case_id', 'citation_text', 'citation_type'])

    parties_list = [{'party_id': v, 'party_name': k} for k, v in party_map.items()]
    _write_csv(OUTPUT_DIR / 'parties.csv', parties_list, ['party_id', 'party_name'])

    _write_csv(OUTPUT_DIR / 'case_parties.csv', case_party_links,
               ['case_id', 'party_id', 'party_name', 'role'])

    _write_csv(OUTPUT_DIR / 'case_sections.csv', case_section_links,
               ['case_id', 'section_name'])

    # === Write report ===
    report = {
        'timestamp': datetime.now().isoformat(),
        'loader_stats': loader.get_stats(),
        'extractor_stats': extractor.get_stats(),
        'cleaner_stats': cleaner.get_stats(),
        'output_counts': {
            'cases': len(cases),
            'judges': len(judge_map),
            'acts': len(act_map),
            'citations': len(all_citations),
            'parties': len(party_map),
            'case_judge_links': len(case_judge_links),
            'case_act_links': len(case_act_links),
            'case_section_links': len(case_section_links),
            'case_party_links': len(case_party_links),
        }
    }

    report_path = REPORT_DIR / 'extraction_report.json'
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2, default=str)
    logger.info(f"Report written to {report_path}")

    logger.info(f"\n=== Pipeline Complete ===")
    logger.info(f"Cases: {len(cases)}")
    logger.info(f"Judges: {len(judge_map)}")
    logger.info(f"Acts: {len(act_map)}")
    logger.info(f"Citations: {len(all_citations)}")
    logger.info(f"Parties: {len(party_map)}")

    return report


def _write_csv(path, records, fieldnames):
    """Write records to CSV."""
    with open(path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(records)
    logger.info(f"  Written {len(records)} rows to {path.name}")


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Legal Case Extraction Pipeline')
    parser.add_argument('--input', '-i', default=str(BASE / 'raw_data' / 'csv' / 'case_files_total.csv'))
    parser.add_argument('--sample', '-s', type=int, default=50000)
    args = parser.parse_args()
    run_pipeline(args.input, args.sample)
