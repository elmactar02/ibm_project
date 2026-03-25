"""
main.py
-------
Point d'entree pour tester le Frontend Developer Agent.

Pre-requis :
    Cle API Groq gratuite -> https://console.groq.com
    export GROQ_API_KEY="gsk_..."

    (Optionnel) Pour depot prive :
    export REPO_USERNAME="..."
    export REPO_PASSWORD="..."

Utilisation :
    python main.py

Le code Streamlit genere est sauvegarde dans output/app.py.
"""

from __future__ import annotations

import logging
import os
import pathlib
import shutil
import textwrap
from typing import Any

from graph import graph
from state import FrontendState
from theme_loader import load_theme
from package_installer import load_repo_config

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  [%(levelname)s]  %(name)s - %(message)s",
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Donnees d'exemple (Task Manager — conforme au sujet IBM)
# ---------------------------------------------------------------------------

FRONTEND_DOC: str = textwrap.dedent("""\
    # Application de Gestion des Taches (Task Manager)

    ## Contexte metier
    Application collaborative de gestion de taches pour des equipes de developpement.
    Les utilisateurs peuvent creer, consulter, mettre a jour et supprimer des taches.
    Chaque tache possede un titre, une description, un statut et une priorite.

    ## Fonctionnalites attendues
    1. Tableau de bord : liste paginee de toutes les taches avec filtres (statut, priorite).
    2. Creation de tache : formulaire avec titre, description, priorite (Low/Medium/High).
    3. Mise a jour de statut : bouton inline pour passer une tache a "Done".
    4. Suppression : bouton de suppression avec confirmation (st.warning).
    5. Detail : affichage complet d'une tache selectionnee.
    6. Connexion utilisateur simplifiee (token Bearer stocke en session).

    ## Contraintes UX
    - Retour visuel immediat apres chaque action (st.success / st.error).
    - Sidebar pour la navigation entre les vues.
    - Respecter strictement la charte graphique client fournie.
""")

BACKEND_SPECS: str = textwrap.dedent("""\
    # API Backend - Task Manager Service
    Base URL : http://localhost:8000/api/v1
    Authentification : Header Authorization: Bearer <token>

    ## Endpoints

    ### GET /tasks
    Query params : status (str), priority (str), page (int), per_page (int)
    Response 200 : { "tasks": [...], "total": int, "page": int, "per_page": int }
    Chaque tache : { "id": "uuid", "title": str, "description": str,
                     "status": "todo|in_progress|done", "priority": "low|medium|high",
                     "created_at": "ISO8601" }

    ### POST /tasks
    Body : { "title": str (requis), "description": str, "priority": "low|medium|high" }
    Response 201 : objet tache complet
    Response 422 : { "detail": [...] }

    ### GET /tasks/{task_id}
    Response 200 : objet tache complet | Response 404

    ### PATCH /tasks/{task_id}/status
    Body : { "status": "todo|in_progress|done" }
    Response 200 : objet tache mis a jour | Response 404

    ### DELETE /tasks/{task_id}
    Response 204 : (no content) | Response 404
""")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _save_output(code: str, output_dir: str = "output") -> pathlib.Path:
    """
    Sauvegarde le code généré avec versioning horodaté.

    Crée deux fichiers :
      - output/app_YYYYMMDD_HHMMSS.py  — version archivée (jamais écrasée)
      - output/app.py                  — symlink/copie vers la dernière version

    Copie aussi theme_runtime.py et client_config.yaml dans output/
    pour que l'app puisse les importer au runtime.
    """
    import datetime, shutil

    out_path = pathlib.Path(output_dir)
    out_path.mkdir(exist_ok=True)

    # ── Fichier versionné ────────────────────────────────────────────────────
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    versioned = out_path / f"app_{timestamp}.py"
    versioned.write_text(code, encoding="utf-8")
    logger.info("Version archivee : %s", versioned.name)

    # ── Copie vers app.py (latest) ───────────────────────────────────────────
    latest = out_path / "app.py"
    shutil.copy2(versioned, latest)

    # ── Copie theme_runtime.py dans output/ (requis par l'app au runtime) ───
    here = pathlib.Path(__file__).parent
    runtime_src = here / "theme_runtime.py"
    if runtime_src.exists():
        shutil.copy2(runtime_src, out_path / "theme_runtime.py")
        logger.info("theme_runtime.py copie dans %s/", output_dir)
    else:
        logger.warning("theme_runtime.py introuvable — l'app generee ne pourra pas charger le theme")

    # ── Copie client_config.yaml dans output/ (lu au runtime par theme_runtime) ─
    cfg_src = here / "client_config.yaml"
    if cfg_src.exists():
        shutil.copy2(cfg_src, out_path / "client_config.yaml")
        logger.info("client_config.yaml copie dans %s/", output_dir)

    return latest


def _print_separator(title: str, width: int = 70) -> None:
    print("\n" + "=" * width)
    print(f"  {title}")
    print("=" * width)


# ---------------------------------------------------------------------------
# Point d'entree
# ---------------------------------------------------------------------------

def main() -> None:
    """Lance l'agent et affiche les resultats etape par etape."""

    # Verification cle Groq
    if not os.environ.get("GROQ_API_KEY"):
        logger.error(
            "Variable d'environnement GROQ_API_KEY manquante.\n"
            "  -> Obtenez une cle gratuite sur https://console.groq.com\n"
            "  -> Puis : export GROQ_API_KEY=\"gsk_...\""
        )
        raise SystemExit(1)
    logger.info("Cle GROQ_API_KEY detectee - modele : qwen/qwen3-32b")

    # Chargement de la charte graphique client
    theme_cfg = load_theme()
    logger.info(
        "Theme client charge : %s / police : %s",
        theme_cfg.get("branding", {}).get("company_name", "N/A"),
        theme_cfg.get("typography", {}).get("font_family", "systeme"),
    )

    # Chargement de la config depot de packages
    repo_cfg = load_repo_config()
    private_enabled = repo_cfg.get("private_repo", {}).get("enabled", False)
    logger.info("Depot prive : %s", "ACTIVE" if private_enabled else "desactive (PyPI)")

    _print_separator("Frontend Developer Agent - Demarrage")

    # Etat initial complet
    initial_state: FrontendState = {
        "messages":            [],
        "frontend_doc":        FRONTEND_DOC,
        "backend_specs":       BACKEND_SPECS,
        "generated_code":      "",
        "iteration_count":     0,
        "feedback":            "",
        # Nouveaux champs
        "theme_config":        theme_cfg,
        "repo_config":         repo_cfg,
        "required_packages":   [],
        "installation_report": "",
    }

    print("\nLancement du graphe en mode streaming...\n")

    final_state: dict[str, Any] = {}

    for step in graph.stream(initial_state, stream_mode="updates"):
        for node_name, node_output in step.items():
            _print_separator(f"Noeud : {node_name.upper()}", width=60)

            if node_name == "analyzer":
                msgs = node_output.get("messages", [])
                pkgs = node_output.get("required_packages", [])
                if msgs:
                    content = msgs[-1].content if hasattr(msgs[-1], "content") else str(msgs[-1])
                    print(content[:1200])
                    if len(content) > 1200:
                        print("  ... [tronque]")
                if pkgs:
                    print(f"\n  Packages detectes : {pkgs}")
                else:
                    print("\n  Aucun package supplementaire detecte.")

            elif node_name == "installer":
                report = node_output.get("installation_report", "")
                print(f"  {report}")

            elif node_name == "coder":
                iteration = node_output.get("iteration_count", "?")
                code = node_output.get("generated_code", "")
                print(f"  Iteration : {iteration}")
                print(f"  Lignes de code : {code.count(chr(10))}")
                print("\n  Apercu (20 premieres lignes) :")
                preview = "\n".join(code.splitlines()[:20])
                print(textwrap.indent(preview, "    "))

            elif node_name == "reviewer":
                msgs = node_output.get("messages", [])
                feedback = node_output.get("feedback", "")
                if msgs:
                    content = msgs[-1].content if hasattr(msgs[-1], "content") else str(msgs[-1])
                    print(f"  Revue :\n{textwrap.indent(content[:600], '    ')}")
                if feedback:
                    print(f"\n  Feedback envoye au coder :\n{textwrap.indent(feedback, '    ')}")
                else:
                    print("\n  Code valide par le reviewer !")

            final_state.update(node_output)

    # Resultat final
    _print_separator("RESULTAT FINAL")

    final_code: str = final_state.get("generated_code", "")
    total_iterations: int = final_state.get("iteration_count", 0)

    if not final_code:
        logger.error("Aucun code genere - verifiez les logs.")
        raise SystemExit(1)

    output_file = _save_output(final_code)

    # Liste les versions archivées
    out_dir = output_file.parent
    versions = sorted(out_dir.glob("app_*.py"), reverse=True)

    print(f"\n  Code Streamlit genere en {total_iterations} iteration(s)")
    print(f"  Derniere version  : {output_file.resolve()}")
    print(f"  Taille            : {output_file.stat().st_size} octets")
    if versions:
        print(f"  Versions archivees ({len(versions)}) :")
        for v in versions[:5]:
            print(f"    - {v.name}")
    print(f"\n  Lancez l'app   : streamlit run {output_file}")
    print(f"  Changer le theme : editer client_config.yaml -> refresh navigateur\n")

    _print_separator("CODE COMPLET GENERE")
    print(final_code)


if __name__ == "__main__":
    main()
