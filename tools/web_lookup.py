"""
Simulated web lookup tool.
Returns pre-cached documents for given topics to ensure reproducibility.
"""

import json
from pathlib import Path
from config import KNOWLEDGE_BASE_DIR

_web_cache: dict[str, str] | None = None


def _load_web_cache() -> dict[str, str]:
    """Load the web lookup cache from disk."""
    global _web_cache
    if _web_cache is not None:
        return _web_cache

    cache_path = Path(KNOWLEDGE_BASE_DIR) / "web_cache.json"
    if not cache_path.exists():
        _web_cache = {}
        return _web_cache

    with open(cache_path, "r") as f:
        _web_cache = json.load(f)
    return _web_cache


def web_lookup(topic: str) -> str:
    """
    Look up a pre-cached document on a given topic.
    Returns the document text or an error message if not found.
    """
    cache = _load_web_cache()
    if not cache:
        return "Error: Web cache is empty or not found."

    # Exact match first
    topic_lower = topic.lower().strip()
    for key, value in cache.items():
        if key.lower() == topic_lower:
            return value

    # Fuzzy match: find best matching key
    best_key = None
    best_score = 0
    topic_terms = set(topic_lower.split())
    for key in cache:
        key_terms = set(key.lower().split())
        overlap = len(topic_terms & key_terms)
        if overlap > best_score:
            best_score = overlap
            best_key = key

    if best_key and best_score > 0:
        return f"[Closest match: '{best_key}']\n{cache[best_key]}"

    return f"No cached document found for topic: '{topic}'"
