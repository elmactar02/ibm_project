"""
app_architect.py — Interface Streamlit pour l'Architect Agent (Manal)

LANCEMENT : streamlit run app_architect.py
"""

import streamlit as st
import json
import os
import sys
import time
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))
_env = ROOT / ".env"
if _env.exists():
    load_dotenv(dotenv_path=str(_env), override=True)

st.set_page_config(
    page_title="Architect Agent — Manal",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Fonts ─────────────────────────────────────────────────────────────────────
st.markdown('<link href="https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Mono:wght@300;400;500&family=DM+Sans:wght@300;400;500&display=swap" rel="stylesheet">', unsafe_allow_html=True)

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
/* ── Reset & base ─────────────────────────────────────── */
html, body, .stApp {
  background: #0c0f14 !important;
  color: #e2e8f0;
  font-family: 'DM Sans', sans-serif;
}
.block-container { padding: 1.5rem 2rem 2rem !important; max-width: 1400px !important; }
h1,h2,h3,h4 { font-family: 'Syne', sans-serif !important; }
code, pre, .stCode { font-family: 'DM Mono', monospace !important; }

/* ── Hide streamlit chrome ───────────────────────────── */
#MainMenu, footer, header { visibility: hidden; }
.stDeployButton { display:none; }

/* ── Sidebar ─────────────────────────────────────────── */
.css-1d391kg, [data-testid="stSidebar"] {
  background: #0f1318 !important;
  border-right: 1px solid #1e2530 !important;
}

/* ── Tab bar ─────────────────────────────────────────── */
.stTabs [data-baseweb="tab-list"] {
  background: transparent;
  gap: 4px;
  border-bottom: 1px solid #1e2530;
  padding-bottom: 0;
}
.stTabs [data-baseweb="tab"] {
  background: transparent;
  border: none;
  color: #64748b;
  font-family: 'Syne', sans-serif;
  font-size: 13px;
  font-weight: 600;
  letter-spacing: 0.04em;
  padding: 10px 18px;
  border-radius: 8px 8px 0 0;
  transition: all 0.2s;
}
.stTabs [aria-selected="true"] {
  background: #141920 !important;
  color: #38e8c8 !important;
  border-bottom: 2px solid #38e8c8 !important;
}
.stTabs [data-baseweb="tab-panel"] {
  background: #0f1318;
  border-radius: 0 12px 12px 12px;
  border: 1px solid #1e2530;
  border-top: none;
  padding: 20px;
}

/* ── Inputs ──────────────────────────────────────────── */
.stTextInput input, .stSelectbox select, .stTextArea textarea {
  background: #141920 !important;
  border: 1px solid #1e2530 !important;
  border-radius: 8px !important;
  color: #e2e8f0 !important;
  font-family: 'DM Sans', sans-serif !important;
}
.stTextInput input:focus, .stTextArea textarea:focus {
  border-color: #38e8c8 !important;
  box-shadow: 0 0 0 2px rgba(56,232,200,0.12) !important;
}
label[data-testid="stWidgetLabel"] {
  color: #94a3b8 !important;
  font-size: 12px !important;
  font-weight: 500 !important;
  letter-spacing: 0.06em !important;
  text-transform: uppercase !important;
  font-family: 'Syne', sans-serif !important;
}

/* ── Button ──────────────────────────────────────────── */
.stButton > button {
  background: linear-gradient(135deg, #38e8c8, #1a9e8a) !important;
  color: #0c0f14 !important;
  border: none !important;
  border-radius: 8px !important;
  font-family: 'Syne', sans-serif !important;
  font-weight: 700 !important;
  font-size: 13px !important;
  letter-spacing: 0.06em !important;
  padding: 10px 24px !important;
  transition: all 0.2s !important;
}
.stButton > button:hover {
  transform: translateY(-1px) !important;
  box-shadow: 0 8px 24px rgba(56,232,200,0.25) !important;
}
.stButton > button:disabled {
  background: #1e2530 !important;
  color: #4a5568 !important;
}

/* ── Download button ─────────────────────────────────── */
.stDownloadButton > button {
  background: transparent !important;
  border: 1px solid #38e8c8 !important;
  color: #38e8c8 !important;
  border-radius: 6px !important;
  font-size: 12px !important;
  font-family: 'DM Mono', monospace !important;
}

/* ── Progress bar ────────────────────────────────────── */
.stProgress > div > div {
  background: linear-gradient(90deg, #38e8c8, #5ba3ff) !important;
  border-radius: 4px !important;
}

/* ── Metrics ─────────────────────────────────────────── */
[data-testid="metric-container"] {
  background: #141920;
  border: 1px solid #1e2530;
  border-radius: 10px;
  padding: 14px 16px;
}
[data-testid="metric-container"] label {
  color: #64748b !important;
  font-size: 11px !important;
  text-transform: uppercase !important;
  letter-spacing: 0.08em !important;
}
[data-testid="stMetricValue"] {
  color: #38e8c8 !important;
  font-family: 'Syne', sans-serif !important;
  font-size: 1.5rem !important;
  font-weight: 700 !important;
}

/* ── Divider ─────────────────────────────────────────── */
hr { border-color: #1e2530 !important; }

/* ── Expander ────────────────────────────────────────── */
.streamlit-expanderHeader {
  background: #141920 !important;
  border: 1px solid #1e2530 !important;
  border-radius: 8px !important;
  color: #e2e8f0 !important;
  font-family: 'DM Sans', sans-serif !important;
}
.streamlit-expanderContent {
  background: #0f1318 !important;
  border: 1px solid #1e2530 !important;
  border-top: none !important;
}

/* ── Custom components ───────────────────────────────── */
.agent-header {
  display: flex;
  align-items: center;
  gap: 14px;
  margin-bottom: 24px;
  padding-bottom: 20px;
  border-bottom: 1px solid #1e2530;
}
.agent-hex {
  width: 44px; height: 44px;
  background: linear-gradient(135deg, #38e8c8, #1a9e8a);
  clip-path: polygon(50% 0%, 100% 25%, 100% 75%, 50% 100%, 0% 75%, 0% 25%);
  flex-shrink: 0;
}
.agent-title {
  font-family: 'Syne', sans-serif;
  font-size: 1.5rem;
  font-weight: 800;
  color: #f1f5f9;
  line-height: 1;
  margin: 0;
}
.agent-sub {
  font-size: 12px;
  color: #64748b;
  margin: 3px 0 0;
  font-family: 'DM Mono', monospace;
}
.status-dot {
  display: inline-block;
  width: 8px; height: 8px;
  border-radius: 50%;
  margin-right: 6px;
}
.dot-idle    { background: #4a5568; }
.dot-running { background: #fbbf24; animation: pulse 1s infinite; }
.dot-done    { background: #38e8c8; }
.dot-error   { background: #ef4444; }
@keyframes pulse { 0%,100%{opacity:1} 50%{opacity:.3} }

.terminal {
  background: #080b0f;
  border: 1px solid #1e2530;
  border-radius: 10px;
  overflow: hidden;
}
.terminal-bar {
  background: #141920;
  padding: 8px 14px;
  display: flex;
  align-items: center;
  gap: 6px;
  border-bottom: 1px solid #1e2530;
}
.dot-r { width:10px;height:10px;border-radius:50%;background:#ef4444; }
.dot-y { width:10px;height:10px;border-radius:50%;background:#fbbf24; }
.dot-g { width:10px;height:10px;border-radius:50%;background:#38e8c8; }
.terminal-title {
  font-family: 'DM Mono', monospace;
  font-size: 11px;
  color: #4a5568;
  margin-left: 6px;
}
.terminal-body {
  padding: 14px 16px;
  font-family: 'DM Mono', monospace;
  font-size: 11.5px;
  line-height: 1.8;
  color: #94a3b8;
  min-height: 360px;
  max-height: 360px;
  overflow-y: auto;
  white-space: pre-wrap;
  word-break: break-all;
}
.log-phase   { color: #38e8c8; font-weight: 500; }
.log-ok      { color: #4ade80; }
.log-tool    { color: #fbbf24; }
.log-llm     { color: #5ba3ff; }
.log-error   { color: #ef4444; }
.log-dim     { color: #4a5568; }

.section-label {
  font-family: 'Syne', sans-serif;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: #64748b;
  margin-bottom: 12px;
}

.tag {
  display: inline-block;
  padding: 3px 10px;
  border-radius: 100px;
  font-size: 11px;
  font-family: 'DM Mono', monospace;
  margin: 2px;
}
.tag-teal  { background: rgba(56,232,200,0.12); color: #38e8c8; border: 1px solid rgba(56,232,200,0.25); }
.tag-blue  { background: rgba(91,163,255,0.12); color: #5ba3ff; border: 1px solid rgba(91,163,255,0.25); }
.tag-amber { background: rgba(251,191,36,0.12);  color: #fbbf24; border: 1px solid rgba(251,191,36,0.25); }
.tag-red   { background: rgba(239,68,68,0.12);   color: #ef4444; border: 1px solid rgba(239,68,68,0.25); }
.tag-green { background: rgba(74,222,128,0.12);  color: #4ade80; border: 1px solid rgba(74,222,128,0.25); }

.card {
  background: #141920;
  border: 1px solid #1e2530;
  border-radius: 10px;
  padding: 16px;
  margin-bottom: 12px;
}
.card-title {
  font-family: 'Syne', sans-serif;
  font-weight: 700;
  font-size: 13px;
  color: #e2e8f0;
  margin-bottom: 8px;
}

.ep-row {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 6px 10px;
  border-radius: 6px;
  margin: 3px 0;
  background: #141920;
  border: 1px solid #1e2530;
  font-size: 12px;
}
.ep-badge {
  font-family: 'DM Mono', monospace;
  font-size: 10px;
  font-weight: 700;
  padding: 2px 8px;
  border-radius: 4px;
  min-width: 54px;
  text-align: center;
}
.ep-get    { background: rgba(74,222,128,0.15);  color: #4ade80; }
.ep-post   { background: rgba(91,163,255,0.15);  color: #5ba3ff; }
.ep-put    { background: rgba(251,191,36,0.15);  color: #fbbf24; }
.ep-delete { background: rgba(239,68,68,0.15);   color: #ef4444; }
.ep-patch  { background: rgba(167,139,250,0.15); color: #a78bfa; }

.stack-row {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 12px;
  border-radius: 6px;
  border: 1px solid #1e2530;
  margin: 4px 0;
  background: #141920;
}
.stack-icon { font-size: 16px; width: 20px; }
.stack-key  { font-family: 'DM Mono', monospace; font-size: 11px; color: #64748b; min-width: 110px; }
.stack-val  { font-family: 'DM Sans', sans-serif; font-size: 13px; color: #e2e8f0; }

.file-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 6px 12px;
  border-radius: 6px;
  border: 1px solid #1e2530;
  margin: 3px 0;
  background: #141920;
  font-family: 'DM Mono', monospace;
  font-size: 11px;
  color: #94a3b8;
}
.file-ok { color: #38e8c8; margin-right: 8px; }
.file-size { color: #4a5568; }
</style>
""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
# SESSION STATE
# ═══════════════════════════════════════════════════════════════════════════════
for k, v in [("result",None),("elapsed",0),("run_count",0),
              ("log_lines",[]),("status","idle"),
              ("project_name","my-app")]:
    if k not in st.session_state:
        st.session_state[k] = v

# Nom du projet global (mis à jour depuis l'onglet ▶ Lancer)
project_name = st.session_state.get("project_name", "my-app")
output_dir   = f"./output/{project_name}"


# ═══════════════════════════════════════════════════════════════════════════════
# SIDEBAR — config
# ═══════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown('<p style="font-family:Syne,sans-serif;font-weight:700;font-size:14px;color:#38e8c8;margin:0">⚙ Configuration</p>', unsafe_allow_html=True)
    st.divider()
    _key = os.getenv("MISTRAL_API_KEY","")
    api_key = st.text_input("Clé API Mistral", type="password", value=_key,
                             help="Chargée depuis .env automatiquement")
    if api_key: st.success(f"✓ {api_key[:8]}…")
    else:        st.warning("Clé manquante")
    st.divider()
    st.caption(f"Projet actif : `{project_name}`")
    st.caption(f"Sortie : `./output/{project_name}/`")
    model = st.selectbox("Modèle", ["mistral-large-latest","mistral-small-latest"])
    st.caption("large ~80s · small ~30s")
    st.divider()
    st.metric("Runs", st.session_state.run_count)


# ═══════════════════════════════════════════════════════════════════════════════
# EN-TÊTE
# ═══════════════════════════════════════════════════════════════════════════════
status = st.session_state.status
dot_cls = {"idle":"dot-idle","running":"dot-running","done":"dot-done","error":"dot-error"}.get(status,"dot-idle")
status_html = f'<span class="status-dot {dot_cls}"></span><span style="font-family:DM Mono,monospace;font-size:11px;color:#64748b">{status.upper()}</span>'

st.markdown(f"""
<div class="agent-header">
  <div class="agent-hex"></div>
  <div>
    <p class="agent-title">Architect Agent</p>
    <p class="agent-sub">
      Manal — Blueprint · C4 · Tech Stack · Documentation
      &nbsp;·&nbsp;
      <span style="color:#38e8c8;font-family:DM Mono,monospace">{project_name}</span>
      &nbsp;&nbsp; {status_html}
    </p>
  </div>
</div>
""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
# ONGLETS PRINCIPAUX
# ═══════════════════════════════════════════════════════════════════════════════
tab_run, tab_bp, tab_c4, tab_doc, tab_dl = st.tabs([
    "▶  Lancer",
    "📋  Blueprint",
    "🗺  Diagrammes C4",
    "📄  Documentation",
    "⬇  Télécharger",
])


# ─────────────────────────────────────────────────────────────────────────────
# ONGLET 1 — LANCER (saisie + logs sur la même page)
# ─────────────────────────────────────────────────────────────────────────────
DEFAULT_SPEC = """Construire une application de gestion de tâches (To-Do + suivi de demandes).

Fonctionnalités :
- Inscription et connexion utilisateur avec JWT
- Tableau de bord listant toutes les tâches, filtrable par statut et priorité
- Créer, modifier, supprimer des tâches
- Détail d'une tâche : titre, description, priorité, date d'échéance, statut
- Assigner des tâches à des utilisateurs enregistrés
- Ajouter des commentaires sur les tâches
- Historique des modifications

Contraintes :
- API REST avec documentation OpenAPI
- SQLite pour le développement, compatible PostgreSQL en production
- Conteneurisé avec Docker + Docker Compose
- Pipeline CI/CD sur GitHub Actions"""

with tab_run:

    # ── Layout 2 colonnes ────────────────────────────────────────────────────
    left, right = st.columns([1, 1], gap="large")

    with left:
        # ── Nom du projet (optionnel) ────────────────────────────────────────
        st.markdown('<p class="section-label">Nom du projet <span style="color:#4a5568;font-weight:400;text-transform:none;letter-spacing:0">(optionnel — généré automatiquement si vide)</span></p>', unsafe_allow_html=True)
        project_name_input = st.text_input(
            "project_name_main",
            value="",
            placeholder="Laisser vide pour générer automatiquement…",
            label_visibility="collapsed",
        )
        # Si vide → nom par défaut "my-app"
        if project_name_input.strip():
            project_name = project_name_input.strip().lower().replace(" ", "-")
        else:
            project_name = "my-app"
        output_dir = f"./output/{project_name}"
        # Persister en session state pour la sidebar et le header
        st.session_state["project_name"] = project_name
        st.caption(f"📁 Sortie → `./output/{project_name}/`")

        st.markdown("&nbsp;", unsafe_allow_html=True)

        # ── Spec ─────────────────────────────────────────────────────────────
        st.markdown('<p class="section-label">Besoin utilisateur</p>', unsafe_allow_html=True)
        spec_input = st.text_area(
            "spec",
            value=DEFAULT_SPEC,
            height=260,
            label_visibility="collapsed",
            placeholder="Décris le besoin fonctionnel de ton application…",
        )
        st.caption(f"📝 {len(spec_input)} chars · {len(spec_input.split())} mots")

        st.markdown("&nbsp;", unsafe_allow_html=True)

        run_btn = st.button(
            "▶  Lancer l'Architect",
            disabled=not api_key or not spec_input.strip(),
            use_container_width=True,
        )
        if not api_key:
            st.markdown('<p style="font-size:12px;color:#ef4444">Configure la clé API dans la sidebar (◂)</p>', unsafe_allow_html=True)


    with right:
        st.markdown('<p class="section-label">Logs d\'exécution</p>', unsafe_allow_html=True)

        progress_ph = st.empty()
        terminal_ph = st.empty()

        def render_terminal(lines=None, title="bash — architect_agent"):
            content = "\n".join((lines or st.session_state.log_lines)[-55:])
            if not content:
                content = '<span class="log-dim">En attente de lancement…</span>'
            terminal_ph.markdown(f"""
<div class="terminal">
  <div class="terminal-bar">
    <div class="dot-r"></div><div class="dot-y"></div><div class="dot-g"></div>
    <span class="terminal-title">{title}</span>
  </div>
  <div class="terminal-body">{content}</div>
</div>
""", unsafe_allow_html=True)

        render_terminal()

    # ── Exécution ────────────────────────────────────────────────────────────
    def add_log(line, cls=""):
        tag = f'<span class="{cls}">' if cls else ""
        end = "</span>" if cls else ""
        st.session_state.log_lines.append(f"{tag}{line}{end}")
        render_terminal()

    if run_btn and api_key and spec_input.strip():
        st.session_state.log_lines = []
        st.session_state.status    = "running"
        st.session_state.result    = None

        os.environ["MISTRAL_API_KEY"] = api_key

        try:
            from langchain_mistralai import ChatMistralAI
            llm = ChatMistralAI(model=model, api_key=api_key, temperature=0.1)
        except ImportError as e:
            st.error(f"Dépendance manquante : {e}")
            st.stop()

        from state.schema import AgentState
        state = {
            "raw_input": spec_input, "project_name": project_name,
            "input_images": None, "architect_blueprint": None, "reasoning_trace": [],
            "c4_context": None, "c4_containers": None, "c4_components": None,
            "tech_stack": None, "architecture_doc": None,
            "repo_path": output_dir, "repo_url": None, "cicd_config": None,
            "database_files": [], "backend_files": [], "frontend_files": [],
            "generated_files": [], "test_files": [],
            "qa_report": None, "validation_passed": False, "qa_attempts": 0,
            "current_phase": "architect", "error": None, "messages": [],
        }

        add_log("══════════════════════════════════════════", "log-phase")
        add_log(f"  ◈  ARCHITECT AGENT — {project_name}", "log-phase")
        add_log(f"  Modèle : {model}", "log-dim")
        add_log("══════════════════════════════════════════", "log-phase")
        add_log("")
        add_log("⟳  Initialisation du LLM Mistral…", "log-llm")
        progress_ph.progress(5, text="Connexion à Mistral…")

        start = time.time()

        try:
            from agents.architect import architect_node

            add_log("✓  LLM prêt", "log-ok")
            add_log(f"▶  Envoi du besoin ({len(spec_input)} chars)…", "log-llm")
            add_log("  ⏳ ~30 à 90 secondes selon le modèle…", "log-dim")
            add_log("")
            progress_ph.progress(15, text="Appel LLM en cours…")

            result = architect_node(state, llm)
            elapsed = round(time.time() - start, 1)

            st.session_state.result   = result
            st.session_state.elapsed  = elapsed
            st.session_state.run_count += 1
            st.session_state.status   = "done"

            progress_ph.progress(100, text=f"✓ Terminé en {elapsed}s")

            bp = result.get("architect_blueprint", {})
            ts = result.get("tech_stack", {})

            add_log(f"✓  Réponse reçue en {elapsed}s", "log-ok")
            add_log("")
            add_log("━━━━━━━━━  BLUEPRINT  ━━━━━━━━━", "log-phase")
            add_log(f"  Modules   : {bp.get('modules', [])}")
            add_log(f"  Entités   : {[e.get('name') for e in bp.get('entities', [])]}")
            add_log(f"  Endpoints : {len(bp.get('api_endpoints', []))} routes")
            add_log(f"  Complexité: {bp.get('project', {}).get('complexity', '?')}")
            add_log("")
            add_log("━━━━━━━━━  TECH STACK  ━━━━━━━━━", "log-phase")
            for k, v in ts.items():
                add_log(f"  {k:<16} {v}", "log-dim")
            add_log("")
            add_log("━━━━━━━━━  FICHIERS  ━━━━━━━━━", "log-phase")
            out = Path(output_dir) / "docs"
            if out.exists():
                for f in sorted(out.rglob("*")):
                    if f.is_file():
                        add_log(f"  ✓ {f.relative_to(Path(output_dir))}  ({f.stat().st_size} o)", "log-ok")
            add_log("")
            add_log("══════════════════════════════════════════", "log-phase")
            add_log("  ✓  TERMINÉ — Consulte les autres onglets", "log-ok")
            add_log("══════════════════════════════════════════", "log-phase")

        except Exception as e:
            st.session_state.status = "error"
            progress_ph.progress(100, text="Erreur")
            add_log(f"✗  ERREUR : {e}", "log-error")
            st.exception(e)

    # ── Métriques rapides sous les colonnes ──────────────────────────────────
    if st.session_state.result:
        st.divider()
        st.markdown('<p class="section-label">Résumé de l\'exécution</p>', unsafe_allow_html=True)
        bp = st.session_state.result.get("architect_blueprint", {})
        m1,m2,m3,m4,m5 = st.columns(5)
        m1.metric("Modules",   len(bp.get("modules",[])))
        m2.metric("Entités",   len(bp.get("entities",[])))
        m3.metric("Endpoints", len(bp.get("api_endpoints",[])))
        m4.metric("Doc",       f"{len(st.session_state.result.get('architecture_doc','').split())} mots")
        m5.metric("Durée",     f"{st.session_state.elapsed}s")
        st.info("Les résultats détaillés sont dans les onglets **Blueprint**, **Diagrammes C4**, **Documentation** et **Télécharger**.")


# ─────────────────────────────────────────────────────────────────────────────
# ONGLET 2 — BLUEPRINT
# ─────────────────────────────────────────────────────────────────────────────
with tab_bp:
    if not st.session_state.result:
        st.markdown('<p style="color:#64748b;text-align:center;padding:40px 0;font-family:DM Mono,monospace">Lance l\'agent dans l\'onglet <strong>▶ Lancer</strong></p>', unsafe_allow_html=True)
    else:
        bp = st.session_state.result.get("architect_blueprint", {})
        ts = st.session_state.result.get("tech_stack", {})

        col1, col2 = st.columns([1,1], gap="large")

        with col1:
            # Modules
            st.markdown('<p class="section-label">Modules fonctionnels</p>', unsafe_allow_html=True)
            tags = "".join(f'<span class="tag tag-teal">{m}</span>' for m in bp.get("modules",[]))
            st.markdown(f'<div style="margin-bottom:16px">{tags}</div>', unsafe_allow_html=True)

            # Entités
            st.markdown('<p class="section-label">Entités de données</p>', unsafe_allow_html=True)
            for entity in bp.get("entities", []):
                with st.expander(f"**{entity.get('name')}**"):
                    fc, rc = st.columns(2)
                    with fc:
                        st.markdown("**Champs**")
                        for f in entity.get("fields", []): st.markdown(f"- `{f}`")
                    with rc:
                        st.markdown("**Relations**")
                        for r in entity.get("relations", []): st.markdown(f"- {r}")

            # Instructions devs
            st.markdown('<p class="section-label" style="margin-top:16px">Instructions développeurs</p>', unsafe_allow_html=True)
            di = bp.get("dev_instructions", {})
            for dev, label, cls in [
                ("database","🗄  Oumeyma — Base de données","tag-teal"),
                ("backend", "⚙  Akram — Backend",          "tag-blue"),
                ("frontend","🖥  Mactar — Frontend",        "tag-amber"),
            ]:
                instr = di.get(dev,"")
                if isinstance(instr, dict): instr = " ".join(instr.get("instructions",[]))
                with st.expander(f'{label}'):
                    st.markdown(str(instr) if instr else "_Pas d'instructions_")

        with col2:
            # Tech Stack
            st.markdown('<p class="section-label">Tech Stack</p>', unsafe_allow_html=True)
            icons = {"frontend":"🖥","backend":"⚙","database":"🗄","auth":"🔐",
                     "cache":"⚡","message_broker":"📨","container":"🐳","cloud":"☁"}
            for k, v in ts.items():
                st.markdown(f"""
<div class="stack-row">
  <span class="stack-icon">{icons.get(k,"•")}</span>
  <span class="stack-key">{k}</span>
  <span class="stack-val">{v}</span>
</div>""", unsafe_allow_html=True)

            # Endpoints
            st.markdown('<p class="section-label" style="margin-top:16px">Endpoints API</p>', unsafe_allow_html=True)
            badge_cls = {"GET":"ep-get","POST":"ep-post","PUT":"ep-put","DELETE":"ep-delete","PATCH":"ep-patch"}
            for ep in bp.get("api_endpoints", []):
                m   = ep.get("method","?")
                cls = badge_cls.get(m,"ep-get")
                auth = "🔒" if ep.get("auth_required") else "🔓"
                st.markdown(f"""
<div class="ep-row">
  <span class="ep-badge {cls}">{m}</span>
  <code style="color:#94a3b8;font-size:12px">{ep.get('path')}</code>
  <span>{auth}</span>
  <span style="color:#64748b;font-size:12px">{ep.get('description','')}</span>
</div>""", unsafe_allow_html=True)

        st.divider()
        st.markdown('<p class="section-label">JSON complet — architect_blueprint.json</p>', unsafe_allow_html=True)
        st.json(bp)


# ─────────────────────────────────────────────────────────────────────────────
# ONGLET 3 — DIAGRAMMES C4
# ─────────────────────────────────────────────────────────────────────────────
with tab_c4:
    if not st.session_state.result:
        st.markdown('<p style="color:#64748b;text-align:center;padding:40px 0;font-family:DM Mono,monospace">Lance l\'agent dans l\'onglet <strong>▶ Lancer</strong></p>', unsafe_allow_html=True)
    else:
        result = st.session_state.result
        d1, d2, d3 = st.tabs(["Niveau 1 — Contexte","Niveau 2 — Conteneurs","Niveau 3 — Composants"])
        for tab_obj, key, title, desc in [
            (d1,"c4_context",   "Contexte système",       "Utilisateurs, système principal, systèmes externes"),
            (d2,"c4_containers","Conteneurs et services", "API, frontend, base de données et leurs technologies"),
            (d3,"c4_components","Composants internes",    "Modules internes du backend : routers, auth, couche BDD"),
        ]:
            with tab_obj:
                content = result.get(key,"")
                if content:
                    st.caption(desc)
                    st.code(content, language="text")
                    c1, c2 = st.columns([1,1])
                    with c1:
                        st.markdown("[🔗 Visualiser sur mermaid.live](https://mermaid.live)",
                                    help="Copie le code et colle-le sur mermaid.live")
                    with c2:
                        st.download_button(f"⬇ {key}.md",
                            data=f"# {title}\n\n```mermaid\n{content}\n```\n",
                            file_name=f"{key}.md", mime="text/markdown", key=f"dl_{key}")
                else:
                    st.warning("Diagramme non généré.")


# ─────────────────────────────────────────────────────────────────────────────
# ONGLET 4 — DOCUMENTATION
# ─────────────────────────────────────────────────────────────────────────────
with tab_doc:
    if not st.session_state.result:
        st.markdown('<p style="color:#64748b;text-align:center;padding:40px 0;font-family:DM Mono,monospace">Lance l\'agent dans l\'onglet <strong>▶ Lancer</strong></p>', unsafe_allow_html=True)
    else:
        result   = st.session_state.result
        arch_doc = result.get("architecture_doc","")
        ts       = result.get("tech_stack",{})
        dt1, dt2 = st.tabs(["📄 ARCHITECTURE.md","🔧 tech_stack.json"])

        with dt1:
            if arch_doc:
                st.caption(f"{len(arch_doc.split())} mots · généré par Mistral")
                st.markdown(arch_doc)
                st.download_button("⬇ ARCHITECTURE.md", data=arch_doc,
                    file_name="ARCHITECTURE.md", mime="text/markdown")
            else:
                st.warning("Non généré.")

        with dt2:
            if ts:
                st.json(ts)
                st.download_button("⬇ tech_stack.json",
                    data=json.dumps(ts, indent=2, ensure_ascii=False),
                    file_name="tech_stack.json", mime="application/json")


# ─────────────────────────────────────────────────────────────────────────────
# ONGLET 5 — TÉLÉCHARGER
# ─────────────────────────────────────────────────────────────────────────────
with tab_dl:
    if not st.session_state.result:
        st.markdown('<p style="color:#64748b;text-align:center;padding:40px 0;font-family:DM Mono,monospace">Lance l\'agent dans l\'onglet <strong>▶ Lancer</strong></p>', unsafe_allow_html=True)
    else:
        result = st.session_state.result
        bp     = result.get("architect_blueprint",{})
        ts     = result.get("tech_stack",{})

        st.markdown('<p class="section-label">Fichiers générés sur disque</p>', unsafe_allow_html=True)
        out_path = Path(output_dir) / "docs"
        if out_path.exists():
            for f in sorted(out_path.rglob("*")):
                if not f.is_file(): continue
                rel  = f.relative_to(Path(output_dir))
                size = f.stat().st_size
                fc, sc, dc = st.columns([5,1,1])
                fc.markdown(f'<div class="file-row"><span class="file-ok">✓</span>{rel}<span class="file-size">{size:,} o</span></div>', unsafe_allow_html=True)
                dc.download_button("⬇", data=f.read_bytes(),
                    file_name=f.name, key=f"dl_f_{f.name}")
        else:
            st.warning(f"Dossier `{out_path}` non trouvé.")

        st.divider()
        st.markdown('<p class="section-label">Tout en un seul fichier</p>', unsafe_allow_html=True)
        all_out = {
            "project_name": project_name, "architect_blueprint": bp, "tech_stack": ts,
            "c4_context": result.get("c4_context",""), "c4_containers": result.get("c4_containers",""),
            "c4_components": result.get("c4_components",""), "architecture_doc": result.get("architecture_doc",""),
            "reasoning_trace": result.get("reasoning_trace",[]),
        }
        st.download_button("⬇ architect_output.json",
            data=json.dumps(all_out, indent=2, ensure_ascii=False),
            file_name="architect_output.json", mime="application/json")