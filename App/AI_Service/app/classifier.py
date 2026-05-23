"""
Case Classification Module

This module provides AI-powered classification of case intake requests using Ollama.
Supports bilingual (Arabic/English) classification with confidence scoring and fallback handling.
"""

import json
import re
import time
import uuid
from pathlib import Path
from typing import Any, Dict, Optional

import requests

# Configuration
OLLAMA_URL = "http://localhost:11434/api/generate"

# Allowed classification values - enforced during normalization
ALLOWED_CASE_TYPES = {"Administrative", "Financial", "Enforcement", "Other"}
ALLOWED_URGENCY = {"Urgent", "Normal"}
ALLOWED_UNITS = {"InitialIntake", "UrgentCasesUnit", "SpecializedReview"}
ALLOWED_LANGUAGES = {"ar", "en"}

# Default fallback response when classification fails
FALLBACK = {
    "case_type": "Other",
    "urgency": "Normal",
    "handling_unit": "InitialIntake",
    "confidence": 0.2,
    "reason": "Unable to classify automatically; needs manual review.",
    "highlights": [],
}

# Map language codes to prompt files
def get_prompt_path(lang: str) -> Path:
    """
    Get the prompt file path based on language code.
    
    Args:
        lang: Language code ('ar' or 'en')
    
    Returns:
        Path to the prompt file
        
    Raises:
        ValueError: If language is not supported
    """
    if lang not in ALLOWED_LANGUAGES:
        raise ValueError(f"Unsupported language: {lang}. Allowed: {ALLOWED_LANGUAGES}")
    
    script_dir = Path(__file__).parent.parent
    return script_dir / "Prompts" / f"{lang}_prompt.txt"

def load_prompt(prompt_path: str) -> str:
    return Path(prompt_path).read_text(encoding="utf-8").rstrip()

def build_prompt(base_prompt: str, user_text: str) -> str:
    return f"{base_prompt}\n{user_text.strip()}"

def _extract_json_block(text: str) -> Optional[str]:
    """
    If the model returns extra text, attempt to extract the first JSON object.
    """
    text = text.strip()
    # Fast path: already JSON
    if text.startswith("{") and text.endswith("}"):
        return text

    # Try to find a JSON
    match = re.search(r"\{.*\}", text, flags=re.DOTALL)
    if match:
        return match.group(0).strip()

    return None

def _normalize_result(obj: Dict[str, Any]) -> Dict[str, Any]:
    """
    Enforce allowed labels and required keys; coerce confidence into [0,1].
    """
    out = dict(FALLBACK)  # start with defaults

    # Map keys if the model uses slightly different naming
    key_map = {
        "caseType": "case_type",
        "CaseType": "case_type",
        "urgency": "urgency",
        "Urgency": "urgency",
        "handlingUnit": "handling_unit",
        "HandlingUnit": "handling_unit",
        "unit": "handling_unit",
        "confidence": "confidence",
        "reason": "reason",
        "highlights": "highlights",
    }

    normalized = {}
    for k, v in obj.items():
        nk = key_map.get(k, k)
        normalized[nk] = v

    case_type = normalized.get("case_type", out["case_type"])
    urgency = normalized.get("urgency", out["urgency"])
    unit = normalized.get("handling_unit", out["handling_unit"])

    if case_type in ALLOWED_CASE_TYPES:
        out["case_type"] = case_type
    if urgency in ALLOWED_URGENCY:
        out["urgency"] = urgency
    if unit in ALLOWED_UNITS:
        out["handling_unit"] = unit

    # Confidence
    conf = normalized.get("confidence", out["confidence"])
    try:
        conf_f = float(conf)
        out["confidence"] = max(0.0, min(1.0, conf_f))
    except Exception:
        pass

    # Reason
    reason = normalized.get("reason", out["reason"])
    if isinstance(reason, str) and reason.strip():
        out["reason"] = _clean_mixed_language(reason.strip())

    # Highlights
    highlights = normalized.get("highlights", [])
    if isinstance(highlights, list):
        out["highlights"] = [_clean_mixed_language(str(x)[:80]) for x in highlights][:5]

    return out


def _clean_mixed_language(text: str) -> str:
    """
    Remove non-Arabic/non-English characters from text to prevent language leaking.
    
    Multilingual models like Qwen sometimes mix languages (Chinese, Russian, Vietnamese, etc.)
    in their outputs. This function strips those characters while preserving Arabic and English.
    
    Args:
        text: Input text that may contain mixed languages
    
    Returns:
        Cleaned text with only Arabic, English, punctuation, and numbers
        Falls back to generic message if cleaning leaves text empty
    """
    # Define allowed Unicode ranges
    allowed_ranges = [
        (0x0600, 0x06FF),  # Arabic
        (0x0750, 0x077F),  # Arabic Supplement
        (0x0000, 0x007F),  # Basic Latin (English)
        (0x0020, 0x0020),  # Space
    ]
    
    def is_allowed(char):
        codepoint = ord(char)
        # Allow common punctuation and digits
        if char.isdigit() or char in ".,!?-()[]{}؛،؟":
            return True
        # Check if in allowed ranges
        for start, end in allowed_ranges:
            if start <= codepoint <= end:
                return True
        return False
    
    cleaned = ''.join(c if is_allowed(c) else '' for c in text)
    # Clean up multiple spaces
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    return cleaned if cleaned else "Unable to classify automatically; needs manual review."

def classify_with_ollama(
    text: str,
    lang: str = "ar",
    model: str = "qwen2.5:7b-instruct",
    temperature: float = 0.2,
    timeout_s: int = 30,
) -> Dict[str, Any]:
    """
    Classify case intake text using Ollama.
    
    Args:
        text: The case request text to classify
        lang: Language code ('ar' for Arabic, 'en' for English)
        model: Ollama model name
        temperature: Model temperature (0.0-1.0)
        timeout_s: Request timeout in seconds
    
    Returns:
        Dict with case_type, urgency, handling_unit, confidence, reason, highlights, etc.
    """
    prompt_path = get_prompt_path(lang)
    base_prompt = load_prompt(str(prompt_path))
    prompt = build_prompt(base_prompt, text)

    request_id = str(uuid.uuid4())
    start = time.perf_counter()

    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": temperature},
    }

    try:
        resp = requests.post(OLLAMA_URL, json=payload, timeout=timeout_s)
        resp.raise_for_status()
        raw = resp.json().get("response", "").strip()
    except Exception:
        latency_ms = int((time.perf_counter() - start) * 1000)
        out = dict(FALLBACK)
        out.update({"request_id": request_id, "model": "fallback", "latency_ms": latency_ms})
        return out

    json_block = _extract_json_block(raw)
    if not json_block:
        latency_ms = int((time.perf_counter() - start) * 1000)
        out = dict(FALLBACK)
        out.update({"request_id": request_id, "model": model, "latency_ms": latency_ms})
        return out

    try:
        obj = json.loads(json_block)
        result = _normalize_result(obj)
    except Exception:
        latency_ms = int((time.perf_counter() - start) * 1000)
        out = dict(FALLBACK)
        out.update({"request_id": request_id, "model": model, "latency_ms": latency_ms})
        return out

    latency_ms = int((time.perf_counter() - start) * 1000)
    result.update({"request_id": request_id, "model": model, "latency_ms": latency_ms})
    return result
