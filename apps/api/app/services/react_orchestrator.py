import json
import re
from dataclasses import dataclass
from typing import Any

from app.services.metrics_service import MetricsService
from app.services.tool_executor import ToolExecutor
from app.tools.registry import TOOLS


ACTION_PATTERN = re.compile(r"Action:\s*([a-zA-Z0-9_]+)\((\{.*\})\)", re.DOTALL)
FINAL_PATTERN = re.compile(r"Final Answer:\s*(.*)", re.DOTALL)


@dataclass
class AgentRunResult:
    reply: str
    steps_used: int
    tools_called: list[str]
    usage_prompt_tokens: int
    usage_completion_tokens: int
    total_ms: int


class ReactOrchestrator:
    def __init__(self, llm: Any, metrics: MetricsService):
        self.llm = llm
        self.metrics = metrics
        self.executor = ToolExecutor()

    def _system_prompt(self) -> str:
        tool_lines = "\n".join([f"- {t.name}: {t.description}" for t in TOOLS])
        # Huong dan format de parser backend xu ly on dinh (strict action format).
        return (
            "Ban la tro ly du lich theo kieu ReAct.\n"
            "Cong cu co san:\n"
            f"{tool_lines}\n\n"
            "Tra ve mot trong hai dinh dang:\n"
            '1) Action: tool_name({"key":"value"})\n'
            "2) Final Answer: ...\n"
            "Khong dung markdown code fence."
        )

    def run(
        self,
        *,
        session_id: str,
        correlation_id: str,
        user_input: str,
        history_text: str,
        max_steps: int,
    ) -> AgentRunResult:
        prompt_context = f"Lich su:\n{history_text}\n\nYeu cau moi:\n{user_input}"
        steps = 0
        tools_called: list[str] = []
        sum_prompt = 0
        sum_completion = 0
        sum_latency = 0

        while steps < max_steps:
            response = self.llm.generate(prompt_context, system_prompt=self._system_prompt())
            content = response.get("content", "")
            usage = response.get("usage", {}) or {}
            latency_ms = int(response.get("latency_ms", 0))
            sum_prompt += int(usage.get("prompt_tokens", 0))
            sum_completion += int(usage.get("completion_tokens", 0))
            sum_latency += latency_ms

            self.metrics.log_event(
                session_id=session_id,
                correlation_id=correlation_id,
                component="travel_chat",
                event_type="llm_call",
                duration_ms=latency_ms,
                prompt_tokens=int(usage.get("prompt_tokens", 0)),
                completion_tokens=int(usage.get("completion_tokens", 0)),
                step_index=steps,
                metadata_json={"phase": "react", "provider": response.get("provider", "unknown")},
            )

            final_match = FINAL_PATTERN.search(content)
            if final_match:
                final_reply = final_match.group(1).strip()
                if not final_reply:
                    final_reply = "Minh da xu ly xong yeu cau du lich cua ban."
                return AgentRunResult(
                    reply=final_reply,
                    steps_used=steps + 1,
                    tools_called=tools_called,
                    usage_prompt_tokens=sum_prompt,
                    usage_completion_tokens=sum_completion,
                    total_ms=sum_latency,
                )

            action_match = ACTION_PATTERN.search(content)
            if not action_match:
                self.metrics.log_event(
                    session_id=session_id,
                    correlation_id=correlation_id,
                    component="travel_chat",
                    event_type="parse_error",
                    step_index=steps,
                    error_code="JSON_PARSE",
                    metadata_json={"raw_snippet": content[:500]},
                    message="Khong parse duoc Action.",
                )
                prompt_context += "\nObservation: Parse error. Please output valid Action format."
                steps += 1
                continue

            tool_name = action_match.group(1)
            raw_args = action_match.group(2)
            try:
                args = json.loads(raw_args)
            except json.JSONDecodeError:
                self.metrics.log_event(
                    session_id=session_id,
                    correlation_id=correlation_id,
                    component="travel_chat",
                    event_type="parse_error",
                    step_index=steps,
                    error_code="JSON_PARSE",
                    metadata_json={"raw_args": raw_args[:500]},
                    message="Action args is not valid JSON",
                )
                prompt_context += "\nObservation: Action args invalid JSON."
                steps += 1
                continue

            tools_called.append(tool_name)
            tool_result, tool_duration = self.executor.execute(tool_name, args)
            self.metrics.log_event(
                session_id=session_id,
                correlation_id=correlation_id,
                component="travel_chat",
                event_type="tool_call",
                duration_ms=tool_duration,
                step_index=steps,
                error_code=tool_result.error_code,
                metadata_json={
                    "tool_name": tool_name,
                    "arguments_redacted": args,
                    "ok": tool_result.ok,
                },
                message=tool_result.message,
            )
            self.metrics.log_tool_invocation(
                session_id=session_id,
                correlation_id=correlation_id,
                step_index=steps,
                tool_name=tool_name,
                arguments_json=args,
                result_ok=tool_result.ok,
                result_text=tool_result.data,
                error_code=tool_result.error_code,
                duration_ms=tool_duration,
            )

            observation = tool_result.data if tool_result.ok else f"Tool error: {tool_result.message}"
            prompt_context += f"\nObservation: {observation}\nPlease continue."
            steps += 1

        self.metrics.log_event(
            session_id=session_id,
            correlation_id=correlation_id,
            component="travel_chat",
            event_type="turn_complete",
            step_index=steps,
            error_code="MAX_STEPS",
            metadata_json={"mode": "agent", "steps_used": steps},
            message="Agent reached max steps.",
        )
        return AgentRunResult(
            reply=(
                "Minh da dat gioi han so buoc xu ly. "
                "Ban co the dat cau hoi cu the hon de minh tra loi chinh xac."
            ),
            steps_used=steps,
            tools_called=tools_called,
            usage_prompt_tokens=sum_prompt,
            usage_completion_tokens=sum_completion,
            total_ms=sum_latency,
        )
