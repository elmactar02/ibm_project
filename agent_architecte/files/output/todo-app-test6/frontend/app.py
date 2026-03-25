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

def render_login_page():
    """Page de connexion utilisateur"""
    st.title("Connexion")
    with st.form("login_form"):
        email = st.text_input("Email")
        password = st.text_input("Mot de passe", type="password")
        submitted = st.form_submit_button("Se connecter")
        
        if submitted:
            try:
                response = requests.post(
                    "http://localhost:8000/auth/login",
                    json={"email": email, "password": password},
                    headers=auth_headers()
                )
                response.raise_for_status()
                st.success("Connexion réussie!")
                st.rerun()
            except requests.exceptions.RequestException as e:
                st.error("Échec de la connexion. Vérifiez vos identifiants.")

def render_register_page():
    """Page d'inscription utilisateur"""
    st.title("Inscription")
    with st.form("register_form"):
        name = st.text_input("Nom")
        email = st.text_input("Email")
        password = st.text_input("Mot de passe", type="password")
        submitted = st.form_submit_button("S'inscrire")
        
        if submitted:
            try:
                response = requests.post(
                    "http://localhost:8000/auth/register",
                    json={"name": name, "email": email, "password": password},
                    headers=auth_headers()
                )
                response.raise_for_status()
                st.success("Inscription réussie!")
                st.rerun()
            except requests.exceptions.RequestException as e:
                st.error("Échec de l'inscription. Vérifiez les informations.")

def render_dashboard_page():
    """Page principale avec gestion des tâches"""
    st.title("Tableau de bord")
    
    # Filtres
    col1, col2 = st.columns(2)
    with col1:
        status_filter = st.selectbox(
            "Filtrer par statut",
            ["Toutes", "À faire", "En cours", "Terminée"]
        )
    with col2:
        priority_filter = st.selectbox(
            "Filtrer par priorité",
            ["Toutes", "Basse", "Moyenne", "Haute"]
        )
    
    try:
        # Récupérer les tâches
        params = {}
        if status_filter != "Toutes":
            params["status"] = status_filter.lower()
        if priority_filter != "Toutes":
            params["priority"] = priority_filter.lower()
            
        response = requests.get(
            "http://localhost:8000/tasks",
            params=params,
            headers=auth_headers()
        )
        response.raise_for_status()
        tasks = response.json()
        
        if not tasks:
            st.info("Aucune tâche trouvée.")
            return
            
        # Afficher les tâches
        st.dataframe(tasks)
        
        # Formulaire de création
        with st.form("create_task_form"):
            st.subheader("Créer une tâche")
            title = st.text_input("Titre")
            description = st.text_area("Description")
            priority = st.selectbox("Priorité", ["Basse", "Moyenne", "Haute"])
            due_date = st.date_input("Date d'échéance")
            
            submitted = st.form_submit_button("Créer")
            
            if submitted:
                create_data = {
                    "title": title,
                    "description": description,
                    "priority": priority.lower(),
                    "due_date": due_date.isoformat()
                }
                try:
                    response = requests.post(
                        "http://localhost:8000/tasks",
                        json=create_data,
                        headers=auth_headers()
                    )
                    response.raise_for_status()
                    st.success("Tâche créée avec succès!")
                    st.rerun()
                except requests.exceptions.RequestException as e:
                    st.error("Échec de la création de la tâche.")
                    
        # Formulaire de modification
        if tasks:
            task_ids = [task["id"] for task in tasks]
            selected_id = st.selectbox("Sélectionner une tâche à modifier", task_ids)
            
            selected_task = next(task for task in tasks if task["id"] == selected_id)
            
            with st.form(f"edit_task_form_{selected_id}"):
                st.subheader("Modifier la tâche")
                new_title = st.text_input("Titre", value=selected_task["title"])
                new_description = st.text_area("Description", value=selected_task["description"])
                new_priority = st.selectbox("Priorité", ["Basse", "Moyenne", "Haute"], 
                                          index=["Basse", "Moyenne", "Haute"].index(selected_task["priority"].capitalize()))
                new_due_date = st.date_input("Date d'échéance", value=selected_task["due_date"])
                
                submitted = st.form_submit_button("Mettre à jour")
                
                if submitted:
                    update_data = {
                        "title": new_title,
                        "description": new_description,
                        "priority": new_priority.lower(),
                        "due_date": new_due_date.isoformat()
                    }
                    try:
                        response = requests.put(
                            f"http://localhost:8000/tasks/{selected_id}",
                            json=update_data,
                            headers=auth_headers()
                        )
                        response.raise_for_status()
                        st.success("Tâche mise à jour avec succès!")
                        st.rerun()
                    except requests.exceptions.RequestException as e:
                        st.error("Échec de la mise à jour de la tâche.")
                        
        # Suppression de tâche
        if tasks:
            delete_id = st.selectbox("Sélectionner une tâche à supprimer", task_ids)
            if st.button("Supprimer la tâche sélectionnée"):
                try:
                    response = requests.delete(
                        f"http://localhost:8000/tasks/{delete_id}",
                        headers=auth_headers()
                    )
                    response.raise_for_status()
                    st.success("Tâche supprimée avec succès!")
                    st.rerun()
                except requests.exceptions.RequestException as e:
                    st.error("Échec de la suppression de la tâche.")
                    
    except requests.exceptions.RequestException as e:
        st.error("Impossible de charger les tâches. Vérifiez que le serveur backend est actif.")

# ── Navigation ─────────────────────────────────────────────────────────────
if "current_page" not in st.session_state:
    st.session_state.current_page = "dashboard"

MODULES_INTERNES = ["auth", "tasks", "dashboard"]
pages = [
    ("Connexion", "auth"),
    ("Inscription", "tasks"),
    ("Tableau de bord", "dashboard")
]

# Créer la navigation
st.sidebar.title("Navigation")
selected_page = st.sidebar.radio(
    "Aller à",
    [p[0] for p in pages],
    index=pages.index(next(p for p in pages if p[1] == st.session_state.current_page))) if st.session_state.current_page in [p[1] for p in pages] else 0
)

# Mettre à jour la page courante
for label, value in pages:
    if label == selected_page:
        st.session_state.current_page = value

# Rendre la page sélectionnée
if st.session_state.current_page == "auth":
    render_login_page()
elif st.session_state.current_page == "tasks":
    render_register_page()
elif st.session_state.current_page == "dashboard":
    render_dashboard_page()