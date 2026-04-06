import logging
import json
import os
from datetime import datetime, timezone

# Ensure logs directory exists
LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)

LOG_FILE = os.path.join(LOG_DIR, "agent_trace.log")

# ---------------------------------------------------------------------------
# File handler – one line per JSON record (JSON-Lines format)
# ---------------------------------------------------------------------------
_file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
_file_handler.setLevel(logging.DEBUG)

# Console handler – human-readable
_console_handler = logging.StreamHandler()
_console_handler.setLevel(logging.INFO)
_console_handler.setFormatter(logging.Formatter("[%(levelname)s] %(message)s"))

agent_logger = logging.getLogger("agent_trace")
agent_logger.setLevel(logging.DEBUG)
agent_logger.addHandler(_file_handler)
agent_logger.addHandler(_console_handler)
agent_logger.propagate = False  # don't bubble up to root logger


def _write(record: dict):
    """Write a structured JSON record to the log file (one line each).
    
    Uses direct file I/O instead of _file_handler.stream to avoid
    'NoneType has no attribute write' when running under uvicorn/API server.
    """
    record.setdefault("timestamp", datetime.now(timezone.utc).isoformat())
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


# ---------------------------------------------------------------------------
# Public helpers
# ---------------------------------------------------------------------------

def log_llm_call(
    *,
    step: str,
    content: str,
    tool_calls: list,
    usage: dict,
    latency_ms: int,
    provider: str = "google",
    model: str = "",
):
    """
    Log one LLM invocation.

    Parameters
    ----------
    step        : A label such as "call_model"
    content     : The text content returned by the LLM (thought / final answer)
    tool_calls  : List of tool_call dicts [{name, args}, ...]
    usage       : {prompt_tokens, completion_tokens, total_tokens}
    latency_ms  : Wall-clock time of the .invoke() call in milliseconds
    provider    : LLM provider name, e.g. "google"
    model       : Model name string
    """
    record = {
        "type": "llm",
        "step": step,
        "provider": provider,
        "model": model,
        "content": content,
        "tool_calls": tool_calls,
        "usage": usage,
        "latency_ms": latency_ms,
    }
    _write(record)

    # Pretty console summary
    agent_logger.info(
        f"[LLM] step={step} | latency={latency_ms}ms | "
        f"tokens(in/out/total)={usage.get('prompt_tokens',0)}/"
        f"{usage.get('completion_tokens',0)}/{usage.get('total_tokens',0)} | "
        f"tools_called={[tc['name'] for tc in tool_calls]}"
    )
    if content:
        agent_logger.debug(f"[LLM thought] {content[:200]}")


def log_tool_call(
    *,
    tool_name: str,
    tool_input: dict,
    tool_output: str,
    latency_ms: int,
):
    """
    Log one tool execution.

    Parameters
    ----------
    tool_name   : Name of the tool that was called
    tool_input  : Arguments passed to the tool
    tool_output : String result returned by the tool
    latency_ms  : Execution time in milliseconds
    """
    record = {
        "type": "tool",
        "tool_name": tool_name,
        "tool_input": tool_input,
        "tool_output": tool_output[:500] if tool_output else "",
        "latency_ms": latency_ms,
    }
    _write(record)

    agent_logger.info(
        f"[TOOL] {tool_name} | latency={latency_ms}ms | "
        f"output_preview={str(tool_output)[:100]}"
    )
