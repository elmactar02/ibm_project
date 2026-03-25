import streamlit as st
from theme_runtime import inject_theme, get_auth_handler

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
    try:
        response = requests.get("http://localhost:8000/tasks", headers=auth_headers())
        response.raise_for_status()
        return response.json()
    except requests.exceptions.ConnectionError:
        st.error("Backend non disponible — vérifiez que le serveur tourne.")
        return []

def create_task(title, description, priority, status):
    try:
        response = requests.post(
            "http://localhost:8000/tasks",
            headers=auth_headers(),
            json={"title": title, "description": description, "priority": priority, "status": status}
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.ConnectionError:
        st.error("Backend non disponible — vérifiez que le serveur tourne.")
        return None

def update_task(task_id, title, description, priority, status):
    try:
        response = requests.put(
            f"http://localhost:8000/tasks/{task_id}",
            headers=auth_headers(),
            json={"title": title, "description": description, "priority": priority, "status": status}
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.ConnectionError:
        st.error("Backend non disponible — vérifiez que le serveur tourne.")
        return None

def delete_task(task_id):
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

def render_task_list():
    tasks = get_tasks()
    if not tasks:
        st.info("Aucune tâche trouvée.")
        return
    
    st.subheader("Liste des tâches")
    for task in tasks:
        col1, col2, col3 = st.columns([4, 1, 1])
        with col1:
            st.write(f"**{task['title']}**")
            st.write(f"Statut: {task['status']}")
            st.write(f"Priorité: {task['priority']}")
            st.write(f"Description: {task['description']}")
        with col2:
            if st.button("Modifier", key=f"edit_{task['id']}"):
                st.session_state.edit_task = task
        with col3:
            if st.button("Supprimer", key=f"delete_{task['id']}"):
                if delete_task(task['id']):
                    st.success("Tâche supprimée")
                    st.rerun()

def render_task_form(task=None):
    if task:
        title = st.text_input("Titre", task['title'])
        description = st.text_area("Description", task['description'])
        priority = st.selectbox("Priorité", ["low", "medium", "high"], index=["low", "medium", "high"].index(task['priority']))
        status = st.selectbox("Statut", ["todo", "in_progress", "done"], index=["todo", "in_progress", "done"].index(task['status']))
    else:
        title = st.text_input("Titre")
        description = st.text_area("Description")
        priority = st.selectbox("Priorité", ["low", "medium", "high"])
        status = st.selectbox("Statut", ["todo", "in_progress", "done"])
    
    if st.form_submit_button("Soumettre"):
        if task:
            result = update_task(task['id'], title, description, priority, status)
            if result:
                st.success("Tâche mise à jour")
                st.session_state.edit_task = None
                st.rerun()
        else:
            result = create_task(title, description, priority, status)
            if result:
                st.success("Tâche créée")
                st.rerun()

def render_dashboard():
    tasks = get_tasks()
    if not tasks:
        return
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Tâches totales", len(tasks))
    with col2:
        st.metric("En cours", sum(1 for t in tasks if t['status'] == 'in_progress'))
    with col3:
        st.metric("Terminées", sum(1 for t in tasks if t['status'] == 'done'))
    
    st.subheader("Filtres")
    status_filter = st.selectbox("Filtrer par statut", ["all", "todo", "in_progress", "done"])
    priority_filter = st.selectbox("Filtrer par priorité", ["all", "low", "medium", "high"])
    
    filtered_tasks = tasks
    if status_filter != "all":
        filtered_tasks = [t for t in filtered_tasks if t['status'] == status_filter]
    if priority_filter != "all":
        filtered_tasks = [t for t in filtered_tasks if t['priority'] == priority_filter]
    
    st.dataframe(filtered_tasks)

def main():
    if "current_page" not in st.session_state:
        st.session_state.current_page = "dashboard"
    
    pages = [
        ("Tableau de bord", "dashboard"),
        ("Mes tâches", "tasks"),
        ("Créer une tâche", "create_task")
    ]
    
    labels = [p[0] for p in pages]
    values = [p[1] for p in pages]
    
    current_idx = values.index(st.session_state.current_page) if st.session_state.current_page in values else 0
    selected = st.sidebar.radio("Navigation", labels, index=current_idx)
    st.session_state.current_page = values[labels.index(selected)]
    
    if st.session_state.current_page == "dashboard":
        render_dashboard()
    elif st.session_state.current_page == "tasks":
        render_task_list()
    elif st.session_state.current_page == "create_task":
        render_task_form()
    
    if "edit_task" in st.session_state:
        st.subheader("Modifier la tâche")
        render_task_form(st.session_state.edit_task)

if __name__ == "__main__":
    main()