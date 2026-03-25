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

# ──────────────────────── GESTION DE LA NAVIGATION ───────────────────────────
if "current_page" not in st.session_state:
    st.session_state.current_page = "dashboard"

MODULES_INTERNES = ["auth", "tasks", "dashboard"]
pages = [
    ("Connexion", "auth"),
    ("Mes tâches", "tasks"),
    ("Tableau de bord", "dashboard")
]

labels = [p[0] for p in pages]
values = [p[1] for p in pages]

try:
    current_idx = values.index(st.session_state.current_page)
except ValueError:
    current_idx = 0

selected = st.sidebar.radio("Navigation", labels, index=current_idx)
st.session_state.current_page = values[labels.index(selected)]

# ──────────────────────── COMPOSANTS PAR MODULE ───────────────────────────────
def render_auth_page():
    """Page de connexion"""
    st.title("Connexion")
    
    with st.form("login_form"):
        email = st.text_input("Email")
        password = st.text_input("Mot de passe", type="password")
        submitted = st.form_submit_button("Connexion")
        
        if submitted:
            try:
                response = requests.post(
                    "http://localhost:8000/auth/login",
                    json={"email": email, "password": password},
                    headers=auth_headers()
                )
                if response.status_code == 200:
                    st.success("Connexion réussie!")
                    st.session_state.current_page = "dashboard"
                    st.rerun()
                else:
                    st.error("Identifiants invalides")
            except requests.exceptions.ConnectionError:
                st.error("Backend non disponible — vérifiez que le serveur tourne.")

def render_register_page():
    """Page d'inscription"""
    st.title("Inscription")
    
    with st.form("register_form"):
        email = st.text_input("Email")
        password = st.text_input("Mot de passe", type="password")
        confirm = st.text_input("Confirmer le mot de passe", type="password")
        submitted = st.form_submit_button("S'inscrire")
        
        if submitted:
            if password != confirm:
                st.error("Les mots de passe ne correspondent pas")
                return
                
            if len(password) < 8:
                st.error("Le mot de passe doit contenir au moins 8 caractères")
                return
                
            if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
                st.error("Email invalide")
                return
                
            try:
                response = requests.post(
                    "http://localhost:8000/auth/register",
                    json={"email": email, "password": password},
                    headers=auth_headers()
                )
                if response.status_code == 201:
                    st.success("Inscription réussie! Vous pouvez maintenant vous connecter.")
                    st.session_state.current_page = "auth"
                    st.rerun()
                else:
                    st.error("Erreur lors de l'inscription")
            except requests.exceptions.ConnectionError:
                st.error("Backend non disponible — vérifiez que le serveur tourne.")

def render_tasks_page():
    """Page de gestion des tâches"""
    st.title("Mes tâches")
    
    # Filtres
    col1, col2 = st.columns(2)
    with col1:
        status_filter = st.selectbox(
            "Statut",
            ["Toutes", "En cours", "Terminée"],
            key="status_filter"
        )
    with col2:
        priority_filter = st.selectbox(
            "Priorité",
            ["Toutes", "Basse", "Moyenne", "Haute"],
            key="priority_filter"
        )
    
    # Boutons d'action
    if st.button("Créer une tâche"):
        st.session_state.show_create_form = True
    
    # Récupération des tâches
    try:
        params = {}
        if status_filter != "Toutes":
            params["status"] = status_filter
        if priority_filter != "Toutes":
            params["priority"] = priority_filter
            
        response = requests.get(
            "http://localhost:8000/tasks",
            params=params,
            headers=auth_headers()
        )
        
        if response.status_code == 200:
            tasks = response.json()
            if tasks:
                st.dataframe(tasks)
                
                # Formulaire de création
                if "show_create_form" in st.session_state and st.session_state.show_create_form:
                    with st.form("create_task_form"):
                        title = st.text_input("Titre")
                        description = st.text_area("Description")
                        status = st.selectbox("Statut", ["En cours", "Terminée"])
                        priority = st.selectbox("Priorité", ["Basse", "Moyenne", "Haute"])
                        
                        submitted = st.form_submit_button("Créer")
                        
                        if submitted:
                            create_data = {
                                "title": title,
                                "description": description,
                                "status": status,
                                "priority": priority
                            }
                            
                            create_response = requests.post(
                                "http://localhost:8000/tasks",
                                json=create_data,
                                headers=auth_headers()
                            )
                            
                            if create_response.status_code == 201:
                                st.success("Tâche créée avec succès!")
                                st.session_state.show_create_form = False
                                st.rerun()
                            else:
                                st.error("Erreur lors de la création")
            else:
                st.info("Aucune tâche trouvée")
        else:
            st.error("Erreur lors de la récupération des tâches")
            
    except requests.exceptions.ConnectionError:
        st.error("Backend non disponible — vérifiez que le serveur tourne.")

def render_dashboard_page():
    """Page de tableau de bord"""
    st.title("Tableau de bord")
    
    try:
        response = requests.get(
            "http://localhost:8000/tasks",
            headers=auth_headers()
        )
        
        if response.status_code == 200:
            tasks = response.json()
            if tasks:
                total_tasks = len(tasks)
                completed = sum(1 for t in tasks if t["status"] == "Terminée")
                pending = total_tasks - completed
                urgent = sum(1 for t in tasks if t["priority"] == "Haute")
                
                col1, col2, col3 = st.columns(3)
                col1.metric("Total tâches", total_tasks)
                col2.metric("Terminées", completed)
                col3.metric("En cours", pending)
                
                st.progress(completed / total_tasks if total_tasks > 0 else 0)
                
                st.subheader("Top 5 tâches urgentes")
                urgent_tasks = [t for t in tasks if t["priority"] == "Haute"][:5]
                if urgent_tasks:
                    st.dataframe(urgent_tasks)
                else:
                    st.info("Aucune tâche urgente")
            else:
                st.info("Aucune tâche trouvée")
        else:
            st.error("Erreur lors de la récupération des données")
            
    except requests.exceptions.ConnectionError:
        st.error("Backend non disponible — vérifiez que le serveur tourne.")

# ──────────────────────── RENDU DE LA PAGE COURANTE ───────────────────────────
if st.session_state.current_page == "auth":
    render_auth_page()
elif st.session_state.current_page == "tasks":
    render_tasks_page()
elif st.session_state.current_page == "dashboard":
    render_dashboard_page()