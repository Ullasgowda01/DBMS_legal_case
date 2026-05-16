"""
Data Cleaning Pipeline
=======================
Normalizes extracted legal data: judges, dates, citations, text, deduplication.
"""

import re
import logging
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import asdict

logger = logging.getLogger(__name__)

MONTH_MAP = {
    'january': '01', 'february': '02', 'march': '03', 'april': '04',
    'may': '05', 'june': '06', 'july': '07', 'august': '08',
    'september': '09', 'october': '10', 'november': '11', 'december': '12',
    'jan': '01', 'feb': '02', 'mar': '03', 'apr': '04',
    'jun': '06', 'jul': '07', 'aug': '08', 'sep': '09',
    'oct': '10', 'nov': '11', 'dec': '12',
}


class DataCleaner:
    """Cleans and normalizes extracted legal metadata."""

    def __init__(self):
        self.stats = {'cleaned': 0, 'duplicates': 0, 'date_fixes': 0, 'judge_fixes': 0}
        self._seen_cases = set()

    def clean_record(self, metadata_dict: Dict) -> Optional[Dict]:
        """Clean a single metadata record."""
        self.stats['cleaned'] += 1

        # Dedup by case_number
        key = metadata_dict.get('case_number', '') or metadata_dict.get('case_title', '')
        if key and key in self._seen_cases:
            self.stats['duplicates'] += 1
            return None
        if key:
            self._seen_cases.add(key)

        # Clean individual fields
        metadata_dict['case_title'] = self._clean_text(metadata_dict.get('case_title', ''))
        metadata_dict['judgment_date'] = self._clean_date(metadata_dict.get('judgment_date', ''))
        metadata_dict['judges'] = self._clean_judges(metadata_dict.get('judges', []))
        metadata_dict['petitioners'] = self._clean_party_names(metadata_dict.get('petitioners', []))
        metadata_dict['respondents'] = self._clean_party_names(metadata_dict.get('respondents', []))
        metadata_dict['acts_cited'] = self._clean_acts(metadata_dict.get('acts_cited', []))
        metadata_dict['air_citations'] = self._clean_citations(metadata_dict.get('air_citations', []))
        metadata_dict['scc_citations'] = self._clean_citations(metadata_dict.get('scc_citations', []))
        metadata_dict['scr_citations'] = self._clean_citations(metadata_dict.get('scr_citations', []))
        metadata_dict['verdict'] = self._clean_verdict(metadata_dict.get('verdict', ''))

        return metadata_dict

    def _clean_text(self, text: str) -> str:
        """Remove corrupted symbols, normalize whitespace."""
        if not text:
            return ''
        text = re.sub(r'[^\x20-\x7E\n]', '', text)
        text = re.sub(r'\s+', ' ', text).strip()
        return text[:500]

    def _clean_date(self, date_str: str) -> str:
        """Normalize all dates to YYYY-MM-DD."""
        if not date_str:
            return ''

        # DD/MM/YYYY or DD-MM-YYYY
        match = re.match(r'(\d{1,2})[/\-](\d{1,2})[/\-](\d{4})', date_str)
        if match:
            d, m, y = match.groups()
            try:
                dt = datetime(int(y), int(m), int(d))
                self.stats['date_fixes'] += 1
                return dt.strftime('%Y-%m-%d')
            except ValueError:
                pass

        # "19th day of september, 1997" or "october 21, 1964"
        match = re.search(r'(\d{1,2})(?:st|nd|rd|th)?\s+(?:day\s+of\s+)?(\w+),?\s+(\d{4})', date_str, re.I)
        if match:
            d, month_name, y = match.groups()
            m = MONTH_MAP.get(month_name.lower(), '')
            if m:
                try:
                    dt = datetime(int(y), int(m), int(d))
                    self.stats['date_fixes'] += 1
                    return dt.strftime('%Y-%m-%d')
                except ValueError:
                    pass

        # "month day, year"
        match = re.search(r'(\w+)\s+(\d{1,2}),?\s+(\d{4})', date_str, re.I)
        if match:
            month_name, d, y = match.groups()
            m = MONTH_MAP.get(month_name.lower(), '')
            if m:
                try:
                    dt = datetime(int(y), int(m), int(d))
                    self.stats['date_fixes'] += 1
                    return dt.strftime('%Y-%m-%d')
                except ValueError:
                    pass

        return ''

    def _clean_judges(self, judges: List[str]) -> List[str]:
        """Normalize judge names."""
        cleaned = []
        for name in judges:
            name = name.strip()
            # Remove suffixes
            name = re.sub(r'\s*,?\s*(?:j\.?|cj\.?|jj\.?)$', '', name, flags=re.I).strip()
            # Remove "Justice" prefix for storage (we add it in display)
            name = re.sub(r'^(?:hon[\'.]?ble\s+)?(?:mr\.?\s+)?(?:justice\s+)?', '', name, flags=re.I).strip()
            # Proper case
            if name and len(name) > 2:
                # Handle initials: "s.m. sikri" -> "S.M. Sikri"
                parts = name.split()
                formatted = []
                for p in parts:
                    if re.match(r'^[a-z]\.', p):
                        formatted.append(p.upper())
                    else:
                        formatted.append(p.capitalize())
                name = ' '.join(formatted)
                if name not in cleaned:
                    cleaned.append(name)
                    self.stats['judge_fixes'] += 1
        return cleaned

    def _clean_party_names(self, parties: List[str]) -> List[str]:
        """Clean party names."""
        cleaned = []
        for name in parties:
            name = re.sub(r'[^\x20-\x7E]', '', name).strip()
            name = re.sub(r'\s+', ' ', name)
            name = re.sub(r'^(?:shri|smt|mrs?|dr)\.?\s+', '', name, flags=re.I)
            if name and len(name) > 2 and len(name) < 200:
                cleaned.append(name.title())
        return cleaned

    def _clean_acts(self, acts: List[str]) -> List[str]:
        """Clean and deduplicate act names."""
        cleaned = set()
        for act in acts:
            act = re.sub(r'\s+', ' ', act).strip().title()
            # Filter out noise
            if len(act) > 5 and not re.match(r'^(The|Of|And|In|For|By)\s*$', act, re.I):
                cleaned.add(act)
        return sorted(cleaned)

    def _clean_citations(self, citations: List[str]) -> List[str]:
        """Normalize citation format."""
        cleaned = []
        for cit in citations:
            cit = re.sub(r'\s+', ' ', cit).strip().upper()
            if cit and cit not in cleaned:
                cleaned.append(cit)
        return cleaned

    def _clean_verdict(self, verdict: str) -> str:
        """Standardize verdict labels."""
        v = verdict.strip().lower()
        if v in ('accepted', 'allowed', 'granted'):
            return 'Accepted'
        elif v in ('rejected', 'dismissed', 'denied'):
            return 'Rejected'
        elif v in ('other', 'partial', 'modified'):
            return 'Other'
        return verdict.strip() or 'Unknown'

    def get_stats(self) -> Dict:
        return dict(self.stats)
