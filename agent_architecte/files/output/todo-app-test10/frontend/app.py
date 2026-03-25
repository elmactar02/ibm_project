import streamlit as st
import requests
from datetime import datetime
from typing import Optional, Dict, List

# ── Thème client (relu depuis client_config.yaml à chaque refresh) ───────────
_cfg  = inject_theme(st)
_auth = get_auth_handler(_cfg)

# ── Authentification ─────────────────────────────────────────────────────────
_auth.require(st)

def auth_headers() -> dict:
    """Retourne les headers HTTP avec le Bearer token courant."""
    return _auth.headers(st)

# ── Fin du bloc thème / auth — code métier ci-dessous ────────────────────────

def get_tasks(filters: Optional[Dict] = None) -> List[Dict]:
    """Récupère la liste des tâches avec filtres optionnels"""
    try:
        params = filters or {}
        response = requests.get(
            "http://localhost:8000/tasks",
            headers=auth_headers(),
            params=params
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error("Erreur lors de la récupération des tâches")
        return []

def create_task(data: Dict) -> Dict:
    """Crée une nouvelle tâche"""
    try:
        response = requests.post(
            "http://localhost:8000/tasks",
            headers=auth_headers(),
            json=data
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error("Erreur lors de la création de la tâche")
        return {}

def update_task(task_id: int, data: Dict) -> Dict:
    """Met à jour une tâche existante"""
    try:
        response = requests.put(
            f"http://localhost:8000/tasks/{task_id}",
            headers=auth_headers(),
            json=data
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error("Erreur lors de la mise à jour de la tâche")
        return {}

def delete_task(task_id: int) -> bool:
    """Supprime une tâche"""
    try:
        response = requests.delete(
            f"http://localhost:8000/tasks/{task_id}",
            headers=auth_headers()
        )
        response.raise_for_status()
        return True
    except requests.exceptions.RequestException as e:
        st.error("Erreur lors de la suppression de la tâche")
        return False

def task_form(task_data: Optional[Dict] = None) -> None:
    """Formulaire de création/mise à jour de tâche"""
    with st.form("task_form", clear_on_submit=True):
        task_id = task_data.get("id", 0) if task_data else 0
        
        title = st.text_input(
            "Titre",
            value=task_data.get("title", "") if task_data else ""
        )
        
        description = st.text_area(
            "Description",
            value=task_data.get("description", "") if task_data else ""
        )
        
        status = st.selectbox(
            "Statut",
            options=["pending", "in_progress", "completed"],
            index=["pending", "in_progress", "completed"].index(
                task_data.get("status", "pending") if task_data else "pending"
            )
        )
        
        priority = st.selectbox(
            "Priorité",
            options=["low", "medium", "high"],
            index=["low", "medium", "high"].index(
                task_data.get("priority", "medium") if task_data else "medium"
            )
        )
        
        due_date = st.date_input(
            "Date d'échéance",
            value=datetime.strptime(
                task_data.get("due_date", datetime.now().strftime("%Y-%m-%d")) if task_data else datetime.now().strftime("%Y-%m-%d"),
                "%Y-%m-%d"
            ).date()
        )
        
        submitted = st.form_submit_button("Soumettre")
        
        if submitted:
            payload = {
                "title": title,
                "description": description,
                "status": status,
                "priority": priority,
                "due_date": due_date.strftime("%Y-%m-%d")
            }
            
            if task_id:
                result = update_task(task_id, payload)
                if result:
                    st.success("Tâche mise à jour avec succès")
                    st.session_state.current_page = "task_management"
                    st.rerun()
                else:
                    st.error("Échec de la mise à jour")
            else:
                result = create_task(payload)
                if result:
                    st.success("Tâche créée avec succès")
                    st.session_state.current_page = "task_management"
                    st.rerun()
                else:
                    st.error("Échec de la création")

def task_list_view() -> None:
    """Affiche la liste des tâches avec filtres et actions"""
    st.title("Gestion des Tâches")
    
    # Filtres
    col1, col2, col3 = st.columns(3)
    with col1:
        status_filter = st.selectbox(
            "Filtrer par statut",
            options=["Tous", "pending", "in_progress", "completed"],
            key="status_filter"
        )
    with col2:
        priority_filter = st.selectbox(
            "Filtrer par priorité",
            options=["Toutes", "low", "medium", "high"],
            key="priority_filter"
        )
    with col3:
        search_query = st.text_input(
            "Rechercher par titre/description",
            key="search_filter"
        )
    
    # Préparer les paramètres de filtre
    filters = {}
    if status_filter != "Tous":
        filters["status"] = status_filter
    if priority_filter != "Toutes":
        filters["priority"] = priority_filter
    if search_query:
        filters["search"] = search_query
    
    tasks = get_tasks(filters)
    
    if not tasks:
        st.info("Aucune tâche trouvée")
        return
    
    # Affichage des tâches
    for task in tasks:
        with st.expander(f"{task['title']} ({task['status'].capitalize()})", expanded=False):
            st.markdown(f"**Description:** {task['description']}")
            st.markdown(f"**Priorité:** {task['priority'].capitalize()}")
            st.markdown(f"**Échéance:** {task['due_date']}")
            
            col1, col2, col3 = st.columns([1, 1, 1])
            with col1:
                if st.button("Modifier", key=f"edit_{task['id']}"):
                    st.session_state.edit_task = task
                    st.session_state.current_page = "task_form"
                    st.rerun()
            with col2:
                if st.button("Supprimer", key=f"delete_{task['id']}"):
                    if st.warning("Voulez-vous vraiment supprimer cette tâche ?"):
                        if delete_task(task["id"]):
                            st.success("Tâche supprimée")
                            st.rerun()
                        else:
                            st.error("Échec de la suppression")
    
    # Bouton pour créer une nouvelle tâche
    if st.button("Nouvelle Tâche", key="new_task"):
        st.session_state.current_page = "task_form"
        st.rerun()

def main():
    # Initialisation de la session
    if "current_page" not in st.session_state:
        st.session_state.current_page = "task_management"
    
    # Navigation sidebar
    st.sidebar.title("Navigation")
    pages = [
        ("Gestion des Tâches", "task_management"),
        ("Créer une Tâche", "task_form"),
        ("Interface Utilisateur", "user_interface"),
        ("CI/CD", "ci_cd")
    ]
    
    labels = [p[0] for p in pages]
    values = [p[1] for p in pages]
    
    current_idx = values.index(st.session_state.current_page) if st.session_state.current_page in values else 0
    selected = st.sidebar.radio("Navigation", labels, index=current_idx)
    st.session_state.current_page = values[labels.index(selected)]
    
    # Contenu principal
    if st.session_state.current_page == "task_management":
        task_list_view()
    elif st.session_state.current_page == "task_form":
        task_form(st.session_state.get("edit_task", None))
    elif st.session_state.current_page == "user_interface":
        st.title("Interface Utilisateur")
        st.info("Cette section est en cours de développement")
    elif st.session_state.current_page == "ci_cd":
        st.title("Pipeline CI/CD")
        st.info("Cette section est en cours de développement")

if __name__ == "__main__":
    main()