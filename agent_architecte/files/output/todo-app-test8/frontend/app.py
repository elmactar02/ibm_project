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

# ────────────────────────────────────────────────────────────────────────────
# ─── CONFIGURATION GLOBALE ────────────────────────────────────────────────────
# ────────────────────────────────────────────────────────────────────────────

if "current_page" not in st.session_state:
    st.session_state.current_page = "tasks"

# ────────────────────────────────────────────────────────────────────────────
# ─── FONCTIONS DE BASE ──────────────────────────────────────────────────────
# ────────────────────────────────────────────────────────────────────────────

def fetch_tasks(filters=None):
    """Récupère la liste des tâches avec filtres"""
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

def create_task(data):
    """Crée une nouvelle tâche"""
    try:
        response = requests.post(
            "http://localhost:8000/tasks",
            headers=auth_headers(),
            json=data
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.ConnectionError:
        st.error("Backend non disponible — vérifiez que le serveur tourne.")
        return None

def update_task(task_id, data):
    """Met à jour une tâche existante"""
    try:
        response = requests.put(
            f"http://localhost:8000/tasks/{task_id}",
            headers=auth_headers(),
            json=data
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.ConnectionError:
        st.error("Backend non disponible — vérifiez que le serveur tourne.")
        return None

def delete_task(task_id):
    """Supprime une tâche"""
    try:
        response = requests.delete(
            f"http://localhost:8000/tasks/{task_id}",
            headers=auth_headers()
        )
        response.raise_for_status()
        return True
    except requests.exceptions.ConnectionError:
        st.error("Backend non disponible — vérifiez que le serveur tourne.")
        return False

def get_task_details(task_id):
    """Récupère les détails d'une tâche"""
    try:
        response = requests.get(
            f"http://localhost:8000/tasks/{task_id}",
            headers=auth_headers()
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.ConnectionError:
        st.error("Backend non disponible — vérifiez que le serveur tourne.")
        return None

# ────────────────────────────────────────────────────────────────────────────
# ─── COMPOSANTS UI ──────────────────────────────────────────────────────────
# ────────────────────────────────────────────────────────────────────────────

def display_task_list(tasks):
    """Affiche la liste des tâches sous forme de tableau"""
    if not tasks:
        st.info("Aucune tâche trouvée")
        return
    
    df = pd.DataFrame(tasks)
    df["created_at"] = pd.to_datetime(df["created_at"]).dt.strftime("%d/%m/%Y %H:%M")
    df["updated_at"] = pd.to_datetime(df["updated_at"]).dt.strftime("%d/%m/%Y %H:%M")
    
    st.dataframe(df[["id", "title", "status", "priority", "created_at", "updated_at"]])

def display_task_form(task=None):
    """Affiche un formulaire pour créer ou modifier une tâche"""
    with st.form("task_form"):
        task_id = st.text_input("ID (lecture seule)", value=task["id"] if task else "", disabled=True)
        title = st.text_input("Titre", value=task["title"] if task else "")
        description = st.text_area("Description", value=task["description"] if task else "")
        
        col1, col2 = st.columns(2)
        with col1:
            status = st.selectbox(
                "Statut",
                options=["TODO", "IN_PROGRESS", "DONE"],
                index=["TODO", "IN_PROGRESS", "DONE"].index(task["status"]) if task else 0
            )
        with col2:
            priority = st.selectbox(
                "Priorité",
                options=["LOW", "MEDIUM", "HIGH"],
                index=["LOW", "MEDIUM", "HIGH"].index(task["priority"]) if task else 0
            )
        
        submitted = st.form_submit_button("Sauvegarder")
        
        if submitted:
            data = {
                "title": title,
                "description": description,
                "status": status,
                "priority": priority
            }
            
            if task:
                result = update_task(task["id"], data)
                if result:
                    st.success("Tâche mise à jour avec succès")
            else:
                result = create_task(data)
                if result:
                    st.success("Tâche créée avec succès")
                    st.session_state.current_page = "tasks"

def display_task_details(task_id):
    """Affiche les détails d'une tâche spécifique"""
    task = get_task_details(task_id)
    if not task:
        st.error("Tâche non trouvée")
        return
    
    st.markdown(f"### Détails de la tâche #{task['id']}")
    st.markdown(f"**Titre** : {task['title']}")
    st.markdown(f"**Description** : {task['description']}")
    st.markdown(f"**Statut** : {task['status']}")
    st.markdown(f"**Priorité** : {task['priority']}")
    st.markdown(f"**Créé le** : {datetime.fromisoformat(task['created_at']).strftime('%d/%m/%Y %H:%M')}")
    st.markdown(f"**Mis à jour le** : {datetime.fromisoformat(task['updated_at']).strftime('%d/%m/%Y %H:%M')}")

# ────────────────────────────────────────────────────────────────────────────
# ─── MODULES DE L'APPLICATION ─────────────────────────────────────────────────
# ────────────────────────────────────────────────────────────────────────────

def render_tasks_module():
    """Module principal pour la gestion des tâches"""
    st.title("Gestion des tâches")
    
    # Filtres
    col1, col2 = st.columns(2)
    with col1:
        status_filter = st.selectbox("Filtrer par statut", ["Tous", "TODO", "IN_PROGRESS", "DONE"])
    with col2:
        priority_filter = st.selectbox("Filtrer par priorité", ["Tous", "LOW", "MEDIUM", "HIGH"])
    
    filters = {}
    if status_filter != "Tous":
        filters["status"] = status_filter
    if priority_filter != "Tous":
        filters["priority"] = priority_filter
    
    tasks = fetch_tasks(filters)
    
    # Affichage de la liste
    display_task_list(tasks)
    
    # Création de tâche
    st.markdown("---")
    st.subheader("Créer une nouvelle tâche")
    display_task_form()
    
    # Détails d'une tâche
    if tasks:
        st.markdown("---")
        st.subheader("Détails d'une tâche")
        task_id = st.selectbox(
            "Sélectionner une tâche",
            options=[t["id"] for t in tasks],
            format_func=lambda x: f"Tâche #{x}"
        )
        
        if st.button("Voir les détails"):
            display_task_details(task_id)
            
        if st.button("Supprimer la tâche sélectionnée"):
            if delete_task(task_id):
                st.success("Tâche supprimée avec succès")
                st.session_state.current_page = "tasks"

def render_dashboard_module():
    """Module d'analyse des tâches"""
    st.title("Tableau de bord")
    
    tasks = fetch_tasks()
    if not tasks:
        st.info("Aucune tâche trouvée")
        return
    
    # Calcul des métriques
    df = pd.DataFrame(tasks)
    total_tasks = len(df)
    completed_tasks = len(df[df["status"] == "DONE"])
    pending_tasks = total_tasks - completed_tasks
    
    # Distribution par statut
    status_counts = df["status"].value_counts().to_dict()
    
    # Distribution par priorité
    priority_counts = df["priority"].value_counts().to_dict()
    
    # Affichage des métriques
    col1, col2, col3 = st.columns(3)
    col1.metric("Total tâches", total_tasks)
    col2.metric("Tâches terminées", completed_tasks)
    col3.metric("Tâches en cours", pending_tasks)
    
    st.markdown("---")
    st.subheader("Distribution par statut")
    st.bar_chart(status_counts)
    
    st.markdown("---")
    st.subheader("Distribution par priorité")
    st.bar_chart(priority_counts)

# ────────────────────────────────────────────────────────────────────────────
# ─── NAVIGATION ─────────────────────────────────────────────────────────────
# ────────────────────────────────────────────────────────────────────────────

MODULES = {
    "tasks": "Gestion des tâches",
    "dashboard": "Tableau de bord"
}

# Navigation sidebar
st.sidebar.title("Navigation")
selected = st.sidebar.radio(
    "Modules",
    options=[v for k, v in MODULES.items()],
    index=0
)

# Mise à jour de l'état de navigation
for module_name, module_label in MODULES.items():
    if selected == module_label:
        st.session_state.current_page = module_name

# ────────────────────────────────────────────────────────────────────────────
# ─── RENDU DE LA PAGE COURANTE ────────────────────────────────────────────────
# ────────────────────────────────────────────────────────────────────────────

if st.session_state.current_page == "tasks":
    render_tasks_module()
elif st.session_state.current_page == "dashboard":
    render_dashboard_module()