"""
agents/frontend_adapter.py
───────────────────────────────────────────────────────────────────────────────
Nœud adaptateur qui branche le sous-graphe Frontend de Mactar
dans le graphe maître de Manal.

POURQUOI UN ADAPTATEUR ?
─────────────────────────
Manal  → graphe plat, un nœud = une fonction (AgentState → dict)
Mactar → sous-graphe riche, plusieurs nœuds internes (FrontendState)

Un sous-graphe compilé LangGraph s'invoque comme n'importe quel callable.
L'adaptateur fait le pont en deux étapes :
  1. AgentState  ──►  FrontendState  (extraction des champs pertinents)
  2. FrontendState ──► AgentState   (écriture du résultat dans frontend_output)

DONNÉES TRANSMISES PAR L'ARCHITECT (architect_blueprint)
──────────────────────────────────────────────────────────
  blueprint["dev_instructions"]["frontend"]  → frontend_doc   (besoin UI détaillé)
  blueprint["api_endpoints"]                 → backend_specs  (endpoints formatés)
  blueprint["tech_stack"]                    → info contexte
  blueprint["user_journeys"]                 → info contexte
  blueprint["modules"]                       → info contexte

POSITION DANS LE GRAPHE MANAL
──────────────────────────────
  architect_node → devops_node → frontend_adapter_node → db_node → backend_node → qa_node
"""

from __future__ import annotations

import json
import logging
import sys
import pathlib
from typing import Any

# ── Import du sous-graphe de Mactar ─────────────────────────────────────────
# Le dossier agent_frontend/ est un dossier FRÈRE de agent_architecte/
# Structure : ibm_project/
#             ├── agent_architecte/files/agents/frontend_adapter.py
#             ├── agent_frontend/graph.py
#             ├── agent_backend/
#             └── ...

_ADAPTER_FILE = pathlib.Path(__file__).resolve()  # .../frontend_adapter.py
_AGENTS_DIR = _ADAPTER_FILE.parent                # .../agents
_FILES_DIR = _AGENTS_DIR.parent                   # .../files
_ARCHITECTE_DIR = _FILES_DIR.parent               # .../agent_architecte
_PROJECT_ROOT = _ARCHITECTE_DIR.parent            # .../ibm_project

# Chemin vers agent_frontend
_FRONTEND_PATH = _PROJECT_ROOT / "agent_frontend"
_FRONTEND_GRAPH_FILE = _FRONTEND_PATH / "graph.py"

_frontend_graph = None

def _load_frontend_graph():
    """
    Charge le sous-graphe frontend de manière lazy et isolée.
    Appelé une seule fois à la première utilisation.
    """
    global _frontend_graph
    
    if _frontend_graph is not None:
        return _frontend_graph  # Déjà chargé
    
    if not _FRONTEND_GRAPH_FILE.exists():
        logging.getLogger(__name__).warning(
            "[frontend_adapter] Chemin attendu introuvable : %s", _FRONTEND_GRAPH_FILE
        )
        return None
    
    try:
        import importlib.util
        
        # Sauvegarder l'état
        _original_path = sys.path.copy()
        _original_modules = dict(sys.modules)
        
        try:
            # CRITICAL: Clean up any backend state modules BEFORE loading frontend
            for _mod_key in list(sys.modules.keys()):
                if "backend_state" in _mod_key or (
                    _mod_key in ["state", "nodes", "router", "utils", "graph"] and
                    sys.modules[_mod_key].__file__ and 
                    "agent_backend" in sys.modules[_mod_key].__file__
                ):
                    try:
                        del sys.modules[_mod_key]
                    except:
                        pass
            
            # Construire un sys.path qui EXCLUT agent_architecte
            _isolated_path = [str(_FRONTEND_PATH)] + [
                p for p in sys.path 
                if str(_FRONTEND_PATH) not in p and "agent_architecte" not in p
            ]
            sys.path = _isolated_path
            
            # Nettoyer les modules 'state' et 'agent' du cache pour les recharger depuis agent_frontend
            for _mod_key in list(sys.modules.keys()):
                if _mod_key.startswith(("state", "agent", "graph", "package_installer", "theme")):
                    if _mod_key in sys.modules and sys.modules[_mod_key].__file__:
                        if "agent_architecte" in sys.modules[_mod_key].__file__:
                            try:
                                del sys.modules[_mod_key]
                            except:
                                pass
            
            # Charger le module
            spec = importlib.util.spec_from_file_location("_frontend_graph_module", str(_FRONTEND_GRAPH_FILE))
            if not spec or not spec.loader:
                logging.getLogger(__name__).error("[frontend_adapter] Impossible de créer spec pour graph.py")
                return None
            
            _frontend_graph_module = importlib.util.module_from_spec(spec)
            sys.modules["_frontend_graph_module"] = _frontend_graph_module
            spec.loader.exec_module(_frontend_graph_module)
            
            _frontend_graph = getattr(_frontend_graph_module, "graph", None)
            
            if _frontend_graph:
                logging.getLogger(__name__).info(
                    "[frontend_adapter] Sous-graphe frontend chargé avec succès depuis %s", _FRONTEND_GRAPH_FILE
                )
                return _frontend_graph
            else:
                logging.getLogger(__name__).error(
                    "[frontend_adapter] Variable 'graph' non trouvée dans %s", _FRONTEND_GRAPH_FILE
                )
                return None
                
        finally:
            # Restaurer sys.path
            sys.path = _original_path
            # Nettoyer UNIQUEMENT les modules temporaires, pas tout
            for _mod_key in list(sys.modules.keys()):
                if _mod_key.startswith(("_frontend_", "agent", "package_installer")) and _mod_key not in _original_modules:
                    try:
                        del sys.modules[_mod_key]
                    except:
                        pass
    
    except Exception as _e:
        logging.getLogger(__name__).error(
            "[frontend_adapter] Erreur lors du chargement du sous-graphe : %s", _e
        )
        return None

# ── Import du logger de Manal ────────────────────────────────────────────────
try:
    from core.logger import (
        log_phase_start,
        log_agent_thinking,
        log_state_update,
        log_error,
    )
except ImportError:
    # Fallback si le logger de Manal n'est pas accessible
    def log_phase_start(a, b):    logging.getLogger(__name__).info("[%s] %s", a, b)
    def log_agent_thinking(a, b): logging.getLogger(__name__).info("[%s] %s", a, b)
    def log_state_update(a, b):   logging.getLogger(__name__).info("[%s] state update: %s", a, b)
    def log_error(a, b):          logging.getLogger(__name__).error("[%s] %s", a, b)


logger = logging.getLogger(__name__)


# ───────────────────────────────────────────────────────────────────────────────
# ÉTAPE 1 — Conversion AgentState → FrontendState
# ───────────────────────────────────────────────────────────────────────────────

def _build_frontend_doc(blueprint: dict) -> str:
    """
    Construit le frontend_doc de manière COMPACTE pour économiser les tokens.
    Version réduite mais avec les infos essentielles.
    
    IMPORTANT: Inclut les noms réels des modules du blueprint pour que le coder
    les utilise comme clés internes (pas de mismatch avec labels français).
    """
    project = blueprint.get("project", {})
    modules = blueprint.get("modules", [])
    dev_instructions = blueprint.get("dev_instructions", {})
    frontend_instructions = dev_instructions.get("frontend", "")
    
    # Ensure everything is a string before slicing
    description = str(project.get('description', ''))[:200] if project.get('description') else ""
    frontend_str = str(frontend_instructions)[:300] if frontend_instructions else ""
    
    # Format très compact
    lines = [
        f"PROJECT: {project.get('name', 'App')}",
        f"DESC: {description}",
    ]
    
    if modules:
        # IMPORTANT: Passe les noms réels des modules pour que le coder les utilise
        # Exemple: ["dashboard", "tasks", "auth"] → sera utilisé comme clés internes
        # Le coder peut créer des labels français mais DOIT mapper sur ces clés
        lines.append(f"MODULES_INTERNES: {', '.join(str(m) for m in modules)}")  # Noms réels
        lines.append(f"MODULE_COUNT: {len(modules)}")
    
    if frontend_str:
        lines.append(f"REQUIREMENTS: {frontend_str}")  # Max 300 chars
    
    return " | ".join(lines)


def _build_backend_specs(blueprint: dict, backend_summary: dict = None) -> str:
    """
    Construit les backend_specs DÉTAILLÉES pour que le coder sache exactement
    quels endpoints appeler et comment les utiliser.
    
    Le backend_summary vient d'Akram (dev_backend_node) et contient :
      - endpoints réels avec paths, methods, auth requirements
      - models avec leurs champs
      - auth config réelle
      - base_url
    
    Format : Incluent les détails sur chaque endpoint (paramètres, réponse exemple, etc.)
    """
    # Priorité 1 : utiliser le backend_summary réel d'Akram (s'il est disponible)
    if backend_summary:
        lines = [
            f"BASE_URL: {backend_summary.get('base_url', 'http://localhost:8000')}",
            f"AUTH_TYPE: {backend_summary.get('auth', {}).get('type', 'JWT Bearer')}",
            f"AUTH_HEADER: Authorization: Bearer <token>",
        ]
        
        # Endpoints avec DÉTAILS
        endpoints = backend_summary.get("endpoints", [])
        if endpoints:
            lines.append("\n=== ENDPOINTS DÉTAILLÉS ===")
            for ep in endpoints[:15]:  # Max 15 endpoints
                method = ep.get("method", "GET")
                path = ep.get("path", "/")
                auth_required = "🔒 PROTÉGÉ" if ep.get("auth_required") else "🔓 PUBLIC"
                description = ep.get("description", "")
                
                ep_line = f"{method:6} {path:30} {auth_required}"
                lines.append(ep_line)
                
                # Ajouter les paramètres s'ils existent
                params = ep.get("parameters", {})
                if params:
                    for pname, pinfo in list(params.items())[:3]:
                        ptype = pinfo.get("type", "string")
                        lines.append(f"        └─ {pname}: {ptype}")
                
                # Ajouter un exemple de réponse si disponible
                example = ep.get("response_example")
                if example:
                    lines.append(f"        └─ Réponse: {str(example)[:80]}...")
        
        # Models
        models = backend_summary.get("models", {})
        if models:
            lines.append("\n=== MODELS ===")
            for mname, mfields in list(models.items())[:5]:
                lines.append(f"{mname}:")
                if isinstance(mfields, dict):
                    for fname in list(mfields.keys())[:5]:
                        lines.append(f"  - {fname}")
        
        notes = backend_summary.get("notes", "")
        if notes:
            lines.append(f"\n=== NOTES ===\n{notes[:300]}")
        
        return "\n".join(lines)
    
    # Fallback 2 : si pas de backend_summary, utiliser le blueprint
    endpoints = blueprint.get("api_endpoints", [])
    tech_stack = blueprint.get("tech_stack", {})
    project = blueprint.get("project", {})
    
    lines = [
        f"=== BACKEND API SPECS ===",
        f"Project: {project.get('name', 'App')}",
        f"Base URL: http://localhost:8000",
        f"Backend: {tech_stack.get('backend', 'FastAPI')}",
        f"Auth: {tech_stack.get('auth', 'Bearer JWT')}",
        f"\n=== ENDPOINTS ===",
    ]
    
    # Endpoints avec détails du blueprint
    if endpoints:
        for ep in endpoints[:15]:
            method = ep.get("method", "GET")
            path = ep.get("path", "/")
            description = ep.get("description", "")
            lines.append(f"{method:6} {path:30} - {description}")
    
    return "\n".join(lines)


def _build_frontend_initial_state(agent_state: dict) -> dict:
    """
    Construit l'état initial complet pour le sous-graphe de Mactar.
    Mappe les champs de l'AgentState de Manal vers le FrontendState de Mactar.
    
    IMPORTANT : Récupère le backend_summary d'Akram pour que le frontend sache
    sur quels endpoints réels il doit requêter.
    """
    blueprint  = agent_state.get("architect_blueprint", {})
    tech_stack = blueprint.get("tech_stack", agent_state.get("tech_stack", {}))
    repo_path  = agent_state.get("repo_path", "./output/app")
    backend_summary = agent_state.get("backend_summary", {})  # ← Récupérer le résumé d'Akram

    return {
        # ── Champs métier ────────────────────────────────────────────────────
        "frontend_doc":   _build_frontend_doc(blueprint),
        "backend_specs":  _build_backend_specs(blueprint, backend_summary),  # ← Passer le backend_summary

        # ── Contrôle interne du sous-graphe ─────────────────────────────────
        "messages":           [],
        "generated_code":     "",
        "iteration_count":    0,
        "feedback":           "",

        # ── Thème client (vide → Mactar utilise les défauts de client_config.yaml) ─
        "theme_config":       {},

        # ── Dépôt de packages (désactivé par défaut) ─────────────────────────
        "repo_config":        {},
        "required_packages":  [],
        "installation_report": "",
    }


# ───────────────────────────────────────────────────────────────────────────────
# NŒUD PRINCIPAL — compatible avec le graphe de Manal
# ───────────────────────────────────────────────────────────────────────────────

def frontend_adapter_node(state: dict, llm=None) -> dict:
    """
    Nœud LangGraph compatible avec l'AgentState de Manal.
    Invoque le sous-graphe de Mactar et retourne les résultats
    dans le format attendu par l'AgentState.

    Paramètres
    ----------
    state : AgentState de Manal (dict-like)
    llm   : ignoré — le sous-graphe de Mactar gère son propre LLM (Groq)

    Retourne
    --------
    dict : champs à mettre à jour dans l'AgentState de Manal
    """
    log_phase_start("frontend_adapter", "Lancement du sous-graphe Frontend (Mactar)")

    blueprint    = state.get("architect_blueprint", {})
    project_name = blueprint.get("project", {}).get("name", state.get("project_name", "app"))

    log_agent_thinking(
        "frontend_adapter",
        f"Projet : '{project_name}'\n"
        f"Modules frontend : {blueprint.get('modules', [])}\n"
        f"Endpoints transmis : {len(blueprint.get('api_endpoints', []))} routes\n"
        "Construction du FrontendState depuis le blueprint...",
    )

    # ── Charger le sous-graphe de manière lazy ──────────────────────────────
    frontend_graph = _load_frontend_graph()
    
    # ── Cas stub : sous-graphe non disponible ───────────────────────────────
    if frontend_graph is None:
        log_error(
            "frontend_adapter",
            "Sous-graphe frontend non chargé — résultat stub retourné."
        )
        return {
            "frontend_output": {
                "status":         "stub",
                "generated_code": "# Sous-graphe frontend non disponible",
                "iterations":     0,
            },
            "reasoning_trace": state.get("reasoning_trace", []) + [
                "[FRONTEND] Stub — sous-graphe non chargé."
            ],
            "current_phase": "database",
        }

    # ── Étape 1 : Construire l'état initial du sous-graphe ──────────────────
    frontend_initial = _build_frontend_initial_state(state)

    log_agent_thinking(
        "frontend_adapter",
        f"frontend_doc   : {len(frontend_initial['frontend_doc'])} caractères\n"
        f"backend_specs  : {len(frontend_initial['backend_specs'])} caractères\n"
        "Invocation du sous-graphe frontend...",
    )

    # ── Étape 2 : Invoquer le sous-graphe de Mactar ─────────────────────────
    try:
        frontend_final = frontend_graph.invoke(frontend_initial)
    except Exception as exc:
        import traceback
        tb = traceback.format_exc()
        log_error("frontend_adapter", f"Erreur dans le sous-graphe frontend : {exc}\n{tb}")
        logging.getLogger(__name__).error("[frontend_adapter] Full traceback:\n%s", tb)
        return {
            "frontend_output": {
                "status": "error",
                "error":  str(exc),
                "generated_code": "",
            },
            "reasoning_trace": state.get("reasoning_trace", []) + [
                f"[FRONTEND] Erreur : {exc}\n{tb}"
            ],
            "current_phase": "database",
        }

    # ── Étape 3 : Extraire les résultats et les remonter dans AgentState ────
    generated_code = frontend_final.get("generated_code", "")
    iterations     = frontend_final.get("iteration_count", 0)
    packages       = frontend_final.get("required_packages", [])
    install_report = frontend_final.get("installation_report", "")

    log_agent_thinking(
        "frontend_adapter",
        f"Sous-graphe terminé en {iterations} itération(s).\n"
        f"Code généré : {generated_code.count(chr(10))} lignes\n"
        f"Packages installés : {packages}",
    )

    # Optionnel : sauvegarder app.py dans le repo du projet
    repo_path = state.get("repo_path", f"./output/{project_name}")
    if not repo_path:
        repo_path = f"./output/{project_name}"
    
    logger.info("[frontend_adapter] Tentative de sauvegarde dans : %s", repo_path)
    _save_frontend_output(repo_path, generated_code, project_name)

    log_state_update(
        "frontend_adapter",
        ["frontend_output", "reasoning_trace", "current_phase"],
    )

    return {
        # Résultat rangé dans le champ dédié de l'AgentState de Manal
        "frontend_output": {
            "status":            "completed",
            "generated_code":    generated_code,
            "iterations":        iterations,
            "required_packages": packages,
            "install_report":    install_report,
            "lines_of_code":     generated_code.count("\n"),
        },

        # Trace de raisonnement accumulée
        "reasoning_trace": state.get("reasoning_trace", []) + [
            f"[FRONTEND] Interface Streamlit générée en {iterations} itération(s). "
            f"{generated_code.count(chr(10))} lignes — "
            f"packages : {packages or 'aucun supplémentaire'}."
        ],

        # Prochain agent dans le pipeline
        "current_phase": "devops",
    }


def _save_frontend_output(repo_path: str, code: str, project_name: str) -> None:
    """
    Sauvegarde app.py ainsi que ses fichiers de configuration dans le dossier frontend.
    
    Fichiers copiés :
      - app.py (code généré)
      - client_config.yaml (configuration de thème)
      - theme_runtime.py (runtime pour les thèmes)
    """
    # Vérifier que repo_path est valide
    if not repo_path:
        logger.warning("[frontend_adapter] repo_path est vide ou None — impossible de sauvegarder les fichiers")
        return
    
    try:
        import shutil
        
        # Convertir en chemin absolu
        repo_path = pathlib.Path(repo_path).resolve()
        frontend_dir = repo_path / "frontend"
        frontend_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info("[frontend_adapter] Création du dossier frontend : %s", frontend_dir)
        logger.info("[frontend_adapter] Chemin du fichier courant : %s", pathlib.Path(__file__).resolve())

        # 1. Sauvegarder app.py (code généré)
        app_file = frontend_dir / "app.py"
        app_file.write_text(code, encoding="utf-8")
        logger.info("[frontend_adapter] ✓ app.py sauvegardé → %s (%d lignes)", app_file, code.count('\n'))

        # 2. Copier theme_runtime.py
        theme_found = False
        _theme_candidates = [
            pathlib.Path(__file__).resolve().parent.parent.parent / "agent_frontend" / "theme_runtime.py",
            pathlib.Path(__file__).resolve().parent.parent.parent.parent / "agent_frontend" / "theme_runtime.py",
        ]
        
        logger.info("[frontend_adapter] Recherche de theme_runtime.py dans :")
        for _src in _theme_candidates:
            logger.info("  - %s (existe: %s)", _src, _src.exists())
            if _src.exists():
                shutil.copy2(_src, frontend_dir / "theme_runtime.py")
                logger.info("[frontend_adapter] ✓ theme_runtime.py copié → %s", frontend_dir / "theme_runtime.py")
                theme_found = True
                break
        
        if not theme_found:
            logger.warning("[frontend_adapter] theme_runtime.py non trouvé")
        
        # 3. Copier client_config.yaml (configuration de thème)
        config_found = False
        _config_candidates = [
            pathlib.Path(__file__).resolve().parent.parent.parent / "agent_frontend" / "client_config.yaml",
            pathlib.Path(__file__).resolve().parent.parent.parent.parent / "agent_frontend" / "client_config.yaml",
        ]
        
        logger.info("[frontend_adapter] Recherche de client_config.yaml dans :")
        for _src in _config_candidates:
            logger.info("  - %s (existe: %s)", _src, _src.exists())
            if _src.exists():
                shutil.copy2(_src, frontend_dir / "client_config.yaml")
                logger.info("[frontend_adapter] ✓ client_config.yaml copié → %s", frontend_dir / "client_config.yaml")
                config_found = True
                break
        
        if not config_found:
            logger.warning("[frontend_adapter] client_config.yaml non trouvé")
        
        logger.info("[frontend_adapter] ✓ Tous les fichiers frontend sauvegardés avec succès")

    except Exception as exc:
        logger.error("[frontend_adapter] Erreur lors de la sauvegarde des fichiers frontend : %s", exc)
