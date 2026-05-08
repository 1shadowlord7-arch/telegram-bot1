from __future__ import annotations
import re
import html
from difflib import SequenceMatcher
from rapidfuzz import fuzz

def normalize_text(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"[^\w\s\-#@.:/]", "", text, flags=re.UNICODE)
    return text

def compact_keywords(text: str) -> list[str]:
    parts = normalize_text(text).split()
    return [p for p in parts if len(p) > 1]

def safe_html(text: str | None) -> str:
    return html.escape(text or "")

def similarity(a: str, b: str) -> int:
    return max(
        fuzz.ratio(a, b),
        fuzz.partial_ratio(a, b),
        int(SequenceMatcher(None, a, b).ratio() * 100),
    )
