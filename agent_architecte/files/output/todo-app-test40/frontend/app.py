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

if "current_page" not in st.session_state:
    st.session_state.current_page = "auth"

def render_auth_page():
    with st.form("register_form"):
        email = st.text_input("Email")
        password = st.text_input("Mot de passe", type="password")
        confirm_password = st.text_input("Confirmer le mot de passe", type="password")
        submitted = st.form_submit_button("S'inscrire")
        if submitted:
            if password != confirm_password:
                st.error("Les mots de passe ne correspondent pas.")
                return
            try:
                response = requests.post(
                    "http://localhost:8000/auth/register",
                    headers=auth_headers(),
                    json={"email": email, "password": password}
                )
                response.raise_for_status()
                st.success("Inscription réussie !")
            except requests.exceptions.RequestException as e:
                if isinstance(e, requests.exceptions.ConnectionError):
                    st.error("Backend non disponible — vérifiez que le serveur tourne.")
                else:
                    st.error("Erreur lors de l'inscription. Vérifiez les informations saisies.")

def render_tasks_page():
    status_options = ["Toutes", "En cours", "Terminée"]
    priority_options = ["Toutes", "Basse", "Moyenne", "Haute"]
    
    col1, col2, col3 = st.columns(3)
    with col1:
        status = st.selectbox("Statut", status_options)
    with col2:
        priority = st.selectbox("Priorité", priority_options)
    with col3:
        page = st.number_input("Page", min_value=1, value=1)
    
    try:
        params = {}
        if status != "Toutes":
            params["status"] = status.lower()
        if priority != "Toutes":
            params["priority"] = priority.lower()
        params["page"] = page
        
        response = requests.get(
            "http://localhost:8000/tasks",
            headers=auth_headers(),
            params=params
        )
        response.raise_for_status()
        tasks = response.json()
        
        if tasks:
            st.dataframe(tasks)
        else:
            st.info("Aucune tâche trouvée.")
            
    except requests.exceptions.RequestException as e:
        if isinstance(e, requests.exceptions.ConnectionError):
            st.error("Backend non disponible — vérifiez que le serveur tourne.")
        else:
            st.error("Erreur lors de la récupération des tâches.")
        return
    
    with st.form("create_task_form"):
        title = st.text_input("Titre")
        description = st.text_area("Description")
        priority = st.selectbox("Priorité", ["Basse", "Moyenne", "Haute"])
        submitted = st.form_submit_button("Créer une tâche")
        if submitted:
            try:
                response = requests.post(
                    "http://localhost:8000/tasks",
                    headers=auth_headers(),
                    json={"title": title, "description": description, "priority": priority}
                )
                response.raise_for_status()
                st.success("Tâche créée avec succès !")
            except requests.exceptions.RequestException as e:
                if isinstance(e, requests.exceptions.ConnectionError):
                    st.error("Backend non disponible — vérifiez que le serveur tourne.")
                else:
                    st.error("Erreur lors de la création de la tâche.")
    
    if tasks:
        task_ids = [task["id"] for task in tasks]
        selected_id = st.selectbox("Sélectionner une tâche à modifier", task_ids)
        selected_task = next(task for task in tasks if task["id"] == selected_id)
        
        with st.form(f"update_task_form_{selected_id}"):
            title = st.text_input("Titre", selected_task["title"])
            description = st.text_area("Description", selected_task["description"])
            priority = st.selectbox("Priorité", ["Basse", "Moyenne", "Haute"], index=["Basse", "Moyenne", "Haute"].index(selected_task["priority"]))
            submitted = st.form_submit_button("Modifier la tâche")
            if submitted:
                try:
                    response = requests.put(
                        f"http://localhost:8000/tasks/{selected_id}",
                        headers=auth_headers(),
                        json={"title": title, "description": description, "priority": priority}
                    )
                    response.raise_for_status()
                    st.success("Tâche modifiée avec succès !")
                except requests.exceptions.RequestException as e:
                    if isinstance(e, requests.exceptions.ConnectionError):
                        st.error("Backend non disponible — vérifiez que le serveur tourne.")
                    else:
                        st.error("Erreur lors de la modification de la tâche.")
        
        if st.button(f"Supprimer la tâche {selected_id}"):
            try:
                response = requests.delete(
                    f"http://localhost:8000/tasks/{selected_id}",
                    headers=auth_headers()
                )
                response.raise_for_status()
                st.success("Tâche supprimée avec succès !")
            except requests.exceptions.RequestException as e:
                if isinstance(e, requests.exceptions.ConnectionError):
                    st.error("Backend non disponible — vérifiez que le serveur tourne.")
                else:
                    st.error("Erreur lors de la suppression de la tâche.")

def render_dashboard_page():
    try:
        response = requests.get(
            "http://localhost:8000/tasks",
            headers=auth_headers()
        )
        response.raise_for_status()
        tasks = response.json()
    except requests.exceptions.RequestException as e:
        if isinstance(e, requests.exceptions.ConnectionError):
            st.error("Backend non disponible — vérifiez que le serveur tourne.")
        else:
            st.error("Erreur lors de la récupération des tâches.")
        return
    
    total_tasks = len(tasks)
    completed_tasks = sum(1 for task in tasks if task["status"] == "Terminée")
    pending_tasks = total_tasks - completed_tasks
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Tâches totales", total_tasks)
    col2.metric("Tâches terminées", completed_tasks)
    col3.metric("Tâches en cours", pending_tasks)
    
    priority_counts = {}
    for task in tasks:
        priority = task["priority"]
        priority_counts[priority] = priority_counts.get(priority, 0) + 1
    
    st.bar_chart(priority_counts)
    
    st.subheader("Dernières tâches")
    if tasks:
        st.table(tasks[-5:])
    else:
        st.info("Aucune tâche trouvée.")

# Navigation sidebar
pages = [
    ("Inscription", "auth"),
    ("Mes tâches", "tasks"),
    ("Tableau de bord", "dashboard")
]
labels = [p[0] for p in pages]
values = [p[1] for p in pages]

current_idx = values.index(st.session_state.current_page) if st.session_state.current_page in values else 0
selected = st.sidebar.radio("Navigation", labels, index=current_idx)
st.session_state.current_page = values[labels.index(selected)]

# Render selected page
if st.session_state.current_page == "auth":
    render_auth_page()
elif st.session_state.current_page == "tasks":
    render_tasks_page()
elif st.session_state.current_page == "dashboard":
    render_dashboard_page()