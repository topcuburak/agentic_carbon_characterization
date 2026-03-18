"""
Visualization module for experiment results.
Generates publication-quality figures for the IISWC paper.
"""

import json
import csv
from pathlib import Path
from collections import defaultdict

import matplotlib
matplotlib.use("Agg")  # Non-interactive backend for server
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np

from config import RESULTS_DIR
from analysis.metrics import (
    load_summary,
    aggregate_metrics,
    compute_amplification_factors,
    compute_phase_energy,
)

# ─── Style ───────────────────────────────────────────────────────────────────

COLORS = {
    "langgraph": "#1f77b4",
    "crewai": "#ff7f0e",
    "smolagents": "#2ca02c",
    "autogen": "#d62728",
    "openai_agents": "#9467bd",
    "baseline": "#7f7f7f",
}

FRAMEWORK_LABELS = {
    "langgraph": "LangGraph",
    "crewai": "CrewAI",
    "smolagents": "smolagents",
    "autogen": "AutoGen",
    "openai_agents": "OAI Agents",
    "baseline": "Baseline",
}

MODEL_LABELS = {
    "Llama-3.1-8B-Instruct": "Llama-3.1 8B",
    "Qwen3.5-0.8B": "Qwen3.5 0.8B",
}

CATEGORY_LABELS = {
    "multihop_qa": "Multi-Hop QA",
    "code_gen": "Code Gen",
    "research_summarization": "Research",
    "data_analysis": "Data Analysis",
    "multi_agent": "Multi-Agent",
}


def _setup_style():
    plt.rcParams.update({
        "figure.figsize": (10, 6),
        "font.size": 11,
        "axes.titlesize": 13,
        "axes.labelsize": 12,
        "xtick.labelsize": 10,
        "ytick.labelsize": 10,
        "legend.fontsize": 10,
        "figure.dpi": 150,
        "savefig.dpi": 300,
        "savefig.bbox": "tight",
    })


def _save_fig(fig, name: str, output_dir: Path):
    """Save figure as both PNG and PDF."""
    figs_dir = output_dir / "figures"
    figs_dir.mkdir(parents=True, exist_ok=True)
    fig.savefig(figs_dir / f"{name}.png")
    fig.savefig(figs_dir / f"{name}.pdf")
    plt.close(fig)
    print(f"  Saved: {figs_dir / name}.{{png,pdf}}")


# ─── Plot Functions ──────────────────────────────────────────────────────────

def plot_token_amplification(aggregated, output_dir):
    """Bar chart: token amplification factor per framework × model, grouped by category."""
    _setup_style()

    models = sorted(set(am.model for am in aggregated))

    for model in models:
        model_data = [am for am in aggregated if am.model == model and am.run_type == "agentic"]
        if not model_data:
            continue

        # Group by category
        categories = sorted(set(am.task_category for am in model_data))
        frameworks = sorted(set(am.framework for am in model_data))

        fig, ax = plt.subplots(figsize=(12, 6))
        x = np.arange(len(categories))
        width = 0.15
        offsets = np.linspace(-width * (len(frameworks) - 1) / 2, width * (len(frameworks) - 1) / 2, len(frameworks))

        for i, fw in enumerate(frameworks):
            vals = []
            for cat in categories:
                matches = [am.token_amplification for am in model_data if am.framework == fw and am.task_category == cat]
                vals.append(np.mean(matches) if matches else 0)
            ax.bar(x + offsets[i], vals, width, label=FRAMEWORK_LABELS.get(fw, fw), color=COLORS.get(fw, "#333"))

        ax.set_xlabel("Task Category")
        ax.set_ylabel("Token Amplification Factor")
        ax.set_title(f"Token Amplification: Agentic vs. Single-Shot — {MODEL_LABELS.get(model, model)}")
        ax.set_xticks(x)
        ax.set_xticklabels([CATEGORY_LABELS.get(c, c) for c in categories], rotation=15)
        ax.legend()
        ax.axhline(y=1.0, color="gray", linestyle="--", alpha=0.5, label="1:1 (no amplification)")
        ax.grid(axis="y", alpha=0.3)

        _save_fig(fig, f"token_amplification_{model.replace(' ', '_').lower()}", output_dir)


def plot_energy_breakdown(aggregated, output_dir):
    """Stacked bar chart: GPU vs CPU energy per framework."""
    _setup_style()

    models = sorted(set(am.model for am in aggregated))
    frameworks = sorted(set(am.framework for am in aggregated if am.run_type == "agentic"))

    for model in models:
        model_data = [am for am in aggregated if am.model == model and am.run_type == "agentic"]
        if not model_data:
            continue

        # Average across all tasks per framework
        fw_gpu = {}
        fw_cpu = {}
        for fw in frameworks:
            fw_runs = [am for am in model_data if am.framework == fw]
            fw_gpu[fw] = np.mean([am.gpu_energy_j_mean for am in fw_runs]) if fw_runs else 0
            fw_cpu[fw] = np.mean([am.cpu_energy_j_mean for am in fw_runs]) if fw_runs else 0

        fig, ax = plt.subplots(figsize=(10, 6))
        x = np.arange(len(frameworks))
        labels = [FRAMEWORK_LABELS.get(fw, fw) for fw in frameworks]

        gpu_vals = [fw_gpu[fw] for fw in frameworks]
        cpu_vals = [fw_cpu[fw] for fw in frameworks]

        ax.bar(x, gpu_vals, label="GPU Energy", color="#e74c3c", alpha=0.85)
        ax.bar(x, cpu_vals, bottom=gpu_vals, label="CPU Energy", color="#3498db", alpha=0.85)

        ax.set_xlabel("Framework")
        ax.set_ylabel("Energy (Joules)")
        ax.set_title(f"CPU vs GPU Energy Breakdown — {MODEL_LABELS.get(model, model)}")
        ax.set_xticks(x)
        ax.set_xticklabels(labels)
        ax.legend()
        ax.grid(axis="y", alpha=0.3)

        _save_fig(fig, f"energy_breakdown_{model.replace(' ', '_').lower()}", output_dir)


def plot_phase_energy(results_dir, output_dir):
    """Stacked bar: energy by execution phase (inference, tool, orchestration)."""
    _setup_style()
    phase_data = compute_phase_energy(results_dir)

    if not phase_data:
        print("  No phase energy data available.")
        return

    # Group by (framework, model)
    fm_phases = defaultdict(lambda: defaultdict(list))
    for (fw, model, cat), phases in phase_data.items():
        for phase, val in phases.items():
            fm_phases[(fw, model)][phase].append(val)

    # Average phase energy per (framework, model)
    keys = sorted(fm_phases.keys())
    if not keys:
        return

    fig, ax = plt.subplots(figsize=(12, 6))
    x = np.arange(len(keys))
    labels = [f"{FRAMEWORK_LABELS.get(fw, fw)}\n{MODEL_LABELS.get(m, m)}" for fw, m in keys]

    phases = ["inference", "tool_execution", "orchestration", "idle"]
    phase_colors = {"inference": "#e74c3c", "tool_execution": "#3498db", "orchestration": "#f39c12", "idle": "#95a5a6"}
    phase_labels = {"inference": "Inference", "tool_execution": "Tool Exec", "orchestration": "Orchestration", "idle": "Idle"}

    bottom = np.zeros(len(keys))
    for phase in phases:
        vals = [np.mean(fm_phases[k].get(phase, [0])) for k in keys]
        ax.bar(x, vals, bottom=bottom, label=phase_labels[phase], color=phase_colors[phase], alpha=0.85)
        bottom += np.array(vals)

    ax.set_xlabel("Framework × Model")
    ax.set_ylabel("Energy (Joules)")
    ax.set_title("Energy by Execution Phase")
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=30, ha="right")
    ax.legend()
    ax.grid(axis="y", alpha=0.3)

    _save_fig(fig, "phase_energy_breakdown", output_dir)


def plot_model_comparison(aggregated, output_dir):
    """Side-by-side comparison: 8B vs 0.8B across frameworks."""
    _setup_style()

    agentic = [am for am in aggregated if am.run_type == "agentic"]
    models = sorted(set(am.model for am in agentic))
    frameworks = sorted(set(am.framework for am in agentic))

    if len(models) < 2:
        print("  Need 2 models for comparison plot.")
        return

    # Metrics to compare
    metric_pairs = [
        ("total_tokens_mean", "Avg Total Tokens"),
        ("num_llm_calls_mean", "Avg LLM Calls"),
        ("total_energy_j_mean", "Avg Energy (J)"),
        ("eval_score_mean", "Avg Eval Score"),
    ]

    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    axes = axes.flatten()

    for idx, (metric, title) in enumerate(metric_pairs):
        ax = axes[idx]
        x = np.arange(len(frameworks))
        width = 0.35

        for m_idx, model in enumerate(models):
            vals = []
            for fw in frameworks:
                matches = [getattr(am, metric) for am in agentic if am.framework == fw and am.model == model]
                vals.append(np.mean(matches) if matches else 0)
            offset = -width / 2 + m_idx * width
            ax.bar(x + offset, vals, width, label=MODEL_LABELS.get(model, model),
                   alpha=0.85, color=["#e74c3c", "#3498db"][m_idx])

        ax.set_title(title)
        ax.set_xticks(x)
        ax.set_xticklabels([FRAMEWORK_LABELS.get(fw, fw) for fw in frameworks], rotation=15)
        ax.legend()
        ax.grid(axis="y", alpha=0.3)

    fig.suptitle("Model Comparison: Llama-3.1 8B vs Qwen3.5 0.8B", fontsize=14, fontweight="bold")
    fig.tight_layout()
    _save_fig(fig, "model_comparison", output_dir)


def plot_power_trace(trace_csv: Path, output_dir: Path, run_id: str = ""):
    """Plot a single power trace (time series) from a CSV file."""
    _setup_style()

    timestamps = []
    phases = []
    gpu_powers = []
    cpu_powers = []

    with open(trace_csv) as f:
        reader = csv.DictReader(f)
        for row in reader:
            timestamps.append(float(row["timestamp_ms"]) / 1000)  # -> seconds
            phases.append(row["phase"])
            # Sum all GPU columns
            gpu_total = sum(float(v) for k, v in row.items() if k.startswith("gpu") and v)
            gpu_powers.append(gpu_total)
            cpu_val = float(row.get("cpu_pkg_power_w", 0) or 0)
            cpu_powers.append(cpu_val)

    if not timestamps:
        return

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 8), sharex=True)

    # GPU power
    ax1.plot(timestamps, gpu_powers, color="#e74c3c", linewidth=0.8, label="GPU Power")
    ax1.set_ylabel("GPU Power (W)")
    ax1.legend()
    ax1.grid(alpha=0.3)

    # CPU power
    ax2.plot(timestamps, cpu_powers, color="#3498db", linewidth=0.8, label="CPU Power")
    ax2.set_ylabel("CPU Power (W)")
    ax2.set_xlabel("Time (s)")
    ax2.legend()
    ax2.grid(alpha=0.3)

    # Color background by phase
    phase_colors = {"inference": "#ffe0e0", "tool_execution": "#e0e0ff", "orchestration": "#fff3e0", "idle": "#f0f0f0"}
    prev_phase = phases[0]
    start_t = timestamps[0]

    for i in range(1, len(phases)):
        if phases[i] != prev_phase or i == len(phases) - 1:
            end_t = timestamps[i]
            color = phase_colors.get(prev_phase, "#f0f0f0")
            ax1.axvspan(start_t, end_t, alpha=0.3, color=color)
            ax2.axvspan(start_t, end_t, alpha=0.3, color=color)
            prev_phase = phases[i]
            start_t = end_t

    title = f"Power Trace: {run_id}" if run_id else "Power Trace"
    fig.suptitle(title, fontsize=13)
    fig.tight_layout()
    _save_fig(fig, f"power_trace_{run_id or 'sample'}", output_dir)


# ─── Generate All Plots ─────────────────────────────────────────────────────

def generate_all_plots(results_dir: Path | None = None, output_dir: Path | None = None):
    """Generate all paper figures from experiment results."""
    results_dir = results_dir or RESULTS_DIR
    output_dir = output_dir or results_dir

    print("Generating plots...")

    aggregated = aggregate_metrics(results_dir)
    if not aggregated:
        print("  No results found. Run experiments first.")
        return

    aggregated = compute_amplification_factors(aggregated)

    plot_token_amplification(aggregated, output_dir)
    plot_energy_breakdown(aggregated, output_dir)
    plot_phase_energy(results_dir, output_dir)
    plot_model_comparison(aggregated, output_dir)

    # Plot a sample power trace if available
    traces_dir = results_dir / "power_traces"
    if traces_dir.exists():
        traces = sorted(traces_dir.glob("*.csv"))
        if traces:
            sample = traces[0]
            run_id = sample.stem.replace("_power_trace", "")
            plot_power_trace(sample, output_dir, run_id)

    print("All plots generated.")


if __name__ == "__main__":
    generate_all_plots()
