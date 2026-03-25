from state import State
from utils import MAX_RETRIES


def task_router(s: State) -> str:
    """
    Called after tester. Three possible outcomes:
    - 'pass'     → current task passed → go to task_picker (next task)
    - 'retry'    → failed but attempts remaining → back to backend_agent
    - 'give_up'  → failed and max retries hit → mark failed, go to task_picker

    Also called after task_picker:
    - 'end'      → no more pending tasks → END
    - 'continue' → task loaded → go to backend_agent
    """
    # ── called after task_picker ───────────────────────────────────────────────
    # task_picker sets current_task = {} when queue is empty
    if not s.current_task:
        return "end"

    # ── called after tester ────────────────────────────────────────────────────
    all_passed = all(r["passed"] for r in s.test_results.values()) if s.test_results else False
    task_id    = s.current_task.get("id", "")

    if all_passed:
        s.task_statuses[task_id] = "passed"
        print(f"\n✅  Task passed: {s.current_task['path']}")
        return "pass"

    if s.current_attempt >= MAX_RETRIES:
        s.task_statuses[task_id] = "failed"
        print(f"\n⛔  Giving up on: {s.current_task['path']} after {MAX_RETRIES} attempts")
        return "give_up"

    print(f"\n🔁  Retrying: {s.current_task['path']} ({s.current_attempt}/{MAX_RETRIES})")
    return "retry"


def picker_router(s: State) -> str:
    """
    Called after task_picker to decide whether to continue or end.
    Kept separate so the graph edges are explicit and readable.
    """
    if not s.current_task:
        return "end"
    return "continue"


def backend_done_router(s: State) -> str:
    """
    Called after task_picker when queue is exhausted.
    If backend phase is done → go to file_writer.
    Normal task available → continue to backend_agent.
    """
    if not s.current_task:
        return "write_files"   # queue empty → hand off to file_writer
    return "continue"          # still tasks left → backend_agent


def analyst_done_router(s: State) -> str:
    """
    Called after project_analyst.
    Always moves to frontend_agent — placeholder for future branching.
    """
    return "frontend"