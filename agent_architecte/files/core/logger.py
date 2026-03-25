"""
logger.py — Rich terminal logging for agent actions, tool calls, and reasoning traces.
Every agent and tool call passes through these helpers so the console shows exactly
what is happening at each step of the pipeline.
"""

import sys
import time
from datetime import datetime
from enum import Enum


# ── ANSI colour palette ──────────────────────────────────────────────────────

class C:
    RESET  = "\033[0m"
    BOLD   = "\033[1m"
    DIM    = "\033[2m"

    # Agents — each gets its own colour
    ORCHESTRATOR = "\033[38;5;99m"   # purple
    ANALYST      = "\033[38;5;39m"   # sky-blue
    ARCHITECT    = "\033[38;5;75m"   # blue
    DEVOPS       = "\033[38;5;220m"  # amber
    DEVELOPER    = "\033[38;5;208m"  # orange
    QA           = "\033[38;5;82m"   # green

    # Events
    TOOL_CALL    = "\033[38;5;213m"  # pink
    TOOL_RESULT  = "\033[38;5;149m"  # light green
    ERROR        = "\033[38;5;196m"  # red
    SUCCESS      = "\033[38;5;46m"   # bright green
    INFO         = "\033[38;5;244m"  # grey
    SEPARATOR    = "\033[38;5;237m"  # dark grey


AGENT_COLORS = {
    "orchestrator": C.ORCHESTRATOR,
    "analyst":      C.ANALYST,
    "architect":    C.ARCHITECT,
    "devops":       C.DEVOPS,
    "developer":    C.DEVELOPER,
    "qa":           C.QA,
}

AGENT_ICONS = {
    "orchestrator": "⬡",
    "analyst":      "◎",
    "architect":    "◈",
    "devops":       "◆",
    "developer":    "◉",
    "qa":           "◐",
}


def _ts() -> str:
    return datetime.now().strftime("%H:%M:%S")


def _separator(char: str = "─", width: int = 72, color: str = C.SEPARATOR) -> None:
    print(f"{color}{char * width}{C.RESET}")


def _indent(text: str, spaces: int = 4) -> str:
    pad = " " * spaces
    return "\n".join(f"{pad}{line}" for line in text.splitlines())


# ── Public helpers ────────────────────────────────────────────────────────────

def log_phase_start(phase: str, description: str) -> None:
    """Print a prominent phase banner."""
    _separator("═")
    color = AGENT_COLORS.get(phase.lower(), C.INFO)
    icon  = AGENT_ICONS.get(phase.lower(), "◇")
    print(
        f"{color}{C.BOLD}  {icon}  PHASE: {phase.upper()}{C.RESET}  "
        f"{C.DIM}({_ts()}){C.RESET}"
    )
    print(f"{C.INFO}     {description}{C.RESET}")
    _separator("─")


def log_agent_thinking(agent: str, message: str) -> None:
    """Agent reasoning step."""
    color = AGENT_COLORS.get(agent.lower(), C.INFO)
    icon  = AGENT_ICONS.get(agent.lower(), "◇")
    print(f"{color}{icon} [{agent.upper()}]{C.RESET}  {C.DIM}{_ts()}{C.RESET}")
    print(_indent(message))


def log_tool_call(agent: str, tool_name: str, inputs: dict) -> None:
    """Announce a tool invocation."""
    color = AGENT_COLORS.get(agent.lower(), C.INFO)
    print(
        f"{C.TOOL_CALL}  ▶ TOOL CALL{C.RESET}  "
        f"{color}{tool_name}{C.RESET}  "
        f"{C.DIM}← {agent.upper()}{C.RESET}"
    )
    for k, v in inputs.items():
        val_str = str(v)
        if len(val_str) > 120:
            val_str = val_str[:120] + "…"
        print(f"{C.DIM}     {k}: {C.RESET}{val_str}")


def log_tool_result(tool_name: str, result: str, success: bool = True) -> None:
    """Show the outcome of a tool call."""
    status_color = C.TOOL_RESULT if success else C.ERROR
    status_icon  = "✓" if success else "✗"
    result_str   = str(result)
    if len(result_str) > 300:
        result_str = result_str[:300] + "\n     … (truncated)"
    print(
        f"{status_color}  {status_icon} RESULT{C.RESET}  "
        f"{C.DIM}{tool_name}{C.RESET}"
    )
    print(_indent(result_str, 6))


def log_llm_call(agent: str, prompt_preview: str) -> None:
    """Show that the agent is calling the LLM."""
    color = AGENT_COLORS.get(agent.lower(), C.INFO)
    print(f"{color}  ⟳ LLM CALL{C.RESET}  {C.DIM}{agent.upper()}{C.RESET}")
    preview = prompt_preview.replace("\n", " ")[:160]
    print(f"{C.DIM}     prompt: {preview}…{C.RESET}")


def log_llm_response(agent: str, response_preview: str) -> None:
    """Show a truncated LLM response."""
    color = AGENT_COLORS.get(agent.lower(), C.INFO)
    preview = response_preview.replace("\n", " ")[:200]
    print(f"{color}  ⟵ LLM RESPONSE{C.RESET}  {C.DIM}{preview}…{C.RESET}")


def log_state_update(agent: str, keys: list[str]) -> None:
    """Show which state keys an agent is writing."""
    color = AGENT_COLORS.get(agent.lower(), C.INFO)
    keys_str = ", ".join(keys)
    print(f"{color}  ↳ STATE UPDATE{C.RESET}  {C.DIM}writing: [{keys_str}]{C.RESET}")


def log_error(agent: str, error: str) -> None:
    print(f"{C.ERROR}  ✗ ERROR  [{agent.upper()}]{C.RESET}")
    print(_indent(error, 6))


def log_success(message: str) -> None:
    _separator("─")
    print(f"{C.SUCCESS}{C.BOLD}  ✓  {message}{C.RESET}")
    _separator("─")


def log_qa_loop(attempt: int, verdict: str) -> None:
    color = C.SUCCESS if verdict == "PASS" else C.ERROR
    print(
        f"{C.QA}  ◐ QA LOOP{C.RESET}  attempt={attempt}  "
        f"{color}verdict={verdict}{C.RESET}"
    )


def log_pipeline_complete(state: dict) -> None:
    _separator("═")
    print(f"{C.SUCCESS}{C.BOLD}  ✓  PIPELINE COMPLETE{C.RESET}")
    files = state.get("generated_files", [])
    print(f"{C.INFO}     Files generated : {len(files)}{C.RESET}")
    print(f"{C.INFO}     Validation      : {state.get('validation_passed')}{C.RESET}")
    print(f"{C.INFO}     Repo path       : {state.get('repo_path', 'N/A')}{C.RESET}")
    print(f"{C.INFO}     Repo URL        : {state.get('repo_url', 'N/A')}{C.RESET}")
    print(f"\n{C.DIM}  Reasoning trace ({len(state.get('reasoning_trace', []))} entries):{C.RESET}")
    for entry in state.get("reasoning_trace", []):
        print(f"{C.DIM}     {entry}{C.RESET}")
    _separator("═")