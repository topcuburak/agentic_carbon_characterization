"""
Post-experiment metrics computation.
Loads results from summary CSV and per-run JSON files, computes derived metrics.
"""

import json
import csv
from pathlib import Path
from dataclasses import dataclass, field
import statistics

from config import RESULTS_DIR, POWER_CONFIG


@dataclass
class AggregatedMetrics:
    """Aggregated metrics across repetitions for a single (framework, model, task) combo."""
    framework: str
    model: str
    task_id: str
    task_category: str
    run_type: str  # "agentic" or "baseline"

    # Token metrics (mean ± std)
    total_tokens_mean: float = 0
    total_tokens_std: float = 0
    input_tokens_mean: float = 0
    output_tokens_mean: float = 0
    num_llm_calls_mean: float = 0
    num_tool_calls_mean: float = 0

    # Timing
    wall_clock_ms_mean: float = 0
    wall_clock_ms_std: float = 0

    # Evaluation
    eval_score_mean: float = 0
    success_rate: float = 0

    # Energy
    total_energy_j_mean: float = 0
    gpu_energy_j_mean: float = 0
    cpu_energy_j_mean: float = 0

    # Phase energy breakdown
    inference_energy_j_mean: float = 0
    tool_energy_j_mean: float = 0
    orchestration_energy_j_mean: float = 0

    # Derived
    token_amplification: float = 0  # vs baseline
    energy_amplification: float = 0  # vs baseline
    energy_per_correct_answer_j: float = 0


def load_summary(results_dir: Path | None = None) -> list[dict]:
    """Load the summary CSV into a list of dicts."""
    results_dir = results_dir or RESULTS_DIR
    csv_path = results_dir / "summary.csv"
    if not csv_path.exists():
        return []
    with open(csv_path, "r") as f:
        return list(csv.DictReader(f))


def load_run_details(run_id: str, results_dir: Path | None = None) -> dict | None:
    """Load detailed JSON for a specific run."""
    results_dir = results_dir or RESULTS_DIR
    json_path = results_dir / "runs" / f"{run_id}.json"
    if not json_path.exists():
        return None
    with open(json_path, "r") as f:
        return json.load(f)


def aggregate_metrics(results_dir: Path | None = None) -> list[AggregatedMetrics]:
    """
    Aggregate results across repetitions.
    Groups by (framework, model, task_id, run_type).
    """
    rows = load_summary(results_dir)
    if not rows:
        return []

    # Group by key
    groups: dict[tuple, list[dict]] = {}
    for row in rows:
        key = (row["framework"], row["model"], row["task_id"], row["task_category"], row["run_type"])
        groups.setdefault(key, []).append(row)

    aggregated = []
    for (fw, model, task_id, cat, run_type), group_rows in groups.items():
        am = AggregatedMetrics(
            framework=fw, model=model, task_id=task_id,
            task_category=cat, run_type=run_type,
        )

        def _safe_floats(key):
            return [float(r[key]) for r in group_rows if r.get(key) and r[key] != ""]

        tokens = _safe_floats("total_tokens")
        am.total_tokens_mean = statistics.mean(tokens) if tokens else 0
        am.total_tokens_std = statistics.stdev(tokens) if len(tokens) > 1 else 0

        input_tok = _safe_floats("input_tokens")
        am.input_tokens_mean = statistics.mean(input_tok) if input_tok else 0

        output_tok = _safe_floats("output_tokens")
        am.output_tokens_mean = statistics.mean(output_tok) if output_tok else 0

        llm_calls = _safe_floats("num_llm_calls")
        am.num_llm_calls_mean = statistics.mean(llm_calls) if llm_calls else 0

        tool_calls = _safe_floats("num_tool_calls")
        am.num_tool_calls_mean = statistics.mean(tool_calls) if tool_calls else 0

        wall = _safe_floats("wall_clock_ms")
        am.wall_clock_ms_mean = statistics.mean(wall) if wall else 0
        am.wall_clock_ms_std = statistics.stdev(wall) if len(wall) > 1 else 0

        scores = _safe_floats("eval_score")
        am.eval_score_mean = statistics.mean(scores) if scores else 0

        successes = [r["success"] == "True" for r in group_rows]
        am.success_rate = sum(successes) / len(successes) if successes else 0

        energy = _safe_floats("total_energy_j")
        am.total_energy_j_mean = statistics.mean(energy) if energy else 0

        gpu_e = _safe_floats("gpu_energy_j")
        am.gpu_energy_j_mean = statistics.mean(gpu_e) if gpu_e else 0

        cpu_e = _safe_floats("cpu_energy_j")
        am.cpu_energy_j_mean = statistics.mean(cpu_e) if cpu_e else 0

        # Energy per correct answer
        if am.eval_score_mean > 0:
            am.energy_per_correct_answer_j = am.total_energy_j_mean / am.eval_score_mean

        aggregated.append(am)

    return aggregated


def compute_amplification_factors(
    aggregated: list[AggregatedMetrics],
) -> list[AggregatedMetrics]:
    """
    Compute token and energy amplification factors (agentic / baseline).
    Modifies the AggregatedMetrics in place and returns them.
    """
    # Index baselines by (model, task_id)
    baselines: dict[tuple, AggregatedMetrics] = {}
    for am in aggregated:
        if am.run_type == "baseline":
            baselines[(am.model, am.task_id)] = am

    for am in aggregated:
        if am.run_type == "agentic":
            baseline = baselines.get((am.model, am.task_id))
            if baseline and baseline.total_tokens_mean > 0:
                am.token_amplification = am.total_tokens_mean / baseline.total_tokens_mean
            if baseline and baseline.total_energy_j_mean > 0:
                am.energy_amplification = am.total_energy_j_mean / baseline.total_energy_j_mean

    return aggregated


def compute_phase_energy(results_dir: Path | None = None) -> dict:
    """
    Compute phase-level energy breakdown from detailed run JSONs.
    Returns dict keyed by (framework, model, task_category) with phase energy averages.
    """
    results_dir = results_dir or RESULTS_DIR
    runs_dir = results_dir / "runs"
    if not runs_dir.exists():
        return {}

    phase_data: dict[tuple, dict[str, list[float]]] = {}

    for json_file in sorted(runs_dir.glob("*.json")):
        with open(json_file) as f:
            data = json.load(f)

        if data.get("run_type") != "agentic":
            continue

        pe = data.get("phase_energy")
        if not pe:
            continue

        key = (data["framework"], data["model"], data["task_category"])
        if key not in phase_data:
            phase_data[key] = {"inference": [], "tool_execution": [], "orchestration": [], "idle": []}

        for phase_name in ["inference", "tool_execution", "orchestration", "idle"]:
            if phase_name in pe:
                total = sum(pe[phase_name].get("gpu_energy_j", [0])) + pe[phase_name].get("cpu_energy_j", 0)
                phase_data[key][phase_name].append(total)

    # Average
    result = {}
    for key, phases in phase_data.items():
        result[key] = {
            phase: statistics.mean(vals) if vals else 0
            for phase, vals in phases.items()
        }

    return result


def generate_summary_table(aggregated: list[AggregatedMetrics]) -> str:
    """Generate a formatted summary table as a string."""
    lines = []
    header = (
        f"{'Framework':<15} {'Model':<20} {'Category':<20} {'Type':<10} "
        f"{'Tokens':>8} {'LLM#':>5} {'Tool#':>6} {'Time(s)':>8} "
        f"{'Score':>6} {'Energy(J)':>10} {'TokAmp':>7}"
    )
    lines.append(header)
    lines.append("-" * len(header))

    for am in sorted(aggregated, key=lambda x: (x.model, x.framework, x.task_category)):
        lines.append(
            f"{am.framework:<15} {am.model:<20} {am.task_category:<20} {am.run_type:<10} "
            f"{am.total_tokens_mean:>8.0f} {am.num_llm_calls_mean:>5.1f} "
            f"{am.num_tool_calls_mean:>6.1f} {am.wall_clock_ms_mean/1000:>8.1f} "
            f"{am.eval_score_mean:>6.2f} {am.total_energy_j_mean:>10.1f} "
            f"{am.token_amplification:>7.1f}"
        )

    return "\n".join(lines)
