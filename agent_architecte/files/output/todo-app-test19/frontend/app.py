import streamlit as st
import requests
import pandas as pd
from datetime import datetime

# === CONFIGURATION ===
BASE_URL = "http://localhost:8000"

# === ÉTAT DE SESSION ===
if "current_page" not in st.session_state:
    st.session_state.current_page = "dashboard"

# === FONCTIONS UTILES ===
def get_tasks():
    try:
        response = requests.get(f"{BASE_URL}/tasks", headers=auth_headers())
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error("Erreur lors de la récupération des tâches")
        return []

def create_task(title, status, due_date):
    try:
        payload = {
            "title": title,
            "status": status,
            "due_date": due_date.isoformat() if due_date else None
        }
        response = requests.post(f"{BASE_URL}/tasks", headers=auth_headers(), json=payload)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error("Erreur lors de la création de la tâche")
        return None

def update_task(task_id, title, status, due_date):
    try:
        payload = {
            "title": title,
            "status": status,
            "due_date": due_date.isoformat() if due_date else None
        }
        response = requests.put(f"{BASE_URL}/tasks/{task_id}", headers=auth_headers(), json=payload)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error("Erreur lors de la mise à jour de la tâche")
        return None

def delete_task(task_id):
    try:
        response = requests.delete(f"{BASE_URL}/tasks/{task_id}", headers=auth_headers())
        response.raise_for_status()
        return True
    except requests.exceptions.RequestException as e:
        st.error("Erreur lors de la suppression de la tâche")
        return False

# === MODULES ===
def render_auth():
    st.title("Authentification")
    tab1, tab2 = st.tabs(["Connexion", "Inscription"])
    
    with tab1:
        with st.form("login_form"):
            email = st.text_input("Email")
            password = st.text_input("Mot de passe", type="password")
            submitted = st.form_submit_button("Se connecter")
            if submitted:
                try:
                    response = requests.post(f"{BASE_URL}/auth/login", 
                                           headers=auth_headers(),
                                           json={"email": email, "password": password})
                    response.raise_for_status()
                    st.success("Connexion réussie!")
                except requests.exceptions.RequestException as e:
                    st.error("Identifiants invalides")
    
    with tab2:
        with st.form("register_form"):
            username = st.text_input("Nom d'utilisateur")
            email = st.text_input("Email")
            password = st.text_input("Mot de passe", type="password")
            submitted = st.form_submit_button("S'inscrire")
            if submitted:
                try:
                    response = requests.post(f"{BASE_URL}/auth/register",
                                           headers=auth_headers(),
                                           json={"username": username, "email": email, "password": password})
                    response.raise_for_status()
                    st.success("Inscription réussie!")
                except requests.exceptions.RequestException as e:
                    st.error("Erreur lors de l'inscription")

def render_tasks():
    st.title("Gestion des tâches")
    
    # Création de tâche
    with st.form("create_task_form"):
        st.subheader("Nouvelle tâche")
        title = st.text_input("Titre")
        status = st.selectbox("Statut", ["pending", "in_progress", "completed"])
        due_date = st.date_input("Date d'échéance")
        submitted = st.form_submit_button("Créer")
        
        if submitted and title:
            result = create_task(title, status, due_date)
            if result:
                st.success("Tâche créée avec succès!")
    
    # Liste des tâches
    tasks = get_tasks()
    if tasks:
        df = pd.DataFrame(tasks)
        st.dataframe(df)
        
        # Sélection d'une tâche
        selected_id = st.selectbox("Modifier/Supprimer une tâche", 
                                 options=[t["id"] for t in tasks],
                                 format_func=lambda x: f"{x} - {next(t['title'] for t in tasks if t['id'] == x)}")
        
        selected_task = next((t for t in tasks if t["id"] == selected_id), None)
        if selected_task:
            with st.form(f"edit_task_form_{selected_id}"):
                st.subheader(f"Modifier la tâche #{selected_id}")
                new_title = st.text_input("Titre", value=selected_task["title"])
                new_status = st.selectbox("Statut", ["pending", "in_progress", "completed"], 
                                        index=["pending", "in_progress", "completed"].index(selected_task["status"]))
                new_due_date = st.date_input("Date d'échéance", 
                                           value=datetime.fromisoformat(selected_task["due_date"]) 
                                           if selected_task["due_date"] else None)
                
                col1, col2 = st.columns(2)
                with col1:
                    update_btn = st.form_submit_button("Mettre à jour")
                with col2:
                    delete_btn = st.form_submit_button("Supprimer")
                
                if update_btn:
                    result = update_task(selected_id, new_title, new_status, new_due_date)
                    if result:
                        st.success("Tâche mise à jour!")
                
                if delete_btn:
                    if delete_task(selected_id):
                        st.success("Tâche supprimée!")
    else:
        st.info("Aucune tâche trouvée")

def render_dashboard():
    st.title("Tableau de bord")
    
    tasks = get_tasks()
    if tasks:
        total_tasks = len(tasks)
        completed = sum(1 for t in tasks if t["status"] == "completed")
        pending = sum(1 for t in tasks if t["status"] == "pending")
        in_progress = sum(1 for t in tasks if t["status"] == "in_progress")
        
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total des tâches", total_tasks)
        col2.metric("Tâches terminées", completed)
        col3.metric("Tâches en cours", in_progress)
        col4.metric("Tâches en attente", pending)
        
        st.progress(completed / total_tasks if total_tasks > 0 else 0)
        
        st.subheader("Détails des tâches")
        df = pd.DataFrame(tasks)
        st.dataframe(df)
    else:
        st.info("Aucune donnée disponible")

def render_ci_cd():
    st.title("CI/CD")
    st.info("Module CI/CD - Intégration en cours")
    st.markdown("Statut du pipeline : ⚙️ En développement")

# === NAVIGATION ===
MODULES = {
    "auth": render_auth,
    "tasks": render_tasks,
    "dashboard": render_dashboard,
    "ci_cd": render_ci_cd
}

# === SIDEBAR NAVIGATION ===
st.sidebar.title("Navigation")
pages = [("Tableau de bord", "dashboard"), 
         ("Mes tâches", "tasks"), 
         ("Authentification", "auth"),
         ("CI/CD", "ci_cd")]
labels = [p[0] for p in pages]
values = [p[1] for p in pages]

current_idx = values.index(st.session_state.current_page) if st.session_state.current_page in values else 0
selected = st.sidebar.radio("Navigation", labels, index=current_idx)
st.session_state.current_page = values[labels.index(selected)]

# === RENDU ===
MODULES[st.session_state.current_page]()