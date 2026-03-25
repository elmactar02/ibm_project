"""
agent.py
--------
Contient les trois nœuds du graphe LangGraph :
  - analyzer  : identifie les composants UI + packages requis
  - coder     : génère le code Streamlit complet (thème client injecté)
  - reviewer  : auto-critique et retour structuré vers le coder

LLM backend : Qwen 3 32B via Groq Cloud (inférence ultra-rapide).
Clé API gratuite sur https://console.groq.com — variable d'env : GROQ_API_KEY
"""

from __future__ import annotations

import re
import logging
from typing import Any

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_groq import ChatGroq

from state import FrontendState
from theme_loader import build_theme_context_for_prompt, build_streamlit_theme_snippet

# ---------------------------------------------------------------------------
# Configuration du logger
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  [%(levelname)s]  %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Initialisation du LLM (Qwen 3 32B — Groq Cloud)
# ---------------------------------------------------------------------------
_llm = ChatGroq(
    model="qwen/qwen3-32b",
    temperature=0.2,
    max_tokens=8192,
    # La clé est lue automatiquement depuis $GROQ_API_KEY
)

# ---------------------------------------------------------------------------
# Constantes
# ---------------------------------------------------------------------------
MAX_ITERATIONS: int = 3


# ===========================================================================
# Nœud 1 : ANALYZER
# ===========================================================================

_ANALYZER_SYSTEM = SystemMessage(content="""\
Tu es un architecte frontend senior expert en Streamlit et en design de systèmes.
Tu analyses une documentation métier et des spécifications d'API backend.

Ta tâche : Produire un PLAN UI DÉTAILLÉ basé sur les SPÉCIFICATIONS BACKEND RÉELLES.

Produis une réponse en DEUX parties séparées par le marqueur "---PACKAGES---" :

PARTIE 1 — Plan détaillé des composants UI Streamlit :

Pour CHAQUE MODULE/PAGE mentionné dans les specs :
  1. Nom du module
  2. Objectif principal (déduit des endpoints disponibles)
  3. Endpoints backend disponibles :
     Extrais TOUS les endpoints pertinents des SPÉCIFICATIONS BACKEND (BASE_URL, ENDPOINTS, etc.)
     Exemple de lecture des specs :
       Si SPECS contient "GET /users" → affichage liste
       Si SPECS contient "POST /users" → formulaire création
       Si SPECS contient "PATCH /users/{id}" → formulaire modification
  4. Composants Streamlit à utiliser (adaptés aux endpoints) :
     - Affichage : st.dataframe, st.table, st.columns, st.metric (basé sur GET endpoints)
     - Saisie : st.form, st.text_input, st.selectbox, st.number_input (basé sur POST/PATCH endpoints)
     - Actions : st.button, st.form_submit_button (basé sur DELETE/PATCH endpoints)
  5. Gestion d'erreurs : try/except + st.error()

TRÈS IMPORTANT :
  - Utilise UNIQUEMENT les endpoints mentionnés dans les SPÉCIFICATIONS BACKEND
  - Pas d'invention d'endpoints qui n'existaient pas dans les specs
  - Chaque endpoint doit être appelé pour de vrai (pas de placeholder)
  - Les données retournées doivent être affichées réellement

---PACKAGES---

PARTIE 2 — Packages Python requis :
Liste UNIQUEMENT les packages pip nécessaires au-delà de streamlit et requests.
Un package par ligne, format pip (ex: pandas>=2.0, plotly).
Si aucun package supplémentaire n'est requis, écris : aucun
""")


def analyzer(state: FrontendState) -> dict[str, Any]:
    """
    Analyse les specs backend + doc métier.
    Produit un plan UI et détecte les packages Python requis.
    """
    logger.info("▶  [analyzer] Début de l'analyse des specs")

    user_prompt = HumanMessage(content=f"""\
=== DOCUMENTATION MÉTIER ===
{state["frontend_doc"]}

=== SPÉCIFICATIONS API BACKEND ===
{state["backend_specs"]}

Analyse ces deux documents et produis le plan de composants UI + liste de packages.
""")

    response: AIMessage = _llm.invoke([_ANALYZER_SYSTEM, user_prompt])
    analysis_text: str = response.content

    ui_plan, packages = _split_analysis(analysis_text)
    logger.info(
        "✔  [analyzer] Analyse terminée — %d car., %d packages détectés",
        len(ui_plan), len(packages),
    )

    return {
        "messages": [
            user_prompt,
            AIMessage(content=ui_plan, name="analyzer"),
        ],
        "required_packages": packages,
    }


# ===========================================================================
# Nœud 2 : CODER
# ===========================================================================

_CODER_SYSTEM = SystemMessage(content="""\
Tu es un développeur frontend expert en Streamlit (Python).
Ta mission est de générer un fichier `app.py` Streamlit complet, prêt à l'emploi.

Règles IMPÉRATIVES — toute violation entraîne un refus du reviewer :

1. COMMENCE par le snippet d'entête fourni EXACTEMENT tel quel (3 lignes).
   Ne le modifie pas, ne le duplique pas.

2. ❌ INTERDIT ABSOLU — ces éléments NE DOIVENT PAS apparaître dans ton code :
   - Tout st.text_input pour "token", "Bearer", "mot de passe", "password", "identifiant"
   - Tout st.button ou st.form_submit_button libellé "Connexion", "Login", "Se connecter"
   - Tout appel requests vers /login, /auth, /token ou tout endpoint d'authentification
   - Toute fonction nommée login, authenticate, show_login, render_login, connect, etc.
   - Tout bloc conditionnel `if not authenticated` ou `if not logged_in`
   - Tout affichage lié à l'auth dans la sidebar (token input, bouton connexion, etc.)
   L'authentification est ENTIÈREMENT et DÉFINITIVEMENT gérée par le snippet d'entête.
   Elle est déjà résolue avant la première ligne de ton code — n'y touche pas.

3. Utilise auth_headers() sur TOUS les appels requests :
   requests.get(url, headers=auth_headers(), ...)

4. Chaque st.button / st.form doit être mappé à un endpoint API backend
   (méthode HTTP + URL exactes du spec). Exclure /login, /auth, /token.

5. Gère les erreurs de connexion (requests.exceptions.ConnectionError) avec un
   st.error() explicite : "Backend non disponible — vérifiez que le serveur tourne."
   Ne laisse jamais une exception remonter brute à l'écran.

6. Utilise st.session_state pour conserver les données entre les reruns.

7. Organise le code en fonctions Python bien nommées.

8. ⚠️  NAVIGATION ET MODULES — TRÈS IMPORTANT :
   Les noms de modules réels du backend sont listés dans MODULES_INTERNES (ex: dashboard, tasks, auth).
   
   RÈGLE : 
   - Initialise TOUJOURS st.session_state.current_page avec le premier module (ex: "dashboard")
   - Les clés internes (st.session_state.current_page) DOIVENT être les noms réels des modules
   - Tu peux créer des labels français pour l'affichage, MAIS ils doivent mapper correctement
   - JAMAIS d'erreur ".index() value not found" — valide toujours avant d'appeler .index()
   
   Exemple (pour modules: dashboard, tasks, create_task):
   ```python
   if "current_page" not in st.session_state:
       st.session_state.current_page = "dashboard"  # ← Clé interne réelle
   
   pages = [("Tableau de bord", "dashboard"), ("Mes tâches", "tasks"), ("Créer", "create_task")]
   labels = [p[0] for p in pages]
   values = [p[1] for p in pages]
   
   current_idx = values.index(st.session_state.current_page) if st.session_state.current_page in values else 0
   selected = st.sidebar.radio("Navigation", labels, index=current_idx)
   st.session_state.current_page = values[labels.index(selected)]
   ```

9. ⚠️  CODE FONCTIONNEL OBLIGATOIRE — PAS DE PLACEHOLDERS :
   ❌ INTERDIT : st.info("...à implémenter")
   ❌ INTERDIT : st.warning("Fonctionnalité non implémentée")
   ❌ INTERDIT : des sections vides avec juste du texte
   ❌ INTERDIT : utiliser _cfg.base_url (vague et peu fiable)
   
   ✅ OBLIGATOIRE : Utilise les endpoints réels des SPÉCIFICATIONS BACKEND :
   - Lis le plan UI fourni par l'analyzer (il liste tous les endpoints à utiliser)
   - Lis les SPÉCIFICATIONS BACKEND (BASE_URL, ENDPOINTS, MODÈLES, etc.)
   - Pour TOUS les appels requests, utilise BASE_URL = "http://localhost:8000" (hardcodé)
   - Exemple : response = requests.get("http://localhost:8000/tasks", headers=auth_headers())
   - Pour chaque endpoint du plan : appelle-le réellement et affiche les données
   - GET : affiche avec st.dataframe() / st.table() / st.write()
   - POST/PATCH : crée/modifie via form, affiche la réponse
   - DELETE : supprime avec confirmation, affiche le succès
   
   Chaque fonction doit :
   - Appeler l'endpoint réel avec URL = "http://localhost:8000" + path
   - Utiliser auth_headers() pour tous les appels
   - Gérer les erreurs (try/except + st.error())
   - Afficher les données retournées (pas de placeholder)
   - Gérer les cas vides gracieusement

10. Retourne UNIQUEMENT le bloc de code Python encadré de ```python ... ```.
   Aucune explication en dehors du bloc.
""")


def coder(state: FrontendState) -> dict[str, Any]:
    """
    Génère le code Streamlit complet.
    Injecte le thème client et prend en compte le feedback éventuel.
    """
    iteration: int = state.get("iteration_count", 0) + 1
    logger.info("▶  [coder] Génération du code — itération %d", iteration)

    analysis_msg = _last_message_by(state["messages"], name="analyzer")

    # ── Thème client ─────────────────────────────────────────────────────────
    theme_cfg: dict = state.get("theme_config", {})
    theme_context = build_theme_context_for_prompt(theme_cfg)
    # Le snippet généré importe theme_runtime qui relit client_config.yaml live
    theme_snippet = build_streamlit_theme_snippet(theme_cfg)

    # Log dev_mode status
    dev = theme_cfg.get("dev_mode", {})
    if dev.get("enabled"):
        logger.info(
            "[coder] dev_mode ACTIF — strategie : %s",
            dev.get("strategy", "mock_login"),
        )

    # ── Rapport d'installation ───────────────────────────────────────────────
    install_report = state.get("installation_report", "")
    install_section = (
        f"\n=== RAPPORT D'INSTALLATION DES PACKAGES ===\n{install_report}\n"
        if install_report and install_report != "Aucune installation requise."
        else ""
    )

    # ── Feedback reviewer ────────────────────────────────────────────────────
    feedback_section = ""
    if state.get("feedback"):
        feedback_section = f"""
=== FEEDBACK DU REVIEWER (itération précédente) ===
{state["feedback"]}

Corrige TOUS les problèmes identifiés ci-dessus.
"""

    # ── Extraction explicite des modules réels ─────────────────────────────────
    # Extraire les modules depuis le frontend_doc au format "MODULES_INTERNES: dash, tasks, auth"
    frontend_doc = state["frontend_doc"]
    modules_str = ""
    if "MODULES_INTERNES:" in frontend_doc:
        # Format: "... | MODULES_INTERNES: dashboard, tasks, auth | ..."
        parts = frontend_doc.split("|")
        for part in parts:
            if "MODULES_INTERNES:" in part:
                modules_str = part.replace("MODULES_INTERNES:", "").strip()
                break
    
    modules_list = [m.strip() for m in modules_str.split(",") if m.strip()] if modules_str else []
    
    modules_warning = ""
    if modules_list:
        modules_warning = f"\n⚠️  MODULES RÉELS À UTILISER COMME CLÉS INTERNES : {modules_list}\n"
        logger.info("[coder] Modules détectés : %s", modules_list)

    user_prompt = HumanMessage(content=f"""\
=== PLAN DE COMPOSANTS UI ===
{analysis_msg}

=== SPÉCIFICATIONS API BACKEND ===
{state["backend_specs"]}

=== DOCUMENTATION MÉTIER ===
{state["frontend_doc"]}

{theme_context}

=== SNIPPET D'ENTÊTE À COLLER TEL QUEL EN DÉBUT DE FICHIER ===
{theme_snippet}

Ce snippet (3 lignes) gère automatiquement :
  - st.set_page_config (titre, icône, layout)
  - Le CSS de la charte graphique (relu depuis client_config.yaml à chaque refresh)
  - L'authentification mock/bypass/prod selon dev_mode.strategy
  - La fonction auth_headers() utilisable partout

RÈGLE : après ce snippet, le reste du code métier peut démarrer directement.
Chaque appel requests doit utiliser : requests.get(url, headers=auth_headers())
{modules_warning}{install_section}{feedback_section}
Génère maintenant le code Streamlit complet.
""")

    response: AIMessage = _llm.invoke([_CODER_SYSTEM, user_prompt])
    generated_code = _extract_code_block(response.content)

    logger.info(
        "✔  [coder] Code généré — %d lignes (itération %d)",
        generated_code.count("\n"), iteration,
    )

    return {
        "messages": [AIMessage(content=generated_code, name="coder")],
        "generated_code": generated_code,
        "iteration_count": iteration,
        "feedback": "",
    }


# ===========================================================================
# Nœud 3 : REVIEWER
# ===========================================================================

_REVIEWER_SYSTEM = SystemMessage(content="""\
Tu es un reviewer. Évalue le code Streamlit en JSON strictement.

[CRITÈRES]
1. PAS DE "à implémenter" / "non implémenté" / code vide
2. API CALLS: requests.get/post/put/delete avec auth_headers()
3. AFFICHAGE: st.dataframe(), st.write(), st.metric() etc.
4. ERREURS: try/except avec st.error()
5. NAVIGATION: modules internes (pas labels hardcodés)
6. AUTH: Pas de login/password inputs (géré par theme_runtime)
7. IMPORTS: Snippet theme_runtime au démarrage
8. SYNTAX: Code valide Python/Streamlit

Retourne JSON (pas Markdown):
{"status": "OK"|"NEEDS_FIX", "issue": "...", "suggestion": "..."}
""")


def reviewer(state: FrontendState) -> dict[str, Any]:
    """
    Vérifie la cohérence entre le code généré, les specs backend et la charte graphique.
    """
    logger.info("▶  [reviewer] Revue du code — itération %d", state.get("iteration_count", 1))

    user_prompt = HumanMessage(content=f"""\
=== CODE STREAMLIT GÉNÉRÉ ===
```python
{state["generated_code"]}
```

=== SPÉCIFICATIONS API BACKEND ===
{state["backend_specs"]}

=== DOCUMENTATION MÉTIER ===
{state["frontend_doc"]}

Effectue ta revue et retourne le JSON de résultat.
""")

    response: AIMessage = _llm.invoke([_REVIEWER_SYSTEM, user_prompt])
    status, feedback_text = _parse_review(response.content)

    logger.info("✔  [reviewer] Statut : %s", status)
    if feedback_text:
        logger.warning("   Issues :\n%s", feedback_text)

    return {
        "messages": [AIMessage(content=response.content, name="reviewer")],
        "feedback": feedback_text if status == "NEEDS_FIX" else "",
    }


# ===========================================================================
# Helpers
# ===========================================================================

def _split_analysis(text: str) -> tuple[str, list[str]]:
    """
    Sépare la réponse de l'analyzer en (plan_ui, liste_packages).
    Le marqueur est '---PACKAGES---'.
    Filtre les lignes qui ne sont pas des noms de packages (headers, texte vide, etc.).
    """
    marker = "---PACKAGES---"
    if marker in text:
        ui_part, pkg_part = text.split(marker, 1)
    else:
        ui_part, pkg_part = text, ""

    packages: list[str] = []
    for line in pkg_part.splitlines():
        line = line.strip().lstrip("-• ").strip()
        
        # Filtrer les lignes vides
        if not line:
            continue
        
        # Filtrer les mots-clés génériques
        if line.lower() in ("aucun", "none", "", "aucune"):
            continue
        
        # Filtrer les en-têtes/sections (contiennent "PARTIE", ":", etc.)
        if any(keyword in line.upper() for keyword in ["PARTIE", "PACKAGES", "PYTHON", "REQUIS"]):
            continue
        if line.endswith(":") or "---" in line:
            continue
        
        # Filtrer le texte explicatif (trop long, contient espaces + autres caractères)
        # Un vrai nom de package ressemble à: "pandas>=2.0" ou "requests" ou "python-jose[crypto]>=1.0"
        # Garder seulement si c'est un format de package valide
        if len(line) > 100:  # Descriptions sont souvent longues
            continue
        
        # Vérifier que ça ressemble à un package (contient alphanumérique, tiret, crochet, point, opérateur de version)
        if re.match(r'^[a-zA-Z0-9\-._\[\]><=~!]+', line):
            packages.append(line)

    return ui_part.strip(), packages


def _extract_code_block(text: str) -> str:
    """Extrait le contenu entre ```python ... ```."""
    match = re.search(r"```python\s*(.*?)```", text, re.DOTALL)
    if match:
        return match.group(1).strip()
    logger.warning("[coder] Aucun bloc ```python``` trouvé — texte brut utilisé")
    return text.strip()


def _parse_review(review_text: str) -> tuple[str, str]:
    """Parse le JSON du reviewer → (status, feedback_formatté)."""
    import json

    # Nettoie les backticks résiduels et le thinking tag de Qwen
    clean = review_text.strip()
    clean = re.sub(r"<think>.*?</think>", "", clean, flags=re.DOTALL).strip()
    clean = clean.removeprefix("```json").removesuffix("```").strip()

    # Tente d'extraire un bloc JSON si du texte l'entoure
    json_match = re.search(r"\{.*\}", clean, re.DOTALL)
    if json_match:
        clean = json_match.group(0)

    try:
        data: dict = json.loads(clean)
        status: str = data.get("status", "NEEDS_FIX")
        issues: list[str] = data.get("issues", [])
        suggestions: list[str] = data.get("suggestions", [])

        parts: list[str] = []
        if issues:
            parts.append("PROBLÈMES :\n" + "\n".join(f"  • {i}" for i in issues))
        if suggestions:
            parts.append("SUGGESTIONS :\n" + "\n".join(f"  → {s}" for s in suggestions))

        return status, "\n\n".join(parts)

    except json.JSONDecodeError:
        logger.warning("[reviewer] JSON invalide — NEEDS_FIX par défaut")
        return "NEEDS_FIX", review_text


def _last_message_by(messages: list, name: str) -> str:
    """Retourne le contenu du dernier message portant un `name` donné."""
    for msg in reversed(messages):
        if getattr(msg, "name", None) == name:
            return msg.content
    return "(aucun message d'analyse disponible)"


# ---------------------------------------------------------------------------
# Fonction de routage (utilisée dans graph.py)
# ---------------------------------------------------------------------------

def should_retry(state: FrontendState) -> str:
    """
    Routage conditionnel reviewer → coder | END.
    Retourne "coder" si NEEDS_FIX et itérations restantes, sinon "end".
    """
    has_feedback: bool = bool(state.get("feedback", "").strip())
    iteration_ok: bool = state.get("iteration_count", 0) < MAX_ITERATIONS

    if has_feedback and iteration_ok:
        logger.info(
            "[router] Retour vers coder (itération %d/%d)",
            state["iteration_count"], MAX_ITERATIONS,
        )
        return "coder"

    if state.get("iteration_count", 0) >= MAX_ITERATIONS:
        logger.warning("[router] Max itérations atteint — arrêt forcé")

    return "end"
