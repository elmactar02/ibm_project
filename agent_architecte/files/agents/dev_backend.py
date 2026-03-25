"""
agents/dev_backend.py — Wrapper pour intégrer l'agent backend (Akram) au pipeline orchestrateur.

Permet le passage du state du coordonneur vers le backend et inversement.
Synchronise aussi le schéma de la DB avec le backend pour qu'il sache sur quelles tables faire requêtes.
"""

import sys
import json
from pathlib import Path
import importlib.util

from state.schema import AgentState


def _load_backend_graph():
    """
    Lazy-load du graphe backend depuis agent_backend/graph.py
    Isole les imports pour éviter les conflits (par exemple avec le module 'graph' local)
    
    Structure :
      ibm_project/
        ├── agent_architecte/files/agents/dev_backend.py  (ce fichier)
        └── agent_backend/
            ├── state.py
            └── graph.py
    
    IMPORTANT : Cette fonction ne fait PAS le cleanup. Le cleanup est fait dans dev_backend_node()
    après l'invocation du graphe, pour éviter de charger les modules trop tôt.
    """
    # Remonter 4 niveaux : agents → files → agent_architecte → ibm_project
    backend_path = Path(__file__).parent.parent.parent.parent / "agent_backend"
    
    print(f"  🔍  Chemin backend: {backend_path}")
    
    if not backend_path.exists():
        raise FileNotFoundError(f"Backend path not found: {backend_path}")
    
    # Sauvegarder le sys.path actuel
    _original_path = sys.path[:]
    
    try:
        # Ajouter le chemin du backend au début du sys.path
        # pour que les imports locaux du backend trouvent ses propres modules
        sys.path.insert(0, str(backend_path))
        
        # Charger les dépendances du backend dans le bon ordre
        # 1. state.py (pas de dépendances)
        state_file = backend_path / "state.py"
        state_spec = importlib.util.spec_from_file_location(
            "backend_state_module",
            state_file
        )
        state_module = importlib.util.module_from_spec(state_spec)
        sys.modules["backend_state_module"] = state_module
        sys.modules["state"] = state_module  # Mapper "state" pour le backend
        state_spec.loader.exec_module(state_module)
        
        # 2. utils.py (peut dépendre de state)
        utils_file = backend_path / "utils.py"
        if utils_file.exists():
            utils_spec = importlib.util.spec_from_file_location(
                "backend_utils_module",
                utils_file
            )
            utils_module = importlib.util.module_from_spec(utils_spec)
            sys.modules["backend_utils_module"] = utils_module
            sys.modules["utils"] = utils_module
            utils_spec.loader.exec_module(utils_module)
        
        # 3. nodes.py (dépend de state, utils)
        nodes_file = backend_path / "nodes.py"
        if nodes_file.exists():
            nodes_spec = importlib.util.spec_from_file_location(
                "backend_nodes_module",
                nodes_file
            )
            nodes_module = importlib.util.module_from_spec(nodes_spec)
            sys.modules["backend_nodes_module"] = nodes_module
            sys.modules["nodes"] = nodes_module
            nodes_spec.loader.exec_module(nodes_module)
        
        # 4. router.py (dépend de state, nodes)
        router_file = backend_path / "router.py"
        if router_file.exists():
            router_spec = importlib.util.spec_from_file_location(
                "backend_router_module",
                router_file
            )
            router_module = importlib.util.module_from_spec(router_spec)
            sys.modules["backend_router_module"] = router_module
            sys.modules["router"] = router_module
            router_spec.loader.exec_module(router_module)
        
        # 5. graph.py (dépend de state, nodes, router)
        graph_file = backend_path / "graph.py"
        graph_spec = importlib.util.spec_from_file_location(
            "backend_graph_module",
            graph_file
        )
        graph_module = importlib.util.module_from_spec(graph_spec)
        sys.modules["backend_graph_module"] = graph_module
        sys.modules["graph"] = graph_module
        graph_spec.loader.exec_module(graph_module)
        
        return graph_module, state_module
        
    finally:
        # Restaurer le sys.path IMMÉDIATEMENT
        sys.path = _original_path


def _convert_state_to_backend(state: AgentState) -> dict:
    """
    Convertit le state du coordonneur (AgentState) vers le state du backend (BackendState).
    Passe notamment le schéma DB et le projet pour sync.
    """
    backend_state = {
        "plan": state.get("architect_blueprint", {}),  # Le blueprint contient les tâches backend
        "db_project_name": state.get("project_name", ""),
        "db_schema": state.get("db_schema", {}),
        "db_api_url": "http://localhost:8003",  # API du coordonneur (port 8003)
        "task_queue": [],
        "current_task_index": 0,
        "current_task": {},
        "current_attempt": 0,
        "error_feedback": {},
        "test_results": {},
        "generated_files": [],
        "task_statuses": {},
        "project_root": state.get("repo_path", "./output/generated"),
        "backend_summary": {},
        "phase": "backend",
        "logs": [],
    }
    return backend_state


def _convert_state_from_backend(backend_state: dict, original_state: AgentState) -> AgentState:
    """
    Convertit le state du backend vers AgentState pour continuer le pipeline.
    """
    # Les fichiers générés par le backend sont accumulés dans backend_files
    original_state["backend_files"] = backend_state.get("generated_files", [])
    original_state["backend_output"] = {
        "endpoints": len(backend_state.get("backend_summary", {}).get("endpoints", [])),
        "models": len(backend_state.get("backend_summary", {}).get("models", {})),
        "auth": backend_state.get("backend_summary", {}).get("auth", {}),
    }
    
    # Stocker le résumé pour le frontend
    original_state["backend_summary"] = backend_state.get("backend_summary", {})
    
    original_state["reasoning_trace"].append(
        f"[dev_backend] Generated {len(backend_state.get('generated_files', []))} backend files"
    )
    
    return original_state


def dev_backend_node(state: AgentState) -> AgentState:
    """
    Node qui orchestrate le backend agent.
    1. Charge le graphe backend (lazy-loading)
    2. Convertit le state du coordonneur
    3. Invoque le graphe backend
    4. Récupère les fichiers générés
    5. Nettoie les modules temporaires
    6. Retourne le state mis à jour
    """
    print("\n🔧  [dev_backend_node] Invocation du backend agent (Akram)...")
    
    # Sauvegarder les modules originaux AVANT de charger le backend
    _original_modules = set(sys.modules.keys())
    
    try:
        # Charger le graphe backend
        backend_graph_module, backend_state_module = _load_backend_graph()
        backend_graph = backend_graph_module.build_graph()
        
        # Convertir le state
        backend_state = _convert_state_to_backend(state)
        
        # Afficher infos DB synchronisées
        if state.get("db_schema"):
            tables = list(state.get("db_schema", {}).keys())
            print(f"  ✅  DB synchronisée: {len(tables)} tables disponibles")
        
        # Invoquer le graphe backend
        print(f"  🚀  Exécution du pipeline backend (projet: {state.get('project_name')})...")
        final_backend_state = backend_graph.invoke(backend_state)
        
        # Convertir le résultat
        result_state = _convert_state_from_backend(final_backend_state, state)
        result_state["current_phase"] = "dev_backend"
        
        generated_count = len(final_backend_state.get("generated_files", []))
        print(f"  ✅  Backend généré: {generated_count} fichiers")
        
        return result_state
        
    except Exception as e:
        import traceback
        print(f"  ❌  Erreur dev_backend: {str(e)}")
        traceback.print_exc()
        state["error"] = f"Backend agent failed: {str(e)}"
        state["current_phase"] = "dev_backend_error"
        return state
    
    finally:
        # Nettoyer TOUS les modules du backend qu'on a chargés
        modules_to_remove = []
        for _mod_key in list(sys.modules.keys()):
            if (_mod_key.startswith("backend_") or 
                _mod_key in ["state", "nodes", "router", "utils", "graph", "plan_agent"]):
                if _mod_key not in _original_modules:
                    modules_to_remove.append(_mod_key)
        
        for _mod_key in modules_to_remove:
            try:
                del sys.modules[_mod_key]
            except:
                pass
        
        # CRITICAL: Remove 'state' from sys.modules so frontend_adapter doesn't see backend's state
        if "state" in sys.modules and "state" not in _original_modules:
            try:
                del sys.modules["state"]
            except:
                pass
        
        print(f"  🧹  Nettoyage: {len(modules_to_remove)} modules temporaires supprimés")
