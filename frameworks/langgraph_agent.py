"""
LangGraph framework adapter.
Uses LangGraph's prebuilt ReAct agent with streaming for phase-aware power monitoring.
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
        from power_monitor import Phase

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

            # Stream events for phase-aware power monitoring
            self._set_phase(Phase.ORCHESTRATION)

            for event in agent.stream({"messages": messages}, config=config, stream_mode="updates"):
                for node_name, node_output in event.items():
                    if node_name == "agent":
                        # LLM just finished generating
                        self._set_phase(Phase.ORCHESTRATION)

                        msgs = node_output.get("messages", [])
                        for msg in msgs:
                            msg_type = type(msg).__name__
                            if msg_type == "AIMessage":
                                usage = getattr(msg, "usage_metadata", None) or {}
                                input_tok = usage.get("input_tokens", 0) if isinstance(usage, dict) else getattr(usage, "input_tokens", 0)
                                output_tok = usage.get("output_tokens", 0) if isinstance(usage, dict) else getattr(usage, "output_tokens", 0)

                                llm_call = LLMCall(
                                    input_tokens=input_tok,
                                    output_tokens=output_tok,
                                    duration_ms=0,
                                    prompt_preview=task_prompt[:200],
                                    completion_preview=str(msg.content)[:200],
                                )
                                metrics.llm_calls.append(llm_call)
                                metrics.num_agent_steps += 1

                                # Check for tool calls
                                if hasattr(msg, "tool_calls") and msg.tool_calls:
                                    # Next node will be tool execution
                                    self._set_phase(Phase.TOOL_EXECUTION)
                                    for tc in msg.tool_calls:
                                        tool_call = ToolCall(
                                            tool_name=tc.get("name", "unknown"),
                                            arguments=tc.get("args", {}),
                                            result="",
                                            duration_ms=0,
                                        )
                                        metrics.tool_calls.append(tool_call)
                                else:
                                    # No tool calls = final answer, back to inference for any follow-up
                                    self._set_phase(Phase.INFERENCE)

                    elif node_name == "tools":
                        # Tools just finished executing
                        self._set_phase(Phase.ORCHESTRATION)

                        msgs = node_output.get("messages", [])
                        tool_msg_idx = 0
                        for msg in msgs:
                            if type(msg).__name__ == "ToolMessage":
                                # Match result to tool calls
                                pending = [tc for tc in metrics.tool_calls if not tc.result]
                                if pending:
                                    pending[0].result = str(msg.content)[:500]

                        # Next step: LLM inference
                        self._set_phase(Phase.INFERENCE)

            # Get final output
            self._set_phase(Phase.ORCHESTRATION)
            if metrics.llm_calls:
                last_call = metrics.llm_calls[-1]
                metrics.final_output = last_call.completion_preview

            metrics.success = True

        except Exception as e:
            metrics.error = str(e)
            metrics.success = False

        self._set_phase(Phase.IDLE)
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
        from power_monitor import Phase

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
            self._set_phase(Phase.INFERENCE)
            response = self._llm.invoke(messages)
            self._set_phase(Phase.IDLE)

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

        self._set_phase(Phase.IDLE)
        metrics.wall_clock_ms = int((time.time() - start) * 1000)
        metrics.finalize()
        return metrics
