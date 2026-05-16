"""
CSV Loader Module
=================
Loads raw CSV legal case datasets with encoding detection,
column validation, and batch processing support.
"""

import csv
import os
import sys
import logging
import chardet
from pathlib import Path
from typing import Generator, Dict, List, Optional

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class CSVLoader:
    """Loads and validates CSV legal case datasets."""

    EXPECTED_COLUMNS = [
        'name', 'case_category', 'case_type', 'case_info',
        'judgement', 'tokens', 'sentences', 'label', 'proof_sentence'
    ]

    def __init__(self, file_path: str, sample_size: Optional[int] = None):
        self.file_path = Path(file_path)
        self.sample_size = sample_size
        self.encoding = None
        self.total_rows = 0
        self.valid_rows = 0
        self.skipped_rows = 0
        self.errors: List[Dict] = []

        if not self.file_path.exists():
            raise FileNotFoundError(f"CSV file not found: {self.file_path}")

    def detect_encoding(self) -> str:
        """Detect file encoding using chardet."""
        logger.info(f"Detecting encoding for {self.file_path.name}...")
        with open(self.file_path, 'rb') as f:
            raw = f.read(100000)  # Read first 100KB
            result = chardet.detect(raw)
            self.encoding = result['encoding'] or 'utf-8'
            logger.info(f"Detected encoding: {self.encoding} (confidence: {result['confidence']:.2f})")
        return self.encoding

    def validate_columns(self, header: List[str]) -> bool:
        """Validate CSV columns against expected schema."""
        # Remove index column if present
        clean_header = [h.strip().lower() for h in header if h.strip()]
        
        missing = set(self.EXPECTED_COLUMNS) - set(clean_header)
        if missing:
            logger.warning(f"Missing columns: {missing}")
            return False
        
        logger.info(f"Column validation passed. Columns: {clean_header}")
        return True

    def load_batch(self, batch_size: int = 1000) -> Generator[List[Dict], None, None]:
        """Load CSV data in batches for memory-efficient processing."""
        if not self.encoding:
            self.detect_encoding()

        batch = []
        
        with open(self.file_path, 'r', encoding=self.encoding, errors='replace') as f:
            reader = csv.DictReader(f)
            
            # Validate columns
            if reader.fieldnames:
                self.validate_columns(reader.fieldnames)

            for i, row in enumerate(reader):
                if self.sample_size and self.total_rows >= self.sample_size:
                    break
                
                self.total_rows += 1

                # Skip empty rows
                if not row.get('name') and not row.get('case_info'):
                    self.skipped_rows += 1
                    continue

                # Clean the row
                cleaned = self._clean_row(row, i)
                if cleaned:
                    batch.append(cleaned)
                    self.valid_rows += 1

                if len(batch) >= batch_size:
                    yield batch
                    batch = []

            if batch:
                yield batch

        logger.info(
            f"Loading complete. Total: {self.total_rows}, "
            f"Valid: {self.valid_rows}, Skipped: {self.skipped_rows}"
        )

    def _clean_row(self, row: Dict, row_num: int) -> Optional[Dict]:
        """Clean and validate a single row."""
        try:
            cleaned = {
                'original_id': row.get('', str(row_num)),
                'file_name': (row.get('name') or '').strip(),
                'case_category': (row.get('case_category') or '').strip().lower(),
                'case_type': (row.get('case_type') or '').strip().lower(),
                'case_info': (row.get('case_info') or '').strip(),
                'judgement_text': (row.get('judgement') or '').strip(),
                'token_count': self._safe_float(row.get('tokens')),
                'sentence_count': self._safe_float(row.get('sentences')),
                'verdict_label': (row.get('label') or '').strip(),
                'proof_sentence': (row.get('proof_sentence') or '').strip(),
            }
            return cleaned
        except Exception as e:
            self.errors.append({'row': row_num, 'error': str(e)})
            return None

    def _safe_float(self, value: Optional[str]) -> Optional[float]:
        """Safely convert a value to float."""
        if not value or value.strip() == '':
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            return None

    def load_all(self) -> List[Dict]:
        """Load all records into memory (use for smaller datasets)."""
        all_records = []
        for batch in self.load_batch():
            all_records.extend(batch)
        return all_records

    def get_stats(self) -> Dict:
        """Return loading statistics."""
        return {
            'file': str(self.file_path),
            'encoding': self.encoding,
            'total_rows': self.total_rows,
            'valid_rows': self.valid_rows,
            'skipped_rows': self.skipped_rows,
            'error_count': len(self.errors),
        }


if __name__ == '__main__':
    # Quick test
    import json
    
    csv_path = sys.argv[1] if len(sys.argv) > 1 else '../../raw_data/csv/case_files_total.csv'
    sample = int(sys.argv[2]) if len(sys.argv) > 2 else 100
    
    loader = CSVLoader(csv_path, sample_size=sample)
    records = loader.load_all()
    
    print(f"\n=== Loading Stats ===")
    print(json.dumps(loader.get_stats(), indent=2))
    
    if records:
        print(f"\n=== Sample Record ===")
        print(json.dumps(records[0], indent=2, default=str))
