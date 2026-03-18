"""
LangGraph framework adapter.
Uses LangGraph's prebuilt ReAct agent with tool calling via OpenAI-compatible endpoint.
"""

import time
import json
from typing import Any

from frameworks.base import FrameworkAdapter, RunMetrics, LLMCall, ToolCall
from config import ModelConfig, VLLM_BASE_URL, VLLM_API_KEY, EXPERIMENT_CONFIG


class LangGraphAdapter(FrameworkAdapter):

    @property
    def name(self) -> str:
        return "langgraph"

    def setup(self):
        from langchain_openai import ChatOpenAI
        from langchain_core.tools import StructuredTool

        self._llm = ChatOpenAI(
            model=self.model_config.model_id,
            openai_api_base=VLLM_BASE_URL,
            openai_api_key=VLLM_API_KEY,
            max_tokens=self.model_config.max_tokens,
            temperature=self.model_config.temperature,
        )

        # Convert our tool registry to LangChain tools
        self._lc_tools = []
        for tool_name, tool_info in self.tools.items():
            func = tool_info["function"]
            desc = tool_info["description"]
            params = tool_info["parameters"]

            # Build argument schema from our parameters spec
            lc_tool = StructuredTool.from_function(
                func=func,
                name=tool_name,
                description=desc,
            )
            self._lc_tools.append(lc_tool)

    def run_task(
        self,
        task_prompt: str,
        task_id: str,
        task_category: str,
        system_prompt: str = "",
        max_steps: int = 30,
    ) -> RunMetrics:
        from langgraph.prebuilt import create_react_agent
        from langchain_core.messages import HumanMessage, SystemMessage

        metrics = RunMetrics(
            framework=self.name,
            model=self.model_config.name,
            task_id=task_id,
            task_category=task_category,
        )

        agent = create_react_agent(self._llm, self._lc_tools)

        messages = []
        if system_prompt:
            messages.append(SystemMessage(content=system_prompt))
        messages.append(HumanMessage(content=task_prompt))

        start = time.time()
        try:
            config = {"recursion_limit": max_steps * 2}
            result = agent.invoke({"messages": messages}, config=config)

            # Extract metrics from the message history
            for msg in result["messages"]:
                msg_type = type(msg).__name__

                if msg_type == "AIMessage":
                    usage = getattr(msg, "usage_metadata", None) or {}
                    input_tok = usage.get("input_tokens", 0) if isinstance(usage, dict) else getattr(usage, "input_tokens", 0)
                    output_tok = usage.get("output_tokens", 0) if isinstance(usage, dict) else getattr(usage, "output_tokens", 0)

                    llm_call = LLMCall(
                        input_tokens=input_tok,
                        output_tokens=output_tok,
                        duration_ms=0,  # Not available per-call from LangGraph
                        prompt_preview=task_prompt[:200],
                        completion_preview=str(msg.content)[:200],
                    )
                    metrics.llm_calls.append(llm_call)
                    metrics.num_agent_steps += 1

                    # Check for tool calls in the message
                    if hasattr(msg, "tool_calls") and msg.tool_calls:
                        for tc in msg.tool_calls:
                            tool_call = ToolCall(
                                tool_name=tc.get("name", "unknown"),
                                arguments=tc.get("args", {}),
                                result="",  # Result comes in ToolMessage
                                duration_ms=0,
                            )
                            metrics.tool_calls.append(tool_call)

                elif msg_type == "ToolMessage":
                    # Match result to the last tool call
                    if metrics.tool_calls:
                        metrics.tool_calls[-1].result = str(msg.content)[:500]

            # Get final output
            final_msgs = [m for m in result["messages"] if type(m).__name__ == "AIMessage"]
            if final_msgs:
                metrics.final_output = str(final_msgs[-1].content)

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
        from langchain_core.messages import HumanMessage, SystemMessage

        metrics = RunMetrics(
            framework=self.name,
            model=self.model_config.name,
            task_id=task_id,
            task_category=task_category,
        )

        messages = []
        if system_prompt:
            messages.append(SystemMessage(content=system_prompt))
        messages.append(HumanMessage(content=task_prompt))

        start = time.time()
        try:
            response = self._llm.invoke(messages)
            usage = getattr(response, "usage_metadata", None) or {}
            input_tok = usage.get("input_tokens", 0) if isinstance(usage, dict) else getattr(usage, "input_tokens", 0)
            output_tok = usage.get("output_tokens", 0) if isinstance(usage, dict) else getattr(usage, "output_tokens", 0)

            metrics.llm_calls.append(LLMCall(
                input_tokens=input_tok,
                output_tokens=output_tok,
                duration_ms=int((time.time() - start) * 1000),
                prompt_preview=task_prompt[:200],
                completion_preview=str(response.content)[:200],
            ))
            metrics.final_output = str(response.content)
            metrics.success = True

        except Exception as e:
            metrics.error = str(e)
            metrics.success = False

        metrics.wall_clock_ms = int((time.time() - start) * 1000)
        metrics.finalize()
        return metrics
