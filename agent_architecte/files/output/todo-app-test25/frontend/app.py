import streamlit as st
from theme_runtime import inject_theme, get_auth_handler
import requests
import pandas as pd

# ── Thème client (relu depuis client_config.yaml à chaque refresh) ───────────
_cfg  = inject_theme(st)
_auth = get_auth_handler(_cfg)

# ── Authentification ─────────────────────────────────────────────────────────
_auth.require(st)

def auth_headers() -> dict:
    """Retourne les headers HTTP avec le Bearer token courant."""
    return _auth.headers(st)

# ── Fin du bloc thème / auth — code métier ci-dessous ────────────────────────

# ── Configuration de base ───────────────────────────────────────────────────
BASE_URL = "http://localhost:8000"

# ── États de session ────────────────────────────────────────────────────────
if "current_page" not in st.session_state:
    st.session_state.current_page = "task_management"

# ── Navigation ─────────────────────────────────────────────────────────────
MODULES_INTERNES = ["authentication", "task_management", "dashboard", "ci_cd"]
pages = [
    ("Authentification", "authentication"),
    ("Gestion des tâches", "task_management"),
    ("Tableau de bord", "dashboard"),
    ("CI/CD", "ci_cd")
]

labels = [p[0] for p in pages]
values = [p[1] for p in pages]

current_idx = values.index(st.session_state.current_page) if st.session_state.current_page in values else 0
selected = st.sidebar.radio("Navigation", labels, index=current_idx)
st.session_state.current_page = values[labels.index(selected)]

# ── Fonctions métier ────────────────────────────────────────────────────────
def get_tasks():
    try:
        response = requests.get(f"{BASE_URL}/tasks", headers=auth_headers())
        response.raise_for_status()
        return response.json()
    except requests.exceptions.ConnectionError:
        st.error("Backend non disponible — vérifiez que le serveur tourne.")
        return []

def create_task(title, description):
    try:
        response = requests.post(
            f"{BASE_URL}/tasks",
            headers=auth_headers(),
            json={"title": title, "description": description}
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.ConnectionError:
        st.error("Backend non disponible — vérifiez que le serveur tourne.")
        return None

def update_task(task_id, title, description):
    try:
        response = requests.put(
            f"{BASE_URL}/tasks/{task_id}",
            headers=auth_headers(),
            json={"title": title, "description": description}
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.ConnectionError:
        st.error("Backend non disponible — vérifiez que le serveur tourne.")
        return None

def delete_task(task_id):
    try:
        response = requests.delete(f"{BASE_URL}/tasks/{task_id}", headers=auth_headers())
        response.raise_for_status()
        return True
    except requests.exceptions.ConnectionError:
        st.error("Backend non disponible — vérifiez que le serveur tourne.")
        return False

def register_user(username, password):
    try:
        response = requests.post(
            f"{BASE_URL}/auth/register",
            headers=auth_headers(),
            json={"username": username, "password": password}
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.ConnectionError:
        st.error("Backend non disponible — vérifiez que le serveur tourne.")
        return None

# ── Modules ─────────────────────────────────────────────────────────────────
def render_authentication():
    st.title("Authentification")
    with st.form("register_form"):
        username = st.text_input("Nom d'utilisateur")
        password = st.text_input("Mot de passe", type="password")
        submitted = st.form_submit_button("S'inscrire")
        if submitted:
            result = register_user(username, password)
            if result:
                st.success("Inscription réussie !")
            else:
                st.error("Erreur lors de l'inscription")

def render_task_management():
    st.title("Gestion des tâches")
    
    # Formulaire de création
    with st.form("create_task_form"):
        title = st.text_input("Titre")
        description = st.text_area("Description")
        submitted = st.form_submit_button("Créer une tâche")
        if submitted:
            result = create_task(title, description)
            if result:
                st.success("Tâche créée avec succès !")
                st.rerun()
    
    # Liste des tâches
    tasks = get_tasks()
    if tasks:
        df = pd.DataFrame(tasks)
        st.dataframe(df)
        
        # Formulaire de mise à jour
        selected_task = st.selectbox("Sélectionner une tâche à modifier", tasks, format_func=lambda x: x["title"])
        if selected_task:
            with st.form(f"update_task_form_{selected_task['id']}"):
                new_title = st.text_input("Nouveau titre", value=selected_task["title"])
                new_description = st.text_area("Nouvelle description", value=selected_task["description"])
                update_submitted = st.form_submit_button("Mettre à jour")
                if update_submitted:
                    result = update_task(selected_task["id"], new_title, new_description)
                    if result:
                        st.success("Tâche mise à jour !")
                        st.rerun()
        
        # Suppression
        task_to_delete = st.selectbox("Sélectionner une tâche à supprimer", tasks, format_func=lambda x: x["title"])
        if st.button("Supprimer la tâche sélectionnée"):
            if delete_task(task_to_delete["id"]):
                st.success("Tâche supprimée !")
                st.rerun()
    else:
        st.info("Aucune tâche trouvée")

def render_dashboard():
    st.title("Tableau de bord")
    tasks = get_tasks()
    if tasks:
        df = pd.DataFrame(tasks)
        st.metric("Total des tâches", len(tasks))
        st.metric("Tâches en cours", len([t for t in tasks if t["status"] == "pending"]))
        st.metric("Tâches terminées", len([t for t in tasks if t["status"] == "completed"]))
        st.bar_chart(df["status"].value_counts())
    else:
        st.info("Aucune donnée disponible")

def render_ci_cd():
    st.title("CI/CD")
    st.info("Pipeline CI/CD en cours d'exécution...")
    st.markdown("""
    1. Test unitaires : ✅
    2. Build Docker : ⏳
    3. Déploiement : 🔧
    """)
    st.success("Dernière mise à jour : 2023-10-15 14:30 UTC")

# ── Exécution du module sélectionné ───────────────────────────────────────────
if st.session_state.current_page == "authentication":
    render_authentication()
elif st.session_state.current_page == "task_management":
    render_task_management()
elif st.session_state.current_page == "dashboard":
    render_dashboard()
elif st.session_state.current_page == "ci_cd":
    render_ci_cd()