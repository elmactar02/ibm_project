"""
graph.py
--------
Assemble le graphe LangGraph du Frontend Developer Agent.

Topologie :
    START → analyzer → installer → coder → reviewer ──(NEEDS_FIX)──▶ coder
                                                     ──(OK / max)────▶ END

Le nœud `installer` est transparent si aucun package n'est requis.
"""

from __future__ import annotations

import logging

from langgraph.graph import END, START, StateGraph

from agent import analyzer, coder, reviewer, should_retry
from package_installer import installer
from state import FrontendState

logger = logging.getLogger(__name__)


def build_graph() -> StateGraph:
    """
    Instancie et compile le StateGraph du Frontend Developer Agent.

    Retourne
    --------
    CompiledGraph
        Graphe compilé prêt à être invoqué via .invoke() ou .stream().
    """
    builder = StateGraph(FrontendState)

    # Noeuds
    builder.add_node("analyzer",  analyzer)
    builder.add_node("installer", installer)   # Nouveau : installe les packages
    builder.add_node("coder",     coder)
    builder.add_node("reviewer",  reviewer)

    # Aretes statiques
    builder.add_edge(START,       "analyzer")
    builder.add_edge("analyzer",  "installer")  # Toujours via installer (skip si rien)
    builder.add_edge("installer", "coder")
    builder.add_edge("coder",     "reviewer")

    # Arete conditionnelle (cycle ou fin)
    builder.add_conditional_edges(
        "reviewer",
        should_retry,
        {
            "coder": "coder",
            "end":   END,
        },
    )

    compiled = builder.compile()
    logger.info("Graphe compile — topology: analyzer -> installer -> coder -> reviewer")
    return compiled


# Instance singleton exportee
graph = build_graph()
