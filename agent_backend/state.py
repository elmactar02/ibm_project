from dataclasses import dataclass, field


@dataclass
class State:
    # ── Input ──────────────────────────────────────────────────────────────────
    plan:               dict                                # raw JSON plan

    # ── Database Context ───────────────────────────────────────────────────────
    db_project_name:    str  = ""                           # project_name from orchestrator
    db_schema:          dict = field(default_factory=dict)  # {table_name: {columns: [...], fks: [...]}}
    db_api_url:         str  = "http://localhost:8000"      # API URL to query database

    # ── Queue ──────────────────────────────────────────────────────────────────
    task_queue:         list = field(default_factory=list)  # built by plan_agent
    current_task_index: int  = 0                            # pointer into task_queue
    current_task:       dict = field(default_factory=dict)  # task being worked on now

    # ── Per-task retry ─────────────────────────────────────────────────────────
    current_attempt:    int  = 0                            # resets to 0 between tasks
    error_feedback:     dict = field(default_factory=dict)  # current task errors only
    test_results:       dict = field(default_factory=dict)  # current task results only

    # ── Outputs ────────────────────────────────────────────────────────────────
    generated_files:    list = field(default_factory=list)  # [{path, content}] grows only
    task_statuses:      dict = field(default_factory=dict)  # {task_id: "passed"/"failed"/"pending"}
    project_root:       str  = "generated"                  # where file_writer saves to disk

    # ── Cross-agent handoff ────────────────────────────────────────────────────
    backend_summary:    dict = field(default_factory=dict)  # project_analyst → frontend_agent
    phase:              str  = "backend"                    # "backend" | "analysis" | "frontend"

    # ── Trace ──────────────────────────────────────────────────────────────────
    logs:               list = field(default_factory=list)
