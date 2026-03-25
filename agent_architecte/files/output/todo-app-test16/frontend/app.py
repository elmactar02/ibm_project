import streamlit as st
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

# ──────────────────────── CONFIGURATION ────────────────────────
BASE_URL = "http://localhost:8000"

# ──────────────────────── FONCTIONS API ────────────────────────
def fetch_tasks(filters=None):
    """Récupère les tâches avec filtres optionnels"""
    try:
        params = {}
        if filters:
            params.update(filters)
        response = requests.get(f"{BASE_URL}/tasks", headers=auth_headers(), params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.ConnectionError:
        st.error("Backend non disponible — vérifiez que le serveur tourne.")
        return []

def create_task(task_data):
    """Crée une nouvelle tâche"""
    try:
        response = requests.post(f"{BASE_URL}/tasks", headers=auth_headers(), json=task_data)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Erreur création tâche: {str(e)}")
        return None

def update_task(task_id, task_data):
    """Met à jour une tâche existante"""
    try:
        response = requests.put(f"{BASE_URL}/tasks/{task_id}", headers=auth_headers(), json=task_data)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Erreur mise à jour tâche: {str(e)}")
        return None

def delete_task(task_id):
    """Supprime une tâche"""
    try:
        response = requests.delete(f"{BASE_URL}/tasks/{task_id}", headers=auth_headers())
        response.raise_for_status()
        return True
    except requests.exceptions.RequestException as e:
        st.error(f"Erreur suppression tâche: {str(e)}")
        return False

# ──────────────────────── LOGIQUE PRINCIPALE ────────────────────────
def main():
    # Initialisation de la session
    if "current_page" not in st.session_state:
        st.session_state.current_page = "dashboard"
    
    # Configuration de la sidebar
    st.sidebar.title("Navigation")
    pages = [("Tableau de bord", "dashboard"), ("Mes tâches", "tasks")]
    labels = [p[0] for p in pages]
    values = [p[1] for p in pages]
    
    current_idx = values.index(st.session_state.current_page) if st.session_state.current_page in values else 0
    selected = st.sidebar.radio("Navigation", labels, index=current_idx)
    st.session_state.current_page = values[labels.index(selected)]
    
    # Gestion des pages
    if st.session_state.current_page == "dashboard":
        dashboard_page()
    elif st.session_state.current_page == "tasks":
        tasks_page()

# ──────────────────────── PAGE DASHBOARD ────────────────────────
def dashboard_page():
    st.title("📊 Tableau de bord")
    
    # Récupération des données
    tasks = fetch_tasks()
    if not tasks:
        return
    
    # Calcul des métriques
    total_tasks = len(tasks)
    completed = sum(1 for t in tasks if t["status"] == "completed")
    in_progress = sum(1 for t in tasks if t["status"] == "in_progress")
    pending = sum(1 for t in tasks if t["status"] == "pending")
    
    # Affichage des métriques
    col1, col2, col3 = st.columns(3)
    col1.metric("Total tâches", total_tasks)
    col2.metric("En cours", in_progress)
    col3.metric("Terminées", completed)
    
    # Progress bar
    progress = (completed / total_tasks) * 100 if total_tasks > 0 else 0
    st.progress(progress / 100)
    st.caption(f"{progress:.1f}% des tâches terminées")
    
    # Affichage des tâches récentes
    st.subheader("Dernières tâches")
    recent_tasks = sorted(tasks, key=lambda x: x["created_at"], reverse=True)[:5]
    for task in recent_tasks:
        st.markdown(f"**{task['title']}** - {task['status'].capitalize()}")
        st.caption(f"Créé le {datetime.fromisoformat(task['created_at']).strftime('%d/%m/%Y')}")
        st.write("---")

# ──────────────────────── PAGE TÂCHES ────────────────────────
def tasks_page():
    st.title("📋 Mes tâches")
    
    # Filtres
    st.markdown("### Filtres")
    col1, col2 = st.columns(2)
    
    with col1:
        status_filter = st.selectbox(
            "Statut",
            ["Tous", "pending", "in_progress", "completed"],
            key="status_filter"
        )
    
    with col2:
        priority_filter = st.selectbox(
            "Priorité",
            ["Toutes", "low", "medium", "high"],
            key="priority_filter"
        )
    
    # Préparation des filtres
    filters = {}
    if status_filter != "Tous":
        filters["status"] = status_filter
    if priority_filter != "Toutes":
        filters["priority"] = priority_filter
    
    # Récupération des tâches
    tasks = fetch_tasks(filters)
    if not tasks:
        return
    
    # Conversion en DataFrame
    df = pd.DataFrame(tasks)
    df["created_at"] = pd.to_datetime(df["created_at"]).dt.strftime("%d/%m/%Y")
    df["updated_at"] = pd.to_datetime(df["updated_at"]).dt.strftime("%d/%m/%Y")
    
    # Affichage des tâches
    st.markdown("### Liste des tâches")
    st.dataframe(df[["title", "description", "priority", "status", "created_at"]])
    
    # Formulaire de création de tâche
    st.markdown("### Créer une nouvelle tâche")
    with st.form("create_task_form", clear_on_submit=True):
        title = st.text_input("Titre", key="new_title")
        description = st.text_area("Description", key="new_description")
        priority = st.selectbox("Priorité", ["low", "medium", "high"], key="new_priority")
        status = st.selectbox("Statut", ["pending", "in_progress", "completed"], key="new_status")
        
        submitted = st.form_submit_button("Créer")
        if submitted:
            task_data = {
                "title": title,
                "description": description,
                "priority": priority,
                "status": status
            }
            result = create_task(task_data)
            if result:
                st.success("Tâche créée avec succès!")
                st.experimental_rerun()
    
    # Formulaire de modification de tâche
    st.markdown("### Modifier une tâche")
    if tasks:
        task_ids = [t["id"] for t in tasks]
        selected_id = st.selectbox("Sélectionnez une tâche", task_ids, key="edit_task_id")
        
        selected_task = next(t for t in tasks if t["id"] == selected_id)
        
        with st.form("edit_task_form", clear_on_submit=True):
            title = st.text_input("Titre", selected_task["title"], key="edit_title")
            description = st.text_area("Description", selected_task["description"], key="edit_description")
            priority = st.selectbox("Priorité", ["low", "medium", "high"], index=["low", "medium", "high"].index(selected_task["priority"]), key="edit_priority")
            status = st.selectbox("Statut", ["pending", "in_progress", "completed"], index=["pending", "in_progress", "completed"].index(selected_task["status"]), key="edit_status")
            
            submitted = st.form_submit_button("Mettre à jour")
            if submitted:
                task_data = {
                    "title": title,
                    "description": description,
                    "priority": priority,
                    "status": status
                }
                result = update_task(selected_id, task_data)
                if result:
                    st.success("Tâche mise à jour avec succès!")
                    st.experimental_rerun()
    
    # Suppression de tâche
    st.markdown("### Supprimer une tâche")
    if tasks:
        task_ids = [t["id"] for t in tasks]
        selected_id = st.selectbox("Sélectionnez une tâche", task_ids, key="delete_task_id")
        
        if st.button("Supprimer"):
            if st.checkbox("Confirmez la suppression"):
                if delete_task(selected_id):
                    st.success("Tâche supprimée avec succès!")
                    st.experimental_rerun()

# ──────────────────────── LANCEMENT DE L'APP ────────────────────────
if __name__ == "__main__":
    main()