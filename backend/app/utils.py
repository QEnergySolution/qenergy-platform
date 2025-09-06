"""
Utility functions shared across modules

Method:
- Accent-insensitive alias matching (space/_/- variants; digits glued; alnum-only).
- Generic 'Name + capacity' patterns mapped back by fuzzy token_set_ratio.
- Cluster expansion (mentioning cluster names maps to all projects in that cluster).
- Near-boundary merge: if two project mentions are too close, extend first section to the third boundary
  and duplicate for the second project, so both get the same source_text.
"""

import csv
import logging
import re
import unicodedata
from pathlib import Path
from typing import Optional, Iterable, Dict, List, Tuple, Set

from docx import Document
from fastapi import UploadFile
from sqlalchemy import text
from rapidfuzz import process, fuzz

logger = logging.getLogger(__name__)

# ------------------------------ filename parsing (unchanged signature/output) ------------------------------

# Legacy strict pattern (kept for reference)
_FILENAME_RE_STRICT = re.compile(r"^(?P<year>\d{4})_CW(?P<cw>\d{2})_(?P<cat>DEV|EPC|FINANCE|INVESTMENT)\.docx$", re.IGNORECASE)

# Flexible patterns for CW and category extraction
_CW_PATTERN = re.compile(r"CW(\d{1,2})", re.IGNORECASE)
_CATEGORY_PATTERNS = [
    (re.compile(r"(?:^|[^a-zA-Z])(DEV|DEVELOPMENT)(?:[^a-zA-Z]|$)", re.IGNORECASE), "DEV"),
    (re.compile(r"(?:^|[^a-zA-Z])(EPC)(?:[^a-zA-Z]|$)", re.IGNORECASE), "EPC"),
    (re.compile(r"(?:^|[^a-zA-Z])(FINANCE|FINANCIAL|FIN)(?:[^a-zA-Z]|$)", re.IGNORECASE), "FINANCE"),
    (re.compile(r"(?:^|[^a-zA-Z])(INVESTMENT|INVEST|INV)(?:[^a-zA-Z]|$)", re.IGNORECASE), "INVESTMENT"),
]

_CAT_MAP = {
    "DEV": "Development",
    "EPC": "EPC",
    "FINANCE": "Finance",
    "INVESTMENT": "Investment",
}

def parse_filename(filename: str):
    """Parse filename to extract year, cw_label and category (signature & output unchanged)."""
    name_without_ext = filename.lower()
    if name_without_ext.endswith('.docx'):
        name_without_ext = name_without_ext[:-5]

    strict_match = _FILENAME_RE_STRICT.match(filename)
    if strict_match:
        year = int(strict_match.group("year"))
        cw_label = f"CW{strict_match.group('cw').upper()}"
        raw = strict_match.group("cat").upper()
        category = _CAT_MAP.get(raw, raw)
        return year, cw_label, raw, category

    cw_match = _CW_PATTERN.search(filename)
    if not cw_match:
        raise ValueError("INVALID_NAME: No calendar week (CW##) found in filename")
    cw_num = int(cw_match.group(1))
    cw_label = f"CW{cw_num:02d}"

    category_raw = None
    category = None
    for pattern, cat_raw in _CATEGORY_PATTERNS:
        if pattern.search(filename):
            category_raw = cat_raw
            category = _CAT_MAP.get(cat_raw, cat_raw)
            break
    if not category_raw:
        raise ValueError("INVALID_NAME: No valid category (DEV, EPC, FINANCE, INVESTMENT) found in filename")

    year_match = re.search(r"\b(20\d{2})\b", filename)
    if year_match:
        year = int(year_match.group(1))
    else:
        from datetime import datetime
        year = datetime.now().year

    return year, cw_label, category_raw, category


# ------------------------------ CSV/KB utilities ------------------------------

_PROJECT_NAME_TO_CODE_CACHE: dict[str, str] | None = None

def _default_project_csv_path() -> Path:
    """Resolve canonical data/project.csv path (repo-root/data/project.csv)."""
    here = Path(__file__).resolve()
    repo_root = here.parents[2]  # .../qenergy-platform
    return repo_root / "data" / "project.csv"

def load_project_name_to_code_mapping(csv_path: Optional[Path] = None, *, force_reload: bool = False) -> dict[str, str]:
    """project_name -> project_code (status=1 only). Keys are lowercase."""
    global _PROJECT_NAME_TO_CODE_CACHE
    if _PROJECT_NAME_TO_CODE_CACHE is not None and not force_reload:
        return _PROJECT_NAME_TO_CODE_CACHE

    path = csv_path or _default_project_csv_path()
    mapping: dict[str, str] = {}
    if not path.exists():
        _PROJECT_NAME_TO_CODE_CACHE = mapping
        return mapping

    for encoding in ["utf-8", "latin-1", "cp1252"]:
        try:
            with path.open("r", encoding=encoding) as f:
                reader = csv.DictReader(f, delimiter=";")
                for row in reader:
                    code = (row.get("project_code") or "").strip()
                    name = (row.get("project_name") or "").strip()
                    status_str = (row.get("status") or "0").strip()
                    if not code or not name:
                        continue
                    if status_str not in ("1", "true", "True"):
                        continue
                    mapping[name.lower()] = code
            break
        except UnicodeDecodeError:
            continue

    _PROJECT_NAME_TO_CODE_CACHE = mapping
    return mapping

def _load_kb_from_csv() -> tuple[list[str], dict[str, list[str]]]:
    """Return (project_names_original_case, cluster_to_projects) for status==1."""
    path = _default_project_csv_path()
    projects: list[str] = []
    clusters: dict[str, list[str]] = {}
    if not path.exists():
        return projects, clusters

    for encoding in ["utf-8", "latin-1", "cp1252"]:
        try:
            with path.open("r", encoding=encoding) as f:
                reader = csv.DictReader(f, delimiter=";")
                for row in reader:
                    name = (row.get("project_name") or "").strip()
                    cluster = (row.get("portfolio_cluster") or "").strip()
                    status_str = (row.get("status") or "0").strip()
                    if not name or status_str not in ("1", "true", "True"):
                        continue
                    projects.append(name)
                    if cluster:
                        clusters.setdefault(cluster, []).append(name)
            break
        except UnicodeDecodeError:
            continue
    return projects, clusters


# ------------------------------ text/alias utilities ------------------------------

LATIN_EXT = r"A-Za-z0-9'’_\-\s\.+À-ÖØ-öø-ÿ"

def _fold_accents(s: str) -> str:
    """Accent-insensitive folding (NFKD + remove diacritics)."""
    s = unicodedata.normalize("NFKD", s)
    return "".join(ch for ch in s if not unicodedata.combining(ch))

def _norm(s: str) -> str:
    """Normalize string for comparison."""
    s0 = _fold_accents(s).lower()
    s0 = re.sub(r'[_\-]+', ' ', s0)
    s0 = re.sub(r'\s+', ' ', s0).strip()
    return s0

def _alias_variants(name: str) -> Set[str]:
    """Generate alias variants without hardcoding lists."""
    base = name.strip()
    if not base:
        return set()
    v = {
        base,
        base.replace('_', ' '),
        base.replace('_', '-'),
        base.replace('-', ' '),
        base.replace('-', '_'),
        re.sub(r'\s+', ' ', base),
        re.sub(r'([A-Za-z])\s+(\d)', r'\1\2', base),
        re.sub(r'(\d)\s+([A-Za-z])', r'\1\2', base),
        re.sub(r'[\s_\-]+', '', base),
    }
    return {re.sub(r'\s+', ' ', x).strip() for x in v if x}

def _compile_alias_regex(aliases: Iterable[str]) -> List[re.Pattern]:
    """Chunked boundary-aware regexes over normalized/folded text."""
    alias_list = sorted({a for a in (_norm(x) for x in aliases) if a and len(a) >= 3}, key=len, reverse=True)

    def to_pat(a: str) -> str:
        parts = [re.escape(p) for p in a.split(' ') if p]
        if not parts:
            return ''
        return r'\b' + r'[ _\-]+'.join(parts) + r'\b'

    pats = [to_pat(a) for a in alias_list if to_pat(a)]
    CHUNK = 1200
    compiled = []
    for i in range(0, len(pats), CHUNK):
        sub = pats[i:i+CHUNK]
        if sub:
            compiled.append(re.compile('(?:' + '|'.join(sub) + ')', flags=re.IGNORECASE))
    return compiled


# ------------------------------ mention detection ------------------------------

def _find_alias_mentions(full_text: str,
                         project_names: List[str],
                         cluster_to_projects: Dict[str, List[str]]
                         ) -> Tuple[List[Tuple[int, str, List[str], str]], List[str]]:
    """
    Returns:
      mentions: [(pos, raw_slice, [canonical_projects], kind)] kind in {"project","cluster"}
      debug_unmatched: raw alias slices that could not be mapped confidently
    """
    project_aliases = set()
    for pname in project_names:
        project_aliases |= _alias_variants(pname)

    cluster_aliases = set()
    for cluster in cluster_to_projects.keys():
        cluster_aliases |= _alias_variants(cluster)

    text_fold = _fold_accents(full_text).lower()
    mentions: List[Tuple[int, str, List[str], str]] = []
    debug_unmatched: List[str] = []

    # Projects
    for rx in _compile_alias_regex(project_aliases):
        for m in rx.finditer(text_fold):
            start, end = m.span()
            raw = full_text[start:end]
            best = process.extractOne(raw, project_names, scorer=fuzz.token_set_ratio)
            if best and best[1] >= 90:
                mentions.append((start, raw, [best[0]], "project"))
            else:
                debug_unmatched.append(raw)

    # Clusters (expand to all projects)
    cluster_list = list(cluster_to_projects.keys())
    for rx in _compile_alias_regex(cluster_aliases):
        for m in rx.finditer(text_fold):
            start, end = m.span()
            raw = full_text[start:end]
            best = process.extractOne(raw, cluster_list, scorer=fuzz.token_set_ratio)
            if best and best[1] >= 88:
                expanded = cluster_to_projects.get(best[0], [])
                if expanded:
                    mentions.append((start, raw, list(expanded), "cluster"))
            else:
                debug_unmatched.append(raw)

    return mentions, debug_unmatched

def _find_generic_pattern_mentions(full_text: str,
                                   project_names: List[str],
                                   cluster_to_projects: Dict[str, List[str]],
                                   fuzzy_threshold_project: int = 86,
                                   fuzzy_threshold_cluster: int = 84
                                   ) -> Tuple[List[Tuple[int, str, List[str], str]], List[Tuple[str, int, int]]]:
    """
    Generic patterns like:
      "(Country) Name 105MW", "Name (65 MW)", "Name 95.88 MW", "Name 62.5MWp"
      "(Country) Name (Details)", "(Country) Name (capacity details)"
    Returns:
      mentions: [(pos, doc_name, [canonical_projects], kind)]
      low_conf: [(doc_name, start_pos, best_project_score)]
    """
    name_token = rf"[{LATIN_EXT}]+?"
    cap = r"(?:\d+(?:[.,]\d+)?\s*(?:MWp?|MVA|MWh(?:/\d+h)?))"
    re_country = re.compile(rf"\((?:[^)]+)\)\s*({name_token})\s+{cap}", re.IGNORECASE)
    re_paren_cap = re.compile(rf"({name_token})\s*\(\s*{cap}\s*\)", re.IGNORECASE)
    re_inline_cap = re.compile(rf"({name_token})\s+{cap}", re.IGNORECASE)
    # New pattern for (Country) Name (Details) format
    re_country_paren = re.compile(rf"\((?:[^)]+)\)\s*({name_token})\s*\((?:[^)]+)\)", re.IGNORECASE)

    mentions: List[Tuple[int, str, List[str], str]] = []
    low_conf: List[Tuple[str, int, int]] = []

    cluster_list = list(cluster_to_projects.keys())

    def try_accept(doc_name: str, start_pos: int):
        s = doc_name.strip(" _-:;,.()").strip()
        if len(s) < 3:
            return
        best_p = process.extractOne(s, project_names, scorer=fuzz.token_set_ratio)
        if best_p and best_p[1] >= fuzzy_threshold_project:
            mentions.append((start_pos, s, [best_p[0]], "project"))
            return
        best_c = process.extractOne(s, cluster_list, scorer=fuzz.token_set_ratio)
        if best_c and best_c[1] >= fuzzy_threshold_cluster:
            expanded = cluster_to_projects.get(best_c[0], [])
            if expanded:
                mentions.append((start_pos, s, list(expanded), "cluster"))
                return
        low_conf.append((s, start_pos, (best_p[1] if best_p else 0)))

    for rx in (re_country, re_paren_cap, re_inline_cap, re_country_paren):
        for m in rx.finditer(full_text):
            try_accept(m.group(1), m.start(1))

    return mentions, low_conf

def _dedupe_and_pack(mentions: List[Tuple[int, str, List[str], str]]) -> List[Tuple[int, List[str]]]:
    """
    Deduplicate and return [(pos, [canonical_project_names])]
    (We keep only canonical names and positions for sectioning.)
    """
    # expand to (pos, proj)
    expanded: List[Tuple[int, str]] = []
    for pos, _raw, projs, _kind in mentions:
        expanded.extend((pos, p) for p in projs)

    # dedupe by (pos, project) while preserving order
    seen = set()
    pos_to_projects: Dict[int, List[str]] = {}
    for pos, proj in sorted(expanded, key=lambda x: (x[0], x[1].lower())):
        key = (pos, proj.lower())
        if key in seen:
            continue
        seen.add(key)
        pos_to_projects.setdefault(pos, [])
        if proj not in pos_to_projects[pos]:
            pos_to_projects[pos].append(proj)

    return sorted(pos_to_projects.items(), key=lambda x: x[0])


def _extract_sections_with_near_merge(full_text: str,
                                      pos_to_projects: List[Tuple[int, List[str]]],
                                      min_gap: int = 80) -> List[Tuple[int, int, str]]:
    """
    Build sections using near-boundary merging.
    Returns: [(start_pos, end_pos, canonical_project_name)] duplicated per project.
    """
    boundaries = [p for p, _ in pos_to_projects]
    sections: List[Tuple[int, int, str]] = []
    i = 0
    n = len(boundaries)
    L = len(full_text)

    while i < n:
        start = boundaries[i]
        end_next = boundaries[i + 1] if (i + 1) < n else L
        projs_here = pos_to_projects[i][1]

        if (i + 1) < n and (end_next - start) < min_gap:
            # merge to third boundary
            end = boundaries[i + 2] if (i + 2) < n else L
            # include both i and i+1 projects
            merged_projects = list(dict.fromkeys(projs_here + pos_to_projects[i + 1][1]))
            text_slice = full_text[start:end].strip()
            if text_slice:
                for p in merged_projects:
                    sections.append((start, end, p))
            i += 2
        else:
            end = end_next
            text_slice = full_text[start:end].strip()
            if text_slice:
                for p in projs_here:
                    sections.append((start, end, p))
            i += 1

    return sections


# ------------------------------ main parser (unchanged signature/output) ------------------------------

def parse_docx_rows(file: UploadFile, cw_label: str, category: str) -> list[dict]:
    """
    Enhanced project-aware parser that identifies project sections and aggregates text by project.
    Signature & return type unchanged. Adds 'source_text' (same as 'summary') to each row.
    """
    rows: list[dict] = []

    # Attempt to read DOCX
    try:
        # reset pointer if needed
        try:
            file.file.seek(0)
        except Exception:
            pass
        document = Document(file.file)
    except Exception as e:
        logger.warning(f"DOCX parsing failed: {e}")
        rows.append({
            "category": category,
            "entry_type": "Report",
            "cw_label": cw_label,
            "title": None,
            "summary": "",
            "source_text": "",
            "next_actions": None,
            "owner": None,
            "attachment_url": None,
        })
        return rows

    # Build knowledge base (projects + clusters)
    project_names, cluster_to_projects = _load_kb_from_csv()
    if not project_names:
        logger.warning("No active projects loaded from CSV; falling back to raw summary.")
    project_set = set(project_names)

    # Collect plain text lines from paragraphs and tables
    all_lines: list[str] = []
    for p in document.paragraphs:
        t = (p.text or "").strip()
        if t:
            all_lines.append(t)
    for table in document.tables:
        for row in table.rows:
            cells = [(cell.text or "").strip() for cell in row.cells]
            cells = [c for c in cells if c]
            if cells:
                all_lines.append(" | ".join(cells))

    if not all_lines:
        rows.append({
            "category": category,
            "entry_type": "Report",
            "cw_label": cw_label,
            "title": None,
            "summary": "",
            "source_text": "",
            "next_actions": None,
            "owner": None,
            "attachment_url": None,
        })
        return rows

    full_text = "\n".join(all_lines)

    # (1) Mentions via alias matching
    alias_mentions, alias_unmatched = _find_alias_mentions(full_text, project_names, cluster_to_projects)

    # (2) Mentions via generic capacity patterns
    generic_mentions, low_conf = _find_generic_pattern_mentions(full_text, project_names, cluster_to_projects)

    mentions = alias_mentions + generic_mentions
    if not mentions:
        logger.info("No project-like mentions detected; emitting single summary row.")

    # Log unmatched project-like names (for troubleshooting, keeping I/O unchanged)
    if alias_unmatched or low_conf:
        logger.info(
            "Unmatched/low-confidence mentions (count=%d): %s",
            len(alias_unmatched) + len(low_conf),
            [m if isinstance(m, str) else m[0] for m in alias_unmatched + [x[0] for x in low_conf]]
        )

    # (3) Deduplicate and pack to pos->projects
    pos_to_projects = _dedupe_and_pack(mentions)

    # (4) Section extraction with near-boundary merge
    sections = _extract_sections_with_near_merge(full_text, pos_to_projects, min_gap=80)

    # (5) Build output rows
    for start, end, pname in sections:
        # Final guard: keep only names that exist in CSV (precision)
        if pname not in project_set:
            # map back using best fuzzy; discard if still not in set
            best = process.extractOne(pname, project_names, scorer=fuzz.token_set_ratio)
            if not best or best[1] < 86:
                continue
            pname = best[0]

        section_text = full_text[start:end].strip()
        if not section_text:
            continue

        rows.append({
            "category": category,
            "entry_type": "Report",
            "cw_label": cw_label,
            "title": f"{pname} - {cw_label}",
            "summary": section_text,
            "source_text": section_text,   # <-- added as requested
            "next_actions": None,
            "owner": None,
            "attachment_url": None,
        })

    # Fallback: if no section rows, emit one summary row
    if not rows:
        raw_summary = full_text.strip()
        rows.append({
            "category": category,
            "entry_type": "Report",
            "cw_label": cw_label,
            "title": None,
            "summary": raw_summary,
            "source_text": raw_summary,
            "next_actions": None,
            "owner": None,
            "attachment_url": None,
        })

    return rows


# ------------------------------ optional DB helpers (unchanged) ------------------------------

def get_project_code_by_name(project_name: str) -> Optional[str]:
    """Return project_code for a given project_name using CSV mapping (case-insensitive)."""
    if not project_name:
        return None
    name_key = project_name.strip().lower()
    mapping = load_project_name_to_code_mapping()
    return mapping.get(name_key)

def get_project_code_by_name_db(db, project_name: str) -> Optional[str]:
    """Lookup project_code by project_name in the database (status=1 only)."""
    if not project_name:
        return None
    name_key = project_name.strip().lower()
    rec = db.execute(
        text(
            """
            SELECT project_code
            FROM projects
            WHERE status = 1 AND lower(project_name) = :name
            LIMIT 1
            """
        ),
        {"name": name_key},
    ).first()
    return rec.project_code if rec else None

def seed_projects_from_csv(db, csv_path: Optional[Path] = None, created_by: str = "sys") -> int:
    """Idempotently load projects from CSV into the `projects` table (unchanged)."""
    path = csv_path or _default_project_csv_path()
    if not path.exists():
        return 0

    upserts = 0
    for encoding in ["utf-8", "latin-1", "cp1252"]:
        try:
            with path.open("r", encoding=encoding) as f:
                reader = csv.DictReader(f, delimiter=";")
                for row in reader:
                    code = (row.get("project_code") or "").strip()
                    name = (row.get("project_name") or "").strip()
                    portfolio = (row.get("portfolio_cluster") or None)
                    status_raw = (row.get("status") or "0").strip()
                    if not code or not name:
                        continue
                    status_val = 1 if status_raw in ("1", "true", "True") else 0
                    db.execute(
                        text(
                            """
                            INSERT INTO projects (
                                project_code, project_name, portfolio_cluster, status,
                                created_by, updated_by
                            ) VALUES (
                                :project_code, :project_name, :portfolio_cluster, :status,
                                :created_by, :updated_by
                            )
                            ON CONFLICT (project_code) DO UPDATE SET
                                project_name = EXCLUDED.project_name,
                                portfolio_cluster = EXCLUDED.portfolio_cluster,
                                status = EXCLUDED.status,
                                updated_by = EXCLUDED.updated_by,
                                updated_at = NOW()
                            """
                        ),
                        {
                            "project_code": code,
                            "project_name": name,
                            "portfolio_cluster": portfolio,
                            "status": status_val,
                            "created_by": created_by,
                            "updated_by": created_by,
                        },
                    )
                    upserts += 1
            break
        except UnicodeDecodeError:
            continue

    db.commit()
    return upserts
