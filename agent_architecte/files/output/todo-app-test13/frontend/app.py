import streamlit as st
from theme_runtime import inject_theme, get_auth_handler
import requests
import pandas as pd
from datetime import datetime

# ── Thème client (relu depuis client_config.yaml à chaque refresh) ───────────
_cfg  = inject_theme(st)
_auth = get_auth_handler(_cfg)

# ── Authentification ─────────────────────────────────────────────────────────
_auth.require(st)

def auth_headers() -> dict:
    """Retourne les headers HTTP avec le Bearer token courant."""
    return _auth.headers(st)

# ── Fin du bloc thème / auth — code métier ci-dessous ────────────────────────

# ──────────────────────── CONFIGURATION DE BASE ───────────────────────────────
BASE_URL = "http://localhost:8000"

# ──────────────────────── ÉTAT DE LA SESSION ────────────────────────────────
if "current_page" not in st.session_state:
    st.session_state.current_page = "task_management"

# ──────────────────────── FONCTIONS UTILITAIRES ───────────────────────────────
def fetch_tasks(filters=None):
    """Récupère les tâches avec filtres optionnels"""
    try:
        params = {}
        if filters:
            params.update(filters)
        response = requests.get(f"{BASE_URL}/tasks", headers=auth_headers(), params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.ConnectionError:
        st.error("Backend non disponible — vérifiez que le serveur tourne.")
        return []
    except Exception as e:
        st.error(f"Erreur lors de la récupération des tâches: {str(e)}")
        return []

def create_task(task_data):
    """Crée une nouvelle tâche"""
    try:
        response = requests.post(f"{BASE_URL}/tasks", headers=auth_headers(), json=task_data)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.ConnectionError:
        st.error("Backend non disponible — vérifiez que le serveur tourne.")
        return None
    except Exception as e:
        st.error(f"Erreur lors de la création de la tâche: {str(e)}")
        return None

def update_task(task_id, task_data):
    """Met à jour une tâche existante"""
    try:
        response = requests.put(f"{BASE_URL}/tasks/{task_id}", headers=auth_headers(), json=task_data)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.ConnectionError:
        st.error("Backend non disponible — vérifiez que le serveur tourne.")
        return None
    except Exception as e:
        st.error(f"Erreur lors de la mise à jour de la tâche: {str(e)}")
        return None

def delete_task(task_id):
    """Supprime une tâche"""
    try:
        response = requests.delete(f"{BASE_URL}/tasks/{task_id}", headers=auth_headers())
        response.raise_for_status()
        return True
    except requests.exceptions.ConnectionError:
        st.error("Backend non disponible — vérifiez que le serveur tourne.")
        return False
    except Exception as e:
        st.error(f"Erreur lors de la suppression de la tâche: {str(e)}")
        return False

# ──────────────────────── COMPOSANTS UI ─────────────────────────────────────
def task_management_page():
    """Page de gestion des tâches"""
    st.title("Gestion des tâches")
    
    # Filtres
    st.sidebar.header("Filtres")
    status_filter = st.sidebar.selectbox("Statut", ["Tous", "En attente", "En cours", "Terminé"])
    priority_filter = st.sidebar.selectbox("Priorité", ["Toutes", "Basse", "Moyenne", "Haute"])
    
    filters = {}
    if status_filter != "Tous":
        filters["status"] = status_filter.lower()
    if priority_filter != "Toutes":
        filters["priority"] = priority_filter.lower()
    
    # Affichage des tâches
    tasks = fetch_tasks(filters)
    if tasks:
        df = pd.DataFrame(tasks)
        df["due_date"] = pd.to_datetime(df["due_date"]).dt.strftime("%d/%m/%Y")
        st.dataframe(df)
    else:
        st.info("Aucune tâche trouvée avec ces critères.")
    
    # Formulaire de création
    st.header("Créer une tâche")
    with st.form("create_task_form"):
        title = st.text_input("Titre")
        description = st.text_area("Description")
        due_date = st.date_input("Date d'échéance")
        priority = st.selectbox("Priorité", ["Basse", "Moyenne", "Haute"])
        submitted = st.form_submit_button("Créer")
        
        if submitted:
            task_data = {
                "title": title,
                "description": description,
                "due_date": due_date.isoformat(),
                "priority": priority.lower()
            }
            result = create_task(task_data)
            if result:
                st.success("Tâche créée avec succès!")
                st.experimental_rerun()
    
    # Formulaire de modification
    if tasks:
        st.header("Modifier une tâche")
        task_ids = [t["id"] for t in tasks]
        selected_id = st.selectbox("Sélectionner une tâche", task_ids)
        selected_task = next(t for t in tasks if t["id"] == selected_id)
        
        with st.form(f"edit_task_form_{selected_id}"):
            new_title = st.text_input("Nouveau titre", value=selected_task["title"])
            new_description = st.text_area("Nouvelle description", value=selected_task["description"])
            new_due_date = st.date_input("Nouvelle date d'échéance", value=datetime.fromisoformat(selected_task["due_date"]))
            new_priority = st.selectbox("Nouvelle priorité", ["Basse", "Moyenne", "Haute"], index=["Basse", "Moyenne", "Haute"].index(selected_task["priority"].capitalize()))
            
            update_submitted = st.form_submit_button("Mettre à jour")
            
            if update_submitted:
                update_data = {
                    "title": new_title,
                    "description": new_description,
                    "due_date": new_due_date.isoformat(),
                    "priority": new_priority.lower()
                }
                result = update_task(selected_id, update_data)
                if result:
                    st.success("Tâche mise à jour avec succès!")
                    st.experimental_rerun()
    
    # Suppression de tâche
    if tasks:
        st.header("Supprimer une tâche")
        delete_id = st.selectbox("Sélectionner une tâche à supprimer", task_ids)
        if st.button("Supprimer"):
            if delete_task(delete_id):
                st.success("Tâche supprimée avec succès!")
                st.experimental_rerun()

def dashboard_page():
    """Page du tableau de bord"""
    st.title("Tableau de bord")
    
    # Filtres
    st.sidebar.header("Filtres")
    status_filter = st.sidebar.selectbox("Statut", ["Tous", "En attente", "En cours", "Terminé"], key="dashboard_status")
    priority_filter = st.sidebar.selectbox("Priorité", ["Toutes", "Basse", "Moyenne", "Haute"], key="dashboard_priority")
    
    filters = {}
    if status_filter != "Tous":
        filters["status"] = status_filter.lower()
    if priority_filter != "Toutes":
        filters["priority"] = priority_filter.lower()
    
    # Métriques
    tasks = fetch_tasks(filters)
    if tasks:
        total_tasks = len(tasks)
        completed_tasks = sum(1 for t in tasks if t["status"] == "completed")
        pending_tasks = total_tasks - completed_tasks
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Total des tâches", total_tasks)
        col2.metric("Tâches terminées", completed_tasks)
        col3.metric("Tâches en attente", pending_tasks)
        
        # Affichage des tâches
        df = pd.DataFrame(tasks)
        df["due_date"] = pd.to_datetime(df["due_date"]).dt.strftime("%d/%m/%Y")
        st.dataframe(df)
    else:
        st.info("Aucune tâche trouvée avec ces critères.")

def ci_cd_page():
    """Page CI/CD (placeholder)"""
    st.title("Pipeline CI/CD")
    st.info("Statut du pipeline CI/CD : En attente de mise en place")

# ──────────────────────── NAVIGATION ───────────────────────────────────────
MODULES_INTERNES = ["task_management", "dashboard", "ci_cd"]
pages = [
    ("Gestion des tâches", "task_management"),
    ("Tableau de bord", "dashboard"),
    ("Pipeline CI/CD", "ci_cd")
]

current_idx = MODULES_INTERNES.index(st.session_state.current_page) if st.session_state.current_page in MODULES_INTERNES else 0
selected = st.sidebar.radio("Navigation", [p[0] for p in pages], index=current_idx)
st.session_state.current_page = [p[1] for p in pages if p[0] == selected][0]

# ──────────────────────── RENDU DE LA PAGE ─────────────────────────────────
if st.session_state.current_page == "task_management":
    task_management_page()
elif st.session_state.current_page == "dashboard":
    dashboard_page()
elif st.session_state.current_page == "ci_cd":
    ci_cd_page()