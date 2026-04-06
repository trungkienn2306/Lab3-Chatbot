from dataclasses import dataclass
from typing import Any, Callable


@dataclass
class ToolResult:
    ok: bool
    data: str
    error_code: str | None = None
    message: str | None = None


@dataclass
class ToolSpec:
    name: str
    description: str
    parameters_schema: dict[str, Any]
    handler: Callable[[dict[str, Any]], ToolResult]
    timeout_seconds: int = 5
