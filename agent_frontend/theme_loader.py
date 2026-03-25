"""
theme_loader.py
---------------
Charge la configuration client (client_config.yaml) et génère :
  1. Un dict structuré utilisé par le nœud `coder` pour contextualiser les prompts.
  2. Un bloc CSS Streamlit (st.markdown) injecté dans l'app générée.
  3. Un snippet d'import Google Fonts si une police est spécifiée.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)

DEFAULT_CONFIG_PATH = Path(__file__).parent / "client_config.yaml"


# ---------------------------------------------------------------------------
# Chargement & validation
# ---------------------------------------------------------------------------

def load_theme(config_path: str | Path = DEFAULT_CONFIG_PATH) -> dict[str, Any]:
    """
    Charge le fichier client_config.yaml et retourne un dict validé.

    Paramètres
    ----------
    config_path : chemin vers le fichier YAML (défaut : client_config.yaml)

    Retourne
    --------
    dict
        Configuration complète avec valeurs par défaut pour les clés manquantes.
    """
    path = Path(config_path)

    if not path.exists():
        logger.warning(
            "[theme_loader] %s introuvable — utilisation des valeurs par défaut", path
        )
        return _default_config()

    with path.open(encoding="utf-8") as f:
        raw: dict = yaml.safe_load(f) or {}

    config = _merge_with_defaults(raw)
    logger.info("[theme_loader] Configuration client chargée depuis %s", path)
    return config


# ---------------------------------------------------------------------------
# Génération du CSS Streamlit
# ---------------------------------------------------------------------------

def build_streamlit_theme_snippet(theme_cfg: dict[str, Any]) -> str:
    """
    Génère le bloc Python à insérer en tête de l'app Streamlit générée.
    Au lieu de hardcoder le CSS, génère un import de theme_runtime
    qui relit client_config.yaml EN DIRECT à chaque refresh Streamlit.

    Avantage : changer client_config.yaml ne nécessite qu'un refresh
    du navigateur, pas une régénération complète de l'app.
    """
    # Le snippet généré importe theme_runtime au lieu d'embarquer le CSS statique.
    # theme_runtime.py est copié dans output/ par main.py et relu à chaque refresh.
    _ = theme_cfg  # conservé pour compatibilité avec build_theme_context_for_prompt

    snippet = """import streamlit as st
from theme_runtime import inject_theme, get_auth_handler

# ── Thème client (relu depuis client_config.yaml à chaque refresh) ───────────
_cfg  = inject_theme(st)
_auth = get_auth_handler(_cfg)

# ── Authentification ─────────────────────────────────────────────────────────
_auth.require(st)

def auth_headers() -> dict:
    \"\"\"Retourne les headers HTTP avec le Bearer token courant.\"\"\"
    return _auth.headers(st)

# ── Fin du bloc thème / auth — code métier ci-dessous ────────────────────────
"""
    return snippet


def build_theme_context_for_prompt(theme_cfg: dict[str, Any]) -> str:
    """
    Retourne un résumé textuel de la charte graphique destiné à enrichir
    le prompt du nœud `coder`.
    """
    theme = theme_cfg.get("theme", {})
    typo = theme_cfg.get("typography", {})
    comp = theme_cfg.get("components", {})
    app = theme_cfg.get("app", {})
    branding = theme_cfg.get("branding", {})

    return f"""\
=== CHARTE GRAPHIQUE CLIENT ===
Titre de l'app    : {app.get("title", "App")}
Entreprise        : {branding.get("company_name", "N/A")}
Layout            : {app.get("layout", "wide")}

Couleurs :
  Primaire        : {theme.get("primary_color")}  (boutons, liens)
  Secondaire      : {theme.get("secondary_color")}  (sidebar, headers)
  Accent/Succès   : {theme.get("accent_color")}  (badges, confirmations)
  Danger          : {theme.get("danger_color")}  (erreurs, suppressions)
  Avertissement   : {theme.get("warning_color")}  (alertes, priorité haute)
  Fond de page    : {theme.get("background_color")}
  Surface/Carte   : {theme.get("surface_color")}
  Texte principal : {theme.get("text_primary")}

Typographie :
  Police          : {typo.get("font_family", "système")}
  Police code     : {typo.get("font_family_code", "monospace")}
  Taille de base  : {typo.get("base_font_size", "16px")}

Composants :
  Border-radius   : {comp.get("border_radius", "4px")}

IMPORTANT : Le code généré doit commencer par le snippet de thème fourni
(st.set_page_config + st.markdown CSS). Ne pas redéfinir les couleurs en dur
dans le code — utiliser les variables CSS --color-primary, --color-accent, etc.
"""


# ---------------------------------------------------------------------------
# Helpers internes
# ---------------------------------------------------------------------------

def _default_config() -> dict[str, Any]:
    return {
        "app": {
            "title": "App",
            "page_icon": "🚀",
            "layout": "wide",
            "sidebar_state": "expanded",
        },
        "branding": {"logo_url": "", "logo_width": 180, "company_name": ""},
        "theme": {
            "primary_color": "#0F62FE",
            "secondary_color": "#393939",
            "accent_color": "#42BE65",
            "danger_color": "#DA1E28",
            "warning_color": "#F1C21B",
            "background_color": "#F4F4F4",
            "surface_color": "#FFFFFF",
            "text_primary": "#161616",
            "text_secondary": "#6F6F6F",
        },
        "typography": {
            "font_family": "",
            "font_family_code": "",
            "base_font_size": "16px",
        },
        "components": {
            "border_radius": "4px",
            "card_shadow": "0 1px 3px rgba(0,0,0,0.12)",
            "sidebar_width": "280px",
        },
    }


def _merge_with_defaults(raw: dict) -> dict[str, Any]:
    """Fusionne le YAML chargé avec les valeurs par défaut (deep merge)."""
    defaults = _default_config()
    for section, values in defaults.items():
        if section not in raw:
            raw[section] = values
        elif isinstance(values, dict):
            for key, default_val in values.items():
                raw[section].setdefault(key, default_val)
    return raw


def build_dev_mode_snippet(theme_cfg: dict[str, Any]) -> str:
    """
    Génère le bloc Python de gestion du mode développement.
    A insérer juste après le snippet de thème dans l'app générée.

    Stratégies :
      - "bypass"     : session_state["authenticated"] = True directement
      - "mock_login" : formulaire login qui accepte les credentials mock
    """
    dev = theme_cfg.get("dev_mode", {})
    if not dev.get("enabled", False):
        # Mode production : retourne un stub qui ne fait rien
        # (le vrai appel API auth sera géré dans le code métier)
        return ""

    strategy: str = dev.get("strategy", "mock_login")
    mock_user: str = dev.get("mock_username", "demo")
    mock_pass: str = dev.get("mock_password", "demo")
    mock_token: str = dev.get("mock_token", "dev-token-00000000")
    show_banner: bool = dev.get("show_dev_banner", True)
    banner_msg: str = dev.get("banner_message", "MODE DEVELOPPEMENT")

    banner_code = ""
    if show_banner:
        banner_code = f"""
    st.warning("{banner_msg}", icon="⚠️")"""

    if strategy == "bypass":
        return f'''
# ── Authentification : MODE DEV (bypass total) ──────────────────────────────
def init_auth():
    \"\"\"Bypass total : accès direct sans login.\"\"\"
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = True
        st.session_state["token"] = "{mock_token}"
        st.session_state["username"] = "{mock_user}"

def auth_headers() -> dict:
    return {{"Authorization": f"Bearer {{st.session_state.get('token', '')}}"}}

init_auth()
{banner_code}
'''

    # Stratégie mock_login (défaut)
    return f'''
# ── Authentification : MODE DEV (mock login) ────────────────────────────────
def init_auth():
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False
        st.session_state["token"] = ""
        st.session_state["username"] = ""

def auth_headers() -> dict:
    return {{"Authorization": f"Bearer {{st.session_state.get('token', '')}}"}}

def show_login_page():
    st.title("Connexion")
    st.caption("Mode développement — identifiants : **{mock_user}** / **{mock_pass}**")
    with st.form("login_form"):
        username = st.text_input("Identifiant")
        password = st.text_input("Mot de passe", type="password")
        submitted = st.form_submit_button("Se connecter", use_container_width=True)
        if submitted:
            # Mock : accepte n'importe quel identifiant non vide,
            # ou les credentials mock exacts selon la rigueur souhaitée
            if username.strip() and password.strip():
                st.session_state["authenticated"] = True
                st.session_state["token"] = "{mock_token}"
                st.session_state["username"] = username
                st.rerun()
            else:
                st.error("Identifiant et mot de passe requis.")

init_auth()

if not st.session_state["authenticated"]:
    show_login_page()
    st.stop()   # Bloque tout le reste de l'app tant que non connecté
{banner_code}
# ── Fin du bloc auth ─────────────────────────────────────────────────────────
'''
