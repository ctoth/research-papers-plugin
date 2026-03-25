"""Shared paper identifier parsing and classification.

Provides:
  - parse_citation / generate_dirname — extracted from paper_hash.py
  - IdType / classify_identifier / to_s2_id — new identifier classification
"""

from __future__ import annotations

import re
from enum import Enum


# ---------------------------------------------------------------------------
# Constants (moved from paper_hash.py)
# ---------------------------------------------------------------------------

FILLER_WORDS = {
    'a', 'an', 'the', 'of', 'in', 'on', 'for', 'and', 'or', 'to', 'with',
    'from', 'by', 'as', 'at', 'is', 'are', 'was', 'were', 'be', 'been',
    'its', 'their', 'our', 'your', 'that', 'this', 'these', 'those',
    'using', 'via', 'through', 'toward', 'towards', 'into', 'between',
    'based', 'how', 'what', 'when', 'where', 'why', 'which', 'who',
}

MAX_TITLE_WORDS = 4


# ---------------------------------------------------------------------------
# Citation parsing (moved from paper_hash.py)
# ---------------------------------------------------------------------------

def parse_citation(text):
    """Parse a freeform citation string into (author, year, title).

    Handles formats like:
      Fan et al. (2018) - "Hierarchical neural story generation"
      **Fan et al., 2018** - "Hierarchical neural story generation"
      Genette, G. (1972). *Narrative discourse: an essay in method.*
      Fan et al. (2018) - source of Writing Prompts dataset
      Roemmele and Gordon (2015) - "Creative help"
    """
    text = text.strip()
    # Strip leading markdown bold/italic
    text = re.sub(r'^\*+\s*', '', text)
    text = re.sub(r'\s*\*+$', '', text)
    text = text.strip()

    author = None
    year = None
    title = None

    # Extract year - look for (YYYY) or just YYYY near the start
    year_match = re.search(r'\((\d{4})\)', text)
    if not year_match:
        year_match = re.search(r'[\s,](\d{4})[\s,)]', text)
    if not year_match:
        year_match = re.search(r'(\d{4})', text)
    if year_match:
        year = year_match.group(1)

    # Extract author - everything before the year (or first punctuation pattern)
    if year_match:
        before_year = text[:year_match.start()].strip()
    else:
        before_year = text.split('-')[0].split('\u2014')[0].strip()

    # Clean up author string
    before_year = re.sub(r'[,\s]+$', '', before_year)
    before_year = re.sub(r'\s+et\s+al\.?$', '', before_year)
    # Get surname (first capitalized word)
    author_match = re.match(r'([A-Z][a-z]+)', before_year)
    if author_match:
        author = author_match.group(1)

    # Extract title - look for quoted or italicized text after author+year
    if year_match:
        after_year = text[year_match.end():]
    else:
        after_year = text

    # Try quoted title: "Title here"
    title_match = re.search(r'"([^"]+)"', after_year)
    if not title_match:
        # Try italicized: *Title here*
        title_match = re.search(r'\*([^*]+)\*', after_year)
    if not title_match:
        # Try after dash/colon separator
        sep_match = re.search(r'[\-\u2014:]\s*(.+?)(?:\s*[\-\u2014]|$)', after_year)
        if sep_match:
            candidate = sep_match.group(1).strip()
            # Only use if it looks like a title (starts with cap, reasonable length)
            if candidate and candidate[0].isupper() and len(candidate) > 5:
                title = candidate
    if title_match and not title:
        title = title_match.group(1).strip()

    # Strip trailing periods from title
    if title:
        title = title.rstrip('.')

    return author, year, title


def generate_dirname(author, year, title):
    """Generate canonical directory name: Author_Year_ShortTitle.

    ShortTitle is 2-4 CamelCase words from the title, dropping filler words.
    Keeps acronyms (all-caps words) as-is.
    """
    if not author or not year:
        return None

    if not title:
        return f"{author}_{year}"

    # Split title, drop filler, take first MAX_TITLE_WORDS meaningful words
    words = re.split(r'[\s/]+', title)
    meaningful = []
    for w in words:
        # Strip punctuation from edges
        clean = re.sub(r'^[^a-zA-Z0-9]+|[^a-zA-Z0-9]+$', '', w)
        if not clean:
            continue
        if clean.lower() in FILLER_WORDS:
            continue
        # Capitalize unless it's an acronym (already all-caps)
        if clean.isupper() and len(clean) > 1:
            meaningful.append(clean)
        else:
            meaningful.append(clean[0].upper() + clean[1:])
        if len(meaningful) >= MAX_TITLE_WORDS:
            break

    short_title = ''.join(meaningful) if meaningful else 'Untitled'
    return f"{author}_{year}_{short_title}"


# ---------------------------------------------------------------------------
# Identifier classification (new)
# ---------------------------------------------------------------------------

class IdType(Enum):
    ARXIV_ID = "arxiv_id"
    ARXIV_URL = "arxiv_url"
    DOI = "doi"
    ACL_URL = "acl_url"
    S2_ID = "s2_id"
    GENERIC_URL = "generic_url"


# Patterns for identifier classification
_ARXIV_ID_RE = re.compile(
    r'^(?:arXiv:)?(\d{4}\.\d{4,5}(?:v\d+)?)$', re.IGNORECASE
)
_ARXIV_URL_RE = re.compile(
    r'https?://(?:export\.)?arxiv\.org/(?:abs|pdf)/(\d{4}\.\d{4,5}(?:v\d+)?)'
)
_DOI_RE = re.compile(
    r'^(?:https?://(?:dx\.)?doi\.org/)?(10\.\d{4,9}/\S+)$'
)
_ACL_URL_RE = re.compile(
    r'https?://aclanthology\.org/([^\s/]+?)(?:\.pdf)?/?$'
)
_S2_ID_RE = re.compile(
    r'^(?:CorpusId:|S2:)(\d+)$', re.IGNORECASE
)


def classify_identifier(raw: str) -> tuple[IdType, str]:
    """Classify and normalize a paper identifier.

    Returns (IdType, normalized_value) where normalized_value is:
      ARXIV_ID:    "2401.12345" (bare ID, no prefix, no version unless specified)
      ARXIV_URL:   "2401.12345" (extracted ID)
      DOI:         "10.xxx/yyy" (bare DOI, no URL prefix)
      ACL_URL:     "2024.acl-long.1" (anthology ID)
      S2_ID:       "12345" (corpus ID)
      GENERIC_URL: original URL unchanged
    """
    raw = raw.strip()

    # Arxiv URL (check before DOI since arxiv.org URLs contain slashes)
    m = _ARXIV_URL_RE.match(raw)
    if m:
        return IdType.ARXIV_URL, m.group(1)

    # ACL Anthology URL
    m = _ACL_URL_RE.match(raw)
    if m:
        return IdType.ACL_URL, m.group(1)

    # Arxiv ID (bare, with or without arXiv: prefix)
    m = _ARXIV_ID_RE.match(raw)
    if m:
        return IdType.ARXIV_ID, m.group(1)

    # S2 corpus ID
    m = _S2_ID_RE.match(raw)
    if m:
        return IdType.S2_ID, m.group(1)

    # DOI (bare or as URL)
    m = _DOI_RE.match(raw)
    if m:
        return IdType.DOI, m.group(1)

    # Generic URL
    if raw.startswith('http://') or raw.startswith('https://'):
        return IdType.GENERIC_URL, raw

    # Fallback: treat as DOI if it looks like one (contains slash)
    if '/' in raw and raw[0:3] == '10.':
        return IdType.DOI, raw

    # Last resort: might be a bare arxiv ID without the dot pattern
    # (old-style like hep-ph/9905221)
    old_arxiv = re.match(r'^[a-z-]+/\d{7}$', raw)
    if old_arxiv:
        return IdType.ARXIV_ID, raw

    # Unknown — treat as generic
    return IdType.GENERIC_URL, raw


def to_s2_id(id_type: IdType, value: str) -> str:
    """Convert a classified identifier to Semantic Scholar query format.

    Returns a string suitable for S2 API paper lookup:
      ARXIV_ID/ARXIV_URL -> "ArXiv:2401.12345"
      DOI                -> "DOI:10.xxx/yyy"
      ACL_URL            -> "ACL:2024.acl-long.1"
      S2_ID              -> "CorpusId:12345"
      GENERIC_URL        -> "URL:https://..."
    """
    match id_type:
        case IdType.ARXIV_ID | IdType.ARXIV_URL:
            return f"ArXiv:{value}"
        case IdType.DOI:
            return f"DOI:{value}"
        case IdType.ACL_URL:
            return f"ACL:{value}"
        case IdType.S2_ID:
            return f"CorpusId:{value}"
        case IdType.GENERIC_URL:
            return f"URL:{value}"
