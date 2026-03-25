"""
═══════════════════════════════════════════════════════════════════════════════
agents/architect.py — Architect Agent  (Manal)
═══════════════════════════════════════════════════════════════════════════════

RÔLE CENTRAL DANS LE PIPELINE
───────────────────────────────
L'Agent ARCHITECT est le PREMIER agent à s'exécuter après la saisie utilisateur.
Elle produit UN SEUL fichier JSON : architect_blueprint.json
Ce fichier est la SOURCE DE VÉRITÉ pour tous les agents suivants.

  [Interface] → raw_input
        │
        ▼
  [Architect — Manal]
        │
        ├── Analyse le besoin
        ├── Identifie les modules, entités, endpoints
        ├── Décide le tech stack
        ├── Génère les 3 diagrammes C4
        ├── Rédige la documentation d'architecture
        └── Produit : architect_blueprint.json ──► tous les agents

AGENTS QUI LISENT architect_blueprint
───────────────────────────────────────
  • dev_database  (Oumeyma) → lit entities, tech_stack.database
  • dev_backend   (Akram)   → lit api_endpoints, entities, tech_stack.backend
  • dev_frontend  (Mactar)  → lit modules, user_journeys, tech_stack.frontend
  • devops                  → lit project.name, tech_stack.container

OUTILS UTILISÉS
───────────────
  • save_c4_diagram(repo_path, diagram_type, content)  → docs/architecture/*.md
  • save_architecture_doc(repo_path, content)           → docs/ARCHITECTURE.md
  • save_tech_stack_json(repo_path, tech_stack)         → docs/tech_stack.json
  • write_file(path, content)                           → docs/architect_blueprint.json

ENTRÉES  (lues depuis AgentState)
──────────────────────────────────
  • raw_input    → texte brut saisi par l'utilisateur
  • project_name → nom du projet (ex: "todo-app")
  • repo_path    → chemin local du repo (ex: "./output/todo-app")

SORTIES  (écrites dans AgentState)
───────────────────────────────────
  • architect_blueprint → JSON central pour tous les agents
  • c4_context / c4_containers / c4_components → diagrammes Mermaid
  • tech_stack          → dict des choix technologiques
  • architecture_doc    → document Markdown
  • reasoning_trace     → log de ce que l'architect a décidé
  • current_phase       → "devops" (prochain agent)
═══════════════════════════════════════════════════════════════════════════════
"""

import json
import os
from langchain_core.prompts import ChatPromptTemplate
from state.schema import AgentState
from tools.diagram_tools import (
    save_c4_diagram,
    save_architecture_doc,
    save_tech_stack_json,
)
from tools.file_tools import write_file
from core.logger import (
    log_phase_start,
    log_agent_thinking,
    log_llm_call,
    log_llm_response,
    log_state_update,
    log_error,
)


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 1 — MARQUEURS DE SECTIONS
# Les marqueurs délimitent les 6 blocs dans la réponse du LLM.
# Ils doivent être IDENTIQUES dans le prompt et dans le code de parsing.
# ═══════════════════════════════════════════════════════════════════════════════

MARKER_CONTEXT    = "---CONTEXT---"
MARKER_CONTAINERS = "---CONTAINERS---"
MARKER_COMPONENTS = "---COMPONENTS---"
MARKER_TECHSTACK  = "---TECHSTACK---"
MARKER_ARCHDOC    = "---ARCHDOC---"
MARKER_BLUEPRINT  = "---BLUEPRINT---"

# Ordre important : utilisé pour parser les sections dans le bon ordre
MARKERS = [
    MARKER_CONTEXT,
    MARKER_CONTAINERS,
    MARKER_COMPONENTS,
    MARKER_TECHSTACK,
    MARKER_ARCHDOC,
    MARKER_BLUEPRINT,
]


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 2 — PROMPT SYSTÈME
# Instruction principale envoyée à Mistral.
# Structure : RÔLE → FORMAT DE RÉPONSE (6 sections) → RÈGLES STRICTES
# ═══════════════════════════════════════════════════════════════════════════════

SYSTEM_PROMPT = """
Tu es un architecte logiciel senior.
Tu reçois un besoin utilisateur en langage naturel et tu produis TOUTE la documentation d'architecture.

Ton output sera utilisé directement par 4 autres agents :
  • Oumeyma (dev base de données) → a besoin des entités, relations, tech stack BDD
  • Akram   (dev backend)         → a besoin des endpoints API, logique métier, auth
  • Mactar  (dev frontend)        → a besoin des modules UI, parcours utilisateurs, composants
  • DevOps                        → a besoin du nom projet, stack, configuration Docker

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
FORMAT DE RÉPONSE — 6 sections obligatoires
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Commence DIRECTEMENT par ---CONTEXT--- sans introduction.

---CONTEXT---
Diagramme C4 Niveau 1 (Mermaid C4Context).
Montre : utilisateurs, système principal, systèmes externes.

  C4Context
    title Contexte — [nom du projet]
    Person(user, "Utilisateur", "description")
    System(api, "Nom système", "description")
    System_Ext(ext, "Système externe", "description")
    Rel(user, api, "Utilise", "HTTPS")

---CONTAINERS---
Diagramme C4 Niveau 2 (Mermaid C4Container).
Montre : tous les services avec leur technologie.

  C4Container
    title Conteneurs — [nom du projet]
    Person(user, "Utilisateur")
    Container(frontend, "Frontend", "React 18", "Interface SPA")
    Container(api, "API Backend", "FastAPI", "Logique métier")
    ContainerDb(db, "Base de données", "PostgreSQL", "Stockage")
    Rel(user, frontend, "Utilise", "HTTPS")
    Rel(frontend, api, "Appelle", "REST/JSON")
    Rel(api, db, "Lit/Écrit", "SQL")

---COMPONENTS---
Diagramme C4 Niveau 3 (Mermaid C4Component).
Montre : les modules internes du backend.

  C4Component
    title Composants — API Backend
    Component(auth, "Auth Router", "FastAPI Router", "login/register/JWT")
    Component(tasks, "Tasks Router", "FastAPI Router", "CRUD tâches")
    Component(db_layer, "Database Layer", "SQLAlchemy", "ORM sessions")
    Rel(auth, db_layer, "Utilise")
    Rel(tasks, db_layer, "Utilise")

---TECHSTACK---
JSON brut (sans backticks, sans commentaires) :

  {{
    "database": "Instructions précises pour Oumeyma : modèles à créer, relations SQLAlchemy, types de champs",
    "backend":  "Instructions précises pour Akram : endpoints à implémenter, auth JWT, structure des routers",
    "frontend": "Instructions précises pour Mactar : composants à créer, pages, routing React"
    "auth":           "approche exacte (ex: JWT avec python-jose + passlib bcrypt)",
    "cache":          "technologie ou none",
    "message_broker": "technologie ou none",
    "container":      "Docker + Docker Compose",
    "cloud":          "local ou plateforme cible"
  }}

---ARCHDOC---
Document Markdown d'architecture (minimum 300 mots) avec :
  ## Vue d'ensemble
  ## Décisions d'architecture
  ## Flux de données
  ## Sécurité
  ## Scalabilité

---BLUEPRINT---
JSON central complet (sans backticks) transmis à tous les agents.
Structure EXACTE à respecter :

  {{
    "project": {{
      "name": "nom-du-projet",
      "description": "description courte",
      "complexity": "low|medium|high"
    }},
    "modules": ["module1", "module2"],
    "user_journeys": [
      {{"name": "Nom du parcours", "steps": ["étape 1", "étape 2"]}}
    ],
    "entities": [
      {{
        "name": "NomEntité",
        "fields": ["id", "champ1", "champ2"],
        "relations": ["relation avec autre entité"]
      }}
    ],
    "api_endpoints": [
      {{
        "method": "GET|POST|PUT|DELETE",
        "path": "/route",
        "description": "action",
        "auth_required": true
      }}
    ],
    "tech_stack": {{
      "frontend": "...", "backend": "...", "database": "...",
      "auth": "...", "cache": "...", "message_broker": "...",
      "container": "...", "cloud": "..."
    }},
    "dev_instructions": {{
      "database": "Instructions précises pour Oumeyma : modèles à créer, relations SQLAlchemy, types de champs",
      "backend":  "Instructions précises pour Akram : endpoints à implémenter, auth JWT, structure des routers",
      "frontend": "Instructions précises pour Mactar : composants à créer, pages, routing React"
    }},
    "constraints": ["contrainte technique 1", "contrainte 2"],
    "estimated_files": {{
      "database": 3,
      "backend":  8,
      "frontend": 10
    }}
  }}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
RÈGLES STRICTES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. Syntaxe Mermaid C4 valide uniquement (C4Context, C4Container, C4Component).
2. Chaque conteneur et composant DOIT avoir une technologie entre parenthèses.
3. JSON ---TECHSTACK--- et ---BLUEPRINT--- : parseable, sans backticks, sans commentaires, sans virgule finale.
4. ---BLUEPRINT--- doit contenir des dev_instructions DÉTAILLÉES pour chaque développeur.
5. ---ARCHDOC--- minimum 300 mots en Markdown structuré.
6. Commence ta réponse DIRECTEMENT par ---CONTEXT--- sans texte introductif.
"""


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 3 — PROMPT UTILISATEUR
# Envoie le besoin brut + le nom du projet au LLM.
# ═══════════════════════════════════════════════════════════════════════════════

ARCHITECT_PROMPT = ChatPromptTemplate.from_messages([
    ("system", SYSTEM_PROMPT),
    ("human", """
Besoin utilisateur :
\"\"\"{raw_input}\"\"\"

Nom du projet : {project_name}

Analyse ce besoin et produis les 6 sections en commençant par ---CONTEXT---.
"""),
])


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 4 — FONCTIONS UTILITAIRES DE PARSING
# ═══════════════════════════════════════════════════════════════════════════════

def _parse_sections(raw_text: str) -> dict[str, str]:
    """
    Découpe la réponse brute du LLM en sections selon les marqueurs.

    Exemple :
      "---CONTEXT---\nC4Context...\n---CONTAINERS---\nC4Container..."
      → {"---CONTEXT---": "C4Context...", "---CONTAINERS---": "C4Container..."}

    Les sections absentes ne sont pas incluses dans le dict retourné.
    """
    sections: dict[str, str] = {}

    for i, marker in enumerate(MARKERS):
        marker_pos = raw_text.find(marker)
        if marker_pos == -1:
            continue  # section manquante, gérée en aval

        content_start = marker_pos + len(marker)

        # Le contenu se termine au début du marqueur suivant
        content_end = len(raw_text)
        for next_marker in MARKERS[i + 1:]:
            next_pos = raw_text.find(next_marker, content_start)
            if next_pos != -1:
                content_end = next_pos
                break

        sections[marker] = raw_text[content_start:content_end].strip()

    return sections


def _parse_json_section(raw: str) -> dict:
    """
    Parse un bloc JSON en nettoyant les artefacts LLM courants :
    backticks ```json, backticks simples ```, espaces parasites.

    Lève json.JSONDecodeError si le JSON est invalide (géré dans architect_node).
    """
    cleaned = (
        raw
        .replace("```json", "")
        .replace("```", "")
        .strip()
    )
    return json.loads(cleaned)


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 5 — NODE PRINCIPAL (appelé par LangGraph ou directement par test_architect.py)
# ═══════════════════════════════════════════════════════════════════════════════

def architect_node(state: AgentState, llm) -> dict:
    """
    Node LangGraph de l'Architect Agent.

    5 étapes dans l'ordre :
      1. Lire les inputs depuis l'AgentState
      2. Appeler le LLM avec le prompt
      3. Parser les 6 sections de la réponse
      4. Sauvegarder les artefacts sur disque via les outils
      5. Retourner les outputs vers l'AgentState
    """

    # ── Étape 1 : Lire les inputs ────────────────────────────────────────────
    log_phase_start("architect", "Analyse du besoin et génération du blueprint central")

    raw_input    = state.get("raw_input", "")
    project_name = state.get("project_name", "app")
    repo_path    = state.get("repo_path") or f"./output/{project_name}"

    log_agent_thinking(
        "architect",
        f"Projet : '{project_name}'\n"
        f"Besoin reçu ({len(raw_input)} chars) : {raw_input[:200]}…\n"
        f"Repo cible : {repo_path}\n"
        "Je vais produire : C4 + tech stack + blueprint.json pour Oumeyma, Akram et Mactar.",
    )

    # ── Étape 2 : Appel LLM ──────────────────────────────────────────────────
    log_llm_call("architect", f"Envoi du besoin à Mistral : {raw_input[:120]}…")

    llm_response = (ARCHITECT_PROMPT | llm).invoke({
        "raw_input":    raw_input,
        "project_name": project_name,
    })

    log_llm_response("architect", llm_response.content[:300])

    # ── Étape 3 : Parser les 6 sections ─────────────────────────────────────
    sections = _parse_sections(llm_response.content)

    # Tech stack JSON
    tech_stack: dict = {}
    try:
        tech_stack = _parse_json_section(sections.get(MARKER_TECHSTACK, "{}"))
        log_agent_thinking(
            "architect",
            f"Tech stack décidé :\n{json.dumps(tech_stack, indent=2, ensure_ascii=False)}",
        )
    except (json.JSONDecodeError, ValueError) as e:
        log_error("architect", f"Tech stack JSON invalide : {e}")

    # Blueprint JSON central
    blueprint: dict = {}
    try:
        blueprint = _parse_json_section(sections.get(MARKER_BLUEPRINT, "{}"))
        # Injecter le tech stack si absent du blueprint
        if "tech_stack" not in blueprint and tech_stack:
            blueprint["tech_stack"] = tech_stack
        log_agent_thinking(
            "architect",
            f"Blueprint généré :\n"
            f"  Modules   : {blueprint.get('modules', [])}\n"
            f"  Entités   : {[e.get('name') for e in blueprint.get('entities', [])]}\n"
            f"  Endpoints : {len(blueprint.get('api_endpoints', []))} routes\n"
            f"  Instructions database : {str(blueprint.get('dev_instructions', {}).get('database', ''))[:100]}\n"
            f"  Instructions backend  : {str(blueprint.get('dev_instructions', {}).get('backend', ''))[:100]}\n"
            f"  Instructions frontend : {str(blueprint.get('dev_instructions', {}).get('frontend', ''))[:100]}",
        )
    except (json.JSONDecodeError, ValueError) as e:
        log_error("architect", f"Blueprint JSON invalide : {e} — construction d'un blueprint minimal")
        blueprint = {
            "project": {"name": project_name, "description": raw_input[:100], "complexity": "medium"},
            "modules": [], "user_journeys": [], "entities": [], "api_endpoints": [],
            "tech_stack": tech_stack,
            "dev_instructions": {"database": "", "backend": "", "frontend": ""},
            "constraints": [],
            "estimated_files": {"database": 3, "backend": 8, "frontend": 10},
        }

    arch_doc = sections.get(MARKER_ARCHDOC, "")

    # ── Étape 4 : Sauvegarder les artefacts sur disque ───────────────────────
    log_agent_thinking("architect", "Sauvegarde des diagrammes C4 et de la documentation…")

    # 4a. Les 3 diagrammes C4
    for marker, diagram_type, label in [
        (MARKER_CONTEXT,    "context",    "Context niveau 1"),
        (MARKER_CONTAINERS, "containers", "Containers niveau 2"),
        (MARKER_COMPONENTS, "components", "Components niveau 3"),
    ]:
        content = sections.get(marker, "")
        if content:
            save_c4_diagram.invoke({
                "repo_path":    repo_path,
                "diagram_type": diagram_type,
                "content":      content,
            })
        else:
            log_error("architect", f"Section manquante : {label} ({marker})")

    # 4b. Document d'architecture Markdown
    if arch_doc:
        save_architecture_doc.invoke({"repo_path": repo_path, "content": arch_doc})
    else:
        log_error("architect", "Section ARCHDOC manquante.")

    # 4c. Tech stack JSON
    if tech_stack:
        save_tech_stack_json.invoke({"repo_path": repo_path, "tech_stack": tech_stack})

    # 4d. Blueprint JSON central — le fichier le plus important
    blueprint_path = os.path.join(repo_path, "docs", "architect_blueprint.json")
    write_file.invoke({
        "path":    blueprint_path,
        "content": json.dumps(blueprint, indent=2, ensure_ascii=False),
    })
    log_agent_thinking(
        "architect",
        f"architect_blueprint.json écrit → {blueprint_path}\n"
        "Ce fichier sera lu par : Oumeyma (BDD), Akram (Backend), Mactar (Frontend), DevOps.",
    )

    # ── Étape 5 : Retourner les outputs vers l'AgentState ────────────────────
    log_state_update(
        "architect",
        ["architect_blueprint", "c4_context", "c4_containers", "c4_components",
         "tech_stack", "architecture_doc", "reasoning_trace", "current_phase"],
    )

    return {
        # JSON central — source de vérité pour tous les agents suivants
        "architect_blueprint": blueprint,

        # Diagrammes C4 individuels (stockés aussi dans l'état)
        "c4_context":       sections.get(MARKER_CONTEXT,    ""),
        "c4_containers":    sections.get(MARKER_CONTAINERS, ""),
        "c4_components":    sections.get(MARKER_COMPONENTS, ""),

        # Tech stack et documentation
        "tech_stack":       tech_stack,
        "architecture_doc": arch_doc,

        # Trace de raisonnement accumulée par tous les agents
        "reasoning_trace": [
            f"[ARCHITECT] Blueprint généré pour '{project_name}'. "
            f"Modules : {blueprint.get('modules', [])} | "
            f"Entités : {[e.get('name') for e in blueprint.get('entities', [])]} | "
            f"Stack : {tech_stack.get('backend','?')} + "
            f"{tech_stack.get('frontend','?')} + "
            f"{tech_stack.get('database','?')}"
        ],

        # Prochain agent à exécuter : DevOps crée le repo avant les developers
        "current_phase": "frontend_adapter",
    }