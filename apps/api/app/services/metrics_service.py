from typing import Any

from sqlalchemy.orm import Session

from app.config import settings
from app.models.lab_metric_log import LabMetricLog
from app.models.tool_invocation import ToolInvocation


class MetricsService:
    def __init__(self, db: Session):
        self.db = db

    def log_event(
        self,
        *,
        session_id: str | None,
        correlation_id: str | None,
        component: str,
        event_type: str,
        duration_ms: int | None = None,
        prompt_tokens: int | None = None,
        completion_tokens: int | None = None,
        step_index: int | None = None,
        error_code: str | None = None,
        metadata_json: dict[str, Any] | None = None,
        message: str | None = None,
    ) -> None:
        # Ghi metric theo event de phan tich cho bao cao lab (event-level metrics).
        row = LabMetricLog(
            session_id=session_id,
            correlation_id=correlation_id,
            component=component,
            event_type=event_type,
            duration_ms=duration_ms,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            step_index=step_index,
            error_code=error_code,
            metadata_json=metadata_json,
            message=message,
        )
        self.db.add(row)
        self.db.commit()

    def log_tool_invocation(
        self,
        *,
        session_id: str,
        correlation_id: str,
        step_index: int,
        tool_name: str,
        arguments_json: dict[str, Any],
        result_ok: bool,
        result_text: str | None,
        error_code: str | None,
        duration_ms: int | None,
    ) -> None:
        if not settings.enable_tool_invocation_table:
            return
        row = ToolInvocation(
            session_id=session_id,
            correlation_id=correlation_id,
            step_index=step_index,
            tool_name=tool_name,
            arguments_json=arguments_json,
            result_ok=result_ok,
            result_text=result_text,
            error_code=error_code,
            duration_ms=duration_ms,
        )
        self.db.add(row)
        self.db.commit()
