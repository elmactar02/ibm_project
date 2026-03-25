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

# ────────────────────────────────────────────────────────────────────────────
# ─── CONFIGURATION DE BASE ───────────────────────────────────────────────────
# ────────────────────────────────────────────────────────────────────────────

BASE_URL = "http://localhost:8000"

# ────────────────────────────────────────────────────────────────────────────
# ─── GESTION DE LA NAVIGATION ────────────────────────────────────────────────
# ────────────────────────────────────────────────────────────────────────────

if "current_page" not in st.session_state:
    st.session_state.current_page = "task_management"

# Configuration des modules
MODULES = {
    "task_management": "Gestion des tâches",
    "dashboard": "Tableau de bord",
    "ci_cd": "CI/CD"
}

# Navigation sidebar
st.sidebar.title("Navigation")
selected_page = st.sidebar.radio(
    "Modules",
    list(MODULES.values()),
    index=list(MODULES.values()).index(MODULES[st.session_state.current_page])
)

# Mise à jour de la page courante
for key, value in MODULES.items():
    if selected_page == value:
        st.session_state.current_page = key

# ────────────────────────────────────────────────────────────────────────────
# ─── MODULE : GESTION DES TÂCHES ─────────────────────────────────────────────
# ────────────────────────────────────────────────────────────────────────────

def task_management():
    st.title("Gestion des tâches")
    
    # Création de tâche
    with st.form("create_task_form"):
        st.subheader("Créer une nouvelle tâche")
        title = st.text_input("Titre")
        description = st.text_area("Description")
        due_date = st.date_input("Date d'échéance")
        submitted = st.form_submit_button("Créer")
        
        if submitted:
            try:
                response = requests.post(
                    f"{BASE_URL}/tasks",
                    headers=auth_headers(),
                    json={
                        "title": title,
                        "description": description,
                        "due_date": due_date.isoformat()
                    }
                )
                response.raise_for_status()
                st.success("Tâche créée avec succès !")
            except requests.exceptions.RequestException as e:
                st.error("Erreur lors de la création de la tâche")

    # Liste des tâches
    st.subheader("Liste des tâches")
    try:
        response = requests.get(f"{BASE_URL}/tasks", headers=auth_headers())
        response.raise_for_status()
        tasks = response.json()
        
        if tasks:
            df = pd.DataFrame(tasks)
            st.dataframe(df)
            
            # Actions par tâche
            for task in tasks:
                col1, col2, col3 = st.columns([3, 1, 1])
                col1.text(task["title"])
                
                # Bouton de modification
                if col2.button("Modifier", key=f"edit_{task['id']}"):
                    st.session_state.edit_task_id = task["id"]
                    st.session_state.edit_task_data = {
                        "title": task["title"],
                        "description": task["description"],
                        "due_date": task["due_date"]
                    }
                
                # Bouton de suppression
                if col3.button("Supprimer", key=f"delete_{task['id']}"):
                    try:
                        response = requests.delete(
                            f"{BASE_URL}/tasks/{task['id']}",
                            headers=auth_headers()
                        )
                        response.raise_for_status()
                        st.success("Tâche supprimée")
                        st.experimental_rerun()
                    except requests.exceptions.RequestException as e:
                        st.error("Erreur lors de la suppression")
        else:
            st.info("Aucune tâche trouvée")
            
    except requests.exceptions.RequestException as e:
        st.error("Impossible de charger les tâches")

    # Formulaire de modification
    if "edit_task_id" in st.session_state:
        st.subheader("Modifier une tâche")
        with st.form(f"edit_task_form_{st.session_state.edit_task_id}"):
            title = st.text_input("Titre", value=st.session_state.edit_task_data["title"])
            description = st.text_area("Description", value=st.session_state.edit_task_data["description"])
            due_date = st.date_input("Date d'échéance", value=st.session_state.edit_task_data["due_date"])
            
            if st.form_submit_button("Enregistrer"):
                try:
                    response = requests.put(
                        f"{BASE_URL}/tasks/{st.session_state.edit_task_id}",
                        headers=auth_headers(),
                        json={
                            "title": title,
                            "description": description,
                            "due_date": due_date.isoformat()
                        }
                    )
                    response.raise_for_status()
                    st.success("Tâche mise à jour")
                    del st.session_state.edit_task_id
                    del st.session_state.edit_task_data
                    st.experimental_rerun()
                except requests.exceptions.RequestException as e:
                    st.error("Erreur lors de la mise à jour")

# ────────────────────────────────────────────────────────────────────────────
# ─── MODULE : TABLEAU DE BORD ────────────────────────────────────────────────
# ────────────────────────────────────────────────────────────────────────────

def dashboard():
    st.title("Tableau de bord")
    
    try:
        response = requests.get(f"{BASE_URL}/tasks", headers=auth_headers())
        response.raise_for_status()
        tasks = response.json()
        
        if tasks:
            # Calcul des métriques
            total_tasks = len(tasks)
            completed_tasks = sum(1 for t in tasks if t.get("completed", False))
            pending_tasks = total_tasks - completed_tasks
            
            # Affichage des métriques
            col1, col2, col3 = st.columns(3)
            col1.metric("Total des tâches", total_tasks)
            col2.metric("Tâches terminées", completed_tasks)
            col3.metric("Tâches en cours", pending_tasks)
            
            # Progression
            st.progress(completed_tasks / total_tasks)
            
            # Tableau des tâches
            df = pd.DataFrame(tasks)
            st.table(df)
        else:
            st.info("Aucune tâche trouvée")
            
    except requests.exceptions.RequestException as e:
        st.error("Impossible de charger les données du tableau de bord")

# ────────────────────────────────────────────────────────────────────────────
# ─── MODULE : CI/CD ────────────────────────────────────────────────────────
# ────────────────────────────────────────────────────────────────────────────

def ci_cd():
    st.title("CI/CD")
    st.info("Module CI/CD - À implémenter selon les besoins du projet")

# ────────────────────────────────────────────────────────────────────────────
# ─── RENDU DE LA PAGE COURANTE ───────────────────────────────────────────────
# ────────────────────────────────────────────────────────────────────────────

if st.session_state.current_page == "task_management":
    task_management()
elif st.session_state.current_page == "dashboard":
    dashboard()
elif st.session_state.current_page == "ci_cd":
    ci_cd()