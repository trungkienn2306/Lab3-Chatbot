import os
import sys
import time
from pathlib import Path
from typing import Any

from app.config import settings


# Bo sung repo root vao PYTHONPATH de tai su dung provider co san (reuse provider).
REPO_ROOT = Path(__file__).resolve().parents[4]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


class MockLLMProvider:
    def __init__(self, model_name: str = "mock-model") -> None:
        self.model_name = model_name

    def generate(self, prompt: str, system_prompt: str | None = None) -> dict[str, Any]:
        start = time.time()
        content = self._mock_response(prompt)
        latency_ms = int((time.time() - start) * 1000)
        usage = {
            "prompt_tokens": max(1, len(prompt) // 4),
            "completion_tokens": max(1, len(content) // 4),
            "total_tokens": max(1, (len(prompt) + len(content)) // 4),
        }
        return {
            "content": content,
            "usage": usage,
            "latency_ms": latency_ms,
            "provider": "mock",
        }

    def _mock_response(self, prompt: str) -> str:
        # Sau buoc tool, prompt se chua Observation — mock ket thuc bang Final Answer (complete ReAct).
        low = prompt.lower()
        if "observation:" in low:
            tail = prompt.rsplit("Observation:", 1)[-1]
            tail = tail.split("Please continue.")[0].strip()
            if tail.lower().startswith("parse error") or tail.lower().startswith("tool error"):
                return (
                    "Final Answer: Minh khong hoan tat buoc truoc do. "
                    "Ban gui lai yeu cau ro hon hoac thu lai sau."
                )
            return f"Final Answer: {tail}"

        p = prompt.lower()
        if "quy doi" in p or "usd" in p:
            return 'Thought: Can quy doi tien.\nAction: get_exchange_rate({"from_currency":"USD","to_currency":"VND","amount":100})'
        if "ngan sach" in p or "da lat" in p:
            return (
                'Thought: Can uoc tinh va tong hop chi phi.\n'
                'Action: estimate_stay_budget({"city":"da lat","nights":2,"comfort":"standard"})'
            )
        if "9999-99-99" in p or "99/99/2099" in p:
            return (
                'Thought: Can kiem tra ngay bay.\n'
                'Action: validate_flight_request({"origin_iata":"HAN","dest_iata":"SGN","departure_date":"9999-99-99"})'
            )
        if "hack" in p or "tai khoan" in p:
            return (
                'Thought: Yeu cau nhay cam.\n'
                'Action: escalate_to_human({"reason":"out_of_scope","user_summary":"security request"})'
            )
        return (
            "Final Answer: Minh la tro ly du lich. Ban co the hoi ve lich trinh, ngan sach, "
            "goi y diem den hoac quy doi tien te."
        )


def build_provider():
    provider_name = settings.llm_provider.lower().strip()
    if provider_name == "openai":
        from src.core.openai_provider import OpenAIProvider

        api_key = settings.llm_api_key or os.getenv("OPENAI_API_KEY")
        if not api_key:
            return MockLLMProvider()
        return OpenAIProvider(model_name=settings.llm_model, api_key=api_key)
    if provider_name == "gemini":
        from src.core.gemini_provider import GeminiProvider

        api_key = settings.gemini_api_key
        if not api_key:
            return MockLLMProvider()
        return GeminiProvider(model_name=settings.llm_model, api_key=api_key)
    return MockLLMProvider()
