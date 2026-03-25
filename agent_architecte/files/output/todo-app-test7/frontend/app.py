import streamlit as st
from theme_runtime import inject_theme, get_auth_handler
import requests
import pandas as pd
from typing import Optional, Dict, Any

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
# ─── CONFIGURATION GLOBALE ───────────────────────────────────────────────────
# ────────────────────────────────────────────────────────────────────────────

MODULES_INTERNES = ["auth", "tasks", "dashboard", "ci_cd"]

if "current_page" not in st.session_state:
    st.session_state.current_page = "tasks"

# ────────────────────────────────────────────────────────────────────────────
# ─── FONCTIONS DE GESTION DES MODULES ────────────────────────────────────────
# ────────────────────────────────────────────────────────────────────────────

def render_auth_module():
    """Module d'authentification avec formulaires d'inscription/connexion"""
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("S'inscrire")
        with st.form("register_form"):
            username = st.text_input("Nom d'utilisateur", key="register_username")
            email = st.text_input("Email", key="register_email")
            password = st.text_input("Mot de passe", type="password", key="register_password")
            if st.form_submit_button("S'inscrire"):
                try:
                    response = requests.post(
                        "http://localhost:8000/auth/register",
                        json={"username": username, "email": email, "password": password},
                        headers=auth_headers()
                    )
                    response.raise_for_status()
                    st.success("Inscription réussie !")
                except requests.exceptions.RequestException as e:
                    st.error(f"Erreur d'inscription : {str(e)}")

    with col2:
        st.subheader("Se connecter")
        with st.form("login_form"):
            username = st.text_input("Nom d'utilisateur", key="login_username")
            password = st.text_input("Mot de passe", type="password", key="login_password")
            if st.form_submit_button("Se connecter"):
                try:
                    response = requests.post(
                        "http://localhost:8000/auth/login",
                        data={"username": username, "password": password},
                        headers=auth_headers()
                    )
                    response.raise_for_status()
                    st.success("Connexion réussie !")
                except requests.exceptions.RequestException as e:
                    st.error(f"Erreur de connexion : {str(e)}")

def render_tasks_module():
    """Module de gestion des tâches avec CRUD et filtres"""
    # Filtres
    st.sidebar.header("Filtres")
    status_filter = st.sidebar.selectbox(
        "Statut",
        ["Toutes", "En cours", "Terminée"],
        key="status_filter"
    )
    priority_filter = st.sidebar.selectbox(
        "Priorité",
        ["Toutes", "Basse", "Moyenne", "Haute"],
        key="priority_filter"
    )
    
    # Récupération des tâches
    try:
        params = {}
        if status_filter != "Toutes":
            params["status"] = status_filter
        if priority_filter != "Toutes":
            params["priority"] = priority_filter
            
        response = requests.get(
            "http://localhost:8000/tasks/",
            params=params,
            headers=auth_headers()
        )
        response.raise_for_status()
        tasks = response.json()
        
        if tasks:
            df = pd.DataFrame(tasks)
            st.dataframe(df)
        else:
            st.info("Aucune tâche trouvée avec ces critères")
            
    except requests.exceptions.RequestException as e:
        st.error("Impossible de charger les tâches")
        
    # Création de tâche
    st.subheader("Créer une tâche")
    with st.form("create_task_form"):
        title = st.text_input("Titre", key="create_title")
        description = st.text_area("Description", key="create_description")
        status = st.selectbox("Statut", ["En cours", "Terminée"], key="create_status")
        priority = st.selectbox("Priorité", ["Basse", "Moyenne", "Haute"], key="create_priority")
        
        if st.form_submit_button("Créer"):
            try:
                response = requests.post(
                    "http://localhost:8000/tasks/",
                    json={
                        "title": title,
                        "description": description,
                        "status": status,
                        "priority": priority
                    },
                    headers=auth_headers()
                )
                response.raise_for_status()
                st.success("Tâche créée avec succès !")
            except requests.exceptions.RequestException as e:
                st.error(f"Erreur lors de la création : {str(e)}")
    
    # Édition/Suppression
    st.subheader("Modifier/Supprimer une tâche")
    if tasks:
        task_ids = [task["id"] for task in tasks]
        selected_id = st.selectbox("Sélectionner une tâche", task_ids, key="select_task")
        
        # Récupérer les détails de la tâche sélectionnée
        try:
            response = requests.get(
                f"http://localhost:8000/tasks/{selected_id}",
                headers=auth_headers()
            )
            response.raise_for_status()
            task = response.json()
            
            # Formulaire d'édition
            with st.form("edit_task_form"):
                title = st.text_input("Titre", task["title"], key="edit_title")
                description = st.text_area("Description", task["description"], key="edit_description")
                status = st.selectbox("Statut", ["En cours", "Terminée"], index=["En cours", "Terminée"].index(task["status"]), key="edit_status")
                priority = st.selectbox("Priorité", ["Basse", "Moyenne", "Haute"], index=["Basse", "Moyenne", "Haute"].index(task["priority"]), key="edit_priority")
                
                if st.form_submit_button("Modifier"):
                    try:
                        response = requests.put(
                            f"http://localhost:8000/tasks/{selected_id}",
                            json={
                                "title": title,
                                "description": description,
                                "status": status,
                                "priority": priority
                            },
                            headers=auth_headers()
                        )
                        response.raise_for_status()
                        st.success("Tâche mise à jour avec succès !")
                    except requests.exceptions.RequestException as e:
                        st.error(f"Erreur lors de la mise à jour : {str(e)}")
                
                if st.form_submit_button("Supprimer"):
                    try:
                        response = requests.delete(
                            f"http://localhost:8000/tasks/{selected_id}",
                            headers=auth_headers()
                        )
                        response.raise_for_status()
                        st.success("Tâche supprimée avec succès !")
                    except requests.exceptions.RequestException as e:
                        st.error(f"Erreur lors de la suppression : {str(e)}")
        except requests.exceptions.RequestException as e:
            st.error("Impossible de charger les détails de la tâche")
    else:
        st.info("Aucune tâche à modifier/supprimer")

def render_dashboard_module():
    """Module dashboard avec métriques agrégées"""
    try:
        response = requests.get(
            "http://localhost:8000/tasks/",
            headers=auth_headers()
        )
        response.raise_for_status()
        tasks = response.json()
        
        total_tasks = len(tasks)
        completed_tasks = sum(1 for t in tasks if t["status"] == "Terminée")
        pending_tasks = total_tasks - completed_tasks
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Total tâches", total_tasks)
        col2.metric("Tâches terminées", completed_tasks)
        col3.metric("Tâches en cours", pending_tasks)
        
        # Progression
        st.progress(completed_tasks / total_tasks if total_tasks > 0 else 0)
        
    except requests.exceptions.RequestException as e:
        st.error("Impossible de charger les métriques du dashboard")

def render_ci_cd_module():
    """Module CI/CD (placeholder)"""
    st.info("Pipeline CI/CD en cours de développement")
    st.text("Dernière build : réussie")

# ────────────────────────────────────────────────────────────────────────────
# ─── GESTION DE LA NAVIGATION ───────────────────────────────────────────────
# ────────────────────────────────────────────────────────────────────────────

pages = {
    "auth": ("Authentification", render_auth_module),
    "tasks": ("Mes tâches", render_tasks_module),
    "dashboard": ("Tableau de bord", render_dashboard_module),
    "ci_cd": ("CI/CD", render_ci_cd_module)
}

# Navigation sidebar
st.sidebar.title("Navigation")
page_labels = [v[0] for v in pages.values()]
page_values = [k for k in pages.keys()]
current_idx = page_values.index(st.session_state.current_page) if st.session_state.current_page in page_values else 0

selected_label = st.sidebar.radio("Aller à", page_labels, index=current_idx)
selected_key = [k for k, v in pages.items() if v[0] == selected_label][0]
st.session_state.current_page = selected_key

# ────────────────────────────────────────────────────────────────────────────
# ─── RENDU DE LA PAGE ACTUELLE ───────────────────────────────────────────────
# ────────────────────────────────────────────────────────────────────────────

try:
    pages[st.session_state.current_page][1]()
except KeyError:
    st.error("Module non trouvé")
except requests.exceptions.ConnectionError:
    st.error("Backend non disponible — vérifiez que le serveur tourne.")