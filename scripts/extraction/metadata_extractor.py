"""
Metadata Extraction Engine
===========================
Extracts structured legal entities from raw legal text using regex patterns.
"""

import re
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class CaseMetadata:
    """Structured case metadata extracted from raw text."""
    case_number: str = ''
    case_title: str = ''
    court_name: str = 'Supreme Court of India'
    judgment_date: str = ''
    case_type: str = ''
    case_category: str = ''
    judges: List[str] = field(default_factory=list)
    bench_strength: int = 0
    bench_type: str = ''
    petitioners: List[str] = field(default_factory=list)
    respondents: List[str] = field(default_factory=list)
    acts_cited: List[str] = field(default_factory=list)
    sections_cited: List[str] = field(default_factory=list)
    articles_cited: List[str] = field(default_factory=list)
    air_citations: List[str] = field(default_factory=list)
    scc_citations: List[str] = field(default_factory=list)
    scr_citations: List[str] = field(default_factory=list)
    other_citations: List[str] = field(default_factory=list)
    verdict: str = ''
    judgment_summary: str = ''
    word_count: int = 0


class MetadataExtractor:
    """Regex-based metadata extraction engine for Indian legal judgments."""

    CASE_NUM_RE = [
        re.compile(r'(?:civil|criminal|special|writ)\s+(?:appeal|petition|case)\s+(?:number|no\.?)\s*(\d+(?:\s*[-/]\s*\d+)?)\s+(?:of\s+)?(\d{4})', re.I),
        re.compile(r'case\s+number\s+(?:appeal|petition|writ|special)\s*(?:\(\s*(?:civil|criminal)\s*\))?\s*(\d+)\s+of\s+(\d{4})', re.I),
        re.compile(r'(?:C\.?A\.?|W\.?P\.?|SLP|Cr\.?A\.?)\s*(?:No\.?)\s*(\d+)\s*(?:of\s+)?(\d{4})', re.I),
        re.compile(r'(?:no|number)\.?\s*(\d+)\s+of\s+(\d{4})', re.I),
    ]

    DATE_RE = [
        re.compile(r'date\s+of\s+judg(?:ment|ement)\s*:?\s*(\d{1,2}[/\-]\d{1,2}[/\-]\d{4})', re.I),
        re.compile(r'date\s+of\s+judg(?:ment|ement)\s*(\d{1,2}[/\-]\d{1,2}[/\-]\d{4})', re.I),
        re.compile(r'(\d{1,2}(?:st|nd|rd|th)?\s+day\s+of\s+\w+,?\s+\d{4})', re.I),
    ]

    CIT_RE = {
        'AIR': re.compile(r'(?:AIR\s+\d{4}\s+\w+\s+\d+|\d{4}\s+AIR\s+\d+)', re.I),
        'SCC': re.compile(r'\d{4}\s*\(\s*\d+\s*\)\s*SCC\s+\d+', re.I),
        'SCR': re.compile(r'\d{4}\s*\(\s*\d+\s*\)\s*SCR\s+\d+', re.I),
    }

    SEC_RE = re.compile(r'(?:section|s\.?|sec\.?)\s*(\d+[a-z]?(?:\s*\(\s*\d+\s*\))?)', re.I)
    ART_RE = re.compile(r'article[s]?\s+(\d+[a-z]?(?:\s*\(\s*\d+\s*\))?)', re.I)
    ACT_RE = re.compile(r'(?:the\s+)?([a-z][a-z\s]{3,60}(?:act|code|ordinance)),?\s*(?:\d{4})?', re.I)
    PET_RE = re.compile(r'petitioner[s]?\s+(.+?)(?:\s+(?:vs?\.?|versus)\s+|\s+respondent)', re.I | re.DOTALL)
    RESP_RE = re.compile(r'respondent[s]?\s+(.+?)(?:\s+date|\s+bench|\s+act|\s+judgment|\n\n)', re.I | re.DOTALL)
    APP_RE = re.compile(r'appellant[s]?\s+(.+?)(?:\s+(?:vs?\.?|versus)\s+)', re.I | re.DOTALL)

    def __init__(self):
        self.stats = {k: 0 for k in ['total', 'case_nums', 'judges', 'dates', 'citations', 'acts', 'parties']}

    def extract(self, record: Dict) -> CaseMetadata:
        """Extract all metadata from a single record."""
        self.stats['total'] += 1
        ci = record.get('case_info', '')
        jt = record.get('judgement_text', '')
        full = f"{ci}\n{jt}"

        m = CaseMetadata()
        m.case_type = record.get('case_type', '')
        m.case_category = record.get('case_category', '')
        m.verdict = record.get('verdict_label', '')
        m.word_count = len(full.split())
        m.judgment_summary = record.get('proof_sentence', '')

        m.case_number = self._case_number(ci)
        m.case_title = self._case_title(ci)
        m.judgment_date = self._date(ci)
        m.judges = self._judges(ci)
        m.bench_strength = len(m.judges)
        m.bench_type = ('single' if m.bench_strength == 1 else 'division' if m.bench_strength == 2
                        else 'full' if m.bench_strength <= 5 else 'constitutional' if m.bench_strength > 5 else 'unknown')

        m.petitioners, m.respondents = self._parties(ci)
        m.air_citations = self._citations(full, 'AIR')
        m.scc_citations = self._citations(full, 'SCC')
        m.scr_citations = self._citations(full, 'SCR')
        m.acts_cited = self._acts(full)
        m.sections_cited = self._sections(full)
        m.articles_cited = self._articles(full)

        if m.case_number: self.stats['case_nums'] += 1
        if m.judges: self.stats['judges'] += 1
        if m.judgment_date: self.stats['dates'] += 1
        if any([m.air_citations, m.scc_citations, m.scr_citations]): self.stats['citations'] += 1
        if m.acts_cited: self.stats['acts'] += 1
        if m.petitioners or m.respondents: self.stats['parties'] += 1
        return m

    def _case_number(self, text):
        for p in self.CASE_NUM_RE:
            match = p.search(text)
            if match:
                g = match.groups()
                return f"{g[0].strip()}/{g[1]}" if len(g) >= 2 else g[0].strip()
        return ''

    def _case_title(self, text):
        match = re.search(r'(.{5,80}?)\s+(?:vs?\.?|versus)\s+(.{5,80}?)(?:\s+date|\s+bench|\n)', text, re.I | re.DOTALL)
        if match:
            p = re.sub(r'^(?:petitioner|appellant)\s+', '', match.group(1).strip(), flags=re.I).strip()
            r = re.sub(r'\s+(?:respondent|defendant).*$', '', match.group(2).strip(), flags=re.I).strip()
            return f"{p} v. {r}"
        return ''

    def _date(self, text):
        for p in self.DATE_RE:
            match = p.search(text)
            if match: return match.group(1).strip()
        return ''

    def _judges(self, text):
        judges = set()
        bench = re.search(r'bench\s+(.+?)(?:\n|judgment|citation|act\s)', text, re.I)
        if bench:
            for part in re.split(r'\s{2,}|,\s*', bench.group(1)):
                name = re.sub(r'\s*\(?\s*(?:cj|j)\s*\.?\s*\)?$', '', part.strip(), flags=re.I).strip()
                if name and len(name) > 2: judges.add(name)
        for match in re.finditer(r'(?:justice|hon.?ble\s+(?:mr\.\s+)?justice)\s+([a-z.\s]+?)(?:[,.\s](?:j\.?|cj\.?)|\n)', text[:1000], re.I):
            name = match.group(1).strip().rstrip(',. ')
            if name and len(name) > 2: judges.add(name)
        return list(judges)[:10]

    def _parties(self, text):
        pets, resps = [], []
        for pat, lst in [(self.PET_RE, pets), (self.APP_RE, pets), (self.RESP_RE, resps)]:
            match = pat.search(text)
            if match and not lst:
                t = re.sub(r'\s+', ' ', match.group(1).strip())[:200]
                lst.extend([p.strip() for p in re.split(r'\s+(?:and|&|ors\.?)\s+', t) if p.strip()][:5])
        return pets, resps

    def _citations(self, text, ctype):
        p = self.CIT_RE.get(ctype)
        if not p: return []
        seen = set()
        result = []
        for m in p.findall(text):
            c = re.sub(r'\s+', ' ', m.strip())
            if c not in seen: seen.add(c); result.append(c)
        return result[:50]

    def _acts(self, text):
        acts = set()
        for m in self.ACT_RE.finditer(text):
            a = re.sub(r'\s+', ' ', m.group(1).strip()).title()
            if 5 < len(a) < 100: acts.add(a)
        return list(acts)[:20]

    def _sections(self, text):
        return list({f"Section {m.group(1).strip()}" for m in self.SEC_RE.finditer(text)})[:30]

    def _articles(self, text):
        return list({f"Article {m.group(1).strip()}" for m in self.ART_RE.finditer(text)})[:20]

    def get_stats(self): return dict(self.stats)
