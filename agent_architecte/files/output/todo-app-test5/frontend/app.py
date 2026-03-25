import streamlit as st
import requests
import pandas as pd
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

# ── Initialisation de l'état ─────────────────────────────────────────────────
if "current_page" not in st.session_state:
    st.session_state.current_page = "dashboard"
if "tasks" not in st.session_state:
    st.session_state.tasks = []

# ── Fonctions métier ───────────────────────────────────────────────────────
def get_tasks():
    """Récupère la liste des tâches depuis l'API."""
    try:
        response = requests.get(
            "http://localhost:8000/tasks",
            headers=auth_headers()
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.ConnectionError:
        st.error("Backend non disponible — vérifiez que le serveur tourne.")
        return []

def create_task(data):
    """Crée une nouvelle tâche."""
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
    """Met à jour une tâche existante."""
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
    """Supprime une tâche."""
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

# ── Composants UI ───────────────────────────────────────────────────────────
def render_tasks():
    """Affiche la liste des tâches avec fonctionnalités CRUD."""
    st.title("Gestion des tâches")
    
    # Formulaire de création
    with st.form("create_task_form", clear_on_submit=True):
        title = st.text_input("Titre")
        description = st.text_area("Description")
        priority = st.selectbox("Priorité", ["low", "medium", "high"])
        status = st.selectbox("Statut", ["todo", "in_progress", "done"])
        duration = st.number_input("Durée (heures)", min_value=0.1, step=0.5)
        submitted = st.form_submit_button("Créer la tâche")
        
        if submitted and title:
            task_data = {
                "title": title,
                "description": description,
                "priority": priority,
                "status": status,
                "duration": duration
            }
            new_task = create_task(task_data)
            if new_task:
                st.success("Tâche créée avec succès !")
                st.session_state.tasks = get_tasks()
    
    # Filtres
    st.markdown("### Filtres")
    col1, col2 = st.columns(2)
    with col1:
        status_filter = st.selectbox("Filtrer par statut", ["Tous", "todo", "in_progress", "done"])
    with col2:
        priority_filter = st.selectbox("Filtrer par priorité", ["Toutes", "low", "medium", "high"])
    
    # Récupération et affichage des tâches
    tasks = get_tasks()
    filtered_tasks = tasks.copy()
    
    if status_filter != "Tous":
        filtered_tasks = [t for t in filtered_tasks if t["status"] == status_filter]
    if priority_filter != "Toutes":
        filtered_tasks = [t for t in filtered_tasks if t["priority"] == priority_filter]
    
    if filtered_tasks:
        df = pd.DataFrame(filtered_tasks)
        st.dataframe(df)
        
        # Actions par tâche
        for task in filtered_tasks:
            col1, col2, col3 = st.columns([3, 1, 1])
            col1.write(f"**{task['title']}**")
            col2.button("Modifier", key=f"edit_{task['id']}", on_click=lambda t=task: render_edit_form(t))
            col3.button("Supprimer", key=f"delete_{task['id']}", on_click=lambda t=task: delete_task_action(t))
    else:
        st.info("Aucune tâche ne correspond aux filtres sélectionnés.")

def render_edit_form(task):
    """Affiche le formulaire de modification d'une tâche."""
    with st.form(f"edit_form_{task['id']}"):
        st.write(f"Modifier la tâche : {task['title']}")
        title = st.text_input("Titre", task["title"])
        description = st.text_area("Description", task["description"])
        priority = st.selectbox("Priorité", ["low", "medium", "high"], index=["low", "medium", "high"].index(task["priority"]))
        status = st.selectbox("Statut", ["todo", "in_progress", "done"], index=["todo", "in_progress", "done"].index(task["status"]))
        duration = st.number_input("Durée (heures)", value=task["duration"], min_value=0.1, step=0.5)
        
        submitted = st.form_submit_button("Mettre à jour")
        
        if submitted:
            updated_task = update_task(task["id"], {
                "title": title,
                "description": description,
                "priority": priority,
                "status": status,
                "duration": duration
            })
            if updated_task:
                st.success("Tâche mise à jour avec succès !")
                st.session_state.tasks = get_tasks()
                st.rerun()

def delete_task_action(task):
    """Gère la suppression d'une tâche avec confirmation."""
    if st.checkbox(f"Confirmer la suppression de '{task['title']}'"):
        if delete_task(task["id"]):
            st.success("Tâche supprimée avec succès !")
            st.session_state.tasks = get_tasks()
            st.rerun()

def render_dashboard():
    """Affiche le tableau de bord avec métriques agrégées."""
    st.title("Tableau de bord")
    
    tasks = get_tasks()
    if not tasks:
        st.info("Aucune tâche trouvée.")
        return
    
    df = pd.DataFrame(tasks)
    
    # Métriques
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total tâches", len(tasks))
    with col2:
        st.metric("En cours", len(df[df["status"] == "in_progress"]))
    with col3:
        st.metric("Terminées", len(df[df["status"] == "done"]))
    
    # Tableau détaillé
    st.markdown("### Détails des tâches")
    st.dataframe(df)
    
    # Filtres avancés
    st.markdown("### Filtres avancés")
    col1, col2 = st.columns(2)
    with col1:
        priority_filter = st.selectbox("Priorité", ["Toutes", "low", "medium", "high"], key="dashboard_priority")
    with col2:
        status_filter = st.selectbox("Statut", ["Tous", "todo", "in_progress", "done"], key="dashboard_status")
    
    filtered_df = df.copy()
    if priority_filter != "Toutes":
        filtered_df = filtered_df[filtered_df["priority"] == priority_filter]
    if status_filter != "Tous":
        filtered_df = filtered_df[filtered_df["status"] == status_filter]
    
    if not filtered_df.empty:
        st.dataframe(filtered_df)
    else:
        st.info("Aucune tâche ne correspond aux filtres sélectionnés.")

def render_register_form():
    """Affiche le formulaire d'inscription."""
    st.title("Inscription")
    
    with st.form("register_form", clear_on_submit=True):
        username = st.text_input("Nom d'utilisateur")
        email = st.text_input("Email")
        password = st.text_input("Mot de passe", type="password")
        submitted = st.form_submit_button("S'inscrire")
        
        if submitted:
            response = requests.post(
                "http://localhost:8000/auth/register",
                json={"username": username, "email": email, "password": password}
            )
            if response.status_code == 200:
                st.success("Inscription réussie ! Vous pouvez maintenant vous connecter.")
            else:
                st.error("Erreur lors de l'inscription. Vérifiez les informations saisies.")

# ── Navigation ─────────────────────────────────────────────────────────────
MODULES_INTERNES = ["dashboard", "tasks", "auth"]

# Configuration des labels pour l'affichage
pages = [
    ("Tableau de bord", "dashboard"),
    ("Mes tâches", "tasks"),
    ("Inscription", "auth")
]

# Récupération des valeurs et labels
labels = [p[0] for p in pages]
values = [p[1] for p in pages]

# Détection de l'index actuel
try:
    current_idx = values.index(st.session_state.current_page)
except ValueError:
    current_idx = 0

# Navigation sidebar
selected = st.sidebar.radio("Navigation", labels, index=current_idx)
st.session_state.current_page = values[labels.index(selected)]

# ── Rendu de la page courante ────────────────────────────────────────────────
if st.session_state.current_page == "dashboard":
    render_dashboard()
elif st.session_state.current_page == "tasks":
    render_tasks()
elif st.session_state.current_page == "auth":
    render_register_form()