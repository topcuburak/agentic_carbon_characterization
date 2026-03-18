"""
smolagents (HuggingFace) framework adapter.
Uses smolagents' ToolCallingAgent with vLLM backend.
"""

import time
import json
from typing import Any

from frameworks.base import FrameworkAdapter, RunMetrics, LLMCall, ToolCall
from config import ModelConfig, VLLM_BASE_URL, VLLM_API_KEY, EXPERIMENT_CONFIG


class SmolagentsAdapter(FrameworkAdapter):

    @property
    def name(self) -> str:
        return "smolagents"

    def setup(self):
        from smolagents import Tool, OpenAIServerModel

        # Configure model to point at vLLM
        self._model = OpenAIServerModel(
            model_id=self.model_config.model_id,
            api_base=VLLM_BASE_URL,
            api_key=VLLM_API_KEY,
            max_tokens=self.model_config.max_tokens,
            temperature=self.model_config.temperature,
        )

        # Convert our tools to smolagents Tool objects
        self._sm_tools = []
        for tool_name, tool_info in self.tools.items():
            func = tool_info["function"]
            desc = tool_info["description"]
            params = tool_info["parameters"]

            # Build input/output types for smolagents
            inputs = {}
            for pname, pspec in params.get("properties", {}).items():
                inputs[pname] = {
                    "type": pspec.get("type", "string"),
                    "description": pspec.get("description", ""),
                }

            # Create a Tool subclass dynamically
            tool_func = func
            tool_class = type(
                f"Smol_{tool_name}",
                (Tool,),
                {
                    "name": tool_name,
                    "description": desc,
                    "inputs": inputs,
                    "output_type": "string",
                    "forward": lambda self, _f=tool_func, **kwargs: _f(**kwargs),
                },
            )
            self._sm_tools.append(tool_class())

    def run_task(
        self,
        task_prompt: str,
        task_id: str,
        task_category: str,
        system_prompt: str = "",
        max_steps: int = 30,
    ) -> RunMetrics:
        from smolagents import ToolCallingAgent

        metrics = RunMetrics(
            framework=self.name,
            model=self.model_config.name,
            task_id=task_id,
            task_category=task_category,
        )

        agent = ToolCallingAgent(
            tools=self._sm_tools,
            model=self._model,
            max_steps=max_steps,
        )

        if system_prompt:
            agent.system_prompt = system_prompt

        start = time.time()
        try:
            result = agent.run(task_prompt)
            metrics.final_output = str(result)

            # Extract metrics from agent logs
            if hasattr(agent, "logs"):
                for step in agent.logs:
                    # Each step may contain an LLM call and tool calls
                    if hasattr(step, "input_token_count") or hasattr(step, "token_count"):
                        input_tok = getattr(step, "input_token_count", 0) or 0
                        output_tok = getattr(step, "output_token_count", 0) or 0
                        metrics.llm_calls.append(LLMCall(
                            input_tokens=input_tok,
                            output_tokens=output_tok,
                            duration_ms=0,
                        ))
                    if hasattr(step, "tool_calls"):
                        for tc in step.tool_calls:
                            tool_name = tc.name if hasattr(tc, "name") else str(tc.get("name", "unknown"))
                            args = tc.arguments if hasattr(tc, "arguments") else tc.get("arguments", {})
                            metrics.tool_calls.append(ToolCall(
                                tool_name=tool_name,
                                arguments=args if isinstance(args, dict) else {},
                                result="",
                                duration_ms=0,
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
        """Single-shot via direct model call."""
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
            response = self._model(messages)

            # Extract text and token counts
            output_text = str(response)
            # smolagents model returns a ChatMessage; try to get usage
            input_tok = 0
            output_tok = 0
            if hasattr(response, "token_usage"):
                input_tok = getattr(response.token_usage, "input_tokens", 0)
                output_tok = getattr(response.token_usage, "output_tokens", 0)

            metrics.llm_calls.append(LLMCall(
                input_tokens=input_tok,
                output_tokens=output_tok,
                duration_ms=int((time.time() - start) * 1000),
            ))
            metrics.final_output = output_text
            metrics.success = True

        except Exception as e:
            metrics.error = str(e)
            metrics.success = False

        metrics.wall_clock_ms = int((time.time() - start) * 1000)
        metrics.finalize()
        return metrics
