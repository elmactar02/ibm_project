"""
═══════════════════════════════════════════════════════════════════════════════
state/schema.py — Contrat de données partagé entre tous les agents
═══════════════════════════════════════════════════════════════════════════════

FLUX SELON LE SCHÉMA DE L'ÉQUIPE
──────────────────────────────────

  [Interface utilisateur]
        │  raw_input (texte libre)
        ▼
  [Architect Agent]
        │  architect_blueprint (JSON central)
        │  → contient TOUT : C4, tech stack, specs, modules, entités
        ▼
  ┌─────────────────────────────────────┐
  │  Developers (lisent architect_blueprint)
  │  ├── dev_database  (Oumeyma) → models, migrations, schemas
  │  ├── dev_backend   (Akram)   → API, routes, logique métier
  │  └── dev_frontend  (Mactar)  → composants UI, pages
  └─────────────────────────────────────┘
        │  generated_files (accumulés par operator.add)
        ▼
  [DevOps]
        │  repo git + CI/CD + push branche dev
        ▼
  [QA]
        │  tests + review + verdict
        ▼
  [Fin ou boucle retour Developer]

RÈGLE OPERATOR.ADD
───────────────────
Les champs annotés Annotated[List, operator.add] s'ACCUMULENT à chaque agent.
Exemple : si dev_database ajoute 5 fichiers et dev_backend en ajoute 8,
generated_files contiendra 13 éléments à la fin.
═══════════════════════════════════════════════════════════════════════════════
"""

from typing import TypedDict, Annotated, List, Optional
from langchain_core.messages import BaseMessage
import operator


class AgentState(TypedDict):

    # ══════════════════════════════════════════════════════
    # ENTRÉE UTILISATEUR
    # Rempli par l'interface (Streamlit / API / CLI)
    # ══════════════════════════════════════════════════════
    raw_input:    str            # texte brut saisi par l'utilisateur
    project_name: str            # nom du projet (ex: "todo-app")
    input_images: Optional[List[str]]  # images base64 (maquettes, croquis)

    # ══════════════════════════════════════════════════════
    # PHASE 1 — ARCHITECT
    # Produit UN SEUL objet JSON central : architect_blueprint
    # Tous les autres agents lisent ce JSON pour travailler
    # ══════════════════════════════════════════════════════

    # Le JSON central produit par l'Architect
    # Structure : voir ArchitectBlueprint ci-dessous
    architect_blueprint: Optional[dict]

    # Artefacts C4 sauvegardés sur disque
    c4_context:    Optional[str]   # Mermaid C4Context
    c4_containers: Optional[str]   # Mermaid C4Container
    c4_components: Optional[str]   # Mermaid C4Component

    # Décisions technologiques
    tech_stack: Optional[dict]     # {frontend, backend, database, auth, ...}

    # Document d'architecture Markdown
    architecture_doc: Optional[str]

    # ══════════════════════════════════════════════════════
    # PHASE 2 — DEVOPS
    # Crée le repo git et la pipeline CI/CD
    # S'exécute AVANT les developers pour que le repo existe
    # ══════════════════════════════════════════════════════
    repo_path:   Optional[str]   # chemin local (ex: ./output/todo-app)
    repo_url:    Optional[str]   # URL GitHub si push activé
    cicd_config: Optional[str]   # contenu du ci.yml généré

    # ══════════════════════════════════════════════════════
    # PHASE 3 — DEVELOPERS (Oumeyma, Akram, Mactar)
    # Chaque developer lit architect_blueprint et génère ses fichiers
    # Les listes s'ACCUMULENT grâce à operator.add
    # ══════════════════════════════════════════════════════

    # Fichiers générés par dev_database (Oumeyma)
    # Ex: models.py, database.py, schemas.py, migrations/
    database_files: Annotated[List[dict], operator.add]
    db_output:       dict
    db_schema:       dict  # Schéma de la base de données (tables, colonnes, FKs)
    db_project_name: str  # Nom du projet pour l'API de la DB
    
    # Fichiers générés par dev_backend (Akram)
    # Ex: routers/tasks.py, routers/auth.py, main.py, auth.py
    backend_files: Annotated[List[dict], operator.add]

    # Fichiers générés par dev_frontend (Mactar)
    # Ex: frontend/components/, frontend/pages/, styles/
    frontend_files: Annotated[List[dict], operator.add]

    frontend_output: dict

    # Tous les fichiers réunis (database + backend + frontend)
    # Rempli par l'étape de merge avant DevOps/QA
    generated_files: Annotated[List[dict], operator.add]

    # Fichiers de tests générés par les developers
    test_files: Annotated[List[dict], operator.add]

    # ══════════════════════════════════════════════════════
    # PHASE 4 — QA
    # Valide le code généré, lance les tests, fait une review LLM
    # ══════════════════════════════════════════════════════
    qa_report:        Optional[dict]  # {verdict, score, issues, suggestions}
    validation_passed: bool           # True si QA valide
    qa_attempts:       int            # nombre de tentatives (max 2)

    # ══════════════════════════════════════════════════════
    # CONTRÔLE DU PIPELINE (LangGraph)
    # ══════════════════════════════════════════════════════
    current_phase: str               # agent en cours d'exécution
    error:         Optional[str]     # message d'erreur si échec
    reasoning_trace: Annotated[List[str], operator.add]  # log de tous les agents
    messages:        Annotated[List[BaseMessage], operator.add]


# ═══════════════════════════════════════════════════════════════════════════════
# STRUCTURE DU JSON CENTRAL : architect_blueprint
# ═══════════════════════════════════════════════════════════════════════════════
# Ce dict est produit par l'Architect et lu par TOUS les agents suivants.
# Il remplace les functional_requirements de l'ancienne version.
#
# {
#   "project": {
#     "name": "todo-app",
#     "description": "Application de gestion de tâches",
#     "complexity": "medium"
#   },
#   "modules": ["auth", "tasks", "users", "comments"],
#   "user_journeys": [
#     {"name": "Créer une tâche", "steps": ["login", "dashboard", "create form", "submit"]}
#   ],
#   "entities": [
#     {"name": "User",    "fields": ["id", "email", "password", "created_at"]},
#     {"name": "Task",    "fields": ["id", "title", "description", "status", "priority", "user_id"]},
#     {"name": "Comment", "fields": ["id", "content", "task_id", "user_id", "created_at"]}
#   ],
#   "api_endpoints": [
#     {"method": "POST", "path": "/auth/login",   "description": "Authentification JWT"},
#     {"method": "POST", "path": "/auth/register","description": "Inscription"},
#     {"method": "GET",  "path": "/tasks",        "description": "Liste des tâches"},
#     {"method": "POST", "path": "/tasks",        "description": "Créer une tâche"},
#     {"method": "PUT",  "path": "/tasks/{id}",   "description": "Modifier une tâche"},
#     {"method": "DELETE","path": "/tasks/{id}",  "description": "Supprimer une tâche"}
#   ],
#   "tech_stack": {
#     "frontend":       "React 18 + Vite + TailwindCSS",
#     "backend":        "FastAPI + Python 3.11",
#     "database":       "PostgreSQL 16 + SQLAlchemy 2.0",
#     "auth":           "JWT avec python-jose + passlib bcrypt",
#     "cache":          "none",
#     "message_broker": "none",
#     "container":      "Docker + Docker Compose",
#     "cloud":          "local"
#   },
#   "c4": {
#     "context":    "<mermaid C4Context string>",
#     "containers": "<mermaid C4Container string>",
#     "components": "<mermaid C4Component string>"
#   },
#   "architecture_doc": "<markdown string>",
#   "dev_instructions": {
#     "database": "Instructions spécifiques pour Oumeyma : fichiers à créer, modèles, relations",
#     "backend":  "Instructions spécifiques pour Akram : endpoints, auth, logique métier",
#     "frontend": "Instructions spécifiques pour Mactar : composants, pages, routing"
#   }
# }
# ═══════════════════════════════════════════════════════════════════════════════