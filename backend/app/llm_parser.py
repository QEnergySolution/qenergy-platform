from typing import List, Dict
import os
import json
import re
import logging

import httpx
from docx import Document
from pydantic import ValidationError

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


def _load_doc_text(file_path: str) -> str:
    d = Document(file_path)
    parts: List[str] = []
    for p in d.paragraphs:
        t = (p.text or "").strip()
        if t:
            parts.append(t)
    for table in d.tables:
        for row in table.rows:
            cells = [ (cell.text or "").strip() for cell in row.cells ]
            cells = [c for c in cells if c]
            if cells:
                parts.append(" | ".join(cells))
    return _clean_text("\n".join(parts).lower())


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
    
    Args:
        file_path: Path to the DOCX file
        cw_label: Calendar week label (e.g., "CW01")
        category_from_filename: Default category derived from filename
        
    Returns:
        List of validated project entry dictionaries
    """
    text = _load_doc_text(file_path)
    
    # Smart text truncation to fit within token limits
    safe_text = _safe_truncate_text(text)
    
    user_prompt = f"""Extract project entries from this weekly report document.

Context:
- Calendar week: {cw_label}
- Default category (if unclear): {category_from_filename}

Document content:
{safe_text}

Return valid JSON only with the exact structure specified in the system prompt."""
    
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT_V2},
        {"role": "user", "content": user_prompt},
    ]
    
    # Log token usage for monitoring
    total_input_tokens = sum(_estimate_tokens(msg["content"]) for msg in messages)
    logger.info(f"Processing file: {len(text)} chars -> {len(safe_text)} chars, ~{total_input_tokens} input tokens")

    # Try different JSON enforcement strategies
    strategies = [
        {"use_json_mode": True, "use_function_calling": False},
        {"use_json_mode": False, "use_function_calling": True},
        {"use_json_mode": False, "use_function_calling": False},  # Fallback to prompt-only
    ]
    
    for attempt, strategy in enumerate(strategies, 1):
        try:
            logger.debug(f"Attempt {attempt}: {strategy}")
            data = _azure_chat_completion(messages, **strategy)
            
            # Extract content based on response type
            if strategy["use_function_calling"]:
                # Function calling response format
                choice = data.get("choices", [{}])[0]
                function_call = choice.get("message", {}).get("function_call", {})
                if function_call.get("name") == "extract_project_entries":
                    content = function_call.get("arguments", "{}")
                else:
                    content = choice.get("message", {}).get("content", "")
            else:
                # Regular chat completion
                content = data.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
            
            # Try to parse and validate with Pydantic
            try:
                # Clean up potential markdown formatting
                content = re.sub(r"```json\s*", "", content)
                content = re.sub(r"\s*```", "", content)
                content = content.strip()
                
                # Parse JSON
                raw_data = json.loads(content)
                
                # Handle both array and object formats
                if isinstance(raw_data, list):
                    # Direct array format (for backward compatibility)
                    raw_data = {"rows": raw_data}
                
                # Validate with Pydantic
                response = ExtractionResponse(**raw_data)
                
                # Convert to legacy format for compatibility
                result = []
                for entry in response.rows:
                    result.append({
                        "project_name": entry.project_name,
                        "title": entry.title,
                        "summary": entry.summary,
                        "next_actions": entry.next_actions,
                        "owner": entry.owner,
                        "category": entry.category.value if entry.category else None,
                        "source_text": entry.source_text,
                    })
                
                logger.info(f"Successfully extracted {len(result)} entries using strategy {attempt}")
                return result
                
            except (json.JSONDecodeError, ValidationError) as e:
                logger.warning(f"Parsing/validation failed for attempt {attempt}: {e}")
                
                # Try manual data cleaning for validation errors
                if isinstance(e, ValidationError) and attempt < len(strategies):
                    try:
                        # Try to clean the data before validation
                        cleaned_data = _clean_raw_data_for_validation(raw_data)
                        if cleaned_data:
                            response = ExtractionResponse(**cleaned_data)
                            result = []
                            for entry in response.rows:
                                result.append({
                                    "project_name": entry.project_name,
                                    "title": entry.title,
                                    "summary": entry.summary,
                                    "next_actions": entry.next_actions,
                                    "owner": entry.owner,
                                    "category": entry.category.value if entry.category else None,
                                    "source_text": entry.source_text,
                                })
                            logger.info(f"Data cleaning succeeded: {len(result)} entries")
                            return result
                    except Exception as clean_error:
                        logger.debug(f"Data cleaning failed: {clean_error}")
                
                # Fallback: Try regex extraction for truncated or malformed responses
                if attempt == len(strategies):
                    try:
                        # First try to extract array from malformed content
                        entries = _extract_array_from_malformed_content(content)
                        if not entries:
                            # Then try complete entries from potentially truncated JSON
                            entries = _extract_complete_entries_from_partial_json(content)
                        
                        if entries:
                            # Validate each entry individually
                            result = []
                            for entry_data in entries:
                                try:
                                    entry = ProjectEntry(**entry_data)
                                    result.append({
                                        "project_name": entry.project_name,
                                        "title": entry.title,
                                        "summary": entry.summary,
                                        "next_actions": entry.next_actions,
                                        "owner": entry.owner,
                                        "category": entry.category.value if entry.category else None,
                                        "source_text": entry.source_text,
                                    })
                                except ValidationError:
                                    # Skip invalid entries
                                    continue
                            if result:
                                logger.info(f"Regex fallback succeeded: {len(result)} entries")
                                return result
                    except Exception as fallback_error:
                        logger.debug(f"Regex fallback failed: {fallback_error}")
                
                if attempt == len(strategies):
                    # Last attempt failed, log the content for debugging
                    logger.error(f"All parsing attempts failed. Last response content: {content[:500]}...")
                continue
                
        except Exception as e:
            logger.error(f"Attempt {attempt} failed with error: {e}")
            if attempt == len(strategies):
                break
            continue
    
    # All attempts failed
    logger.warning("All extraction attempts failed, returning empty list")
    return []


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