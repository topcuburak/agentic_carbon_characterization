"""
OpenAI Agents SDK framework adapter.
Uses openai-agents with vLLM backend via OpenAI-compatible endpoint.
"""

import time
import json
from typing import Any

from frameworks.base import FrameworkAdapter, RunMetrics, LLMCall, ToolCall
from config import ModelConfig, VLLM_BASE_URL, VLLM_API_KEY, EXPERIMENT_CONFIG


class OpenAIAgentsAdapter(FrameworkAdapter):

    @property
    def name(self) -> str:
        return "openai_agents"

    def setup(self):
        from agents import Agent, function_tool, ModelSettings
        from openai import AsyncOpenAI

        # Configure OpenAI client to point at vLLM
        self._openai_client = AsyncOpenAI(
            base_url=VLLM_BASE_URL,
            api_key=VLLM_API_KEY,
        )

        self._model_settings = ModelSettings(
            max_tokens=self.model_config.max_tokens,
            temperature=self.model_config.temperature,
        )

        # Convert our tools to OpenAI Agents SDK function tools
        self._oai_tools = []
        for tool_name, tool_info in self.tools.items():
            func = tool_info["function"]
            # Wrap with @function_tool decorator
            wrapped = function_tool(func)
            self._oai_tools.append(wrapped)

    def _create_agent(self, system_prompt: str):
        from agents import Agent

        return Agent(
            name="benchmark_agent",
            instructions=system_prompt or "You are a helpful assistant. Use available tools to complete tasks accurately.",
            model=self.model_config.model_id,
            tools=self._oai_tools,
            model_settings=self._model_settings,
        )

    def run_task(
        self,
        task_prompt: str,
        task_id: str,
        task_category: str,
        system_prompt: str = "",
        max_steps: int = 30,
    ) -> RunMetrics:
        import asyncio
        from agents import Runner

        metrics = RunMetrics(
            framework=self.name,
            model=self.model_config.name,
            task_id=task_id,
            task_category=task_category,
        )

        agent = self._create_agent(system_prompt)

        start = time.time()
        try:
            loop = asyncio.new_event_loop()
            result = loop.run_until_complete(
                Runner.run(
                    agent,
                    task_prompt,
                    max_turns=max_steps,
                )
            )
            loop.close()

            metrics.final_output = result.final_output if hasattr(result, "final_output") else str(result)

            # Extract from raw responses if available
            if hasattr(result, "raw_responses"):
                for resp in result.raw_responses:
                    usage = getattr(resp, "usage", None)
                    input_tok = getattr(usage, "prompt_tokens", 0) if usage else 0
                    output_tok = getattr(usage, "completion_tokens", 0) if usage else 0
                    metrics.llm_calls.append(LLMCall(
                        input_tokens=input_tok,
                        output_tokens=output_tok,
                        duration_ms=0,
                    ))

            # Extract tool calls from new_items if available
            if hasattr(result, "new_items"):
                for item in result.new_items:
                    item_type = type(item).__name__
                    if "ToolCall" in item_type:
                        metrics.tool_calls.append(ToolCall(
                            tool_name=getattr(item, "name", "unknown"),
                            arguments=getattr(item, "arguments", {}),
                            result=getattr(item, "output", ""),
                            duration_ms=0,
                        ))
                    elif "ModelResponse" in item_type or "Response" in item_type:
                        usage = getattr(item, "usage", None)
                        if usage and not metrics.llm_calls:
                            metrics.llm_calls.append(LLMCall(
                                input_tokens=getattr(usage, "input_tokens", 0),
                                output_tokens=getattr(usage, "output_tokens", 0),
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
        """Single-shot via direct OpenAI API call."""
        import asyncio

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
            loop = asyncio.new_event_loop()
            response = loop.run_until_complete(
                self._openai_client.chat.completions.create(
                    model=self.model_config.model_id,
                    messages=messages,
                    max_tokens=self.model_config.max_tokens,
                    temperature=self.model_config.temperature,
                )
            )
            loop.close()

            usage = response.usage
            metrics.llm_calls.append(LLMCall(
                input_tokens=usage.prompt_tokens if usage else 0,
                output_tokens=usage.completion_tokens if usage else 0,
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
