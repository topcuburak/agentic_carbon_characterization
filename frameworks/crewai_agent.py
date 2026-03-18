"""
CrewAI framework adapter.
Uses CrewAI's Agent and Task abstractions with LiteLLM for vLLM backend.
"""

import time
import json
from typing import Any

from frameworks.base import FrameworkAdapter, RunMetrics, LLMCall, ToolCall
from config import ModelConfig, VLLM_BASE_URL, VLLM_API_KEY, EXPERIMENT_CONFIG


class CrewAIAdapter(FrameworkAdapter):

    @property
    def name(self) -> str:
        return "crewai"

    def setup(self):
        import os
        # CrewAI uses LiteLLM under the hood — configure for vLLM
        os.environ["OPENAI_API_BASE"] = VLLM_BASE_URL
        os.environ["OPENAI_API_KEY"] = VLLM_API_KEY

        from crewai.tools import BaseTool
        from pydantic import Field

        # Convert our tools to CrewAI tools
        self._crewai_tools = []
        for tool_name, tool_info in self.tools.items():
            func = tool_info["function"]
            desc = tool_info["description"]
            params = tool_info["parameters"]

            # Dynamically create a CrewAI tool class for each tool
            tool_func = func
            tool_class = type(
                f"CrewAI_{tool_name}",
                (BaseTool,),
                {
                    "name": tool_name,
                    "description": desc,
                    "_run": lambda self, **kwargs, _f=tool_func: _f(**kwargs),
                },
            )
            self._crewai_tools.append(tool_class())

        # LiteLLM model string for vLLM
        self._model_string = f"openai/{self.model_config.model_id}"

    def _create_agent_and_task(self, task_prompt: str, system_prompt: str, max_steps: int):
        from crewai import Agent, Task, Crew

        agent = Agent(
            role="General Purpose Assistant",
            goal="Complete the given task accurately using available tools.",
            backstory=system_prompt or "You are a helpful assistant that uses tools to accomplish tasks.",
            tools=self._crewai_tools,
            llm=self._model_string,
            max_iter=max_steps,
            verbose=False,
        )

        task = Task(
            description=task_prompt,
            agent=agent,
            expected_output="A complete and accurate answer to the task.",
        )

        crew = Crew(
            agents=[agent],
            tasks=[task],
            verbose=False,
        )

        return crew

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

        crew = self._create_agent_and_task(task_prompt, system_prompt, max_steps)

        start = time.time()
        try:
            result = crew.kickoff()

            # Extract output
            metrics.final_output = str(result)

            # CrewAI exposes usage metrics on the result
            if hasattr(result, "token_usage"):
                usage = result.token_usage
                metrics.llm_calls.append(LLMCall(
                    input_tokens=getattr(usage, "prompt_tokens", 0) or getattr(usage, "total_tokens", 0) // 2,
                    output_tokens=getattr(usage, "completion_tokens", 0) or getattr(usage, "total_tokens", 0) // 2,
                    duration_ms=int((time.time() - start) * 1000),
                ))
            elif hasattr(result, "usage_metrics"):
                usage = result.usage_metrics
                if isinstance(usage, dict):
                    metrics.llm_calls.append(LLMCall(
                        input_tokens=usage.get("prompt_tokens", 0),
                        output_tokens=usage.get("completion_tokens", 0),
                        duration_ms=int((time.time() - start) * 1000),
                    ))

            metrics.success = True

        except Exception as e:
            metrics.error = str(e)
            metrics.success = False

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
        """Single-shot via direct LiteLLM call (no agent overhead)."""
        import litellm

        metrics = RunMetrics(
            framework=self.name,
            model=self.model_config.name,
            task_id=task_id,
            task_category=task_category,
        )

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": task_prompt})

        start = time.time()
        try:
            response = litellm.completion(
                model=self._model_string,
                messages=messages,
                max_tokens=self.model_config.max_tokens,
                temperature=self.model_config.temperature,
                api_base=VLLM_BASE_URL,
                api_key=VLLM_API_KEY,
            )

            usage = response.usage
            metrics.llm_calls.append(LLMCall(
                input_tokens=usage.prompt_tokens,
                output_tokens=usage.completion_tokens,
                duration_ms=int((time.time() - start) * 1000),
            ))
            metrics.final_output = response.choices[0].message.content or ""
            metrics.success = True

        except Exception as e:
            metrics.error = str(e)
            metrics.success = False

        metrics.wall_clock_ms = int((time.time() - start) * 1000)
        metrics.finalize()
        return metrics
