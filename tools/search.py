"""
Knowledge base search tool.
Performs keyword search over pre-loaded JSON documents in the knowledge base directory.
"""

import json
from pathlib import Path
from config import KNOWLEDGE_BASE_DIR

_kb_cache: list[dict] | None = None


def _load_knowledge_base() -> list[dict]:
    """Load all JSON documents from the knowledge base directory."""
    global _kb_cache
    if _kb_cache is not None:
        return _kb_cache

    _kb_cache = []
    kb_path = Path(KNOWLEDGE_BASE_DIR)
    if not kb_path.exists():
        return _kb_cache

    for f in sorted(kb_path.glob("*.json")):
        with open(f, "r") as fh:
            data = json.load(fh)
            if isinstance(data, list):
                _kb_cache.extend(data)
            else:
                _kb_cache.append(data)
    return _kb_cache


def search(query: str) -> str:
    """
    Search the knowledge base for entries matching the query.
    Returns top matching snippets as a formatted string.
    """
    kb = _load_knowledge_base()
    if not kb:
        return "Error: Knowledge base is empty or not found."

    query_terms = query.lower().split()
    scored = []
    for entry in kb:
        title = entry.get("title", "").lower()
        content = entry.get("content", "").lower()
        text = f"{title} {content}"
        score = sum(1 for term in query_terms if term in text)
        if score > 0:
            scored.append((score, entry))

    scored.sort(key=lambda x: x[0], reverse=True)
    top = scored[:5]

    if not top:
        return f"No results found for query: '{query}'"

    results = []
    for i, (score, entry) in enumerate(top, 1):
        title = entry.get("title", "Untitled")
        content = entry.get("content", "")
        # Truncate long content
        if len(content) > 500:
            content = content[:500] + "..."
        results.append(f"[{i}] {title}\n{content}")

    return "\n\n".join(results)
