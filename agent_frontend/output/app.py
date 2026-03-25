from theme_runtime import inject_theme, get_auth_handler, auth_headers
import streamlit as st
import requests
import pandas as pd
from datetime import datetime

# ── Thème client (relu depuis client_config.yaml à chaque refresh) ───────────
_cfg  = inject_theme(st)
_auth = get_auth_handler(_cfg)

# ── Authentification ─────────────────────────────────────────────────────────
_auth.require(st)

# ── Initialisation session_state ────────────────────────────────────────────
if "status_filter" not in st.session_state:
    st.session_state.status_filter = ""
if "priority_filter" not in st.session_state:
    st.session_state.priority_filter = ""
if "selected_task_id" not in st.session_state:
    st.session_state.selected_task_id = None
if "page" not in st.session_state:
    st.session_state.page = 1
if "per_page" not in st.session_state:
    st.session_state.per_page = 10

# ── Fonctions utilitaires ───────────────────────────────────────────────────
def fetch_tasks():
    params = {
        "status": st.session_state.status_filter,
        "priority": st.session_state.priority_filter,
        "page": st.session_state.page,
        "per_page": st.session_state.per_page
    }
    try:
        r = requests.get("http://localhost:8000/api/v1/tasks", 
                         params=params, headers=auth_headers())
        r.raise_for_status()
        return r.json()
    except requests.exceptions.ConnectionError:
        st.error("Backend non disponible — vérifiez que le serveur tourne.")
        return {"tasks": [], "total": 0, "page": 1, "per_page": 10}

def create_task(title, description, priority):
    payload = {
        "title": title,
        "description": description,
        "priority": priority
    }
    try:
        r = requests.post("http://localhost:8000/api/v1/tasks", 
                         json=payload, headers=auth_headers())
        r.raise_for_status()
        return r.json()
    except requests.exceptions.ConnectionError:
        st.error("Backend non disponible — vérifiez que le serveur tourne.")
        return None

def update_task_status(task_id, status):
    payload = {"status": status}
    try:
        r = requests.patch(f"http://localhost:8000/api/v1/tasks/{task_id}/status", 
                          json=payload, headers=auth_headers())
        r.raise_for_status()
        return r.json()
    except requests.exceptions.ConnectionError:
        st.error("Backend non disponible — vérifiez que le serveur tourne.")
        return None

def delete_task(task_id):
    try:
        r = requests.delete(f"http://localhost:8000/api/v1/tasks/{task_id}", 
                           headers=auth_headers())
        r.raise_for_status()
        return r.status_code == 204
    except requests.exceptions.ConnectionError:
        st.error("Backend non disponible — vérifiez que le serveur tourne.")
        return False

def get_task_details(task_id):
    try:
        r = requests.get(f"http://localhost:8000/api/v1/tasks/{task_id}", 
                       headers=auth_headers())
        r.raise_for_status()
        return r.json()
    except requests.exceptions.ConnectionError:
        st.error("Backend non disponible — vérifiez que le serveur tourne.")
        return None

# ── Layout principal ────────────────────────────────────────────────────────
def main():
    # Navigation sidebar
    st.sidebar.title("Navigation")
    view = st.sidebar.radio("Vue", ["Dashboard", "Créer une tâche", "Détails tâche"])
    
    # Filtres sidebar
    st.sidebar.markdown("### Filtres")
    st.session_state.status_filter = st.sidebar.selectbox(
        "Statut", 
        ["", "todo", "in_progress", "done"],
        index=0
    )
    st.session_state.priority_filter = st.sidebar.selectbox(
        "Priorité", 
        ["", "low", "medium", "high"],
        index=0
    )
    
    # Pagination
    col1, col2 = st.sidebar.columns(2)
    with col1:
        st.session_state.page = st.number_input("Page", min_value=1, value=st.session_state.page)
    with col2:
        st.session_state.per_page = st.number_input("Tâches par page", min_value=1, max_value=100, value=st.session_state.per_page)

    # Vue Dashboard
    if view == "Dashboard":
        st.title("Tableau de bord des tâches")
        
        # Boutons d'action globales
        if st.button("Actualiser", key="refresh_tasks"):
            st.rerun()
        
        # Affichage des tâches
        tasks_data = fetch_tasks()
        if tasks_data["tasks"]:
            df = pd.DataFrame(tasks_data["tasks"])
            df["created_at"] = pd.to_datetime(df["created_at"]).dt.strftime("%d/%m/%Y %H:%M")
            st.dataframe(df)
            
            # Pagination
            st.markdown(f"Page {tasks_data['page']} / {int(tasks_data['total'] / tasks_data['per_page']) + 1}")
            
            # Boutons de navigation
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("Page précédente", disabled=st.session_state.page <= 1):
                    st.session_state.page -= 1
                    st.rerun()
            with col2:
                st.markdown(f"Affichage {tasks_data['page'] * tasks_data['per_page'] - tasks_data['per_page'] + 1} à {min(tasks_data['page'] * tasks_data['per_page'], tasks_data['total'])} sur {tasks_data['total']} tâches")
            with col3:
                if st.button("Page suivante", disabled=st.session_state.page * st.session_state.per_page >= tasks_data['total']):
                    st.session_state.page += 1
                    st.rerun()
        else:
            st.info("Aucune tâche trouvée avec ces critères")

    # Vue Création tâche
    elif view == "Créer une tâche":
        st.title("Créer une nouvelle tâche")
        
        with st.form("create_task_form"):
            title = st.text_input("Titre", max_chars=200)
            description = st.text_area("Description", max_chars=1000)
            priority = st.selectbox("Priorité", ["low", "medium", "high"])
            
            submitted = st.form_submit_button("Créer la tâche")
            
            if submitted:
                if not title.strip():
                    st.error("Le titre est obligatoire")
                else:
                    new_task = create_task(title, description, priority)
                    if new_task:
                        st.success("Tâche créée avec succès !")
                        st.json(new_task)
                        st.session_state.page = 1
                        st.rerun()
                    else:
                        st.error("Erreur lors de la création de la tâche")

    # Vue Détails tâche
    elif view == "Détails tâche":
        st.title("Détails d'une tâche")
        
        if st.session_state.selected_task_id:
            task = get_task_details(st.session_state.selected_task_id)
            if task:
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(f"**Titre** : {task['title']}")
                    st.markdown(f"**Description** : {task['description']}")
                    st.markdown(f"**Statut** : {task['status'].capitalize()}")
                    st.markdown(f"**Priorité** : {task['priority'].capitalize()}")
                with col2:
                    st.markdown(f"**Créé le** : {datetime.fromisoformat(task['created_at']).strftime('%d/%m/%Y %H:%M')}")
                    st.markdown(f"**ID** : {task['id']}")
                
                # Boutons d'action
                new_status = st.selectbox("Nouveau statut", ["todo", "in_progress", "done"], 
                                          index=["todo", "in_progress", "done"].index(task['status']))
                if st.button("Mettre à jour le statut"):
                    if update_task_status(task['id'], new_status):
                        st.success("Statut mis à jour")
                        st.rerun()
                
                if st.button("Supprimer cette tâche", type="primary", use_container_width=True):
                    if delete_task(task['id']):
                        st.success("Tâche supprimée")
                        st.session_state.selected_task_id = None
                        st.session_state.page = 1
                        st.rerun()
            else:
                st.error("Tâche non trouvée")
        else:
            st.warning("Veuillez sélectionner une tâche dans le tableau de bord")

    # Gestion des actions sur les tâches du tableau
    if view == "Dashboard" and "tasks" in locals() and tasks_data["tasks"]:
        for task in tasks_data["tasks"]:
            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                st.markdown(f"**{task['title']}**")
                st.markdown(f"{task['description']}")
            with col2:
                if st.button("Détails", key=f"details_{task['id']}"):
                    st.session_state.selected_task_id = task['id']
                    st.rerun()
            with col3:
                if st.button("Supprimer", key=f"delete_{task['id']}"):
                    if delete_task(task['id']):
                        st.success("Tâche supprimée")
                        st.rerun()

if __name__ == "__main__":
    main()