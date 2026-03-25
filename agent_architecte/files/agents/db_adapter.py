"""
agents/db_adapter.py
───────────────────────────────────────────────────────────────────────────────
Nœud adaptateur qui branche le sous-graphe DB (ibm/main.py)
dans le graphe maître de Manal.

DONNÉES LUES depuis architect_blueprint
────────────────────────────────────────
  blueprint["entities"]                        → tables à créer
  blueprint["tech_stack"]["database"]          → type de BDD (SQLite ici)
  blueprint["dev_instructions"]["database"]    → instructions pour le dev DB
  blueprint["constraints"]                     → contraintes techniques
  blueprint["project"]                         → nom du projet

DONNÉES ÉCRITES dans AgentState
────────────────────────────────
  db_output = {
      "status":      "completed" | "error" | "stub",
      "db_path":     chemin vers le fichier .db SQLite,
      "schema":      dict des tables créées,
      "db_report":   rapport complet du db agent,
      "tables":      liste des tables créées,
  }

POSITION DANS LE GRAPHE DE MANAL
──────────────────────────────────
  architect_node → devops_node → frontend_adapter_node → db_adapter_node → backend_node → qa_node

PRÉ-REQUIS : appliquer PATCH_ibm_main.py sur ibm/main.py
"""

from __future__ import annotations

import json
import logging
import sys
import pathlib
from typing import Any

logger = logging.getLogger(__name__)

# ── Import du sous-graphe DB ─────────────────────────────────────────────────
# Le code DB est dans agents/dev_database.py (même dossier que ce fichier).

_db_graph  = None
_DB_MODULE = None

try:
    import importlib, sys as _sys, pathlib as _pathlib
    _agents_dir = _pathlib.Path(__file__).resolve().parent        # dossier agents/
    _root_dir   = _agents_dir.parent                               # racine projet Manal
    if str(_root_dir) not in _sys.path:
        _sys.path.insert(0, str(_root_dir))
    _DB_MODULE = importlib.import_module("agents.dev_database")
    _db_graph  = _DB_MODULE.graph
    logger.info("[db_adapter] Sous-graphe DB chargé depuis agents/dev_database.py")
except Exception as _e:
    logger.error("[db_adapter] Import agents/dev_database échoué : %s", _e)

if _db_graph is None:
    logger.warning("[db_adapter] Sous-graphe DB introuvable — mode stub activé")

# ── Import du logger de Manal ────────────────────────────────────────────────
try:
    from core.logger import (
        log_phase_start,
        log_agent_thinking,
        log_state_update,
        log_error,
    )
except ImportError:
    def log_phase_start(a, b):    logger.info("[%s] %s", a, b)
    def log_agent_thinking(a, b): logger.info("[%s] %s", a, b)
    def log_state_update(a, b):   logger.info("[%s] state update: %s", a, b)
    def log_error(a, b):          logger.error("[%s] %s", a, b)


# ───────────────────────────────────────────────────────────────────────────────
# Construction du DBAgentState depuis l'AgentState de Manal
# ───────────────────────────────────────────────────────────────────────────────

def _build_db_initial_state(agent_state: dict) -> dict:
    """
    Mappe les champs de l'AgentState de Manal vers le DBAgentState.

    Le DBAgentState attend :
      messages        → liste vide au départ
      blueprint       → le JSON complet de l'architect (directement compatible !)
      schema_data     → vide
      migrations_data → vide
      indexes_data    → vide
      seeders_data    → vide
      db_report       → vide

    Le blueprint de Manal contient déjà exactement ce dont le DB agent a besoin :
      - entities (avec fields + relations)
      - tech_stack.database
      - dev_instructions.database
      - constraints
      - project
    """
    blueprint = agent_state.get("architect_blueprint", {})

    if not blueprint:
        logger.warning("[db_adapter] architect_blueprint vide — le DB agent va travailler à vide")

    return {
        "messages":        [],
        "blueprint":       blueprint,   # ← directement compatible, pas de transformation !
        "schema_data":     {},
        "migrations_data": {},
        "indexes_data":    {},
        "seeders_data":    {},
        "db_report":       {},
    }


# ───────────────────────────────────────────────────────────────────────────────
# Nœud adaptateur principal
# ───────────────────────────────────────────────────────────────────────────────

def db_adapter_node(state: dict, llm=None) -> dict:
    """
    Nœud LangGraph compatible avec l'AgentState de Manal.
    Invoque le sous-graphe DB et retourne les résultats.

    Paramètres
    ----------
    state : AgentState de Manal
    llm   : ignoré — le DB agent gère ses propres LLMs (Mistral + Groq)

    Retourne
    --------
    dict : mise à jour de l'AgentState avec db_output
    """
    log_phase_start("db_adapter", "Lancement du sous-graphe DB (ibm/main.py)")

    blueprint    = state.get("architect_blueprint", {})
    project_name = blueprint.get("project", {}).get("name", state.get("project_name", "app"))
    entities     = [e.get("name") for e in blueprint.get("entities", [])]

    log_agent_thinking(
        "db_adapter",
        f"Projet     : '{project_name}'\n"
        f"Entités    : {entities}\n"
        f"DB cible   : {blueprint.get('tech_stack', {}).get('database', 'SQLite')}\n"
        f"Instructions DB : {str(blueprint.get('dev_instructions', {}).get('database', ''))[:120]}",
    )

    # ── Cas stub ────────────────────────────────────────────────────────────
    if _db_graph is None:
        log_error("db_adapter", "Sous-graphe DB non chargé — stub retourné")
        return {
            "db_output": {
                "status":  "stub",
                "message": "ibm/main.py non importable — as-tu appliqué PATCH_ibm_main.py ?",
            },
            "reasoning_trace": state.get("reasoning_trace", []) + [
                "[DB] Stub — sous-graphe non chargé."
            ],
            "current_phase": "backend",
        }

    # ── Construction de l'état initial ──────────────────────────────────────
    db_initial = _build_db_initial_state(state)

    log_agent_thinking(
        "db_adapter",
        f"DBAgentState prêt — {len(entities)} entités transmises au sous-graphe\n"
        "Invocation du sous-graphe DB...",
    )

    # ── Invocation du sous-graphe ────────────────────────────────────────────
    try:
        db_final = _db_graph.invoke(db_initial)
    except Exception as exc:
        log_error("db_adapter", f"Erreur dans le sous-graphe DB : {exc}")
        return {
            "db_output": {
                "status": "error",
                "error":  str(exc),
            },
            "reasoning_trace": state.get("reasoning_trace", []) + [
                f"[DB] Erreur : {exc}"
            ],
            "current_phase": "backend",
        }

    # ── Extraction des résultats ─────────────────────────────────────────────
    db_report   = db_final.get("db_report",   {})
    schema_data = db_final.get("schema_data", {})
    tables      = [t["name"] for t in schema_data.get("tables", [])]

    # Chemin du fichier .db (défini dans ibm/main.py comme OUTPUT_DIR / "todo_app.db")
    db_path = None
    if _DB_MODULE and hasattr(_DB_MODULE, "DB_PATH"):
        db_path = _DB_MODULE.DB_PATH

    log_agent_thinking(
        "db_adapter",
        f"Sous-graphe DB terminé !\n"
        f"Tables créées : {tables}\n"
        f"Fichier DB    : {db_path}\n"
        f"Indexes       : {db_report.get('summary', {}).get('indexes', 0)}\n"
        f"Seeders       : {db_report.get('summary', {}).get('seeders', 0)}",
    )

    # ── Sauvegarde optionnelle dans le repo du projet ────────────────────────
    repo_path = state.get("repo_path", f"./output/{project_name}")
    _copy_db_artifacts(repo_path, db_path, db_final)

    log_state_update("db_adapter", ["db_output", "reasoning_trace", "current_phase"])

    # Transformer schema_data en dict {table_name: table_name} pour le backend
    table_names_dict = {table: table for table in tables}
    
    return {
        "db_output": {
            "status":      "completed",
            "db_path":     db_path,
            "tables":      tables,
            "schema":      schema_data,
            "db_report":   db_report,
            # Infos utiles pour le backend
            "full_sql":    db_report.get("for_backend", {}).get("full_sql", ""),
            "indexes":     db_final.get("indexes_data", {}).get("indexes", []),
        },
        "db_schema": table_names_dict,  # {"Task": "Task", "User": "User", ...}
        "reasoning_trace": state.get("reasoning_trace", []) + [
            f"[DB] Base de données créée — {len(tables)} tables : {tables}. "
            f"DB path : {db_path}. "
            f"Indexes : {db_report.get('summary', {}).get('indexes', 0)}. "
            f"Seeders : {db_report.get('summary', {}).get('seeders', 0)}."
        ],
        # L'agent suivant de Manal
        "current_phase": "backend",
    }


def _copy_db_artifacts(repo_path: str, db_path: str | None, db_final: dict) -> None:
    """
    Copie le fichier .db et les JSONs générés dans le dossier du projet.
    Optionnel — ne plante pas si ça échoue.
    """
    try:
        import shutil
        dest = pathlib.Path(repo_path) / "database"
        dest.mkdir(parents=True, exist_ok=True)

        # Copie le .db SQLite
        if db_path and pathlib.Path(db_path).exists():
            shutil.copy2(db_path, dest / pathlib.Path(db_path).name)
            logger.info("[db_adapter] .db copié → %s", dest)

        # Copie les JSONs depuis outputs/ du projet ibm
        ibm_outputs = pathlib.Path(db_path).parent if db_path else pathlib.Path("outputs")
        for json_file in ["schema.json", "migrations.json", "indexes.json",
                          "seeders.json", "test_results.json", "db_report.json"]:
            src = ibm_outputs / json_file
            if src.exists():
                shutil.copy2(src, dest / json_file)

        logger.info("[db_adapter] Artefacts DB copiés dans %s", dest)
    except Exception as exc:
        logger.warning("[db_adapter] Copie artefacts échouée (non bloquant) : %s", exc)