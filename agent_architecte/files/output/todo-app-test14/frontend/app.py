import streamlit as st
from theme_runtime import inject_theme, get_auth_handler
import requests

# ── Thème client (relu depuis client_config.yaml à chaque refresh) ───────────
_cfg  = inject_theme(st)
_auth = get_auth_handler(_cfg)

# ── Authentification ─────────────────────────────────────────────────────────
_auth.require(st)

def auth_headers() -> dict:
    """Retourne les headers HTTP avec le Bearer token courant."""
    return _auth.headers(st)

# ── Fin du bloc thème / auth — code métier ci-dessous ────────────────────────

def get_tasks():
    """Récupère la liste des tâches depuis l'API"""
    try:
        response = requests.get(f"{_cfg.base_url}/tasks", headers=auth_headers())
        response.raise_for_status()
        return response.json()
    except requests.exceptions.ConnectionError:
        st.error("Backend non disponible — vérifiez que le serveur tourne.")
        return []

def create_task(task_data):
    """Crée une nouvelle tâche"""
    try:
        response = requests.post(f"{_cfg.base_url}/tasks", headers=auth_headers(), json=task_data)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.ConnectionError:
        st.error("Backend non disponible — vérifiez que le serveur tourne.")
        return None

def update_task(task_id, task_data):
    """Met à jour une tâche existante"""
    try:
        response = requests.put(f"{_cfg.base_url}/tasks/{task_id}", headers=auth_headers(), json=task_data)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.ConnectionError:
        st.error("Backend non disponible — vérifiez que le serveur tourne.")
        return None

def delete_task(task_id):
    """Supprime une tâche"""
    try:
        response = requests.delete(f"{_cfg.base_url}/tasks/{task_id}", headers=auth_headers())
        response.raise_for_status()
        return response.status_code == 204
    except requests.exceptions.ConnectionError:
        st.error("Backend non disponible — vérifiez que le serveur tourne.")
        return False

def render_tasks_page():
    """Affiche la page de gestion des tâches"""
    st.title("Gestion des tâches")
    
    # Formulaire de création/édition
    with st.form("task_form", clear_on_submit=True):
        task_id = st.text_input("ID de la tâche (laisser vide pour créer)", key="task_id")
        title = st.text_input("Titre", key="title")
        description = st.text_area("Description", key="description")
        status = st.selectbox("Statut", ["pending", "in_progress", "completed"], key="status")
        priority = st.number_input("Priorité", min_value=1, max_value=5, value=1, key="priority")
        
        if st.form_submit_button("Soumettre"):
            task_data = {
                "title": title,
                "description": description,
                "status": status,
                "priority": priority
            }
            
            if task_id:
                if update_task(task_id, task_data):
                    st.success("Tâche mise à jour avec succès")
                else:
                    st.error("Erreur lors de la mise à jour de la tâche")
            else:
                new_task = create_task(task_data)
                if new_task:
                    st.success("Tâche créée avec succès")
                else:
                    st.error("Erreur lors de la création de la tâche")
    
    # Liste des tâches
    tasks = get_tasks()
    if tasks:
        st.subheader("Liste des tâches")
        st.dataframe(tasks)
        
        # Boutons de suppression
        for task in tasks:
            if st.button(f"Supprimer {task['id']}", key=f"delete_{task['id']}"):
                if delete_task(task["id"]):
                    st.success(f"Tâche {task['id']} supprimée avec succès")
                else:
                    st.error(f"Erreur lors de la suppression de la tâche {task['id']}")
    else:
        st.info("Aucune tâche trouvée")

def render_dashboard_page():
    """Affiche le tableau de bord"""
    st.title("Tableau de bord")
    
    tasks = get_tasks()
    if not tasks:
        st.info("Aucune tâche trouvée")
        return
    
    # Calcul des métriques
    total_tasks = len(tasks)
    completed_tasks = sum(1 for t in tasks if t["status"] == "completed")
    pending_tasks = sum(1 for t in tasks if t["status"] == "pending")
    in_progress_tasks = sum(1 for t in tasks if t["status"] == "in_progress")
    
    # Affichage des métriques
    col1, col2, col3 = st.columns(3)
    col1.metric("Tâches totales", total_tasks)
    col2.metric("Tâches en cours", in_progress_tasks)
    col3.metric("Tâches terminées", completed_tasks)
    
    # Affichage des détails
    st.subheader("Détails des tâches")
    st.dataframe(tasks)

def main():
    """Fonction principale de l'application"""
    if "current_page" not in st.session_state:
        st.session_state.current_page = "dashboard"
    
    # Navigation
    pages = [
        ("Tableau de bord", "dashboard"),
        ("Gestion des tâches", "tasks"),
        ("CI/CD", "ci_cd")
    ]
    
    labels = [p[0] for p in pages]
    values = [p[1] for p in pages]
    
    current_idx = values.index(st.session_state.current_page) if st.session_state.current_page in values else 0
    selected = st.sidebar.radio("Navigation", labels, index=current_idx)
    st.session_state.current_page = values[labels.index(selected)]
    
    # Affichage de la page sélectionnée
    if st.session_state.current_page == "dashboard":
        render_dashboard_page()
    elif st.session_state.current_page == "tasks":
        render_tasks_page()
    elif st.session_state.current_page == "ci_cd":
        st.title("CI/CD")
        st.info("Module CI/CD - à implémenter")

if __name__ == "__main__":
    main()