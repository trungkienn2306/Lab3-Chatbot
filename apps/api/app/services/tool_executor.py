import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError

from app.tools.registry import get_tool
from app.tools.schemas import ToolResult


class ToolExecutor:
    def execute(self, tool_name: str, args: dict) -> tuple[ToolResult, int]:
        tool = get_tool(tool_name)
        if not tool:
            return (
                ToolResult(
                    ok=False,
                    data="",
                    error_code="UNKNOWN_TOOL",
                    message=f"Tool {tool_name} not found",
                ),
                0,
            )

        start = time.time()
        with ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(tool.handler, args)
            try:
                result = future.result(timeout=tool.timeout_seconds)
            except TimeoutError:
                duration = int((time.time() - start) * 1000)
                return (
                    ToolResult(
                        ok=False,
                        data="",
                        error_code="TOOL_TIMEOUT",
                        message=f"Tool timeout {tool_name}",
                    ),
                    duration,
                )
        duration = int((time.time() - start) * 1000)
        return result, duration
