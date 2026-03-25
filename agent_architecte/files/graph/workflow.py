import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from langgraph.graph import StateGraph, END

# Ajouter le répertoire parent au path
sys.path.insert(0, str(Path(__file__).parent.parent))

from state.schema import AgentState
from agents.orchestrator import orchestrator_plan, route_after_qa
from agents.architect import architect_node
from agents.db_adapter import db_adapter_node
from agents.dev_backend import dev_backend_node
from agents.frontend_adapter import frontend_adapter_node
#from agents.qa import qa_node

load_dotenv()


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 1 — CONFIGURATION DU LLM
# ═══════════════════════════════════════════════════════════════════════════════

def _build_llm():
    """
    Construit le LLM selon les variables d'environnement disponibles.
    Ordre de priorité : Mistral API > Ollama > OpenAI
    """
    mistral_key = os.getenv("MISTRAL_API_KEY", "")
    ollama_url  = os.getenv("OLLAMA_BASE_URL", "")
    openai_key  = os.getenv("OPENAI_API_KEY", "")

    if mistral_key:
        from langchain_mistralai import ChatMistralAI
        print("🔵  LLM : Mistral API (open-source weights)")
        return ChatMistralAI(
            model=os.getenv("MISTRAL_MODEL", "mistral-large-latest"),
            api_key=mistral_key,
            temperature=0.1,
        )

    if ollama_url:
        from langchain_community.chat_models import ChatOllama
        print("🟢  LLM : Ollama (local)")
        return ChatOllama(
            model=os.getenv("OLLAMA_MODEL", "mistral:7b-instruct"),
            base_url=ollama_url,
            temperature=0.1,
        )

    if openai_key:
        from langchain_openai import ChatOpenAI
        print("🟡  LLM : OpenAI (fallback)")
        return ChatOpenAI(
            model="gpt-4o-mini",
            api_key=openai_key,
            temperature=0.1,
        )

    raise EnvironmentError(
        "Aucun LLM configuré. "
        "Définis MISTRAL_API_KEY, OLLAMA_BASE_URL ou OPENAI_API_KEY dans .env"
    )


# Singleton LLM — une seule instance partagée entre tous les agents
_llm = None

def _get_llm():
    global _llm
    if _llm is None:
        _llm = _build_llm()
    return _llm


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 2 — WRAPPERS DES NODES
# Chaque wrapper injecte le LLM partagé dans le node de l'agent
# ═══════════════════════════════════════════════════════════════════════════════

def _orchestrator_node(state):      return orchestrator_plan(state)
def _architect_node(state):         return architect_node(state,           _get_llm())
def _devops_node(state):            return devops_node(state,              _get_llm())
def _db_adapter_node(state):        return db_adapter_node(state,          _get_llm())
def _dev_backend_node(state):       return dev_backend_node(state)
def _frontend_adapter_node(state):  return frontend_adapter_node(state,    _get_llm())


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 3 — CONSTRUCTION DU GRAPHE
# ═══════════════════════════════════════════════════════════════════════════════

def build_graph():
    """
    Construit et compile le graphe LangGraph selon le schéma de l'équipe.

    Flux linéaire :
      orchestrator → architect → devops → dev_database → dev_backend → frontend_adapter → qa

    Boucle conditionnelle :
      qa → dev_database  (si FAIL et attempts < 2)
      qa → END           (si PASS ou attempts >= 2)
    """
    g = StateGraph(AgentState)

    # ── Enregistrement des nodes ──────────────────────────────────────────────
    g.add_node("orchestrator",      _orchestrator_node)
    g.add_node("architect",         _architect_node)
    g.add_node("devops",            _devops_node)
    g.add_node("dev_database",      _db_adapter_node)
    g.add_node("dev_backend",       _dev_backend_node)
    g.add_node("frontend_adapter",  _frontend_adapter_node)

    # ── Flux principal ────────────────────────────────────────────────────────
    g.set_entry_point("orchestrator")
    g.add_edge("orchestrator",    "architect")         # Interface → Manal
    g.add_edge("architect",       "dev_database")            # Blueprint → repo git
    #g.add_edge("devops",          "dev_database")      # Repo prêt → Oumeyma
    g.add_edge("dev_database",    "dev_backend")       # Models prêts → Akram
    g.add_edge("dev_backend",     "frontend_adapter")  # API prête → Mactar
    #g.add_edge("frontend_adapter", "qa")             # Code complet → QA

    # ── Boucle conditionnelle après QA ───────────────────────────────────────
    """g.add_conditional_edges(
        "qa",
        route_after_qa,
        {
            "dev_database": "dev_database",  # Relance depuis la BDD
            "__end__":       END,
        },
    )"""

    return g.compile()


# ── Export du graphe compilé ──────────────────────────────────────────────────
app_graph = build_graph()