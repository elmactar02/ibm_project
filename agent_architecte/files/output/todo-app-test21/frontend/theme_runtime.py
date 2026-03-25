"""
theme_runtime.py
----------------
Module importé par l'app Streamlit GÉNÉRÉE (output/app.py).
Lit client_config.yaml EN DIRECT à chaque refresh Streamlit.

Avantage : modifier client_config.yaml ne nécessite qu'un refresh du
navigateur — pas besoin de relancer python main.py pour les changements
de thème (couleurs, police, logo, bannière dev_mode).

Ce fichier est copié automatiquement dans output/ par main.py.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Cherche client_config.yaml en remontant depuis ce fichier
def _find_config() -> Path:
    here = Path(__file__).resolve().parent
    for candidate in [here / "client_config.yaml", here.parent / "client_config.yaml"]:
        if candidate.exists():
            return candidate
    raise FileNotFoundError(
        "client_config.yaml introuvable. "
        "Placez-le dans le même dossier que app.py ou dans le dossier parent."
    )


def _load() -> dict[str, Any]:
    try:
        import yaml
        with _find_config().open(encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except Exception as exc:
        logger.warning("[theme_runtime] Impossible de charger le thème : %s", exc)
        return {}


def inject_theme(st: Any) -> dict[str, Any]:
    """
    Appelle st.set_page_config() + st.markdown(CSS) depuis la config live.
    Retourne le dict de config complet pour usage dans l'app.

    Utilisation dans app.py généré :
        import streamlit as st
        from theme_runtime import inject_theme
        cfg = inject_theme(st)
    """
    cfg = _load()

    app    = cfg.get("app", {})
    theme  = cfg.get("theme", {})
    typo   = cfg.get("typography", {})
    comp   = cfg.get("components", {})
    brand  = cfg.get("branding", {})
    dev    = cfg.get("dev_mode", {})

    # ── st.set_page_config ───────────────────────────────────────────────────
    try:
        st.set_page_config(
            page_title=app.get("title", "App"),
            page_icon=app.get("page_icon", "🚀"),
            layout=app.get("layout", "wide"),
            initial_sidebar_state=app.get("sidebar_state", "expanded"),
        )
    except Exception:
        pass  # set_page_config lève si appelé deux fois — sans danger

    # ── Google Fonts ─────────────────────────────────────────────────────────
    font_family = typo.get("font_family", "")
    font_code   = typo.get("font_family_code", "")
    gf_import   = ""
    if font_family or font_code:
        families = []
        if font_family:
            families.append(font_family.replace(" ", "+") + ":wght@400;500;600;700")
        if font_code:
            families.append(font_code.replace(" ", "+") + ":wght@400;500")
        gf_import = (
            f"@import url('https://fonts.googleapis.com/css2?"
            f"family={'&family='.join(families)}&display=swap');\n"
        )

    font_stack      = f"'{font_family}', sans-serif" if font_family else "sans-serif"
    font_code_stack = f"'{font_code}', monospace"    if font_code   else "monospace"

    primary   = theme.get("primary_color",    "#0F62FE")
    secondary = theme.get("secondary_color",  "#393939")
    accent    = theme.get("accent_color",     "#42BE65")
    danger    = theme.get("danger_color",     "#DA1E28")
    warning   = theme.get("warning_color",    "#F1C21B")
    bg        = theme.get("background_color", "#F4F4F4")
    surface   = theme.get("surface_color",    "#FFFFFF")
    text_p    = theme.get("text_primary",     "#161616")
    radius    = comp.get("border_radius",     "4px")
    shadow    = comp.get("card_shadow",       "0 1px 3px rgba(0,0,0,0.12)")
    font_size = typo.get("base_font_size",    "16px")

    css = f"""
<style>
{gf_import}
:root {{
    --color-primary:    {primary};
    --color-secondary:  {secondary};
    --color-accent:     {accent};
    --color-danger:     {danger};
    --color-warning:    {warning};
    --color-bg:         {bg};
    --color-surface:    {surface};
    --color-text:       {text_p};
    --border-radius:    {radius};
    --card-shadow:      {shadow};
    --font-size-base:   {font_size};
}}
html, body, [class*="css"] {{
    font-family: {font_stack} !important;
    font-size: var(--font-size-base);
    color: var(--color-text);
}}
code, pre, .stCode {{ font-family: {font_code_stack} !important; }}
.stApp {{ background-color: var(--color-bg); }}
section[data-testid="stSidebar"] {{
    background-color: var(--color-surface);
    border-right: 1px solid rgba(0,0,0,0.08);
}}
.stButton > button {{
    background-color: var(--color-primary) !important;
    color: #ffffff !important;
    border: none !important;
    border-radius: var(--border-radius) !important;
    font-weight: 500;
    transition: opacity 0.15s ease;
}}
.stButton > button:hover {{ opacity: 0.88; }}
.stButton > button[kind="secondary"] {{
    background-color: transparent !important;
    color: var(--color-primary) !important;
    border: 1px solid var(--color-primary) !important;
}}
.stTextInput > div > div > input,
.stTextArea > div > div > textarea {{
    border-radius: var(--border-radius) !important;
}}
.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus {{
    border-color: var(--color-primary) !important;
    box-shadow: 0 0 0 2px {primary}33 !important;
}}
.badge-success {{ background:{accent};  color:#fff; padding:2px 8px; border-radius:99px; font-size:12px; }}
.badge-danger  {{ background:{danger};  color:#fff; padding:2px 8px; border-radius:99px; font-size:12px; }}
.badge-warning {{ background:{warning}; color:#fff; padding:2px 8px; border-radius:99px; font-size:12px; }}
</style>
"""
    st.markdown(css, unsafe_allow_html=True)

    # ── Logo & nom entreprise ────────────────────────────────────────────────
    logo_url = brand.get("logo_url", "")
    company  = brand.get("company_name", "")
    if logo_url:
        st.sidebar.image(logo_url, width=brand.get("logo_width", 180))
    if company:
        st.sidebar.markdown(
            f"<h3 style='color:{primary};margin-top:0'>{company}</h3>",
            unsafe_allow_html=True,
        )

    # ── Bannière dev_mode ────────────────────────────────────────────────────
    if dev.get("enabled") and dev.get("show_dev_banner"):
        st.warning(dev.get("banner_message", "MODE DEVELOPPEMENT"), icon="⚠️")

    return cfg


def get_auth_handler(cfg: dict[str, Any]) -> "AuthHandler":
    """Retourne un AuthHandler configuré depuis le dict cfg."""
    return AuthHandler(cfg)


class AuthHandler:
    """
    Gère le mock login ou le bypass selon dev_mode.strategy.
    Usage dans app.py généré :

        cfg = inject_theme(st)
        auth = get_auth_handler(cfg)
        auth.require(st)          # bloque si non connecté
        headers = auth.headers(st)  # {"Authorization": "Bearer ..."}
    """

    def __init__(self, cfg: dict[str, Any]) -> None:
        self.dev = cfg.get("dev_mode", {})

    def require(self, st: Any) -> None:
        """
        Vérifie l'authentification et bloque l'app si non connecté.

        IMPORTANT : cette méthode doit être appelée EN PREMIER dans app.py,
        avant tout autre code métier. Elle gère elle-même l'affichage du
        formulaire de login — le code généré NE DOIT PAS avoir de bloc login
        séparé qui ferait un appel API.

        En dev_mode bypass   → session initialisée directement, accès immédiat.
        En dev_mode mock     → formulaire affiché, tout identifiant non vide accepté.
        En mode production   → vérifie st.session_state["authenticated"].
        """
        if not self.dev.get("enabled", False):
            # Mode production : vérification simple de la session
            if not st.session_state.get("authenticated"):
                st.error("Non authentifié. Veuillez vous connecter.")
                st.stop()
            return

        strategy = self.dev.get("strategy", "mock_login")

        if strategy == "bypass":
            if not st.session_state.get("authenticated"):
                st.session_state["authenticated"] = True
                st.session_state["token"]         = self.dev.get("mock_token", "dev-token")
                st.session_state["username"]      = self.dev.get("mock_username", "dev")
            return

        # mock_login — affiche le formulaire et st.stop() si non connecté
        if not st.session_state.get("authenticated"):
            self._show_mock_login(st)
            st.stop()   # ← tout le reste de app.py est ignoré jusqu'à connexion

    def _show_mock_login(self, st: Any) -> None:
        mock_user = self.dev.get("mock_username", "demo")
        mock_pass = self.dev.get("mock_password", "demo")
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.title("Connexion")
            st.caption(
                f"Mode développement — identifiants suggérés : "
                f"**{mock_user}** / **{mock_pass}** (tout identifiant non vide accepté)"
            )
            with st.form("login_form"):
                username  = st.text_input("Identifiant")
                password  = st.text_input("Mot de passe", type="password")
                submitted = st.form_submit_button("Se connecter", use_container_width=True)
                if submitted:
                    if username.strip() and password.strip():
                        st.session_state["authenticated"] = True
                        st.session_state["token"]         = self.dev.get("mock_token", "dev-token")
                        st.session_state["username"]      = username
                        st.rerun()
                    else:
                        st.error("Identifiant et mot de passe requis.")

    def headers(self, st: Any) -> dict[str, str]:
        """Retourne les headers HTTP avec le Bearer token courant."""
        token = st.session_state.get("token", "")
        return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# Fonction utilitaire de module — importable directement dans app.py
# ---------------------------------------------------------------------------

def auth_headers() -> dict[str, str]:
    """
    Raccourci module-level pour récupérer les headers Bearer.
    Utilisable via : from theme_runtime import auth_headers
    Repose sur st.session_state — doit être appelé après inject_theme().
    """
    try:
        import streamlit as st
        token = st.session_state.get("token", "")
    except Exception:
        token = ""
    return {"Authorization": f"Bearer {token}"}
