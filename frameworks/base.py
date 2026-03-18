"""
Abstract base class for framework adapters.
All framework adapters must implement this interface.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any
from config import ModelConfig


@dataclass
class ToolCall:
    """Record of a single tool invocation."""
    tool_name: str
    arguments: dict
    result: str
    duration_ms: int          # Wall clock time
    cpu_time_ms: float = 0.0  # CPU user+system time consumed
    gpu_energy_j: float = 0.0 # GPU energy during this tool call
    cpu_energy_j: float = 0.0 # CPU energy during this tool call


@dataclass
class LLMCall:
    """Record of a single LLM invocation."""
    input_tokens: int
    output_tokens: int
    duration_ms: int            # Wall clock time
    cpu_time_ms: float = 0.0    # CPU time consumed during inference call
    gpu_energy_j: float = 0.0   # GPU energy during this LLM call
    cpu_energy_j: float = 0.0   # CPU energy during this LLM call
    # The prompt sent and completion received (optional, for debugging)
    prompt_preview: str = ""
    completion_preview: str = ""


@dataclass
class RunMetrics:
    """Metrics collected from a single task run."""
    framework: str
    model: str
    task_id: str
    task_category: str

    # Core metrics
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_tokens: int = 0
    num_llm_calls: int = 0
    num_tool_calls: int = 0
    num_agent_steps: int = 0
    wall_clock_ms: int = 0

    # Detailed logs
    llm_calls: list[LLMCall] = field(default_factory=list)
    tool_calls: list[ToolCall] = field(default_factory=list)

    # Final output
    final_output: str = ""
    success: bool = False
    error: str = ""

    # Per-tool breakdown
    tool_call_counts: dict[str, int] = field(default_factory=dict)
    tool_time_ms: dict[str, int] = field(default_factory=dict)
    tool_cpu_time_ms: dict[str, float] = field(default_factory=dict)
    tool_gpu_energy_j: dict[str, float] = field(default_factory=dict)
    tool_cpu_energy_j: dict[str, float] = field(default_factory=dict)

    # LLM call totals
    total_llm_cpu_time_ms: float = 0.0
    total_llm_gpu_energy_j: float = 0.0
    total_llm_cpu_energy_j: float = 0.0

    def finalize(self):
        """Compute derived metrics from logs."""
        self.total_input_tokens = sum(c.input_tokens for c in self.llm_calls)
        self.total_output_tokens = sum(c.output_tokens for c in self.llm_calls)
        self.total_tokens = self.total_input_tokens + self.total_output_tokens
        self.num_llm_calls = len(self.llm_calls)
        self.num_tool_calls = len(self.tool_calls)

        # Per-tool aggregation
        self.tool_call_counts = {}
        self.tool_time_ms = {}
        self.tool_cpu_time_ms = {}
        self.tool_gpu_energy_j = {}
        self.tool_cpu_energy_j = {}
        for tc in self.tool_calls:
            name = tc.tool_name
            self.tool_call_counts[name] = self.tool_call_counts.get(name, 0) + 1
            self.tool_time_ms[name] = self.tool_time_ms.get(name, 0) + tc.duration_ms
            self.tool_cpu_time_ms[name] = self.tool_cpu_time_ms.get(name, 0) + tc.cpu_time_ms
            self.tool_gpu_energy_j[name] = self.tool_gpu_energy_j.get(name, 0) + tc.gpu_energy_j
            self.tool_cpu_energy_j[name] = self.tool_cpu_energy_j.get(name, 0) + tc.cpu_energy_j

        # LLM call totals
        self.total_llm_cpu_time_ms = sum(c.cpu_time_ms for c in self.llm_calls)
        self.total_llm_gpu_energy_j = sum(c.gpu_energy_j for c in self.llm_calls)
        self.total_llm_cpu_energy_j = sum(c.cpu_energy_j for c in self.llm_calls)


class FrameworkAdapter(ABC):
    """
    Abstract base class for framework adapters.

    Each adapter wraps a specific agentic framework and exposes
    a uniform interface for running tasks and collecting metrics.
    """

    def __init__(self, model_config: ModelConfig, tools: dict[str, Any]):
        """
        Initialize the adapter.

        Args:
            model_config: Configuration for the LLM to use.
            tools: Tool registry dict from tools/__init__.py.
        """
        self.model_config = model_config
        self.tools = tools
        self._metrics: RunMetrics | None = None

    @property
    @abstractmethod
    def name(self) -> str:
        """Framework name (e.g., 'langgraph', 'crewai')."""
        ...

    @abstractmethod
    def setup(self):
        """
        One-time setup: initialize the framework, register tools, configure LLM.
        Called once before running any tasks.
        """
        ...

    @abstractmethod
    def run_task(
        self,
        task_prompt: str,
        task_id: str,
        task_category: str,
        system_prompt: str = "",
        max_steps: int = 30,
    ) -> RunMetrics:
        """
        Run a single task and return metrics.

        This method must:
        1. Execute the agent with the given prompt
        2. Collect all LLM calls and tool calls
        3. Return a populated RunMetrics object

        Args:
            task_prompt: The task instruction for the agent.
            task_id: Unique identifier for this task.
            task_category: Category name (e.g., 'multihop_qa').
            system_prompt: Optional system prompt.
            max_steps: Maximum number of agent loop iterations.

        Returns:
            RunMetrics with all collected data.
        """
        ...

    @abstractmethod
    def run_single_shot(
        self,
        task_prompt: str,
        task_id: str,
        task_category: str,
        system_prompt: str = "",
    ) -> RunMetrics:
        """
        Run a single-shot (non-agentic) baseline.
        One LLM call, no tools, no iteration.

        Args:
            task_prompt: The task instruction.
            task_id: Unique identifier for this task.
            task_category: Category name.
            system_prompt: Optional system prompt.

        Returns:
            RunMetrics with single LLM call data.
        """
        ...

    def teardown(self):
        """Optional cleanup after all tasks are done."""
        pass
