import json
from langchain_core.messages import SystemMessage
from langchain_groq import ChatGroq
from langchain_community.chat_models import ChatOllama
from langchain_deepseek import ChatDeepSeek
from dotenv import load_dotenv
load_dotenv()

# ── Constants ──────────────────────────────────────────────────────────────────
MAX_RETRIES = 2  # Reduced to minimize API calls
DEEP_SEEK   = "deepseek-r1:latest"
QWEN        = "qwen2.5-coder:7b"

#MISTRAL
MISTRAL_LARGE_LATEST = "mistral-large-latest"
CODESTRAL_LATEST = "codestral-latest"

import os
llm = ChatDeepSeek(
    model="deepseek-chat",  # or "deepseek-reasoner" for complex reasoning
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    temperature=0.7
)


# ── LLM factories ──────────────────────────────────────────────────────────────
def call_mistral():
    """Use Groq OpenAI GPT-OSS-20B for fast code generation (no rate limits)"""
    return ChatGroq(
        model="openai/gpt-oss-20b",
        temperature=0.3,
        max_tokens=8192,
        # GROQ_API_KEY loaded from .env automatically
    )

def call_deepseek():
    return ChatDeepSeek(
    model="deepseek-chat",  # or "deepseek-reasoner" for complex reasoning
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    temperature=0.7
)

def call_qwen():
    return ChatOllama(model=QWEN, temperature=0.5)

# ── System prompt ──────────────────────────────────────────────────────────────
SYS_MESSAGE = SystemMessage(content="""
You are a Senior Python Developer with 10+ years of experience.

# TASK
Generate production-ready FastAPI backend code that acts as an HTTP PROXY.
This backend does NOT access databases directly. It calls a remote HTTP API instead.

All function parameters and return values MUST have type hints.
Google-style docstrings with Args, Returns, Raises sections.
Specific exceptions only, never bare except.
Each function does exactly one thing.

# CRITICAL: HTTP PROXY ARCHITECTURE
The backend is NOT an ORM application. It is an HTTP proxy that:
1. Receives REST requests from the frontend
2. Calls a remote HTTP API (the database API on port 8003)
3. Returns responses to the frontend

DO NOT generate:
  - SQLAlchemy models (no app/db/models.py)
  - Database sessions (no app/db/session.py)
  - Database declarative base (no app/db/base.py)
  - Any database imports (sqlalchemy, asyncpg, etc.)

DO generate:
  - FastAPI routes that use httpx AsyncClient to call http://localhost:8003/databases/{project}/data/{table}
  - Pydantic schemas for request/response validation only
  - Security utilities (hash_password, verify_password)
  - Configuration for the remote API URL

# PACKAGE STRUCTURE
  app/
    __init__.py
    core/
      __init__.py
      config.py         ← Pydantic BaseSettings (pydantic_settings)
      security.py       ← Password utilities only
    schemas/
      __init__.py
      task.py           ← Pydantic schemas (NOT SQLAlchemy models)
    main.py             ← FastAPI app with httpx calls

# CRITICAL IMPORTS FOR main.py
MUST use these EXACT imports:
  from fastapi import FastAPI, HTTPException, status
  from httpx import AsyncClient
  from app.schemas.task import TaskCreate, TaskRead, TaskUpdate, Priority, Status
  from app.core.security import hash_password, verify_password
  from app.core.config import Settings

NEVER import:
  - from app.db.models (does not exist)
  - from app.db.session (does not exist)
  - sqlalchemy (forbidden)
  - asyncpg (forbidden)

# CRITICAL IMPORTS FOR config.py — PYDANTIC v2 ONLY
MUST use Pydantic v2 imports:
  from pydantic import Field, field_validator
  from pydantic_settings import BaseSettings, SettingsConfigDict
  NOT: from pydantic import BaseSettings (this is v1 and will fail)

# requirements.txt GENERATION RULES
When generating requirements.txt:
- List ONLY these packages: fastapi, uvicorn, httpx, pydantic>=2.7.0, pydantic-settings, python-dotenv, python-multipart, passlib
- DO NOT include: sqlalchemy, asyncpg, psycopg2, mysql-connector, or any other database drivers
- Format: package>=version (one per line)
- NO markdown, NO comments, NO explanations — just list of dependencies

# OUTPUT FORMAT
- Raw Python code only (or plain text for requirements.txt)
- No markdown, no backticks, no explanations
- No introductory or concluding text
- Output will be saved directly to a .py or .txt file

Follow these instructions strictly. Any SQLAlchemy or database imports will cause import errors.
""")


# ── Plan parser ────────────────────────────────────────────────────────────────
# Backend HTTP Proxy Architecture (NO SQLAlchemy ORM)
# Backend calls a remote HTTP API for database operations instead of direct DB access
# Each file knows which already-generated files it needs.
BACKEND_DEPENDENCIES = {
    "app/core/config.py":      [],
    "app/core/security.py":    ["app/core/config.py"],
    "app/schemas/task.py":     [],
    "app/main.py":             ["app/core/security.py", "app/schemas/task.py", "app/core/config.py"],
    "requirements.txt":        [],  # Generated last, no dependencies
}

def _find_entity(entities: list, name: str) -> dict:
    """Safely find an entity by name, return empty dict if not found."""
    for e in entities:
        if e.get("name") == name:
            return e
    return {}  # Empty dict if not found


def parse_plan(plan: dict, db_schema: dict = None, project_name: str = None) -> list:
    """
    Extract Akram's backend tasks from the JSON plan.
    Returns an ordered task_queue list where each item is a task dict.
    Handles different blueprint formats from various architects.

    Args:
        plan: the full raw JSON plan as a dict
        db_schema: optional database schema dict with table names as keys
        project_name: the actual project name (e.g., 'todo-app-test10')

    Returns:
        list of task dicts ordered by dependency layers
    """
    if db_schema is None:
        db_schema = {}
    if project_name is None:
        project_name = "todo-app"  # fallback
    
    # DEBUG: Log what db_schema actually contains
    print(f"\n[parse_plan] db_schema type: {type(db_schema)}")
    print(f"[parse_plan] db_schema keys: {list(db_schema.keys()) if isinstance(db_schema, dict) else 'NOT A DICT'}")
    print(f"[parse_plan] project_name: {project_name}")
    
    # Extract backend spec - handle different formats
    dev_instructions = plan.get("dev_instructions", {})
    backend_spec = dev_instructions.get("backend", {})
    
    # Get Akram section or use backend_spec directly
    if isinstance(backend_spec, dict) and "Akram" in backend_spec:
        akram = backend_spec["Akram"]
    else:
        akram = backend_spec if backend_spec else {}
    
    # Ensure akram is a dict (not a string or other type)
    if not isinstance(akram, dict):
        akram = {}
    
    entities     = plan.get("entities", [])
    tech_stack   = plan.get("tech_stack", {})
    
    # Find endpoints - try different key names
    endpoints_raw = (akram.get("endpoints_à_implémenter", None) or
                     akram.get("api_endpoints", None) or
                     plan.get("api_endpoints", []))
    
    # Convert to router dict format
    if endpoints_raw and isinstance(endpoints_raw, list) and len(endpoints_raw) > 0:
        if isinstance(endpoints_raw[0], dict) and "router" in endpoints_raw[0]:
            endpoints = {r["router"]: r["endpoints"] for r in endpoints_raw}
        else:
            endpoints = {}  # Fallback
    else:
        endpoints = {}
    
    auth_spec    = akram.get("authentification", akram.get("auth", {}))
    structure    = akram.get("structure_projet", akram.get("project_structure", {}))

    # HTTP Proxy Backend — NO SQLAlchemy ORM, just FastAPI + httpx
    file_specs = {
        "app/core/config.py": {
            "description": "App settings using pydantic v2 BaseSettings from pydantic_settings. CRITICAL: Load from .env ONLY: DB_API_URL (defaults to http://localhost:8003). NO APP_SECRET_KEY, NO DATABASE_URL required. Fields: db_api_url: str with default. Use model_config = SettingsConfigDict(env_file='.env'). All fields have defaults or are optional.",
            "context": {"tech_stack": tech_stack}
        },
        "app/core/security.py": {
            "description": "Security utilities ONLY: hash_password(password: str) -> str using passlib bcrypt. verify_password(plain: str, hashed: str) -> bool. NO database access. NO imports from sqlalchemy, app.db, or app.schemas. Only import: from passlib.context import CryptContext.",
            "context": {"tech_stack": tech_stack}
        },
        "app/schemas/task.py": {
            "description": "Pydantic v2 schemas for request/response validation ONLY. DO NOT import uuid or UUID. Generate EXACTLY these 3 classes: (1) TaskCreate(title: str, description: str, priority: str, status: str), (2) TaskRead(id: int, title: str, description: str, priority: str, status: str, created_at: str, updated_at: str, user_id: int), (3) TaskUpdate(title: str = None, description: str = None, priority: str = None, status: str = None). Generate EXACTLY these 2 enums: Priority(HIGH, MEDIUM, LOW), Status(TODO, IN_PROGRESS, DONE). NO other classes, NO UUID, NO DateTime. All types are basic Python types (str, int, float).",
            "context": {"entity": _find_entity(entities, "Task")}
        },
        "app/main.py": {
            "description": "FastAPI HTTP PROXY backend. Imports: from fastapi import FastAPI, HTTPException, status; from httpx import AsyncClient; from app.schemas.task import TaskCreate, TaskRead, TaskUpdate, Priority, Status; from app.core.security import hash_password, verify_password; from app.core.config import Settings. Create Settings instance. Create FastAPI app. Define exactly 5 endpoints: GET /tasks (list all), POST /tasks (create), GET /tasks/{task_id} (detail), PUT /tasks/{task_id} (update), DELETE /tasks/{task_id} (delete). CRITICAL: Use the EXACT table name from db_tables (provided in context). Call http://localhost:8003/databases/{project_name}/data/{table_name} where project_name and table_name come from context. Each endpoint: (1) Extract parameters, (2) Call remote API with exact table name from db_tables, (3) Convert enum values (HIGH ↔ high). NO SQLAlchemy. Run on 0.0.0.0:8000.",
            "context": {"endpoints": plan.get("api_endpoints", []), "tech_stack": tech_stack, "project_name": project_name, "db_tables": list(db_schema.keys())}
        },
        "requirements.txt": {
            "description": "Exact required packages ONLY: fastapi==0.104.1, uvicorn[standard]==0.24.0, httpx==0.25.0, pydantic==2.11.0, pydantic-settings==2.11.0, python-dotenv==1.0.0, python-multipart==0.0.6, passlib[bcrypt]==1.7.4. NO sqlalchemy, NO asyncpg, NO database packages. One package per line. NO comments.",
            "context": {}
        },
    }

    # build ordered task_queue following BACKEND_DEPENDENCIES layer order
    task_queue = []
    for path, deps in BACKEND_DEPENDENCIES.items():
        spec = file_specs[path]
        task_queue.append({
            "id":          path.replace("/", "_").replace(".", "_"),
            "path":        path,
            "description": spec["description"],
            "context":     spec["context"],
            "depends_on":  deps,
            "status":      "pending",
        })

    return task_queue


# ── Error parsing helpers ──────────────────────────────────────────────────────
def parse_verdict(raw: str) -> dict:
    """Safely parse the LLM JSON verdict, fallback to failed if malformed."""
    import re
    try:
        clean = raw.strip()
        clean = re.sub(r"^```json|^```|```$", "", clean, flags=re.MULTILINE).strip()
        return json.loads(clean)
    except (json.JSONDecodeError, ValueError):
        return {
            "passed":         False,
            "failure_reason": "Tester could not parse LLM response",
            "suggestion":     "Check that the LLM returns valid JSON",
            "affected_file":  "",
        }


def format_error_ctx(error_feedback: dict) -> str:
    """Format error_feedback dict into a clean prompt string."""
    if not error_feedback:
        return ""
    lines = ["⚠️  PREVIOUS ATTEMPT FAILED. Fix ALL issues below:\n"]
    for test_name, info in error_feedback.items():
        lines.append(f"  Test        : {test_name}")
        lines.append(f"  File to fix : {info.get('affected_file') or info.get('files_to_fix', '')}")
        lines.append(f"  Reason      : {info['failure_reason']}")
        lines.append(f"  Suggestion  : {info['suggestion']}")
        lines.append("")
    return "\n".join(lines)