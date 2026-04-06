import uuid
from typing import Any

from sqlalchemy.orm import Session

from app.config import settings
from app.providers.llm_provider_adapter import build_provider
from app.schemas.chat import AgentInfo, ChatRequest, ChatResponse, UsageDTO
from app.services.history_service import HistoryService
from app.services.metrics_service import MetricsService
from app.services.react_orchestrator import ReactOrchestrator


class ChatService:
    def __init__(self, db: Session):
        self.db = db
        self.history = HistoryService(db)
        self.metrics = MetricsService(db)
        self.llm = build_provider()

    def handle_turn(self, req: ChatRequest) -> ChatResponse:
        correlation_id = str(uuid.uuid4())

        user_msg = self.history.add_message(session_id=req.session_id, role="user", content=req.message)
        history = self.history.get_history(session_id=req.session_id, limit=100)
        history_text = "\n".join([f"{m.role}: {m.content}" for m in history])

        if req.mode == "simple":
            return self._run_simple(req=req, correlation_id=correlation_id, history_text=history_text)
        return self._run_agent(req=req, correlation_id=correlation_id, history_text=history_text)

    def _run_simple(self, *, req: ChatRequest, correlation_id: str, history_text: str) -> ChatResponse:
        # Nhanh gon cho baseline chatbot (one-shot LLM).
        result: dict[str, Any] = self.llm.generate(
            prompt=f"Lich su:\n{history_text}\n\nUser: {req.message}",
            system_prompt=(
                "Ban la tro ly du lich than thien. "
                "Tra loi ngan gon, ro rang, va khong khang dinh du lieu realtime neu khong co cong cu."
            ),
        )
        content = str(result.get("content", "")).strip() or "Minh da nhan cau hoi cua ban."
        usage = result.get("usage", {}) or {}
        latency_ms = int(result.get("latency_ms", 0))

        assistant = self.history.add_message(session_id=req.session_id, role="assistant", content=content)
        self.metrics.log_event(
            session_id=req.session_id,
            correlation_id=correlation_id,
            component="travel_chat",
            event_type="llm_call",
            duration_ms=latency_ms,
            prompt_tokens=int(usage.get("prompt_tokens", 0)),
            completion_tokens=int(usage.get("completion_tokens", 0)),
            metadata_json={"mode": "simple", "provider": result.get("provider", "unknown")},
        )
        self.metrics.log_event(
            session_id=req.session_id,
            correlation_id=correlation_id,
            component="travel_chat",
            event_type="turn_complete",
            duration_ms=latency_ms,
            metadata_json={"mode": "simple"},
        )

        return ChatResponse(
            reply=content,
            correlation_id=correlation_id,
            session_id=req.session_id,
            assistant_message_id=assistant.id,
            usage=UsageDTO(
                prompt_tokens=int(usage.get("prompt_tokens", 0)),
                completion_tokens=int(usage.get("completion_tokens", 0)),
                total_ms=latency_ms,
            ),
        )

    def _run_agent(self, *, req: ChatRequest, correlation_id: str, history_text: str) -> ChatResponse:
        max_steps = settings.react_max_steps_default
        if req.options and req.options.max_steps:
            max_steps = req.options.max_steps

        orchestrator = ReactOrchestrator(self.llm, self.metrics)
        run = orchestrator.run(
            session_id=req.session_id,
            correlation_id=correlation_id,
            user_input=req.message,
            history_text=history_text,
            max_steps=max_steps,
        )

        assistant = self.history.add_message(session_id=req.session_id, role="assistant", content=run.reply)
        self.metrics.log_event(
            session_id=req.session_id,
            correlation_id=correlation_id,
            component="travel_chat",
            event_type="turn_complete",
            duration_ms=run.total_ms,
            prompt_tokens=run.usage_prompt_tokens,
            completion_tokens=run.usage_completion_tokens,
            metadata_json={"mode": "agent", "steps_used": run.steps_used},
        )

        return ChatResponse(
            reply=run.reply,
            correlation_id=correlation_id,
            session_id=req.session_id,
            assistant_message_id=assistant.id,
            usage=UsageDTO(
                prompt_tokens=run.usage_prompt_tokens,
                completion_tokens=run.usage_completion_tokens,
                total_ms=run.total_ms,
            ),
            agent=AgentInfo(mode="agent", steps_used=run.steps_used, tools_called=run.tools_called),
        )
