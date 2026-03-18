"""
Mock framework adapter for local testing.
Simulates LLM calls and tool usage with fake data to validate the logging pipeline.
"""

import time
import random
from typing import Any

from frameworks.base import FrameworkAdapter, RunMetrics, LLMCall, ToolCall
from config import ModelConfig


class MockAdapter(FrameworkAdapter):
    """Simulates an agentic framework with fake LLM and tool calls."""

    @property
    def name(self) -> str:
        return "mock"

    def setup(self):
        pass

    def run_task(
        self,
        task_prompt: str,
        task_id: str,
        task_category: str,
        system_prompt: str = "",
        max_steps: int = 30,
    ) -> RunMetrics:
        metrics = RunMetrics(
            framework=self.name,
            model=self.model_config.name,
            task_id=task_id,
            task_category=task_category,
        )

        from power_monitor import Phase

        start = time.time()
        self._set_phase(Phase.ORCHESTRATION)

        # Simulate 2-5 agent steps
        num_steps = random.randint(2, 5)
        for step in range(num_steps):
            # Simulate LLM call
            self._set_phase(Phase.INFERENCE)
            input_tok = random.randint(200, 800)
            output_tok = random.randint(50, 300)
            llm_dur = random.randint(100, 500)
            time.sleep(0.05)  # Small delay to make power traces interesting

            metrics.llm_calls.append(LLMCall(
                input_tokens=input_tok,
                output_tokens=output_tok,
                duration_ms=llm_dur,
                prompt_preview=task_prompt[:100],
                completion_preview=f"[Mock step {step+1} response]",
            ))

            # Simulate tool call (not on last step)
            if step < num_steps - 1:
                self._set_phase(Phase.TOOL_EXECUTION)
                from tools.instrumented import call_tool_instrumented

                tool_names = list(self.tools.keys())
                tool_name = random.choice(tool_names)

                # Build simple test arguments per tool
                test_args = {
                    "calculator": {"expression": "2 + 2"},
                    "search": {"query": "Brazil GDP"},
                    "web_lookup": {"topic": "renewable energy Germany"},
                    "database_query": {"sql": "SELECT COUNT(*) as cnt FROM sales"},
                    "python_exec": {"code": "import math; print(sum(range(1000)))"},
                    "shell_exec": {"command": "echo test"},
                    "http_request": {"url": "http://127.0.0.1:8100/api/health"},
                    "list_files": {"directory": "."},
                    "write_file": {"path": "test_output.txt", "content": "mock output"},
                    "read_file": {"path": "test_output.txt"},
                }
                args = test_args.get(tool_name, {})

                # Instrumented call — captures CPU time, GPU/CPU energy
                instr = call_tool_instrumented(tool_name, args)

                metrics.tool_calls.append(ToolCall(
                    tool_name=tool_name,
                    arguments=args,
                    result=instr["result"][:200],
                    duration_ms=instr["duration_ms"],
                    cpu_time_ms=instr["cpu_time_ms"],
                    gpu_energy_j=instr["gpu_energy_j"],
                    cpu_energy_j=instr["cpu_energy_j"],
                ))

            self._set_phase(Phase.ORCHESTRATION)
            metrics.num_agent_steps += 1

        self._set_phase(Phase.IDLE)
        metrics.final_output = f"[Mock answer for {task_id}] The answer is 42."
        metrics.success = True
        metrics.wall_clock_ms = int((time.time() - start) * 1000)
        metrics.finalize()
        return metrics

    def run_single_shot(
        self,
        task_prompt: str,
        task_id: str,
        task_category: str,
        system_prompt: str = "",
    ) -> RunMetrics:
        metrics = RunMetrics(
            framework=self.name,
            model=self.model_config.name,
            task_id=task_id,
            task_category=task_category,
        )

        from power_monitor import Phase

        start = time.time()
        self._set_phase(Phase.INFERENCE)
        time.sleep(0.02)

        input_tok = random.randint(150, 500)
        output_tok = random.randint(100, 400)

        metrics.llm_calls.append(LLMCall(
            input_tokens=input_tok,
            output_tokens=output_tok,
            duration_ms=random.randint(50, 200),
            prompt_preview=task_prompt[:100],
            completion_preview="[Mock single-shot response]",
        ))

        self._set_phase(Phase.IDLE)
        metrics.final_output = f"[Mock baseline answer for {task_id}]"
        metrics.success = True
        metrics.wall_clock_ms = int((time.time() - start) * 1000)
        metrics.finalize()
        return metrics
