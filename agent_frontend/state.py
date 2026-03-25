"""
state.py
--------
Définit le FrontendState partagé entre tous les nœuds du graphe LangGraph.
"""

from __future__ import annotations

from typing import Annotated, Any

from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage
from typing_extensions import TypedDict


class FrontendState(TypedDict):
    """
    État global partagé entre tous les nœuds du graphe.

    Attributs
    ---------
    messages : list[BaseMessage]
        Historique des échanges LLM ; géré par le réducteur `add_messages`
        (accumulation sans écrasement).
    frontend_doc : str
        Documentation métier décrivant le besoin fonctionnel du frontend.
    backend_specs : str
        Spécifications des endpoints API backend (routes, méthodes, payloads…).
    generated_code : str
        Code Streamlit produit par le nœud `coder` (mis à jour à chaque itération).
    iteration_count : int
        Compteur d'itérations coder ↔ reviewer (circuit-breaker).
    feedback : str
        Retour structuré du nœud `reviewer` vers le nœud `coder`.

    -- Adaptabilité client --

    theme_config : dict[str, Any]
        Charte graphique chargée depuis client_config.yaml
        (couleurs, typo, branding, composants).
    repo_config : dict[str, Any]
        Configuration du dépôt de packages privé (repo_config.yaml).
        Vide si aucun dépôt privé configuré.
    required_packages : list[str]
        Packages Python identifiés par `analyzer` comme nécessaires
        (y compris bibliothèques internes client).
    installation_report : str
        Rapport produit par le nœud `installer` après tentative d'installation.
    """

    messages: Annotated[list[BaseMessage], add_messages]
    frontend_doc: str
    backend_specs: str
    generated_code: str
    iteration_count: int
    feedback: str

    # ── Adaptabilité client ───────────────────────────────────────────────
    theme_config: dict[str, Any]
    repo_config: dict[str, Any]
    required_packages: list[str]
    installation_report: str
