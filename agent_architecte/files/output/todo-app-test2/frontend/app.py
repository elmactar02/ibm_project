import streamlit as st
import requests
from theme_runtime import inject_theme, get_auth_handler

_cfg  = inject_theme(st)
_auth = get_auth_handler(_cfg)

def auth_headers() -> dict:
    return _auth.headers(st)

# ── Fin du bloc thème / auth — code métier ci-dessous ────────────────────────

if "current_page" not in st.session_state:
    st.session_state.current_page = "tasks"

pages = [("Mes tâches", "tasks"), ("Tableau de bord", "dashboard")]
labels = [p[0] for p in pages]
values = [p[1] for p in pages]

current_idx = values.index(st.session_state.current_page) if st.session_state.current_page in values else 0
selected = st.sidebar.radio("Navigation", labels, index=current_idx)
st.session_state.current_page = values[labels.index(selected)]

def tasks_page():
    try:
        response = requests.get("http://localhost:8000/tasks", headers=auth_headers())
        response.raise_for_status()
        tasks = response.json()
    except requests.exceptions.ConnectionError:
        st.error("Backend non disponible — vérifiez que le serveur tourne.")
        return
    except requests.exceptions.RequestException as e:
        st.error(f"Erreur lors de la récupération des tâches: {e}")
        return

    st.header("Gestion des tâches")

    with st.form("create_task_form"):
        title = st.text_input("Titre")
        description = st.text_area("Description")
        status = st.selectbox("Statut", ["pending", "in_progress", "completed"])
        priority = st.selectbox("Priorité", ["low", "medium", "high"])
        submitted = st.form_submit_button("Créer une tâche")
        if submitted:
            data = {
                "title": title,
                "description": description,
                "status": status,
                "priority": priority
            }
            try:
                response = requests.post("http://localhost:8000/tasks", headers=auth_headers(), json=data)
                response.raise_for_status()
                st.success("Tâche créée avec succès!")
            except requests.exceptions.RequestException as e:
                st.error(f"Erreur lors de la création de la tâche: {e}")

    if tasks:
        st.dataframe(tasks)
        for task in tasks:
            col1, col2 = st.columns([3, 1])
            with col1:
                st.write(f"{task['title']} - {task['status']} - {task['priority']}")
            with col2:
                if st.button("Modifier", key=f"edit_{task['id']}"):
                    with st.form(f"edit_form_{task['id']}"):
                        new_title = st.text_input("Nouveau titre", value=task['title'])
                        new_status = st.selectbox("Nouveau statut", ["pending", "in_progress", "completed"], index=["pending", "in_progress", "completed"].index(task['status']))
                        new_priority = st.selectbox("Nouvelle priorité", ["low", "medium", "high"], index=["low", "medium", "high"].index(task['priority']))
                        submitted = st.form_submit_button("Mettre à jour")
                        if submitted:
                            data = {
                                "title": new_title,
                                "status": new_status,
                                "priority": new_priority
                            }
                            try:
                                response = requests.put(f"http://localhost:8000/tasks/{task['id']}", headers=auth_headers(), json=data)
                                response.raise_for_status()
                                st.success("Tâche mise à jour!")
                            except requests.exceptions.RequestException as e:
                                st.error(f"Erreur lors de la mise à jour: {e}")
                if st.button("Supprimer", key=f"delete_{task['id']}"):
                    if st.checkbox("Êtes-vous sûr de vouloir supprimer cette tâche?"):
                        try:
                            response = requests.delete(f"http://localhost:8000/tasks/{task['id']}", headers=auth_headers())
                            response.raise_for_status()
                            st.success("Tâche supprimée!")
                        except requests.exceptions.RequestException as e:
                            st.error(f"Erreur lors de la suppression: {e}")
    else:
        st.info("Aucune tâche trouvée.")

def dashboard_page():
    try:
        response = requests.get("http://localhost:8000/tasks", headers=auth_headers())
        response.raise_for_status()
        tasks = response.json()
    except requests.exceptions.ConnectionError:
        st.error("Backend non disponible — vérifiez que le serveur tourne.")
        return
    except requests.exceptions.RequestException as e:
        st.error(f"Erreur lors de la récupération des tâches: {e}")
        return

    st.header("Tableau de bord")

    status_counts = {}
    for task in tasks:
        status = task['status']
        status_counts[status] = status_counts.get(status, 0) + 1

    total_tasks = len(tasks)
    completed_tasks = status_counts.get("completed", 0)
    completion_rate = completed_tasks / total_tasks if total_tasks > 0 else 0

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total des tâches", total_tasks)
    col2.metric("Tâches en attente", status_counts.get("pending", 0))
    col3.metric("Tâches en cours", status_counts.get("in_progress", 0))
    col4.metric("Tâches terminées", completed_tasks)

    st.progress(completion_rate)

    priority_filter = st.selectbox("Filtrer par priorité", ["all", "low", "medium", "high"])
    if priority_filter != "all":
        filtered_tasks = [task for task in tasks if task['priority'] == priority_filter]
        st.write(f"Nombre de tâches avec priorité {priority_filter}:", len(filtered_tasks))
    else:
        st.write("Affichage de toutes les priorités")

if st.session_state.current_page == "tasks":
    tasks_page()
elif st.session_state.current_page == "dashboard":
    dashboard_page()