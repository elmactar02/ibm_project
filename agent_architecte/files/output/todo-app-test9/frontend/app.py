import streamlit as st
from theme_runtime import inject_theme, get_auth_handler
import requests
import pandas as pd
from datetime import datetime

# ── Thème client (relu depuis client_config.yaml à chaque refresh) ───────────
_cfg  = inject_theme(st)
_auth = get_auth_handler(_cfg)

# ── Authentification ─────────────────────────────────────────────────────────
_auth.require(st)

def auth_headers() -> dict:
    """Retourne les headers HTTP avec le Bearer token courant."""
    return _auth.headers(st)

# ── Fin du bloc thème / auth — code métier ci-dessous ────────────────────────

# ────────────────────────────────
# CONFIGURATION DE LA NAVIGATION
# ────────────────────────────────
if "current_page" not in st.session_state:
    st.session_state.current_page = "dashboard"

MODULES_INTERNES = ["dashboard", "tasks", "create_task"]

# Création de la sidebar avec navigation
st.sidebar.title("Navigation")
pages = [
    ("Tableau de bord", "dashboard"),
    ("Mes tâches", "tasks"),
    ("Créer une tâche", "create_task")
]

labels = [p[0] for p in pages]
values = [p[1] for p in pages]

# Vérification que la page courante est valide
if st.session_state.current_page not in values:
    st.session_state.current_page = "dashboard"

# Création du menu de navigation
selected_label = st.sidebar.radio("Navigation", labels)
st.session_state.current_page = values[labels.index(selected_label)]

# ────────────────────────────────
# FONCTIONS DE BASE
# ────────────────────────────────
def get_tasks(filters=None):
    """Récupère les tâches avec des filtres optionnels"""
    try:
        params = {}
        if filters and "status" in filters:
            params["status"] = filters["status"]
        if filters and "priority" in filters:
            params["priority"] = filters["priority"]
        
        response = requests.get(
            "http://localhost:8000/tasks",
            headers=auth_headers(),
            params=params
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.ConnectionError:
        st.error("Backend non disponible — vérifiez que le serveur tourne.")
        return []

def get_user_info():
    """Récupère les informations de l'utilisateur connecté"""
    try:
        response = requests.get(
            "http://localhost:8000/me",
            headers=auth_headers()
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.ConnectionError:
        st.error("Backend non disponible — vérifiez que le serveur tourne.")
        return {}

# ────────────────────────────────
# COMPOSANTS PAR MODULE
# ────────────────────────────────
def render_dashboard():
    """Affiche le tableau de bord avec métriques"""
    st.title("Tableau de bord")
    
    # Récupération des données
    tasks = get_tasks()
    if not tasks:
        return
    
    # Calcul des métriques
    total_tasks = len(tasks)
    completed_tasks = sum(1 for t in tasks if t["status"] == "completed")
    pending_tasks = total_tasks - completed_tasks
    
    # Affichage des métriques
    col1, col2, col3 = st.columns(3)
    col1.metric("Tâches totales", total_tasks)
    col2.metric("Tâches terminées", completed_tasks)
    col3.metric("Tâches en attente", pending_tasks)
    
    # Progress bar
    progress = completed_tasks / total_tasks if total_tasks > 0 else 0
    st.progress(progress)
    
    # Détails par statut
    st.subheader("Répartition par statut")
    status_counts = {}
    for t in tasks:
        status_counts[t["status"]] = status_counts.get(t["status"], 0) + 1
    
    for status, count in status_counts.items():
        st.write(f"**{status.capitalize()}** : {count}")

def render_tasks_list():
    """Affiche la liste des tâches avec filtres"""
    st.title("Mes tâches")
    
    # Filtres
    col1, col2 = st.columns(2)
    with col1:
        status_filter = st.selectbox(
            "Filtrer par statut",
            ["Tous", "pending", "in_progress", "completed"],
            key="status_filter"
        )
    with col2:
        priority_filter = st.selectbox(
            "Filtrer par priorité",
            ["Tous", "low", "medium", "high"],
            key="priority_filter"
        )
    
    # Préparation des filtres
    filters = {}
    if status_filter != "Tous":
        filters["status"] = status_filter
    if priority_filter != "Tous":
        filters["priority"] = priority_filter
    
    # Récupération des tâches
    tasks = get_tasks(filters)
    if not tasks:
        return
    
    # Conversion en DataFrame
    df = pd.DataFrame(tasks)
    df["date_created"] = pd.to_datetime(df["date_created"])
    df["due_date"] = pd.to_datetime(df["due_date"])
    
    # Affichage
    st.dataframe(df[["title", "description", "status", "priority", "date_created", "due_date"]])
    
    # Boutons d'action
    st.subheader("Actions")
    if st.button("Créer une nouvelle tâche"):
        st.session_state.current_page = "create_task"

def render_create_task():
    """Affiche le formulaire de création de tâche"""
    st.title("Créer une tâche")
    
    # Formulaire
    with st.form("create_task_form", clear_on_submit=True):
        title = st.text_input("Titre de la tâche", key="title")
        description = st.text_area("Description", key="description")
        priority = st.selectbox("Priorité", ["low", "medium", "high"], key="priority")
        due_date = st.date_input("Date d'échéance", key="due_date")
        
        submitted = st.form_submit_button("Créer")
        
        if submitted:
            task_data = {
                "title": title,
                "description": description,
                "priority": priority,
                "due_date": due_date.isoformat()
            }
            
            try:
                response = requests.post(
                    "http://localhost:8000/tasks",
                    headers=auth_headers(),
                    json=task_data
                )
                response.raise_for_status()
                st.success("Tâche créée avec succès!")
                st.session_state.current_page = "tasks"
            except requests.exceptions.ConnectionError:
                st.error("Backend non disponible — vérifiez que le serveur tourne.")
            except Exception as e:
                st.error(f"Erreur lors de la création: {str(e)}")

# ────────────────────────────────
# GESTION DE LA NAVIGATION
# ────────────────────────────────
if st.session_state.current_page == "dashboard":
    render_dashboard()
elif st.session_state.current_page == "tasks":
    render_tasks_list()
elif st.session_state.current_page == "create_task":
    render_create_task()