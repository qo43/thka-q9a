"""
Legal Explanation Generation Module

This module generates formal legal explanations from OCR-extracted text.
Takes noisy, unstructured OCR text and produces clean, professional legal paragraphs
suitable for judicial contexts.
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
ALLOWED_LANGUAGES = {"ar", "en"}

# Default response when generation fails
FALLBACK = {
    "success": False,
    "message": "",
    "reason": "Unable to generate explanation automatically; needs manual review.",
    "latency_ms": 0,
}


def get_prompt_path(lang: str) -> Path:
    """
    Get the prompt file path based on language code.
    
    Args:
        lang: Language code ('ar' or 'en')
    
    Returns:
        Path to the explanation prompt file
        
    Raises:
        ValueError: If language is not supported
    """
    if lang not in ALLOWED_LANGUAGES:
        raise ValueError(f"Unsupported language: {lang}. Allowed: {ALLOWED_LANGUAGES}")
    
    script_dir = Path(__file__).parent.parent
    return script_dir / "Prompts" / f"{lang}_explanation_prompt.txt"


def load_prompt(prompt_path: str) -> str:
    """Load prompt template from file."""
    return Path(prompt_path).read_text(encoding="utf-8").rstrip()


def build_prompt(base_prompt: str, ocr_text: str) -> str:
    """Combine base prompt with OCR text."""
    return f"{base_prompt}\n\n{ocr_text.strip()}"


def _clean_ai_output(text: str) -> str:
    """
    Remove AI meta-commentary and artifacts from generated text.
    
    Removes patterns like:
    - "Here is the legal complaint..."
    - "I hope this helps..."
    - Instructional comments
    - Markdown formatting
    - Non-Arabic/non-English characters (Chinese, Russian, Vietnamese, etc.)
    
    Args:
        text: Raw AI-generated text
    
    Returns:
        Cleaned legal explanation text
    """
    if not text or not text.strip():
        return ""
    
    text = text.strip()
    
    # Remove common AI meta-commentary patterns (English)
    meta_patterns_en = [
        r"^here is (the|a) (legal )?.*?:\s*",
        r"^i hope (this|that) helps.*",
        r"^(please )?note that.*",
        r"^this is (a|an) (draft|preliminary).*",
        r"^(based on|according to) (the )?.*?:\s*",
        r"\n\n(please )?feel free to.*",
        r"\n\nif you (have|need).*",
        r"\n\nlet me know.*",
        r"\n\nis this what you want.*",
        r"\n\ndo you (want|need).*",
        r"\n\ni can help.*",
        r"\n\nwould you like.*",
        r"^the legal (complaint|text|petition):\s*",
        r"^legal document:\s*",
    ]
    
    # Remove common AI meta-commentary patterns (Arabic)
    meta_patterns_ar = [
        r"^هذا هو.*?:\s*",
        r"^فيما يلي.*?:\s*",
        r"^إليك.*?:\s*",
        r"^أتمنى أن.*",
        r"^يرجى ملاحظة.*",
        r"\n\nإذا كنت بحاجة.*",
        r"\n\nيمكنك.*",
        r"\n\nهل هذا ما تريد.*",
        r"\n\nهل تحتاج.*",
        r"\n\nيمكنني المساعدة.*",
        r"\n\nهل تريد.*",
        r"\n\nأخبرني.*",
        r"^الشكوى القانونية:\s*",
        r"^النص القانوني:\s*",
        r"^المذكرة القانونية:\s*",
    ]
    
    all_patterns = meta_patterns_en + meta_patterns_ar
    
    for pattern in all_patterns:
        text = re.sub(pattern, "", text, flags=re.IGNORECASE | re.MULTILINE)
    
    # Remove markdown formatting
    text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)  # **bold**
    text = re.sub(r'\*(.*?)\*', r'\1', text)      # *italic*
    text = re.sub(r'`(.*?)`', r'\1', text)        # `code`
    
    # Remove mixed-language characters (Chinese, Russian, Vietnamese, etc.)
    text = _remove_language_leaking(text)
    
    # Remove extra blank lines
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    # Remove leading/trailing whitespace
    text = text.strip()
    
    return text


def _remove_language_leaking(text: str) -> str:
    """
    Remove non-Arabic/non-English characters that indicate language leaking.
    
    Multilingual models like Qwen sometimes mix languages (Chinese: 已经被纠正为, 
    Russian: доказать, Vietnamese: đòi, etc.) in their outputs. 
    This function strips those characters while preserving Arabic and English.
    
    Args:
        text: Text that may contain mixed languages
    
    Returns:
        Cleaned text with only Arabic, English, punctuation, and numbers
    """
    # Define allowed Unicode ranges
    allowed_ranges = [
        (0x0600, 0x06FF),  # Arabic
        (0x0750, 0x077F),  # Arabic Supplement
        (0x08A0, 0x08FF),  # Arabic Extended-A
        (0xFB50, 0xFDFF),  # Arabic Presentation Forms-A
        (0xFE70, 0xFEFF),  # Arabic Presentation Forms-B
        (0x0000, 0x007F),  # Basic Latin (English)
        (0x0020, 0x0020),  # Space
    ]
    
    def is_allowed(char):
        codepoint = ord(char)
        
        # Allow common punctuation and digits
        if char.isdigit() or char in ".,!?-()[]{}:/؛،؟٪":
            return True
        
        # Allow newlines and tabs
        if char in '\n\r\t':
            return True
        
        # Check if in allowed ranges
        for start, end in allowed_ranges:
            if start <= codepoint <= end:
                return True
        
        return False
    
    # Filter characters
    cleaned = ''.join(c if is_allowed(c) else '' for c in text)
    
    # Clean up multiple spaces
    cleaned = re.sub(r' +', ' ', cleaned)
    
    # Clean up spaces around punctuation
    cleaned = re.sub(r'\s+([.,!?؛،؟])', r'\1', cleaned)
    
    return cleaned.strip()


def _extract_legal_text(raw_output: str) -> str:
    """
    Extract the main legal explanation from AI output.
    
    Tries to identify and extract only the core legal paragraph,
    removing any JSON formatting, instructions, or meta-text.
    
    Args:
        raw_output: Raw text from AI model
    
    Returns:
        Extracted legal explanation
    """
    raw_output = raw_output.strip()
    
    # Try to extract from JSON if present
    try:
        json_match = re.search(r'\{.*\}', raw_output, flags=re.DOTALL)
        if json_match:
            obj = json.loads(json_match.group(0))
            if isinstance(obj, dict):
                # Look for common keys
                for key in ['explanation', 'text', 'message', 'content', 'legal_text']:
                    if key in obj and isinstance(obj[key], str):
                        return obj[key].strip()
    except:
        pass
    
    # If no JSON or extraction failed, use the raw text
    return raw_output


def generate_explanation(
    ocr_text: str,
    lang: str = "ar",
    model: str = "qwen2.5:7b-instruct",
    temperature: float = 0.3,
    timeout_s: int = 45,
) -> Dict[str, Any]:
    """
    Generate formal legal explanation from OCR-extracted text.
    
    Args:
        ocr_text: Raw OCR-extracted text from legal document
        lang: Language code ('ar' for Arabic, 'en' for English)
        model: Ollama model name
        temperature: Model temperature (0.0-1.0, lower = more deterministic)
        timeout_s: Request timeout in seconds
    
    Returns:
        Dictionary with:
        - success (bool): Whether generation succeeded
        - message (str): Generated legal explanation text
        - latency_ms (int): Generation time in milliseconds
        - reason (str, optional): Failure reason if success=False
        - request_id (str): Unique request identifier
        - model (str): Model used
    
    Example:
        >>> result = generate_explanation("نص الوثيقة...", lang="ar")
        >>> if result['success']:
        ...     print(result['message'])
    """
    # Validate input
    if not ocr_text or not ocr_text.strip():
        return {
            **FALLBACK,
            "reason": "OCR text is empty or missing.",
            "request_id": str(uuid.uuid4()),
            "model": "none",
        }
    
    # Load prompt
    try:
        prompt_path = get_prompt_path(lang)
        base_prompt = load_prompt(str(prompt_path))
    except Exception as e:
        return {
            **FALLBACK,
            "reason": f"Failed to load prompt: {str(e)}",
            "request_id": str(uuid.uuid4()),
            "model": "none",
        }
    
    prompt = build_prompt(base_prompt, ocr_text)
    request_id = str(uuid.uuid4())
    start = time.perf_counter()
    
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": temperature},
    }
    
    # Call Ollama API
    try:
        resp = requests.post(OLLAMA_URL, json=payload, timeout=timeout_s)
        resp.raise_for_status()
        raw_output = resp.json().get("response", "").strip()
    except requests.Timeout:
        latency_ms = int((time.perf_counter() - start) * 1000)
        return {
            **FALLBACK,
            "reason": "Request timeout - AI model took too long to respond.",
            "request_id": request_id,
            "model": model,
            "latency_ms": latency_ms,
        }
    except requests.RequestException as e:
        latency_ms = int((time.perf_counter() - start) * 1000)
        return {
            **FALLBACK,
            "reason": f"API request failed: {str(e)}",
            "request_id": request_id,
            "model": model,
            "latency_ms": latency_ms,
        }
    except Exception as e:
        latency_ms = int((time.perf_counter() - start) * 1000)
        return {
            **FALLBACK,
            "reason": f"Unexpected error: {str(e)}",
            "request_id": request_id,
            "model": model,
            "latency_ms": latency_ms,
        }
    
    # Extract and clean output
    if not raw_output:
        latency_ms = int((time.perf_counter() - start) * 1000)
        return {
            **FALLBACK,
            "reason": "AI model returned empty response.",
            "request_id": request_id,
            "model": model,
            "latency_ms": latency_ms,
        }
    
    legal_text = _extract_legal_text(raw_output)
    cleaned_text = _clean_ai_output(legal_text)
    
    if not cleaned_text:
        latency_ms = int((time.perf_counter() - start) * 1000)
        return {
            **FALLBACK,
            "reason": "Generated text was empty after cleaning.",
            "request_id": request_id,
            "model": model,
            "latency_ms": latency_ms,
        }
    
    latency_ms = int((time.perf_counter() - start) * 1000)
    
    return {
        "success": True,
        "message": cleaned_text,
        "latency_ms": latency_ms,
        "request_id": request_id,
        "model": model,
    }
