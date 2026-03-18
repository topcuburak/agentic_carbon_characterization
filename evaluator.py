"""
Evaluator: scores task outputs for correctness.
Supports exact match, numeric comparison, rubric-based, and code execution checks.
"""

import re
import json
from dataclasses import dataclass
from tasks.task_schema import Task
from frameworks.base import RunMetrics


@dataclass
class EvalResult:
    """Evaluation result for a single run."""
    task_id: str
    score: float          # 0.0 to 1.0
    max_score: float      # Always 1.0 (normalized)
    correct: bool         # Whether it passes the threshold
    details: str          # Human-readable explanation
    criteria_scores: dict  # Per-criterion scores (for rubric)


def evaluate(task: Task, metrics: RunMetrics) -> EvalResult:
    """
    Evaluate a run's output against the task's expected answer.

    Args:
        task: The task definition with expected answers.
        metrics: The run metrics containing the agent's output.

    Returns:
        EvalResult with score and details.
    """
    output = metrics.final_output
    eval_type = task.evaluation_type
    config = task.evaluation_config

    if eval_type == "exact":
        return _eval_exact(task, output)
    elif eval_type == "numeric":
        return _eval_numeric(task, output, config)
    elif eval_type == "rubric":
        return _eval_rubric(task, output, config)
    elif eval_type == "code_exec":
        return _eval_code_exec(task, output, metrics, config)
    else:
        return EvalResult(
            task_id=task.id,
            score=0.0,
            max_score=1.0,
            correct=False,
            details=f"Unknown evaluation type: {eval_type}",
            criteria_scores={},
        )


def _eval_exact(task: Task, output: str) -> EvalResult:
    """Exact string match (case-insensitive)."""
    expected = str(task.expected_answer).lower().strip()
    actual = output.lower().strip()

    correct = expected in actual
    return EvalResult(
        task_id=task.id,
        score=1.0 if correct else 0.0,
        max_score=1.0,
        correct=correct,
        details=f"Expected '{expected}' in output: {'found' if correct else 'not found'}",
        criteria_scores={},
    )


def _eval_numeric(task: Task, output: str, config: dict) -> EvalResult:
    """Numeric comparison with tolerance."""
    expected = float(task.expected_answer)
    tolerance_pct = config.get("tolerance_pct", 5)

    # Extract numbers from output
    numbers = re.findall(r"-?\d+\.?\d*", output)

    if not numbers:
        return EvalResult(
            task_id=task.id,
            score=0.0,
            max_score=1.0,
            correct=False,
            details=f"No numbers found in output. Expected ~{expected}",
            criteria_scores={},
        )

    # Check if any extracted number is close enough
    for num_str in numbers:
        try:
            actual = float(num_str)
            if expected == 0:
                if abs(actual) < 0.01:
                    return EvalResult(
                        task_id=task.id, score=1.0, max_score=1.0, correct=True,
                        details=f"Found {actual}, expected {expected}", criteria_scores={},
                    )
            else:
                pct_diff = abs(actual - expected) / abs(expected) * 100
                if pct_diff <= tolerance_pct:
                    return EvalResult(
                        task_id=task.id, score=1.0, max_score=1.0, correct=True,
                        details=f"Found {actual}, expected {expected} (±{tolerance_pct}%): diff={pct_diff:.1f}%",
                        criteria_scores={},
                    )
        except ValueError:
            continue

    # Partial credit: closest number
    closest = None
    closest_diff = float("inf")
    for num_str in numbers:
        try:
            actual = float(num_str)
            diff = abs(actual - expected)
            if diff < closest_diff:
                closest_diff = diff
                closest = actual
        except ValueError:
            continue

    pct_diff = (closest_diff / abs(expected) * 100) if expected != 0 else closest_diff
    partial_score = max(0, 1.0 - pct_diff / 100)

    return EvalResult(
        task_id=task.id,
        score=partial_score,
        max_score=1.0,
        correct=False,
        details=f"Closest number: {closest}, expected {expected}, diff={pct_diff:.1f}%",
        criteria_scores={},
    )


def _eval_rubric(task: Task, output: str, config: dict) -> EvalResult:
    """
    Rubric-based evaluation.
    Checks for presence of key criteria in the output using keyword matching.
    """
    criteria = config.get("criteria", [])
    min_score = config.get("min_score", len(criteria) // 2)

    if not criteria:
        return EvalResult(
            task_id=task.id, score=1.0, max_score=1.0, correct=True,
            details="No criteria defined", criteria_scores={},
        )

    output_lower = output.lower()
    criteria_scores = {}
    met = 0

    for criterion in criteria:
        # Simple keyword-based check
        keywords = criterion.lower().split()
        # Check if most keywords appear in output
        keyword_hits = sum(1 for kw in keywords if kw in output_lower)
        ratio = keyword_hits / len(keywords) if keywords else 0
        passed = ratio >= 0.5  # At least half the keywords present
        criteria_scores[criterion] = 1.0 if passed else 0.0
        if passed:
            met += 1

    score = met / len(criteria)
    correct = met >= min_score

    return EvalResult(
        task_id=task.id,
        score=score,
        max_score=1.0,
        correct=correct,
        details=f"Rubric: {met}/{len(criteria)} criteria met (need {min_score})",
        criteria_scores=criteria_scores,
    )


def _eval_code_exec(task: Task, output: str, metrics: RunMetrics, config: dict) -> EvalResult:
    """
    Code execution evaluation.
    Checks: (1) code ran without errors, (2) output contains expected values.
    """
    # Check if code executed successfully (no error in tool calls)
    had_errors = any(
        "error" in tc.result.lower() or "traceback" in tc.result.lower()
        for tc in metrics.tool_calls
        if tc.tool_name == "python_exec" and tc.result
    )

    # Check for successful final execution
    last_exec = None
    for tc in reversed(metrics.tool_calls):
        if tc.tool_name == "python_exec":
            last_exec = tc
            break

    exec_success = last_exec is not None and (
        "error" not in last_exec.result.lower() and
        "traceback" not in last_exec.result.lower()
    ) if last_exec else False

    # Check expected outputs if provided
    expected = task.expected_answer
    output_match = True
    match_details = []

    if expected and config.get("check_outputs", False):
        combined_output = output + " " + (last_exec.result if last_exec else "")

        if isinstance(expected, dict):
            for key, val in expected.items():
                if str(val).lower() in combined_output.lower():
                    match_details.append(f"{key}={val}: found")
                else:
                    match_details.append(f"{key}={val}: not found")
                    output_match = False
        elif isinstance(expected, list):
            for val in expected:
                if str(val) in combined_output:
                    match_details.append(f"{val}: found")
                else:
                    match_details.append(f"{val}: not found")
                    output_match = False
        elif isinstance(expected, str):
            if expected.lower() in combined_output.lower():
                match_details.append(f"'{expected}': found")
            else:
                match_details.append(f"'{expected}': not found")
                output_match = False

    # Score: 0.5 for successful execution, 0.5 for correct output
    exec_score = 0.5 if exec_success else 0.0
    output_score = 0.5 if output_match else 0.0
    total_score = exec_score + output_score

    return EvalResult(
        task_id=task.id,
        score=total_score,
        max_score=1.0,
        correct=total_score >= 0.5,
        details=f"Execution: {'success' if exec_success else 'failed'}, Output: {'match' if output_match else 'mismatch'}. {'; '.join(match_details)}",
        criteria_scores={"execution": exec_score, "output_match": output_score},
    )
