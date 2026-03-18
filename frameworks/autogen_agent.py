"""
AutoGen (Microsoft) framework adapter.
Uses AutoGen's AssistantAgent with OpenAI-compatible vLLM backend.
"""

import time
import json
from typing import Any

from frameworks.base import FrameworkAdapter, RunMetrics, LLMCall, ToolCall
from config import ModelConfig, VLLM_BASE_URL, VLLM_API_KEY, EXPERIMENT_CONFIG


class AutoGenAdapter(FrameworkAdapter):

    @property
    def name(self) -> str:
        return "autogen"

    def setup(self):
        from autogen_agentchat.agents import AssistantAgent
        from autogen_ext.models.openai import OpenAIChatCompletionClient

        self._client = OpenAIChatCompletionClient(
            model=self.model_config.model_id,
            base_url=VLLM_BASE_URL,
            api_key=VLLM_API_KEY,
            max_tokens=self.model_config.max_tokens,
            temperature=self.model_config.temperature,
        )

        # Convert tools to AutoGen format (function schemas + implementations)
        self._ag_tools = []
        for tool_name, tool_info in self.tools.items():
            func = tool_info["function"]
            # AutoGen uses decorated functions — we wrap ours
            self._ag_tools.append(func)

    def run_task(
        self,
        task_prompt: str,
        task_id: str,
        task_category: str,
        system_prompt: str = "",
        max_steps: int = 30,
    ) -> RunMetrics:
        import asyncio
        from autogen_agentchat.agents import AssistantAgent
        from autogen_agentchat.conditions import MaxMessageTermination
        from autogen_agentchat.teams import RoundRobinGroupChat

        metrics = RunMetrics(
            framework=self.name,
            model=self.model_config.name,
            task_id=task_id,
            task_category=task_category,
        )

        agent = AssistantAgent(
            name="assistant",
            model_client=self._client,
            tools=self._ag_tools,
            system_message=system_prompt or "You are a helpful assistant. Use available tools to complete tasks.",
        )

        termination = MaxMessageTermination(max_messages=max_steps * 2)
        team = RoundRobinGroupChat(
            participants=[agent],
            termination_condition=termination,
        )

        start = time.time()
        try:
            # Run the async agent synchronously
            loop = asyncio.new_event_loop()
            result = loop.run_until_complete(
                team.run(task=task_prompt)
            )
            loop.close()

            # Extract metrics from messages
            if hasattr(result, "messages"):
                for msg in result.messages:
                    msg_type = type(msg).__name__

                    # Collect LLM responses
                    if "AssistantMessage" in msg_type or "Response" in msg_type:
                        usage = getattr(msg, "models_usage", None)
                        input_tok = 0
                        output_tok = 0
                        if usage:
                            input_tok = getattr(usage, "prompt_tokens", 0)
                            output_tok = getattr(usage, "completion_tokens", 0)
                        metrics.llm_calls.append(LLMCall(
                            input_tokens=input_tok,
                            output_tokens=output_tok,
                            duration_ms=0,
                        ))
                        metrics.num_agent_steps += 1

                    # Collect tool calls
                    if "ToolCall" in msg_type:
                        content = getattr(msg, "content", [])
                        if isinstance(content, list):
                            for item in content:
                                if hasattr(item, "name"):
                                    metrics.tool_calls.append(ToolCall(
                                        tool_name=item.name,
                                        arguments=json.loads(item.arguments) if hasattr(item, "arguments") else {},
                                        result="",
                                        duration_ms=0,
                                    ))

            # Get final output from last message
            if hasattr(result, "messages") and result.messages:
                last = result.messages[-1]
                metrics.final_output = str(getattr(last, "content", ""))

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
        """Single-shot via direct OpenAI-compatible call."""
        import asyncio
        from autogen_core.models import UserMessage, SystemMessage

        metrics = RunMetrics(
            framework=self.name,
            model=self.model_config.name,
            task_id=task_id,
            task_category=task_category,
        )

        messages = []
        if system_prompt:
            messages.append(SystemMessage(content=system_prompt))
        messages.append(UserMessage(content=task_prompt, source="user"))

        start = time.time()
        try:
            loop = asyncio.new_event_loop()
            response = loop.run_until_complete(
                self._client.create(messages)
            )
            loop.close()

            usage = getattr(response, "usage", None)
            input_tok = getattr(usage, "prompt_tokens", 0) if usage else 0
            output_tok = getattr(usage, "completion_tokens", 0) if usage else 0

            metrics.llm_calls.append(LLMCall(
                input_tokens=input_tok,
                output_tokens=output_tok,
                duration_ms=int((time.time() - start) * 1000),
            ))
            metrics.final_output = response.content if hasattr(response, "content") else str(response)
            metrics.success = True

        except Exception as e:
            metrics.error = str(e)
            metrics.success = False

        metrics.wall_clock_ms = int((time.time() - start) * 1000)
        metrics.finalize()
        return metrics

    def teardown(self):
        pass
