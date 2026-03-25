import streamlit as st
import requests
import pandas as pd
from datetime import datetime

# ────────────────────────────────────────────────────────────────────────────
# Configuration de base
# ────────────────────────────────────────────────────────────────────────────
BASE_URL = "http://localhost:8000"

# ────────────────────────────────────────────────────────────────────────────
# Fonctions utilitaires
# ────────────────────────────────────────────────────────────────────────────
def fetch_tasks():
    """Récupère la liste des tâches avec filtres"""
    try:
        params = {
            "status": st.session_state.get("filter_status", ""),
            "priority": st.session_state.get("filter_priority", "")
        }
        response = requests.get(f"{BASE_URL}/tasks", 
                              headers=auth_headers(), 
                              params=params)
        response.raise_for_status()
        return pd.DataFrame(response.json())
    except requests.exceptions.ConnectionError:
        st.error("Backend non disponible — vérifiez que le serveur tourne.")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Erreur lors de la récupération des tâches: {str(e)}")
        return pd.DataFrame()

def create_task(data):
    """Crée une nouvelle tâche"""
    try:
        response = requests.post(f"{BASE_URL}/tasks", 
                               headers=auth_headers(), 
                               json=data)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.ConnectionError:
        st.error("Backend non disponible — vérifiez que le serveur tourne.")
        return None
    except Exception as e:
        st.error(f"Erreur lors de la création de la tâche: {str(e)}")
        return None

def update_task(task_id, data):
    """Met à jour une tâche existante"""
    try:
        response = requests.put(f"{BASE_URL}/tasks/{task_id}", 
                              headers=auth_headers(), 
                              json=data)
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
        response = requests.delete(f"{BASE_URL}/tasks/{task_id}", 
                                 headers=auth_headers())
        response.raise_for_status()
        return True
    except requests.exceptions.ConnectionError:
        st.error("Backend non disponible — vérifiez que le serveur tourne.")
        return False
    except Exception as e:
        st.error(f"Erreur lors de la suppression de la tâche: {str(e)}")
        return False

def get_task(task_id):
    """Récupère les détails d'une tâche"""
    try:
        response = requests.get(f"{BASE_URL}/tasks/{task_id}", 
                              headers=auth_headers())
        response.raise_for_status()
        return response.json()
    except requests.exceptions.ConnectionError:
        st.error("Backend non disponible — vérifiez que le serveur tourne.")
        return None
    except Exception as e:
        st.error(f"Erreur lors de la récupération de la tâche: {str(e)}")
        return None

# ────────────────────────────────────────────────────────────────────────────
# Initialisation de la session
# ────────────────────────────────────────────────────────────────────────────
if "current_page" not in st.session_state:
    st.session_state.current_page = "dashboard"

if "tasks" not in st.session_state:
    st.session_state.tasks = fetch_tasks()

# ────────────────────────────────────────────────────────────────────────────
# Navigation sidebar
# ────────────────────────────────────────────────────────────────────────────
st.sidebar.title("Navigation")
pages = [("Tableau de bord", "dashboard"), ("Mes tâches", "tasks"), ("Créer", "create_task")]
labels = [p[0] for p in pages]
values = [p[1] for p in pages]

current_idx = values.index(st.session_state.current_page) if st.session_state.current_page in values else 0
selected = st.sidebar.radio("Navigation", labels, index=current_idx)
st.session_state.current_page = values[labels.index(selected)]

# ────────────────────────────────────────────────────────────────────────────
# Contenu principal
# ────────────────────────────────────────────────────────────────────────────
if st.session_state.current_page == "dashboard":
    st.title("Tableau de bord")
    st.write("Bienvenue dans l'application de gestion de tâches")
    
elif st.session_state.current_page == "tasks":
    st.title("Mes tâches")
    
    # Filtres
    col1, col2 = st.columns(2)
    with col1:
        st.selectbox("Statut", 
                    ["", "en attente", "en cours", "terminé"],
                    key="filter_status",
                    on_change=lambda: st.session_state.update({"current_page": "tasks"}))
    with col2:
        st.selectbox("Priorité", 
                    ["", "faible", "moyenne", "élevée"],
                    key="filter_priority",
                    on_change=lambda: st.session_state.update({"current_page": "tasks"}))
    
    # Bouton création
    if st.button("Nouvelle tâche"):
        st.session_state.current_page = "create_task"
    
    # Liste des tâches
    tasks_df = fetch_tasks()
    if not tasks_df.empty:
        st.dataframe(tasks_df)
        
        # Actions par tâche
        for _, row in tasks_df.iterrows():
            col1, col2, col3 = st.columns([3, 1, 1])
            col1.write(f"**{row['title']}**")
            col2.button("Modifier", key=f"edit_{row['id']}", 
                       on_click=lambda id=row['id']: st.session_state.update({"current_page": "edit_task", "edit_task_id": id}))
            col3.button("Supprimer", key=f"delete_{row['id']}", 
                       on_click=lambda id=row['id']: delete_task(id))
    else:
        st.info("Aucune tâche trouvée")

elif st.session_state.current_page == "create_task":
    st.title("Créer une tâche")
    
    with st.form("create_task_form"):
        title = st.text_input("Titre")
        description = st.text_area("Description")
        status = st.selectbox("Statut", ["en attente", "en cours", "terminé"])
        priority = st.selectbox("Priorité", ["faible", "moyenne", "élevée"])
        due_date = st.date_input("Date d'échéance")
        
        submitted = st.form_submit_button("Créer")
        if submitted:
            task_data = {
                "title": title,
                "description": description,
                "status": status,
                "priority": priority,
                "due_date": due_date.isoformat()
            }
            result = create_task(task_data)
            if result:
                st.success("Tâche créée avec succès")
                st.session_state.current_page = "tasks"
            else:
                st.error("Échec de la création de la tâche")

elif st.session_state.current_page == "edit_task":
    task_id = st.session_state.get("edit_task_id")
    if task_id:
        task = get_task(task_id)
        if task:
            st.title(f"Modifier la tâche #{task_id}")
            
            with st.form("edit_task_form"):
                title = st.text_input("Titre", task["title"])
                description = st.text_area("Description", task["description"])
                status = st.selectbox("Statut", ["en attente", "en cours", "terminé"], index=["en attente", "en cours", "terminé"].index(task["status"]))
                priority = st.selectbox("Priorité", ["faible", "moyenne", "élevée"], index=["faible", "moyenne", "élevée"].index(task["priority"]))
                due_date = st.date_input("Date d'échéance", datetime.fromisoformat(task["due_date"]))
                
                submitted = st.form_submit_button("Enregistrer")
                if submitted:
                    task_data = {
                        "title": title,
                        "description": description,
                        "status": status,
                        "priority": priority,
                        "due_date": due_date.isoformat()
                    }
                    result = update_task(task_id, task_data)
                    if result:
                        st.success("Tâche mise à jour avec succès")
                        st.session_state.current_page = "tasks"
                    else:
                        st.error("Échec de la mise à jour de la tâche")
        else:
            st.error("Tâche non trouvée")
            if st.button("Retour"):
                st.session_state.current_page = "tasks"
    else:
        st.error("Aucune tâche sélectionnée")
        if st.button("Retour"):
            st.session_state.current_page = "tasks"