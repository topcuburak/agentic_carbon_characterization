"""
Task schema — defines what a benchmark task looks like.
"""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Task:
    """A single benchmark task."""
    id: str                          # Unique ID, e.g., "mhqa_01"
    category: str                    # Category name, e.g., "multihop_qa"
    prompt: str                      # The task instruction for the agent
    system_prompt: str = ""          # Optional system prompt
    expected_answer: Any = None      # Ground truth for evaluation (string, number, or dict)
    evaluation_type: str = "exact"   # "exact", "numeric", "rubric", "code_exec"
    evaluation_config: dict = field(default_factory=dict)  # Extra eval params (tolerance, rubric criteria, etc.)
    tools_required: list[str] = field(default_factory=list)  # Which tools this task needs
    difficulty: str = "medium"       # "easy", "medium", "hard"
    min_steps: int = 2               # Minimum expected agent steps
