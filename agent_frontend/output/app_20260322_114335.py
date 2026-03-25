import streamlit as st
from theme_runtime import inject_theme, get_auth_handler
import requests
import pandas as pd

# ── Thème client (relu depuis client_config.yaml à chaque refresh) ───────────
_cfg  = inject_theme(st)
_auth = get_auth_handler(_cfg)

# ── Authentification ─────────────────────────────────────────────────────────
def init_auth():
    """Initialise l'authentification et vérifie la validité du token"""
    if 'auth_token' not in st.session_state:
        st.session_state.auth_token = None
    if 'user' not in st.session_state:
        st.session_state.user = None

def validate_token(token: str) -> bool:
    """Valide le token côté serveur"""
    try:
        response = requests.get(
            "http://localhost:8000/api/v1/auth/validate",
            headers={"Authorization": f"Bearer {token}"}
        )
        if response.status_code == 200:
            st.session_state.user = response.json()
            return True
        return False
    except requests.exceptions.RequestException:
        return False

def auth_headers() -> dict:
    """Retourne les headers HTTP avec le Bearer token courant."""
    return _auth.headers(st)

# ── Fin du bloc thème / auth — code métier ci-dessous ────────────────────────

init_auth()

# ── Sidebar Navigation ─────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## Acme Task Manager")
    
    if st.session_state.auth_token:
        st.text_input("Token Bearer", value=st.session_state.auth_token, key="token_input")
        if st.button("Déconnexion"):
            st.session_state.auth_token = None
            st.session_state.user = None
            st.rerun()
    else:
        token = st.text_input("Token Bearer", key="token_input")
        if st.button("Connexion"):
            if validate_token(token):
                st.session_state.auth_token = token
                st.success("Connexion réussie")
                st.rerun()
            else:
                st.error("Token invalide")
                st.stop()

    view = st.radio("Navigation", ["Tableau de bord", "Créer une tâche"])

# ── Fonctions utilitaires ─────────────────────────────────────────────────────
def get_tasks(status=None, priority=None, page=1, per_page=10):
    """Récupère la liste des tâches avec pagination et filtres"""
    params = {
        "status": status,
        "priority": priority,
        "page": page,
        "per_page": per_page
    }
    try:
        response = requests.get(
            "http://localhost:8000/api/v1/tasks",
            params=params,
            headers=auth_headers()
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        st.error(f"Erreur API: {e.response.status_code}")
        return {"tasks": [], "total": 0, "page": 1, "per_page": 10}
    except requests.exceptions.JSONDecodeError:
        st.error("Réponse JSON invalide du serveur")
        return {"tasks": [], "total": 0, "page": 1, "per_page": 10}

def create_task(title, description, priority):
    """Crée une nouvelle tâche"""
    data = {
        "title": title,
        "description": description,
        "priority": priority
    }
    try:
        response = requests.post(
            "http://localhost:8000/api/v1/tasks",
            json=data,
            headers=auth_headers()
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 422:
            st.error("Erreur de validation: " + str(e.response.json()))
        else:
            st.error(f"Erreur API: {e.response.status_code}")
        return None

def update_task_status(task_id, status):
    """Met à jour le statut d'une tâche"""
    data = {"status": status}
    try:
        response = requests.patch(
            f"http://localhost:8000/api/v1/tasks/{task_id}/status",
            json=data,
            headers=auth_headers()
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        st.error(f"Erreur API: {e.response.status_code}")
        return None

def delete_task(task_id):
    """Supprime une tâche"""
    try:
        response = requests.delete(
            f"http://localhost:8000/api/v1/tasks/{task_id}",
            headers=auth_headers()
        )
        response.raise_for_status()
        return response.status_code == 204
    except requests.exceptions.HTTPError as e:
        st.error(f"Erreur API: {e.response.status_code}")
        return False

def get_task_details(task_id):
    """Récupère les détails d'une tâche"""
    try:
        response = requests.get(
            f"http://localhost:8000/api/v1/tasks/{task_id}",
            headers=auth_headers()
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        st.error(f"Erreur API: {e.response.status_code}")
        return None

# ── Composants principaux ────────────────────────────────────────────────────
if view == "Tableau de bord":
    st.title("Tableau de bord des tâches")
    
    # Filtres
    col1, col2 = st.columns(2)
    with col1:
        status_filter = st.selectbox(
            "Filtrer par statut",
            ["Tous", "todo", "in_progress", "done"],
            key="status_filter"
        )
    with col2:
        priority_filter = st.selectbox(
            "Filtrer par priorité",
            ["Toutes", "low", "medium", "high"],
            key="priority_filter"
        )
    
    # Pagination
    page = st.number_input(
        "Page",
        min_value=1,
        value=1,
        key="page_number"
    )
    per_page = st.number_input(
        "Tâches par page",
        min_value=1,
        max_value=100,
        value=10,
        key="per_page"
    )
    
    # Récupération des données
    data = get_tasks(
        status=status_filter if status_filter != "Tous" else None,
        priority=priority_filter if priority_filter != "Toutes" else None,
        page=page,
        per_page=per_page
    )
    
    if data["tasks"]:
        # Création du DataFrame
        tasks_df = pd.DataFrame(data["tasks"])
        tasks_df["created_at"] = pd.to_datetime(tasks_df["created_at"]).dt.strftime("%d/%m/%Y %H:%M")
        
        # Affichage du tableau
        st.dataframe(tasks_df, use_container_width=True)
        
        # Pagination
        st.markdown(f"Page {data['page']} / {data['total'] // data['per_page'] + 1}")
        
        # Boutons d'action par tâche
        for task in data["tasks"]:
            col1, col2, col3 = st.columns([3, 1, 1])
            col1.markdown(f"**{task['title']}**")
            
            # Bouton de mise à jour du statut
            if col2.button("✅", key=f"status_{task['id']}"):
                new_status = "done" if task["status"] != "done" else "todo"
                updated_task = update_task_status(task["id"], new_status)
                if updated_task:
                    st.success(f"Statut mis à jour: {updated_task['status']}")
                    st.rerun()
            
            # Bouton de suppression
            if col3.button("🗑️", key=f"delete_{task['id']}"):
                if st.checkbox(f"Confirmer la suppression de {task['title']}"):
                    if delete_task(task["id"]):
                        st.success("Tâche supprimée")
                        st.rerun()
    else:
        st.info("Aucune tâche trouvée")

elif view == "Créer une tâche":
    st.title("Créer une nouvelle tâche")
    
    with st.form("create_task_form"):
        title = st.text_input("Titre", key="title_input")
        description = st.text_area("Description", key="description_input")
        priority = st.selectbox(
            "Priorité",
            ["low", "medium", "high"],
            key="priority_input"
        )
        
        submitted = st.form_submit_button("Créer")
        
        if submitted:
            if not title.strip():
                st.error("Le titre est obligatoire")
            else:
                new_task = create_task(title, description, priority)
                if new_task:
                    st.success("Tâche créée avec succès")
                    st.json(new_task)
                    st.markdown("[Retour au tableau de bord](#tableau-de-bord-des-tâches)")
                else:
                    st.error("Erreur lors de la création de la tâche")

# ── Vérification d'authentification ───────────────────────────────────────────
if not st.session_state.auth_token:
    st.stop()