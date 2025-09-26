from typing import List, Dict
import os
import json
import re
import logging

import httpx
from docx import Document
from pydantic import ValidationError
from .utils import _load_kb_from_csv
from .database import SessionLocal
from sqlalchemy import text as _sql_text
from .schemas.llm_extraction import ExtractionResponse, ProjectEntry, SYSTEM_PROMPT_V2, EXTRACTION_FUNCTION_SCHEMA

# Set up logger
logger = logging.getLogger(__name__)


def _estimate_tokens(text: str) -> int:
    """Rough token estimation: ~4 chars per token for English"""
    return len(text) // 4


def _get_token_limits() -> dict:
    """Get token limits from environment variables with sensible defaults"""
    return {
        "max_context": int(os.getenv("AZURE_OPENAI_MAX_CONTEXT", "8000")),
        "max_input": int(os.getenv("AZURE_OPENAI_MAX_INPUT", "3500")),
        "max_output": int(os.getenv("AZURE_OPENAI_MAX_OUTPUT", "4000")),
        "safety_buffer": int(os.getenv("AZURE_OPENAI_SAFETY_BUFFER", "500"))
    }


def _safe_truncate_text(text: str, max_tokens: int = None) -> str:
    """Safely truncate text to fit within token limits while preserving word boundaries"""
    if max_tokens is None:
        max_tokens = _get_token_limits()["max_input"]
    
    estimated_chars = max_tokens * 4
    if len(text) <= estimated_chars:
        return text
    
    # Truncate and find last complete sentence or paragraph
    truncated = text[:estimated_chars]
    
    # Try to end at paragraph break
    last_para = truncated.rfind('\n\n')
    if last_para > estimated_chars * 0.7:  # Keep if we don't lose too much
        return truncated[:last_para]
    
    # Try to end at sentence
    last_sentence = max(truncated.rfind('.'), truncated.rfind('!'), truncated.rfind('?'))
    if last_sentence > estimated_chars * 0.7:
        return truncated[:last_sentence + 1]
    
    # Fallback: end at word boundary
    last_space = truncated.rfind(' ')
    if last_space > 0:
        return truncated[:last_space]
    
    return truncated


def _clean_text(s: str) -> str:
    s = s.replace("\r", "\n")
    s = re.sub(r"\n+", "\n", s)
    return s.strip()


from typing import Iterator, Union

from docx.document import Document as _Document
from docx.table import _Cell, Table
from docx.text.paragraph import Paragraph
from docx.oxml.table import CT_Tbl
from docx.oxml.text.paragraph import CT_P

# Import header/footer types for robust iteration (python-docx internals)
try:  # pragma: no cover - type imports
    from docx.section import _Header as HeaderType  # noqa: N812
    from docx.section import _Footer as FooterType  # noqa: N812
except Exception:  # pragma: no cover
    HeaderType = None  # type: ignore
    FooterType = None  # type: ignore


try:
    from docx.header import Header as HeaderType  # type: ignore
except Exception:
    HeaderType = None  # type: ignore

try:
    from docx.footer import Footer as FooterType  # type: ignore
except Exception:
    FooterType = None  # type: ignore


def iter_block_items(parent: Union[_Document, _Cell, object]) -> Iterator[Union[Paragraph, Table]]:
    """
    Yield block-level items (Paragraph or Table) from a parent element while
    preserving the original document order. Supports Document body, table Cell,
    and header/footer (paragraph-only).
    """
    # Header/Footer: yield paragraphs when available
    if not isinstance(parent, (_Document, _Cell)):
        for p in getattr(parent, "paragraphs", []):
            yield p
        return

    # Determine XML container
    if isinstance(parent, _Document):
        parent_elm = parent.element.body
    else:  # _Cell
        parent_elm = parent._tc

    # Walk children in document order
    for child in parent_elm.iterchildren():
        if isinstance(child, CT_P):
            yield Paragraph(child, parent)
        elif isinstance(child, CT_Tbl):
            yield Table(child, parent)


def _is_list_like(par: Paragraph) -> bool:
    """
    Heuristic: treat the paragraph as a list item if it uses numbering (numPr)
    or its style name suggests a list/bullet.
    """
    # numPr detection (robust even if pPr is missing)
    try:
        pPr = par._p.pPr  # noqa: SLF001
        if pPr is not None and pPr.numPr is not None:
            return True
    except Exception:
        pass
    # style name hint
    try:
        name = (par.style.name or "").lower()
        if "list" in name or "bullet" in name:
            return True
    except Exception:
        pass
    return False

def _normalize_list_prefix(text: str) -> str:
    """
    Ensure a consistent '- ' prefix for list-like paragraphs, unless they
    already start with a common bullet/numbering mark.
    """
    if not text:
        return text
    leading = text.lstrip()
    # common bullet/numbering starters to avoid double-prefixing
    common_starters = ("- ", "* ", "• ", "· ", "◦ ", "– ", "— ", "1. ", "a) ", "(1) ")
    if any(leading.startswith(s) for s in common_starters):
        return text
    return "- " + text

def _collect_paragraph_texts(container) -> List[str]:
    """
    Collect non-empty paragraph texts from a container (Document/header/footer),
    preserving order and skipping tables.
    """
    parts: List[str] = []
    # Handle headers/footers directly if possible
    try:
        from docx.section import _Header as HeaderType  # type: ignore
        from docx.section import _Footer as FooterType  # type: ignore
        if isinstance(container, HeaderType) or isinstance(container, FooterType):
            for p in container.paragraphs:
                t = (p.text or "").strip()
                if t:
                    if _is_list_like(p):
                        t = _normalize_list_prefix(t)
                    parts.append(t)
            return parts
    except Exception:
        pass
    for block in iter_block_items(container):
        if isinstance(block, Paragraph):
            t = (block.text or "").strip()
            if t:
                if _is_list_like(block):
                    t = _normalize_list_prefix(t)
                parts.append(t)
    return parts

def _load_doc_text(file_path: str) -> str:
    """
    Load visible paragraph text from a .docx file, skipping tables,
    preserving order, normalizing list items, and returning a single
    lower-cased string cleaned by _clean_text (same I/O contract as original).
    """
    d = Document(file_path)
    parts: List[str] = []

    # Walk blocks to include paragraphs and tables in order
    for block in iter_block_items(d):
        if isinstance(block, Paragraph):
            raw_text = block.text or ""
            t = raw_text.strip()
            if t:
                if _is_list_like(block):
                    t = _normalize_list_prefix(t)
                parts.append(t)
            else:
                # Preserve blank paragraph as boundary
                parts.append("")
        else:
            try:
                # Table: join each row's non-empty cells with ' | '
                from docx.table import Table as _Table
                if isinstance(block, _Table):
                    for row in block.rows:
                        cells = [(cell.text or "").strip() for cell in row.cells]
                        cells = [c for c in cells if c]
                        if cells:
                            parts.append(" | ".join(cells))
            except Exception:
                pass

    # headers/footers (optional but useful; still skipping tables)
    for section in d.sections:
        for hf in (section.header, section.footer):
            if hf is not None:
                parts.extend(_collect_paragraph_texts(hf))

    # Keep original casing; join with '\n' and preserve blank boundaries
    out = "\n".join(parts).replace("\r", "\n")
    return out.strip()


def _split_into_sections(text: str, *, max_chars: int = 6000) -> List[str]:
    """Split cleaned text into sections using strong boundaries and length limits.

    Boundaries:
    - Country label lines like "(Spain)" at the start of a line
    - FULL UPPERCASE headings (length >= 4)
    - Blank line blocks
    """
    if not text:
        return []

    lines = text.split("\n")
    sections: List[str] = []
    current: List[str] = []

    def push_current():
        if current:
            blob = _clean_text("\n".join(current))
            if blob:
                # enforce max length by further chunking if needed
                if len(blob) <= max_chars:
                    sections.append(blob)
                else:
                    for i in range(0, len(blob), max_chars):
                        sections.append(blob[i:i+max_chars])
        current.clear()

    country_re = re.compile(r"^\([^)]+\)\s+", re.IGNORECASE)

    # Pre-scan for any strong boundaries; if none, keep as a single section to
    # preserve legacy behavior for token-limit tests.
    has_boundary = False
    for raw in lines:
        line = (raw or "").rstrip()
        if not line:
            continue
        if bool(country_re.match(line)) or (line.isupper() and len(line) >= 4):
            has_boundary = True
            break

    for raw in lines:
        line = (raw or "").rstrip()
        is_upper = line.isupper() and len(line) >= 4
        is_country = bool(country_re.match(line))
        is_blank = len(line.strip()) == 0

        if is_country or is_upper:
            if current:
                push_current()
            current = [line]
            continue
        if is_blank:
            push_current()
            current = []
            continue
        current.append(line)

    if has_boundary:
        push_current()
        return sections
    else:
        # No strong boundaries; return as a single section
        solo = _clean_text("\n".join(lines))
        return [solo] if solo else []


def _augment_user_prompt(
    base_prompt: str,
    *,
    cw_label: str,
    default_category: str,
    whitelist_projects: List[str],
    whitelist_clusters: List[str] | None = None,
    cluster_members: Dict[str, List[str]] | None = None,
) -> str:
    """Append stricter extraction rules to the user prompt without changing the system prompt itself."""
    limits = _get_token_limits()
    # Default verbose rules
    rules = [
        "Rules for extraction:",
        "- Only return rows for names present in the whitelist.",
        "- If a whitelist name is not actually mentioned in the text, do not output it.",
        "- When multiple projects are mentioned in a section, such as \"Divor PV1+2\", split into multiple entries (do not merge).",
        "- source_text must include the sentences from the document that mention the project or the cluster; do not invent text.",
        "- summary must be factual (<= 1000 chars).",
        "- Use the exact provided calendar week and default category when unclear.",
    ]
    # Compress rules for very small input limits to keep message short
    if limits.get("max_input", 3500) <= 120:
        rules = [
            "Rules:",
            "- Split per project; no merging.",
            "- source_text: include 1+ original sentence.",
            "- summary <= 1000 chars; no hallucinations.",
        ]
    if whitelist_projects:
        sample = ", ".join(sorted(whitelist_projects))
        rules.append("- Allowed project names (strict whitelist): " + sample)
    if whitelist_clusters:
        rules.append("- Allowed clusters (strict whitelist): " + ", ".join(sorted(whitelist_clusters)))
    if cluster_members:
        # Include cluster expansions for LLM awareness
        lines: List[str] = ["- Cluster members mapping (if only a cluster is mentioned, create one row for EACH member project):"]
        for cname, members in sorted(cluster_members.items()):
            if not members:
                continue
            sample_members = ", ".join(sorted(members))
            lines.append(f"  - {cname}: [{sample_members}]")
        rules.extend(lines)

    return f"{base_prompt}\n\nAdditional context:\n- Calendar week: {cw_label}\n- Default category (if unclear): {default_category}\n\n" + "\n".join(rules)


def _extract_rows_from_text_core(
    text: str,
    cw_label: str,
    category_from_filename: str,
    *,
    whitelist_projects: List[str],
    whitelist_clusters: List[str] | None = None,
    cluster_members: Dict[str, List[str]] | None = None,
) -> List[Dict]:
    safe_text = _safe_truncate_text(text)
    limits = _get_token_limits()
    enforce_whitelist = _is_whitelist_enabled()
    if limits.get("max_input", 3500) <= 120:
        # Extremely compact prompt for tiny input budgets
        user_prompt = f"{safe_text}\nReturn JSON object per system schema."
        user_prompt = _augment_user_prompt(
            user_prompt,
            cw_label=cw_label,
            default_category=category_from_filename,
            # Always include provided lists in prompt; actual filtering is gated elsewhere
            whitelist_projects=whitelist_projects or [],
            whitelist_clusters=whitelist_clusters or None,
            cluster_members=cluster_members or None,
        )
    else:
        user_prompt = f"""Extract project entries from this weekly report document section.\n\nDocument section:\n{safe_text}\n\nReturn valid JSON only with the exact structure specified in the system prompt."""
        user_prompt = _augment_user_prompt(
            user_prompt,
            cw_label=cw_label,
            default_category=category_from_filename,
            whitelist_projects=whitelist_projects or [],
            whitelist_clusters=whitelist_clusters or None,
            cluster_members=cluster_members or None,
        )

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT_V2},
        {"role": "user", "content": user_prompt},
    ]

    total_input_tokens = sum(_estimate_tokens(msg["content"]) for msg in messages)
    logger.info(f"Processing section: {len(text)} chars -> {len(safe_text)} chars, ~{total_input_tokens} input tokens")

    strategies = [
        {"use_json_mode": True, "use_function_calling": False},
        {"use_json_mode": False, "use_function_calling": True},
        {"use_json_mode": False, "use_function_calling": False},
    ]

    for attempt, strategy in enumerate(strategies, 1):
        try:
            logger.debug(f"Attempt {attempt}: {strategy}")
            data = _azure_chat_completion(messages, **strategy)

            if strategy["use_function_calling"]:
                choice = data.get("choices", [{}])[0]
                function_call = choice.get("message", {}).get("function_call", {})
                if function_call.get("name") == "extract_project_entries":
                    content = function_call.get("arguments", "{}")
                else:
                    content = choice.get("message", {}).get("content", "")
            else:
                content = data.get("choices", [{}])[0].get("message", {}).get("content", "").strip()

            try:
                content = re.sub(r"```json\s*", "", content)
                content = re.sub(r"\s*```", "", content)
                content = content.strip()
                raw_data = json.loads(content)
                if isinstance(raw_data, list):
                    raw_data = {"rows": raw_data}
                # Optional whitelist post-filtering (LLM guardrail)
                def _filter_rows(data_rows: List[dict]) -> List[dict]:
                    # Collect allowed names from prompt context if provided in messages
                    # In our construction, we pass whitelist via prompt narrative; at runtime we filter against that list we closed over.
                    allowed_projects = set(n.lower() for n in (whitelist_projects or []))
                    # When clusters were provided, we also allow any member project from cluster_members
                    if cluster_members:
                        for _c, members in cluster_members.items():
                            for m in members:
                                allowed_projects.add(m.lower())
                    if not allowed_projects:
                        return data_rows  # No whitelist -> no filtering
                    out: List[dict] = []
                    seen: set[tuple[str, str, str]] = set()
                    for item in data_rows:
                        try:
                            pname = (item.get("project_name") or "").strip()
                            if pname.lower() not in allowed_projects:
                                continue
                            # dedupe by (project_name + first 8 chars of summary + category)
                            k = (pname.lower(), (item.get("summary") or "")[:8].lower(), (item.get("category") or "").lower())
                            if k in seen:
                                continue
                            seen.add(k)
                            out.append(item)
                        except Exception:
                            continue
                    return out

                # Apply filter before validation only when enforcement is enabled
                if _is_whitelist_enabled() and "rows" in raw_data and isinstance(raw_data["rows"], list):
                    raw_data["rows"] = _filter_rows(raw_data["rows"])

                response = ExtractionResponse(**raw_data)
                result: List[Dict] = []
                for entry in response.rows:
                    summary = entry.summary[:1000]
                    # For source_text: only fallback when provided but too short; if missing, keep None
                    fallback_section = text.strip()
                    provided_raw = entry.source_text
                    provided = (provided_raw or "").strip()
                    if provided_raw is None:
                        source_text = None
                    else:
                        source_text = provided if len(provided) >= 80 else fallback_section
                    result.append({
                        "project_name": entry.project_name,
                        "title": entry.title,
                        "summary": summary,
                        "next_actions": entry.next_actions,
                        "owner": entry.owner,
                        "category": _normalize_category(entry.category.value if entry.category else None),
                        "source_text": source_text,
                    })
                logger.info(f"Section extracted {len(result)} entries using strategy {attempt}")
                return result
            except (json.JSONDecodeError, ValidationError) as e:
                logger.warning(f"Parsing/validation failed for attempt {attempt}: {e}")
                if isinstance(e, ValidationError) and attempt < len(strategies):
                    try:
                        cleaned_data = _clean_raw_data_for_validation(raw_data)
                        if cleaned_data:
                            response = ExtractionResponse(**cleaned_data)
                            result: List[Dict] = []
                            for entry in response.rows:
                                summary = entry.summary[:1000]
                                fallback_section = text.strip()
                                provided_raw = entry.source_text
                                provided = (provided_raw or "").strip()
                                if provided_raw is None:
                                    source_text = None
                                else:
                                    source_text = provided if len(provided) >= 80 else fallback_section
                                result.append({
                                    "project_name": entry.project_name,
                                    "title": entry.title,
                                    "summary": summary,
                                    "next_actions": entry.next_actions,
                                    "owner": entry.owner,
                                    "category": entry.category.value if entry.category else None,
                                    "source_text": source_text,
                                })
                            logger.info(f"Data cleaning succeeded: {len(result)} entries")
                            return result
                    except Exception as clean_error:
                        logger.debug(f"Data cleaning failed: {clean_error}")

                if attempt == len(strategies):
                    try:
                        entries = _extract_array_from_malformed_content(content)
                        if not entries:
                            entries = _extract_complete_entries_from_partial_json(content)
                        if entries:
                            result: List[Dict] = []
                            for entry_data in entries:
                                try:
                                    entry = ProjectEntry(**entry_data)
                                    summary = entry.summary[:1000]
                                    fallback_section = text.strip()
                                    provided_raw = entry.source_text
                                    provided = (provided_raw or "").strip()
                                    if provided_raw is None:
                                        source_text = None
                                    else:
                                        source_text = provided if len(provided) >= 80 else fallback_section
                                    result.append({
                                        "project_name": entry.project_name,
                                        "title": entry.title,
                                        "summary": summary,
                                        "next_actions": entry.next_actions,
                                        "owner": entry.owner,
                                        "category": entry.category.value if entry.category else None,
                                        "source_text": source_text,
                                    })
                                except ValidationError:
                                    continue
                            if result:
                                logger.info(f"Regex fallback succeeded: {len(result)} entries")
                                return result
                    except Exception as fallback_error:
                        logger.debug(f"Regex fallback failed: {fallback_error}")
                if attempt == len(strategies):
                    logger.error(f"All parsing attempts failed. Last response content: {content[:500]}...")
                continue
        except Exception as e:
            logger.error(f"Attempt {attempt} failed with error: {e}")
            if attempt == len(strategies):
                break
            continue

    logger.warning("All extraction attempts failed for section, returning empty list")
    return []



def _azure_chat_completion(
    messages: list[dict], 
    temperature: float = 0.2, 
    max_tokens: int = None,
    use_json_mode: bool = True,
    use_function_calling: bool = False
) -> dict:
    api_key = os.getenv("AZURE_OPENAI_API_KEY")
    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT")
    api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview")
    if not (api_key and endpoint and deployment):
        raise RuntimeError("Azure OpenAI env vars missing")
    url = f"{endpoint.rstrip('/')}/openai/deployments/{deployment}/chat/completions?api-version={api_version}"
    headers = {"Content-Type": "application/json", "api-key": api_key}
    
    # Calculate smart max_tokens based on input length if not specified
    if max_tokens is None:
        limits = _get_token_limits()
        input_tokens = sum(_estimate_tokens(msg["content"]) for msg in messages)
        
        # Calculate available tokens for response
        available_tokens = limits["max_context"] - input_tokens - limits["safety_buffer"]
        max_tokens = min(max(available_tokens, 1000), limits["max_output"])
        
        logger.info(f"Token allocation: input={input_tokens}, max_output={max_tokens}, context_limit={limits['max_context']}")
    
    # Build payload with JSON format control
    payload = {
        "messages": messages, 
        "temperature": temperature, 
        "max_tokens": max_tokens
    }
    
    # Add JSON format enforcement if supported by deployment
    if use_json_mode and not use_function_calling:
        # For models that support response_format
        payload["response_format"] = {"type": "json_object"}
        logger.debug("Using JSON response format enforcement")
    elif use_function_calling:
        # Alternative: Use function calling for strict schema enforcement
        payload["functions"] = [EXTRACTION_FUNCTION_SCHEMA]
        payload["function_call"] = {"name": "extract_project_entries"}
        logger.debug("Using function calling for schema enforcement")
    
    with httpx.Client(timeout=60) as client:
        resp = client.post(url, headers=headers, json=payload)
        resp.raise_for_status()
        return resp.json()


def extract_rows_from_docx(file_path: str, cw_label: str, category_from_filename: str) -> List[Dict]:
    """
    Extract project entries from a DOCX file using LLM with strict JSON schema validation.
    Now processes the document in sections for better recall and accuracy.
    """
    full_text = _load_doc_text(file_path)
    sections = _split_into_sections(full_text)
    if not sections:
        sections = [full_text]

    # Load DB-driven knowledge base (projects and clusters)
    project_names_kb, cluster_to_projects = _load_db_kb()
    whitelist_enabled = _is_whitelist_enabled()
    chunk_all = (os.getenv("LLM_DB_WHITELIST_CHUNK_ALL") or "0").strip().lower() in {"1","true","on","yes"}

    all_rows: List[Dict] = []
    for idx, section in enumerate(sections, 1):
        logger.debug(f"Invoking LLM for section {idx}/{len(sections)} (len={len(section)})")
        # Always run detection for potential fallback logic
        det_projects, det_clusters = _detect_whitelist_candidates(section, project_names_kb, cluster_to_projects, threshold=60)
        detection_based = bool(det_projects or det_clusters)
        # Build candidate lists actually passed to LLM
        if whitelist_enabled:
            detected_projects = det_projects
            detected_clusters = det_clusters
        else:
            # Whitelist disabled: include all as candidates, but optionally only the first chunk
            detected_projects = list(project_names_kb)
            detected_clusters = list(cluster_to_projects.keys())

        # Expand cluster members map for detected clusters
        cluster_members = {c: cluster_to_projects.get(c, []) for c in detected_clusters}

        # Chunking: process up to K candidates (projects + clusters) per call
        K = 30
        section_rows_added = False
        if detected_projects or detected_clusters:
            combined = detected_projects + detected_clusters
            # If whitelist disabled and not chunk_all, only send the first chunk to keep calls bounded
            chunk_ranges = [range(0, min(len(combined), K), K)] if (not whitelist_enabled and not chunk_all) else [range(i, min(i+K, len(combined)), K) for i in range(0, len(combined), K)]
            # Flatten chunk indices
            indices: List[int] = []
            for r in chunk_ranges:
                indices.extend(list(r))
            # Guard: if indices empty but we have candidates, ensure a single chunk [0:K]
            if not indices and combined:
                indices = [0]
            processed_any = False
            for start in indices:
                chunk = combined[start:start+K]
                # Split chunk back into projects and clusters
                chunk_projects = [x for x in chunk if x in project_names_kb]
                chunk_clusters = [x for x in chunk if x in cluster_to_projects]
                chunk_cluster_members = {c: cluster_to_projects.get(c, []) for c in chunk_clusters}
                rows = _extract_rows_from_text_core(
                    section,
                    cw_label,
                    category_from_filename,
                    whitelist_projects=chunk_projects,
                    whitelist_clusters=chunk_clusters,
                    cluster_members=chunk_cluster_members,
                )
                if rows:
                    all_rows.extend(rows)
                    section_rows_added = True
                    processed_any = True
            # Fallback: only when detection-based (to avoid exploding when passing all clusters)
            if detection_based and (not section_rows_added) and det_clusters:
                synth_members: List[str] = []
                for _c in det_clusters:
                    members = cluster_to_projects.get(_c, [])
                    synth_members.extend(members)
                # Deduplicate while preserving order
                seen = set()
                uniq_members: List[str] = []
                for m in synth_members:
                    k = m.lower()
                    if k in seen:
                        continue
                    seen.add(k)
                    uniq_members.append(m)
                # Use section text as summary/source_text
                section_text = section.strip()
                for pname in uniq_members:
                    all_rows.append({
                        "project_name": pname,
                        "title": f"{pname} - {cw_label}",
                        "summary": section_text[:1000],
                        "next_actions": None,
                        "owner": None,
                        "category": category_from_filename,
                        "source_text": section_text,
                    })
        else:
            # Nothing detected -> call LLM without whitelist when feature flag is off
            rows = _extract_rows_from_text_core(
                section,
                cw_label,
                category_from_filename,
                whitelist_projects=[],
                whitelist_clusters=None,
                cluster_members=None,
            )
            if rows:
                all_rows.extend(rows)
    return _postprocess_and_expand_entries(all_rows, project_names_kb)


def extract_rows_from_docx_single_pass(file_path: str, cw_label: str, category_from_filename: str) -> List[Dict]:
    """
    Legacy-style single-pass extraction (no section splitting) to enable
    before/after comparison against the new sectioned pipeline.
    """
    full_text = _load_doc_text(file_path)
    whitelist_projects: List[str] = []
    return _extract_rows_from_text_core(full_text, cw_label, category_from_filename, whitelist_projects=whitelist_projects)


def _clean_raw_data_for_validation(raw_data: Dict) -> Dict:
    """Clean raw data to make it compatible with Pydantic validation"""
    try:
        if isinstance(raw_data, list):
            raw_data = {"rows": raw_data}
        
        if "rows" in raw_data and isinstance(raw_data["rows"], list):
            cleaned_rows = []
            for item in raw_data["rows"]:
                # Only keep dictionary items that look like valid entries
                if isinstance(item, dict) and "project_name" in item:
                    cleaned_rows.append(item)
            
            if cleaned_rows:
                return {"rows": cleaned_rows}
    except Exception:
        pass
    
    return {}


def _extract_array_from_malformed_content(content: str) -> List[Dict]:
    """Extract JSON array from content that may have text before/after"""
    try:
        # Look for JSON array pattern
        array_match = re.search(r'\[.*?\]', content, re.S)
        if array_match:
            array_content = array_match.group(0)
            parsed = json.loads(array_content)
            if isinstance(parsed, list):
                return [item for item in parsed if isinstance(item, dict)]
    except Exception:
        pass
    
    return []


def _extract_complete_entries_from_partial_json(content: str) -> List[Dict]:
    """Extract complete JSON entries from potentially truncated response"""
    try:
        # Look for "rows": [ pattern and try to extract complete entries
        rows_match = re.search(r'"rows"\s*:\s*\[(.*)', content, re.S)
        if rows_match:
            rows_content = rows_match.group(1)
            
            # Try to extract complete JSON objects until we hit truncation
            complete_entries = []
            # Split by }, { pattern to get individual entries
            entries = re.split(r'\}\s*,\s*\{', rows_content)
            
            for i, entry in enumerate(entries):
                # Add back the braces that were split
                if i == 0:
                    entry_json = "{" + entry
                elif i == len(entries) - 1:
                    entry_json = "{" + entry
                else:
                    entry_json = "{" + entry + "}"
                
                # Ensure the entry ends properly
                if not entry_json.rstrip().endswith('}'):
                    continue  # Skip incomplete entries
                
                try:
                    parsed_entry = json.loads(entry_json)
                    complete_entries.append(parsed_entry)
                except json.JSONDecodeError:
                    # Skip malformed entries
                    continue
            
            return complete_entries
    except Exception:
        pass
    
    return []



# ------------------------------ LLM parser utilities ------------------------------
def _normalize_project_name(raw: str) -> str:
    s = (raw or "").strip()
    if not s:
        return s
    # Remove country prefix (Spain) / (Portugal) / ...
    s = re.sub(r"^\([^)]+\)\s+", "", s)
    # Remove capacity unit suffix
    s = re.sub(r"\b\d+(?:[.,]\d+)?\s*(?:MWp?|MVA|MWh(?:/\d+h)?|GWh)\b", "", s, flags=re.IGNORECASE)
    # Remove “details” in parentheses
    s = re.sub(r"\s*\([^)]*\)", "", s)
    # Remove obvious random uppercase/hexadecimal IDs (e.g., 153D6F0)
    s = re.sub(r"\b[A-Z0-9]{6,}\b", "", s)
    # Normalize separators
    s = re.sub(r"[_\-]+", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s

_CONJOIN_RE = re.compile(
    r"""^
        (?P<base>.+?)           # Base name (lazy)
        \s*
        (?P<prefix>PV|Wind|ESS|A|B|C|D)?  # Optional prefix
        \s*
        (?P<i1>\d+)
        (?:\s*(?:\+|&|,|/|and)\s*(?P<i2>\d+))+
        \s*$
    """, re.IGNORECASE | re.VERBOSE)

def _expand_conjoined(name: str) -> List[str]:
    """
    'Divor PV1+2' -> ['Divor PV1','Divor PV2']
    'Sisoneras 1,2 & 3' -> ['Sisoneras 1','Sisoneras 2','Sisoneras 3']
    """
    m = _CONJOIN_RE.match(name.strip())
    if not m:
        return [name]
    base = (m.group("base") or "").strip()
    prefix = (m.group("prefix") or "").strip()
    # Capture all numbers
    nums = re.findall(r"\d+", name)
    outs = []
    for n in nums:
        if prefix:
            outs.append(f"{base} {prefix}{n}".strip())
        else:
            outs.append(f"{base} {n}".strip())
    # Deduplicate while preserving order
    seen, uniq = set(), []
    for x in outs:
        if x.lower() in seen: 
            continue
        seen.add(x.lower()); uniq.append(x)
    return uniq

from rapidfuzz import process, fuzz

def _map_to_canonical(pname: str, project_names: List[str], threshold: int = 90) -> str:
    best = process.extractOne(pname, project_names, scorer=fuzz.token_set_ratio)
    return best[0] if best and best[1] >= threshold else pname

def _postprocess_and_expand_entries(rows: List[Dict], project_names: List[str]) -> List[Dict]:
    out: List[Dict] = []
    for r in rows:
        raw = r.get("project_name") or ""
        base = _normalize_project_name(raw)
        # Prioritize splitting conjoined names
        candidates = []
        for n in _expand_conjoined(base):
            n2 = _normalize_project_name(n)
            n3 = _map_to_canonical(n2, project_names, threshold=90)
            candidates.append(n3)

        # Each split project becomes a separate entry
        for i, pname in enumerate(candidates):
            rr = dict(r)
            rr["project_name"] = pname
            # When splitting, supplement title if needed: avoid LLM not splitting
            if i > 0 and rr.get("title"):
                rr["title"] = re.sub(re.escape(raw), pname, rr["title"])
            out.append(rr)

    # Simple deduplication: name+title+summary first 200 chars + source_text first 200 chars
    seen, uniq = set(), []
    for r in out:
        k = (
            re.sub(r"\s+", " ", (r.get("project_name") or "").strip().lower()),
            re.sub(r"\s+", " ", (r.get("title") or "").strip().lower()),
            re.sub(r"\s+", " ", (r.get("summary") or "")[:200].strip().lower()),
            re.sub(r"\s+", " ", (r.get("source_text") or "")[:200].strip().lower()),
        )
        if k in seen: 
            continue
        seen.add(k); uniq.append(r)
    return uniq


# ------------------------------ DB-driven KB and whitelist ------------------------------
def _load_db_kb() -> tuple[List[str], Dict[str, List[str]]]:
    """Load active project names and cluster->projects mapping from DB."""
    try:
        db = SessionLocal()
        rows = db.execute(
            _sql_text(
                """
                SELECT project_name, portfolio_cluster
                FROM projects
                WHERE status = 1
                """
            )
        ).all()
        project_names: List[str] = []
        cluster_to_projects: Dict[str, List[str]] = {}
        for r in rows:
            name = (r.project_name or "").strip()
            cluster = (r.portfolio_cluster or "").strip()
            if not name:
                continue
            project_names.append(name)
            if cluster:
                cluster_to_projects.setdefault(cluster, []).append(name)
        return project_names, cluster_to_projects
    except Exception:
        # Fallback to CSV if DB not available (keeps existing behavior working in tests)
        return _load_kb_from_csv()
    finally:
        try:
            db.close()  # type: ignore[has-type]
        except Exception:
            pass


def _is_whitelist_enabled() -> bool:
    """Feature flag to enable DB-driven whitelist enforcement (default off)."""
    val = (os.getenv("LLM_DB_WHITELIST") or "0").strip().lower()
    return val in {"1", "true", "on", "yes"}


def _detect_whitelist_candidates(
    section_text: str,
    project_names: List[str],
    cluster_to_projects: Dict[str, List[str]],
    *,
    threshold: int = 60,
) -> tuple[List[str], List[str]]:
    """Return (projects_detected, clusters_detected) based on fuzzy search in the section."""
    detected_projects: List[str] = []
    detected_clusters: List[str] = []
    content = (section_text or "").strip()
    if not content:
        return detected_projects, detected_clusters
    # Evaluate fuzzy similarity between candidate name and section; use token_set_ratio
    # Guard against extremely long sections by truncating for similarity computation
    snippet = content if len(content) <= 4000 else content[:4000]
    for name in project_names:
        try:
            score = fuzz.token_set_ratio(name, snippet)
            if score >= threshold:
                detected_projects.append(name)
        except Exception:
            continue
    for cname in list(cluster_to_projects.keys()):
        try:
            score = fuzz.token_set_ratio(cname, snippet)
            if score >= threshold:
                detected_clusters.append(cname)
        except Exception:
            continue
    # Deduplicate preserving order
    seen = set()
    projects_unique = []
    for n in detected_projects:
        key = n.lower()
        if key in seen:
            continue
        seen.add(key)
        projects_unique.append(n)
    seen = set()
    clusters_unique = []
    for n in detected_clusters:
        key = n.lower()
        if key in seen:
            continue
        seen.add(key)
        clusters_unique.append(n)
    return projects_unique, clusters_unique

def _normalize_category(cat: str | None) -> str | None:
    if not cat: return None
    mapping = {
        "development": "Development",
        "epc": "EPC",
        "finance": "Finance",
        "investment": "Investment",
    }
    return mapping.get(cat.strip().lower())