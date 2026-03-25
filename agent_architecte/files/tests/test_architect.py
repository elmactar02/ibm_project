"""
test_architect.py — Test isolé de l'Architect Agent (architect)
═══════════════════════════════════════════════════════

Lance UNIQUEMENT l'Architect, sans LangGraph, sans les autres agents.

USAGE
──────
    python test_architect.py
    python test_architect.py --spec "Mon besoin personnalisé"
    python test_architect.py --name "mon-projet"

SORTIE
───────
    • Affichage coloré dans le terminal (logs de architect)
    • output/{project_name}/docs/architect_blueprint.json
    • output/{project_name}/docs/architecture/context.md
    • output/{project_name}/docs/architecture/containers.md
    • output/{project_name}/docs/architecture/components.md
    • output/{project_name}/docs/ARCHITECTURE.md
    • output/{project_name}/docs/tech_stack.json
"""

import os
import json
import argparse
from dotenv import load_dotenv

load_dotenv()

# ── Vérification de la clé API avant de démarrer ─────────────────────────────
api_key = os.getenv("MISTRAL_API_KEY", "")
if not api_key:
    print("\n✗ MISTRAL_API_KEY manquante dans .env")
    print("  Ajoute : MISTRAL_API_KEY=ta_clé dans le fichier .env")
    exit(1)

print(f"✓ Clé Mistral chargée ({api_key[:8]}…)")

# ── Imports du projet ─────────────────────────────────────────────────────────
from langchain_mistralai import ChatMistralAI
from agents.architect import architect_node

# ── Spécification par défaut ──────────────────────────────────────────────────
DEFAULT_SPEC = """
Construire une application de gestion de tâches (To-Do + suivi de demandes).

Fonctionnalités :
- Inscription et connexion utilisateur avec JWT
- Tableau de bord listant toutes les tâches, filtrable par statut et priorité
- Créer, modifier, supprimer des tâches
- Détail d'une tâche : titre, description, priorité (low/medium/high), date d'échéance, statut
- Assigner des tâches à des utilisateurs enregistrés
- Ajouter des commentaires sur les tâches
- Historique des modifications

Contraintes :
- API REST avec documentation OpenAPI (Swagger)
- SQLite pour le développement, compatible PostgreSQL en production
- Conteneurisé avec Docker + Docker Compose
- Pipeline CI/CD sur GitHub Actions
"""


def run_architect(spec: str, project_name: str):
    """Lance uniquement l'Architect agent (architect) et affiche les résultats."""

    print("\n" + "═" * 60)
    print(f"  TEST ARCHITECT AGENT — architect")
    print(f"  Projet : {project_name}")
    print("═" * 60 + "\n")

    # ── Initialiser le LLM ────────────────────────────────────────────────────
    print("⟳ Initialisation de Mistral…")
    llm = ChatMistralAI(
        model="mistral-large-latest",
        api_key=api_key,
        temperature=0.1,
    )
    print("✓ LLM prêt\n")

    # ── Construire l'état minimal (seulement ce que architect a besoin) ───────────
    state = {
        "raw_input":           spec,
        "project_name":        project_name,
        "input_images":        None,
        "architect_blueprint": None,
        "reasoning_trace":     [],
        "c4_context":          None,
        "c4_containers":       None,
        "c4_components":       None,
        "tech_stack":          None,
        "architecture_doc":    None,
        "repo_path":           f"./output/{project_name}",
        "repo_url":            None,
        "cicd_config":         None,
        "database_files":      [],
        "backend_files":       [],
        "frontend_files":      [],
        "generated_files":     [],
        "test_files":          [],
        "qa_report":           None,
        "validation_passed":   False,
        "qa_attempts":         0,
        "current_phase":       "architect",
        "error":               None,
        "messages":            [],
    }

    # ── Lancer architect ──────────────────────────────────────────────────────────
    print("▶ Lancement de l'Architect Agent (architect)…\n")
    result = architect_node(state, llm)

    # ── Afficher les résultats ────────────────────────────────────────────────
    print("\n" + "═" * 60)
    print("  RÉSULTATS")
    print("═" * 60)

    blueprint = result.get("architect_blueprint", {})

    # Résumé du blueprint
    if blueprint:
        print(f"\n✓ Blueprint JSON généré")
        print(f"  Projet      : {blueprint.get('project', {}).get('name', '?')}")
        print(f"  Complexité  : {blueprint.get('project', {}).get('complexity', '?')}")
        print(f"  Modules     : {blueprint.get('modules', [])}")
        print(f"  Entités     : {[e.get('name') for e in blueprint.get('entities', [])]}")
        print(f"  Endpoints   : {len(blueprint.get('api_endpoints', []))} routes")

        ts = blueprint.get("tech_stack", {})
        if ts:
            print(f"\n  Tech Stack :")
            for k, v in ts.items():
                print(f"    {k:<18} {v}")

        di = blueprint.get("dev_instructions", {})
        if di:
            print(f"\n  Instructions pour les développeurs :")
            for dev, instr in di.items():
                print(f"    [{dev}] {str(instr)[:120]}…")
    else:
        print("\n✗ Blueprint non généré — vérifie les logs ci-dessus")

    # Diagrammes C4
    print(f"\n  Diagrammes C4 :")
    print(f"    Context    : {'✓' if result.get('c4_context')    else '✗'} ({len(result.get('c4_context',''))} chars)")
    print(f"    Containers : {'✓' if result.get('c4_containers') else '✗'} ({len(result.get('c4_containers',''))} chars)")
    print(f"    Components : {'✓' if result.get('c4_components') else '✗'} ({len(result.get('c4_components',''))} chars)")

    # Documentation
    arch_doc = result.get("architecture_doc", "")
    print(f"\n  Architecture doc : {'✓' if arch_doc else '✗'} ({len(arch_doc.split())} mots)")

    # Fichiers sur disque
    output_path = f"./output/{project_name}/docs"
    print(f"\n  Fichiers écrits dans {output_path}/")
    if os.path.exists(output_path):
        for root, _, files in os.walk(output_path):
            for f in files:
                filepath = os.path.join(root, f)
                size = os.path.getsize(filepath)
                rel  = os.path.relpath(filepath, f"./output/{project_name}")
                print(f"    ✓ {rel} ({size} octets)")
    else:
        print(f"    ✗ Dossier non créé")

    # Trace de raisonnement
    print(f"\n  Reasoning trace :")
    for entry in result.get("reasoning_trace", []):
        print(f"    {entry}")

    print("\n" + "═" * 60)
    print("  Test architect terminé")
    print("═" * 60 + "\n")

    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test isolé — Architect Agent (architect)")
    parser.add_argument("--spec", type=str, default=DEFAULT_SPEC, help="Texte du besoin")
    parser.add_argument("--name", type=str, default="todo-app",   help="Nom du projet")
    args = parser.parse_args()

    run_architect(args.spec, args.name)