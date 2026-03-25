import json
from graph import build_graph
from state import State


def load_plan(path: str = "architect_blueprint.json") -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def print_results(result: dict) -> None:
    # ── summary ────────────────────────────────────────────────────────────────
    statuses = result["task_statuses"]
    passed   = [k for k, v in statuses.items() if v == "passed"]
    failed   = [k for k, v in statuses.items() if v == "failed"]
    pending  = [k for k, v in statuses.items() if v == "pending"]

    print("\n" + "="*60)
    print("📊  SUMMARY")
    print("="*60)
    print(f"  ✅  Passed  : {len(passed)}")
    print(f"  ❌  Failed  : {len(failed)}")
    print(f"  ⏳  Pending : {len(pending)}")

    # ── logs ───────────────────────────────────────────────────────────────────
    print("\n" + "="*60)
    print("📋  LOGS")
    print("="*60)
    for log in result["logs"]:
        print(f"  {log}")

    # ── generated files ────────────────────────────────────────────────────────
    print("\n" + "="*60)
    print("📄  GENERATED FILES")
    print("="*60)
    for file in result["generated_files"]:
        task_id = file["path"].replace("/", "_").replace(".", "_")
        status  = statuses.get(task_id, "?")
        icon    = "✅" if status == "passed" else "❌" if status == "failed" else "⏳"
        print(f"\n{icon}  {file['path']}")
        print("─" * 50)
        print(file["content"])


if __name__ == "__main__":
    plan   = load_plan()
    app    = build_graph()

    print("\n🚀  Starting backend code generation pipeline...\n")
    result = app.invoke(State(plan=plan))
    print_results(result)