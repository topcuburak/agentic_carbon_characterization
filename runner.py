"""
Main experiment runner.
Orchestrates: framework setup → task execution → power monitoring → evaluation → logging.
"""

import json
import csv
import time
import os
import argparse
import traceback
from pathlib import Path
from dataclasses import asdict

from config import (
    MODELS, FRAMEWORKS, EXPERIMENT_CONFIG, RESULTS_DIR,
    ensure_dirs,
)
from frameworks.base import RunMetrics
from power_monitor import PowerMonitor, Phase
from evaluator import evaluate, EvalResult
from tasks import ALL_TASKS
from tools import TOOL_REGISTRY
from tools.mock_api_server import start_mock_server, stop_mock_server
from tools.setup_database import create_database
from tools.setup_knowledge_base import create_knowledge_base


# ─── Framework Factory ───────────────────────────────────────────────────────

def get_adapter(framework_name: str, model_config, tools):
    """Instantiate the appropriate framework adapter."""
    if framework_name == "mock":
        from frameworks.mock_agent import MockAdapter
        return MockAdapter(model_config, tools)
    elif framework_name == "langgraph":
        from frameworks.langgraph_agent import LangGraphAdapter
        return LangGraphAdapter(model_config, tools)
    elif framework_name == "crewai":
        from frameworks.crewai_agent import CrewAIAdapter
        return CrewAIAdapter(model_config, tools)
    elif framework_name == "smolagents":
        from frameworks.smolagents_agent import SmolagentsAdapter
        return SmolagentsAdapter(model_config, tools)
    elif framework_name == "autogen":
        from frameworks.autogen_agent import AutoGenAdapter
        return AutoGenAdapter(model_config, tools)
    elif framework_name == "openai_agents":
        from frameworks.openai_agents_agent import OpenAIAgentsAdapter
        return OpenAIAgentsAdapter(model_config, tools)
    else:
        raise ValueError(f"Unknown framework: {framework_name}")


# ─── Result Logging ──────────────────────────────────────────────────────────

def save_run_result(
    metrics: RunMetrics,
    eval_result: EvalResult,
    power_report,
    repetition: int,
    is_baseline: bool,
    output_dir: Path,
):
    """Save a single run's results to JSON and append to the summary CSV."""
    run_type = "baseline" if is_baseline else "agentic"
    run_id = f"{metrics.framework}_{metrics.model}_{metrics.task_id}_rep{repetition}_{run_type}"

    # Detailed JSON per run
    json_dir = output_dir / "runs"
    json_dir.mkdir(parents=True, exist_ok=True)

    run_data = {
        "run_id": run_id,
        "run_type": run_type,
        "framework": metrics.framework,
        "model": metrics.model,
        "task_id": metrics.task_id,
        "task_category": metrics.task_category,
        "repetition": repetition,
        # Metrics
        "total_input_tokens": metrics.total_input_tokens,
        "total_output_tokens": metrics.total_output_tokens,
        "total_tokens": metrics.total_tokens,
        "num_llm_calls": metrics.num_llm_calls,
        "num_tool_calls": metrics.num_tool_calls,
        "num_agent_steps": metrics.num_agent_steps,
        "wall_clock_ms": metrics.wall_clock_ms,
        "tool_call_counts": metrics.tool_call_counts,
        "tool_time_ms": metrics.tool_time_ms,
        "success": metrics.success,
        "error": metrics.error,
        # Evaluation
        "eval_score": eval_result.score,
        "eval_correct": eval_result.correct,
        "eval_details": eval_result.details,
        "eval_criteria_scores": eval_result.criteria_scores,
        # Power
        "total_energy_j": power_report.total_energy_j if power_report else None,
        "total_gpu_energy_j": power_report.total_gpu_energy_j if power_report else None,
        "total_cpu_energy_j": power_report.total_cpu_energy_j if power_report else None,
        "total_dram_energy_j": power_report.total_dram_energy_j if power_report else None,
        "phase_energy": {
            phase: {
                "gpu_energy_j": pe.gpu_energy_j,
                "cpu_energy_j": pe.cpu_energy_j,
                "dram_energy_j": pe.dram_energy_j,
                "duration_ms": pe.duration_ms,
            }
            for phase, pe in power_report.phase_energy.items()
        } if power_report else None,
        "total_duration_ms": power_report.total_duration_ms if power_report else None,
        # Per-tool resource breakdown
        "tool_cpu_time_ms": metrics.tool_cpu_time_ms,
        "tool_gpu_energy_j": metrics.tool_gpu_energy_j,
        "tool_cpu_energy_j": metrics.tool_cpu_energy_j,
        # Per-tool detail log
        "tool_calls_detail": [
            {
                "tool_name": tc.tool_name,
                "duration_ms": tc.duration_ms,
                "cpu_time_ms": tc.cpu_time_ms,
                "gpu_energy_j": tc.gpu_energy_j,
                "cpu_energy_j": tc.cpu_energy_j,
            }
            for tc in metrics.tool_calls
        ],
        # LLM call totals
        "total_llm_cpu_time_ms": metrics.total_llm_cpu_time_ms,
        "total_llm_gpu_energy_j": metrics.total_llm_gpu_energy_j,
        "total_llm_cpu_energy_j": metrics.total_llm_cpu_energy_j,
        # Output preview
        "final_output_preview": metrics.final_output[:500],
    }

    with open(json_dir / f"{run_id}.json", "w") as f:
        json.dump(run_data, f, indent=2, default=str)

    # Append to summary CSV
    csv_path = output_dir / "summary.csv"
    write_header = not csv_path.exists()

    csv_row = {
        "run_id": run_id,
        "run_type": run_type,
        "framework": metrics.framework,
        "model": metrics.model,
        "task_id": metrics.task_id,
        "task_category": metrics.task_category,
        "repetition": repetition,
        "total_tokens": metrics.total_tokens,
        "input_tokens": metrics.total_input_tokens,
        "output_tokens": metrics.total_output_tokens,
        "num_llm_calls": metrics.num_llm_calls,
        "num_tool_calls": metrics.num_tool_calls,
        "wall_clock_ms": metrics.wall_clock_ms,
        "success": metrics.success,
        "eval_score": eval_result.score,
        "eval_correct": eval_result.correct,
        "total_energy_j": power_report.total_energy_j if power_report else "",
        "gpu_energy_j": sum(power_report.total_gpu_energy_j) if power_report else "",
        "cpu_energy_j": power_report.total_cpu_energy_j if power_report else "",
    }

    with open(csv_path, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=csv_row.keys())
        if write_header:
            writer.writeheader()
        writer.writerow(csv_row)

    return run_id


# ─── Main Runner ─────────────────────────────────────────────────────────────

def run_experiments(
    frameworks: list[str] | None = None,
    models: list[str] | None = None,
    categories: list[str] | None = None,
    task_ids: list[str] | None = None,
    repetitions: int | None = None,
    run_baseline: bool | None = None,
    enable_power: bool = True,
    output_dir: Path | None = None,
):
    """
    Run the full experiment suite.

    Args:
        frameworks: List of framework names to test (default: all).
        models: List of model keys to test (default: all).
        categories: List of task categories to run (default: all).
        task_ids: Specific task IDs to run (overrides categories).
        repetitions: Number of repetitions per run.
        run_baseline: Whether to run single-shot baselines.
        enable_power: Whether to enable power monitoring.
        output_dir: Output directory for results.
    """
    # Defaults
    frameworks = frameworks or FRAMEWORKS
    models = models or list(MODELS.keys())
    repetitions = repetitions if repetitions is not None else EXPERIMENT_CONFIG.repetitions
    run_baseline = run_baseline if run_baseline is not None else EXPERIMENT_CONFIG.run_baseline
    output_dir = output_dir or RESULTS_DIR

    # Setup
    ensure_dirs()
    print("Setting up infrastructure...")
    create_database()
    create_knowledge_base()
    mock_server = start_mock_server()
    print("Mock API server started.")

    # Collect tasks
    tasks = []
    if task_ids:
        for cat_tasks in ALL_TASKS.values():
            for t in cat_tasks:
                if t.id in task_ids:
                    tasks.append(t)
    elif categories:
        for cat in categories:
            tasks.extend(ALL_TASKS.get(cat, []))
    else:
        for cat_tasks in ALL_TASKS.values():
            tasks.extend(cat_tasks)

    total_runs = len(tasks) * len(frameworks) * len(models) * repetitions
    if run_baseline:
        total_runs += len(tasks) * len(models) * repetitions
    print(f"\nExperiment plan: {len(tasks)} tasks × {len(frameworks)} frameworks × "
          f"{len(models)} models × {repetitions} reps = {total_runs} total runs\n")

    run_count = 0
    errors = []

    for model_key in models:
        model_config = MODELS[model_key]
        print(f"\n{'='*60}")
        print(f"MODEL: {model_config.name}")
        print(f"{'='*60}")

        # ── Run baselines first ──────────────────────────────────────
        if run_baseline:
            print(f"\n  Running baselines (single-shot, no tools)...")
            # Use the first framework in the list for baseline (or mock if testing)
            baseline_fw = frameworks[0] if frameworks else "langgraph"
            baseline_adapter = get_adapter(baseline_fw, model_config, TOOL_REGISTRY)
            baseline_adapter.setup()

            for task in tasks:
                for rep in range(repetitions):
                    run_count += 1
                    run_label = f"[{run_count}/{total_runs}] BASELINE | {model_config.name} | {task.id} | rep {rep}"
                    print(f"  {run_label}", end="... ", flush=True)

                    monitor = None
                    power_report = None
                    if enable_power:
                        monitor = PowerMonitor(
                            run_id=f"baseline_{model_key}_{task.id}_rep{rep}",
                            output_dir=output_dir / "power_traces",
                        )
                        monitor.start()
                        monitor.set_phase(Phase.INFERENCE)

                    try:
                        metrics = baseline_adapter.run_single_shot(
                            task_prompt=task.prompt,
                            task_id=task.id,
                            task_category=task.category,
                            system_prompt=task.system_prompt,
                        )
                    except Exception as e:
                        metrics = RunMetrics(
                            framework="baseline", model=model_config.name,
                            task_id=task.id, task_category=task.category,
                            error=str(e), success=False,
                        )
                        errors.append(f"{run_label}: {e}")

                    if monitor:
                        monitor.stop()
                        power_report = monitor.get_report()
                        monitor.save_trace(power_report)

                    eval_result = evaluate(task, metrics)
                    save_run_result(metrics, eval_result, power_report, rep, True, output_dir)
                    status = "OK" if metrics.success else "FAIL"
                    print(f"{status} ({metrics.wall_clock_ms}ms, {metrics.total_tokens} tok)")

            baseline_adapter.teardown()

        # ── Run agentic frameworks ───────────────────────────────────
        for fw_name in frameworks:
            print(f"\n  Framework: {fw_name}")
            print(f"  {'-'*50}")

            try:
                adapter = get_adapter(fw_name, model_config, TOOL_REGISTRY)
                adapter.setup()
            except Exception as e:
                print(f"  ERROR: Failed to setup {fw_name}: {e}")
                errors.append(f"Setup {fw_name}: {e}")
                # Skip all tasks for this framework
                run_count += len(tasks) * repetitions
                continue

            for task in tasks:
                for rep in range(repetitions):
                    run_count += 1
                    run_label = f"[{run_count}/{total_runs}] {fw_name} | {model_config.name} | {task.id} | rep {rep}"
                    print(f"  {run_label}", end="... ", flush=True)

                    monitor = None
                    power_report = None
                    if enable_power:
                        monitor = PowerMonitor(
                            run_id=f"{fw_name}_{model_key}_{task.id}_rep{rep}",
                            output_dir=output_dir / "power_traces",
                        )
                        monitor.start()
                        monitor.set_phase(Phase.ORCHESTRATION)

                    try:
                        metrics = adapter.run_task(
                            task_prompt=task.prompt,
                            task_id=task.id,
                            task_category=task.category,
                            system_prompt=task.system_prompt,
                            max_steps=EXPERIMENT_CONFIG.max_agent_steps,
                        )
                    except Exception as e:
                        metrics = RunMetrics(
                            framework=fw_name, model=model_config.name,
                            task_id=task.id, task_category=task.category,
                            error=str(e), success=False,
                        )
                        errors.append(f"{run_label}: {e}")
                        traceback.print_exc()

                    if monitor:
                        monitor.stop()
                        power_report = monitor.get_report()
                        monitor.save_trace(power_report)

                    eval_result = evaluate(task, metrics)
                    save_run_result(metrics, eval_result, power_report, rep, False, output_dir)
                    status = "OK" if metrics.success else "FAIL"
                    print(f"{status} ({metrics.wall_clock_ms}ms, {metrics.total_tokens} tok, "
                          f"{metrics.num_llm_calls} LLM calls, {metrics.num_tool_calls} tool calls)")

            adapter.teardown()

    # Cleanup
    if mock_server:
        stop_mock_server(mock_server)

    # Summary
    print(f"\n{'='*60}")
    print(f"COMPLETE: {run_count} runs finished.")
    print(f"Results saved to: {output_dir}")
    if errors:
        print(f"\n{len(errors)} errors encountered:")
        for err in errors:
            print(f"  - {err}")
    print(f"{'='*60}")


# ─── CLI ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Agentic AI Workload Characterization Benchmark")

    parser.add_argument("--frameworks", nargs="+", default=None,
                        help=f"Frameworks to test (default: all). Options: {FRAMEWORKS}")
    parser.add_argument("--models", nargs="+", default=None,
                        help=f"Models to test (default: all). Options: {list(MODELS.keys())}")
    parser.add_argument("--categories", nargs="+", default=None,
                        help=f"Task categories (default: all). Options: {list(ALL_TASKS.keys())}")
    parser.add_argument("--task-ids", nargs="+", default=None,
                        help="Specific task IDs to run")
    parser.add_argument("--reps", type=int, default=None,
                        help=f"Repetitions per run (default: {EXPERIMENT_CONFIG.repetitions})")
    parser.add_argument("--no-baseline", action="store_true",
                        help="Skip single-shot baseline runs")
    parser.add_argument("--no-power", action="store_true",
                        help="Disable power monitoring (for local testing)")
    parser.add_argument("--output-dir", type=str, default=None,
                        help=f"Output directory (default: {RESULTS_DIR})")

    args = parser.parse_args()

    output_dir = Path(args.output_dir) if args.output_dir else None

    run_experiments(
        frameworks=args.frameworks,
        models=args.models,
        categories=args.categories,
        task_ids=args.task_ids,
        repetitions=args.reps,
        run_baseline=not args.no_baseline,
        enable_power=not args.no_power,
        output_dir=output_dir,
    )


if __name__ == "__main__":
    main()
