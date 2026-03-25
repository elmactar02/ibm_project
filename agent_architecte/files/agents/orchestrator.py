import os
from state.schema import AgentState
from core.logger import (
    log_phase_start,
    log_agent_thinking,
    log_error,
    log_pipeline_complete,
)

MAX_QA_RETRIES = 2


# ═══════════════════════════════════════════════════════════════════════════════
# FONCTION 1 — NOEUD D'ENTRÉE
# Appelé en premier par LangGraph à chaque run du pipeline complet.
# ═══════════════════════════════════════════════════════════════════════════════

def orchestrator_plan(state: AgentState) -> dict:
    """
    Noeud d'entrée du pipeline LangGraph.

    Responsabilités :
      1. Valider que l'état initial est complet
      2. Logger le plan d'exécution
      3. Retourner current_phase = "architect" pour démarrer Manal
    """
    log_phase_start("orchestrator", "Démarrage du pipeline — validation et planification")

    project_name = state.get("project_name", "")
    raw_input    = state.get("raw_input", "")

    # ── Validation ────────────────────────────────────────────────────────────
    if not raw_input.strip():
        log_error("orchestrator", "raw_input est vide — impossible de démarrer.")
        return {"current_phase": "error", "error": "Aucun besoin saisi."}

    if not project_name.strip():
        log_error("orchestrator", "project_name vide — utilisation de 'app'.")
        project_name = "app"

    if not os.getenv("MISTRAL_API_KEY") and not os.getenv("OLLAMA_BASE_URL"):
        log_error("orchestrator", "Aucune clé LLM trouvée dans l'environnement.")
        return {"current_phase": "error", "error": "MISTRAL_API_KEY manquante dans .env"}

    # ── Log du plan ───────────────────────────────────────────────────────────
    log_agent_thinking(
        "orchestrator",
        f"Projet    : '{project_name}'\n"
        f"Input     : {len(raw_input)} chars\n"
        f"Output    : ./output/{project_name}/\n"
        f"Max retries QA : {MAX_QA_RETRIES}\n"
        "\n"
        "Ordre d'exécution :\n"
        "  1. Architect     (Manal)   → blueprint.json + C4 + tech stack + doc\n"
        "  2. DevOps                  → git init + CI/CD + Dockerfile\n"
        "  3. Dev Database  (Oumeyma) → models.py + database.py + schemas.py\n"
        "  4. Dev Backend   (Akram)   → routers + auth + main.py + tests\n"
        "  5. Dev Frontend  (Mactar)  → React pages + composants + services\n"
        "  6. QA                      → pytest + flake8 + review LLM\n"
        "\n"
        "Boucle de correction :\n"
        f"  QA FAIL → retour Dev Database (max {MAX_QA_RETRIES} tentatives)\n"
        "  QA PASS → END",
    )

    return {
        "project_name":  project_name,
        "db_project_name": project_name,  # Initialiser le nom pour la DB
        "db_schema": {},                   # Schéma vide à ce stade
        "current_phase": "architect",
    }


# ═══════════════════════════════════════════════════════════════════════════════
# FONCTION 2 — ROUTAGE CONDITIONNEL APRÈS QA
# Appelée par LangGraph après chaque exécution du noeud QA.
# ═══════════════════════════════════════════════════════════════════════════════

def route_after_qa(state: AgentState) -> str:
    """
    Routage conditionnel post-QA.

    Retourne :
      "dev_database" → relance Oumeyma → Akram → Mactar → QA
      "__end__"      → termine le pipeline
    """
    qa_attempts   = state.get("qa_attempts", 0)
    validation_ok = state.get("validation_passed", False)
    project_name  = state.get("project_name", "?")

    if validation_ok:
        # Succès
        log_agent_thinking(
            "orchestrator",
            f"QA PASS pour '{project_name}' — {qa_attempts} tentative(s).\n"
            "Pipeline terminé avec succès. → END",
        )
        log_pipeline_complete(state)
        return "__end__"

    if qa_attempts < MAX_QA_RETRIES:
        # Échec récupérable → retry
        log_agent_thinking(
            "orchestrator",
            f"QA FAIL — tentative {qa_attempts}/{MAX_QA_RETRIES}.\n"
            "Retour vers Dev Database pour re-génération.\n"
            "Chaîne relancée : dev_database → dev_backend → dev_frontend → qa",
        )
        return "dev_database"

    # Échec définitif → abandon propre
    log_agent_thinking(
        "orchestrator",
        f"QA FAIL après {qa_attempts} tentative(s) — maximum atteint.\n"
        f"Rapport QA dans output/{project_name}/docs/qa_report.json\n"
        "→ END",
    )
    log_pipeline_complete(state)
    return "__end__"