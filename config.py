"""
Global configuration for the agentic AI workload characterization experiments.
Adjust SERVER settings when deploying to the A100 server.
"""

import os
from pathlib import Path
from dataclasses import dataclass, field

# ─── Paths ───────────────────────────────────────────────────────────────────

PROJECT_ROOT = Path(__file__).parent.resolve()
RESULTS_DIR = PROJECT_ROOT / "results"
DATASETS_DIR = PROJECT_ROOT / "tasks" / "datasets"
SANDBOX_DIR = PROJECT_ROOT / "sandbox"  # Sandboxed file I/O for agents
KNOWLEDGE_BASE_DIR = DATASETS_DIR / "knowledge_base"
SQLITE_DB_PATH = DATASETS_DIR / "benchmark.db"

# ─── vLLM Inference Server ───────────────────────────────────────────────────

VLLM_BASE_URL = os.getenv("VLLM_BASE_URL", "http://localhost:8000/v1")
VLLM_API_KEY = os.getenv("VLLM_API_KEY", "EMPTY")

# ─── Models ──────────────────────────────────────────────────────────────────

@dataclass
class ModelConfig:
    name: str           # Display name for results
    model_id: str       # HuggingFace model ID (used by vLLM)
    max_tokens: int = 4096
    temperature: float = 0.0
    tensor_parallel: int = 1  # Number of GPUs for tensor parallelism

MODELS = {
    "llama-8b": ModelConfig(
        name="Llama-3.1-8B-Instruct",
        model_id="meta-llama/Llama-3.1-8B-Instruct",
        tensor_parallel=1,
    ),
    "qwen-0.8b": ModelConfig(
        name="Qwen3.5-0.8B",
        model_id="Qwen/Qwen3.5-0.8B",
        tensor_parallel=1,
    ),
}

# ─── Frameworks ──────────────────────────────────────────────────────────────

FRAMEWORKS = [
    "langgraph",
    "crewai",
    "smolagents",
    "autogen",
    "openai_agents",
]

# ─── Power Monitoring ────────────────────────────────────────────────────────

@dataclass
class PowerConfig:
    sampling_interval_ms: int = 100       # Power sampling rate in milliseconds
    gpu_indices: list[int] = field(default_factory=lambda: [0, 1])
    use_rapl: bool = True                 # Intel RAPL for CPU power
    use_nvml: bool = True                 # NVML for GPU power
    pue: float = 1.1                      # Power Usage Effectiveness multiplier

POWER_CONFIG = PowerConfig()

# ─── Mock API Server ─────────────────────────────────────────────────────────

MOCK_API_HOST = "127.0.0.1"
MOCK_API_PORT = 8100

# ─── Experiment Settings ─────────────────────────────────────────────────────

@dataclass
class ExperimentConfig:
    repetitions: int = 3
    max_agent_steps: int = 30        # Safety limit on agent loop iterations
    timeout_per_task_s: int = 300    # 5 min timeout per task run
    run_baseline: bool = True        # Also run single-shot (non-agentic) baseline

EXPERIMENT_CONFIG = ExperimentConfig()

# ─── Shell Exec Whitelist ────────────────────────────────────────────────────
# Commands allowed in shell_exec tool (security sandbox)
SHELL_WHITELIST = [
    "ls", "cat", "head", "tail", "wc", "sort", "uniq", "grep", "find",
    "echo", "date", "whoami", "pwd", "env", "pip", "python3",
    "curl",  # for http tasks (within sandbox)
]

# ─── Ensure directories exist ────────────────────────────────────────────────

def ensure_dirs():
    """Create required directories if they don't exist."""
    for d in [RESULTS_DIR, DATASETS_DIR, SANDBOX_DIR, KNOWLEDGE_BASE_DIR]:
        d.mkdir(parents=True, exist_ok=True)
