import json
import requests
from langchain_core.messages import HumanMessage, SystemMessage

from state import State
from utils import (
    call_mistral, SYS_MESSAGE, MAX_RETRIES,
    parse_plan, parse_verdict, format_error_ctx
)


# ── Node 0: db_fetcher ─────────────────────────────────────────────────────────
def db_fetcher(s: State) -> State:
    """
    Récupère le schéma de la base de données via l'API du coordonneur.
    Permet au backend_agent de savoir sur quelles tables faire des requêtes.
    
    NOTE : Cette étape est OPTIONNELLE. Si l'API n'est pas accessible,
    on continue juste sans schéma DB (le backend peut générer du code générique).
    """
    if not s.db_project_name:
        print("⚠️  db_fetcher: no project_name provided, skipping DB sync")
        return s
    
    print(f"\n🔗  db_fetcher: tentative de récupération du schéma de '{s.db_project_name}'...")
    
    try:
        # Appel à l'API du coordonneur pour récupérer le schéma
        api_url = f"{s.db_api_url}/databases/{s.db_project_name}/schema"
        response = requests.get(api_url, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            print(f"   [DEBUG] API response: {data}")
            s.db_schema = data.get("schema", {})
            print(f"   [DEBUG] Extracted db_schema: {s.db_schema}")
            
            tables = list(s.db_schema.keys())
            print(f"   ✅  Schéma récupéré: {len(tables)} tables")
            for table_name in tables:
                cols = s.db_schema[table_name].get("columns", [])
                print(f"      • {table_name}: {[c['name'] for c in cols]}")
            
            s.logs.append(f"[db_fetcher] synced {len(tables)} tables from DB")
        else:
            print(f"   ⚠️  API retourna {response.status_code} — schéma non disponible")
            s.logs.append(f"[db_fetcher] API error {response.status_code}")
            
    except requests.exceptions.ConnectionError:
        # L'API n'est pas accessible — c'est OK, on continue sans schéma
        print(f"   ⚠️  API indisponible ({s.db_api_url}) — backend générera du code générique")
        s.logs.append(f"[db_fetcher] API not available - continuing without DB schema")
        
    except requests.exceptions.Timeout:
        print(f"   ⚠️  Timeout API ({s.db_api_url}) — schéma non récupéré")
        s.logs.append(f"[db_fetcher] API timeout")
        
    except Exception as e:
        print(f"   ⚠️  Erreur: {e}")
        s.logs.append(f"[db_fetcher] error: {str(e)}")
    
    return s


# ── Node 1: plan_agent ─────────────────────────────────────────────────────────
def plan_agent(s: State) -> State:
    """
    Runs once at startup.
    Parses the JSON plan, extracts Akram's backend tasks,
    builds the ordered task_queue, and initialises task_statuses.
    """
    print("\n📋  plan_agent: parsing JSON plan...")
    print(f"[plan_agent] db_schema received: {s.db_schema}")
    print(f"[plan_agent] db_schema type: {type(s.db_schema)}")
    print(f"[plan_agent] db_schema keys: {list(s.db_schema.keys()) if isinstance(s.db_schema, dict) else 'NOT A DICT'}")
    print(f"[plan_agent] db_project_name: {s.db_project_name}")

    s.task_queue = parse_plan(s.plan, s.db_schema, s.db_project_name)

    # mark every task as pending
    s.task_statuses = {task["id"]: "pending" for task in s.task_queue}

    s.logs.append(f"[plan_agent] built task_queue with {len(s.task_queue)} tasks")
    print(f"   ✅  {len(s.task_queue)} tasks queued:")
    for i, task in enumerate(s.task_queue):
        print(f"      {i+1:02d}. {task['path']}")

    return s


# ── Node 2: task_picker ────────────────────────────────────────────────────────
def task_picker(s: State) -> State:
    """
    Picks the next pending task from the queue.
    Resets per-task counters (attempt, error_feedback, test_results).
    If queue is exhausted, sets current_task to {} so router sends to END.
    """
    # find next pending task
    for i, task in enumerate(s.task_queue):
        if s.task_statuses.get(task["id"]) == "pending":
            s.current_task       = task
            s.current_task_index = i
            s.current_attempt    = 0
            s.error_feedback     = {}
            s.test_results       = {}
            s.logs.append(f"[task_picker] → {task['path']}")
            print(f"\n{'='*60}")
            print(f"📌  Next task: {task['path']}")
            print(f"{'='*60}")
            return s

    # no pending tasks left
    s.current_task = {}
    s.logs.append("[task_picker] queue exhausted → END")
    print("\n🏁  All tasks processed.")
    return s


# ── Node 3: backend_agent ──────────────────────────────────────────────────────
def backend_agent(s: State) -> State:
    """
    Writes the current task's file.
    Injects content of all dependency files into the prompt
    so the LLM understands relationships between files.
    On retry, injects the broken code + structured error feedback.
    """
    llm  = call_mistral()
    task = s.current_task

    print(f"\n🚀  backend_agent: {task['path']}  (attempt {s.current_attempt + 1}/{MAX_RETRIES})")

    # ── build dependency context ───────────────────────────────────────────────
    # index already-generated files by path
    files_index = {f["path"]: f["content"] for f in s.generated_files}

    dep_context = ""
    if task.get("depends_on"):
        dep_blocks = []
        for dep_path in task["depends_on"]:
            if dep_path in files_index:
                dep_blocks.append(
                    f"# ── {dep_path} (dependency) ──\n{files_index[dep_path]}"
                )
            else:
                dep_blocks.append(f"# ── {dep_path} (dependency — not yet generated) ──")
        if dep_blocks:
            dep_context = (
                "\n\n# DEPENDENCY FILES — read these carefully before writing your code.\n"
                "# Your file must import from and be consistent with these:\n\n"
                + "\n\n".join(dep_blocks)
            )

    # ── build database schema context ──────────────────────────────────────────
    db_context = ""
    if s.db_schema:
        db_context = (
            f"\n\n# DATABASE SCHEMA (synchronized from '{s.db_project_name}'):\n"
            f"# Tables, columns, and relationships available via {s.db_api_url}\n"
            f"{json.dumps(s.db_schema, indent=2, ensure_ascii=False)}"
        )

    # ── build retry context ────────────────────────────────────────────────────
    error_ctx    = format_error_ctx(s.error_feedback)
    old_code_ctx = ""
    if s.error_feedback and task["path"] in files_index:
        old_code_ctx = (
            f"\n\n# CURRENT (BROKEN) CODE in `{task['path']}`:\n"
            f"{files_index[task['path']]}"
        )

    # ── build full prompt ──────────────────────────────────────────────────────
    prompt = (
        f"Write the file `{task['path']}`.\n\n"
        f"Description:\n{task['description']}\n\n"
        f"Additional context (entities, endpoints, auth spec):\n"
        f"{json.dumps(task.get('context', {}), indent=2, ensure_ascii=False)}"
        f"{dep_context}"
        f"{db_context}"
        f"{old_code_ctx}"
        f"{error_ctx}"
    )

    response = llm.invoke([SYS_MESSAGE, HumanMessage(content=prompt)])

    # ── store result ───────────────────────────────────────────────────────────
    # remove previous version of this file if it exists (retry case)
    s.generated_files = [f for f in s.generated_files if f["path"] != task["path"]]
    s.generated_files.append({"path": task["path"], "content": response.content})

    s.logs.append(f"[backend_agent] attempt={s.current_attempt + 1} → wrote {task['path']}")
    print(f"   ✅  Written: {task['path']}")

    return s


# ── Node 4: tester ─────────────────────────────────────────────────────────────
def tester(s: State) -> State:
    """
    Reviews the current task's file only.
    Passes the file content + its dependency files to the LLM
    and asks for a structured JSON verdict.
    No files are written to disk — pure in-memory review.
    """
    llm  = call_mistral()
    task = s.current_task

    print(f"\n🧪  tester: reviewing {task['path']}...")

    # get the file just written
    files_index  = {f["path"]: f["content"] for f in s.generated_files}
    file_content = files_index.get(task["path"], "[FILE NOT FOUND]")

    # include dependency code so the tester can check imports/consistency
    dep_blocks = []
    for dep_path in task.get("depends_on", []):
        if dep_path in files_index:
            dep_blocks.append(f"# ── {dep_path} ──\n{files_index[dep_path]}")
    dep_context = "\n\n".join(dep_blocks)

    # one verdict per "test" (one per task for now — can be expanded)
    test_name = f"review_{task['id']}"

    resp = llm.invoke([
        SystemMessage(content="""
You are a strict Python code reviewer.
You will receive a file to review and optionally its dependency files.
Check for:
- Correct imports consistent with dependency files
- All described functionality is implemented
- No syntax errors
- Type hints present
- No bare except

Respond ONLY with a valid JSON object — no markdown, no backticks.
Format:
{
  "passed": true or false,
  "failure_reason": "one line — what is wrong, or empty string if passed",
  "suggestion": "one line — what to fix, or empty string if passed",
  "affected_file": "path of the file to fix, or empty string if passed"
}
"""),
        HumanMessage(content=(
            f"File to review: `{task['path']}`\n\n"
            f"Description it must implement:\n{task['description']}\n\n"
            f"File content:\n{file_content}"
            + (f"\n\nDependency files for reference:\n{dep_context}" if dep_context else "")
        ))
    ])

    verdict = parse_verdict(resp.content)
    passed  = verdict.get("passed", False)

    s.test_results  = {test_name: {"passed": passed, "failure_reason": verdict.get("failure_reason", "")}}
    s.current_attempt += 1

    if passed:
        s.error_feedback = {}
        print(f"   ✅  Passed")
    else:
        s.error_feedback = {
            test_name: {
                "files_to_fix":   [task["path"]],
                "affected_file":  verdict.get("affected_file", task["path"]),
                "failure_reason": verdict.get("failure_reason", ""),
                "suggestion":     verdict.get("suggestion", ""),
            }
        }
        print(f"   ❌  Failed: {verdict.get('failure_reason', '')}")

    s.logs.append(
        f"[tester] {task['path']} attempt={s.current_attempt}/{MAX_RETRIES} "
        f"→ {'PASS' if passed else 'FAIL'}"
    )

    return s


# ── Node 5: file_writer ────────────────────────────────────────────────────────
def file_writer(s: State) -> State:
    """
    Writes all generated_files to disk under project_root.
    Preserves the exact folder structure (app/api/auth.py etc).
    Runs once after the backend loop completes.
    """
    import os

    root    = s.project_root
    written = 0

    print(f"\n💾  file_writer: saving project to `{root}/`...")

    for file in s.generated_files:
        full_path = os.path.join(root, file["path"])
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(file["content"])
        written += 1
        print(f"   📄  {full_path}")

    s.phase = "analysis"
    s.logs.append(f"[file_writer] wrote {written} files to {root}/")
    print(f"\n   ✅  {written} files saved.")

    return s


# ── Node 6: project_analyst ────────────────────────────────────────────────────
def project_analyst(s: State) -> State:
    """
    Reads all generated_files from memory.
    Asks the LLM to extract a structured backend_summary:
    - all API endpoints (path, method, auth, request/response shapes)
    - authentication mechanism
    - data models and field types
    - relationships between entities
    - base URL and error format

    The summary is stored in s.backend_summary and passed to frontend_agent.
    Also extracts and logs the requirements from requirements.txt.
    """
    llm = call_mistral()

    print("\n🔍  project_analyst: analysing backend project...")

    # Extract requirements first
    requirements = _extract_requirements(s.generated_files)
    if requirements:
        print(f"\n📦  Requirements found ({len(requirements)} packages):")
        for pkg in requirements:
            print(f"      • {pkg}")
        s.logs.append(f"[project_analyst] extracted {len(requirements)} packages from requirements.txt")

    # build one big source block — all files concatenated with clear separators
    source_block = "\n\n".join(
        f"# {'='*10} {f['path']} {'='*10}\n{f['content']}"
        for f in s.generated_files
    )

    resp = llm.invoke([
        SystemMessage(content="""
You are a senior software architect analysing a FastAPI backend project.
Your job is to produce a structured summary that a frontend developer
needs to integrate with this backend — without reading the source code themselves.

Respond ONLY with a valid JSON object. No markdown, no backticks, no explanation.
Use this exact structure:
{
  "base_url": "http://localhost:8000",
  "auth": {
    "type": "JWT Bearer",
    "login_endpoint": "POST /auth/login",
    "token_field": "access_token",
    "refresh_endpoint": "POST /auth/refresh",
    "header": "Authorization: Bearer <token>"
  },
  "endpoints": [
    {
      "path": "/auth/register",
      "method": "POST",
      "auth_required": false,
      "description": "...",
      "request_body": {},
      "response": {}
    }
  ],
  "models": {
    "ModelName": {
      "field_name": "type"
    }
  },
  "enums": {
    "EnumName": ["VALUE1", "VALUE2"]
  },
  "error_format": {
    "detail": "string"
  },
  "notes": "any important integration notes for the frontend team"
}
"""),
        HumanMessage(content=(
            f"Here is the full FastAPI backend source code:\n\n{source_block}\n\n"
            f"Extract the complete backend contract as JSON."
        ))
    ])

    summary = _parse_summary(resp.content)
    s.backend_summary = summary
    s.phase           = "frontend"

    endpoint_count = len(summary.get("endpoints", []))
    model_count    = len(summary.get("models", {}))
    s.logs.append(f"[project_analyst] extracted {endpoint_count} endpoints, {model_count} models")
    print(f"   ✅  Found {endpoint_count} endpoints and {model_count} models")
    print(f"   📦  Summary ready for frontend_agent")

    return s


def _extract_requirements(generated_files: list) -> list:
    """Extract packages from requirements.txt if present."""
    for file_info in generated_files:
        if file_info.get("path") == "requirements.txt":
            content = file_info.get("content", "")
            packages = []
            for line in content.strip().split('\n'):
                line = line.strip()
                # Ignore empty lines and comments
                if line and not line.startswith('#'):
                    packages.append(line)
            return packages
    return []


def _parse_summary(raw: str) -> dict:
    """Safely parse the analyst JSON, return empty dict if malformed."""
    import re
    try:
        clean = raw.strip()
        clean = re.sub(r"^```json|^```|```$", "", clean, flags=re.MULTILINE).strip()
        return json.loads(clean)
    except (json.JSONDecodeError, ValueError):
        print("   ⚠️  Could not parse analyst response as JSON — storing raw text")
        return {"raw": raw}