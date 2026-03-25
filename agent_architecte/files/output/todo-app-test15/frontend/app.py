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

def dashboard_module():
    """Affiche les métriques et un résumé des tâches."""
    try:
        response = requests.get("http://localhost:8000/tasks", headers=auth_headers())
        response.raise_for_status()
        tasks = response.json()
        
        if not tasks:
            st.info("Aucune tâche trouvée")
            return
            
        df = pd.DataFrame(tasks)
        
        # Calcul des métriques
        total_tasks = len(tasks)
        pending_tasks = len([t for t in tasks if t["status"] == "À faire"])
        in_progress = len([t for t in tasks if t["status"] == "En cours"])
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Tâches totales", total_tasks)
        col2.metric("À faire", pending_tasks)
        col3.metric("En cours", in_progress)
        
        st.progress(in_progress / total_tasks if total_tasks > 0 else 0)
        
        st.subheader("Dernières tâches")
        st.dataframe(df[["title", "status", "due_date"]].tail(5))
        
    except requests.exceptions.ConnectionError:
        st.error("Backend non disponible — vérifiez que le serveur tourne.")
    except Exception as e:
        st.error(f"Erreur lors du chargement des tâches: {str(e)}")

def tasks_module():
    """Gère la création, modification et suppression des tâches."""
    try:
        # Création de tâche
        with st.form("create_task_form", clear_on_submit=True):
            st.subheader("Nouvelle tâche")
            title = st.text_input("Titre", key="new_title")
            status = st.selectbox("Statut", ["À faire", "En cours", "Terminé"], key="new_status")
            due_date = st.date_input("Date échéance", key="new_due_date")
            submitted = st.form_submit_button("Créer")
            
            if submitted and title:
                payload = {"title": title, "status": status, "due_date": str(due_date)}
                response = requests.post("http://localhost:8000/tasks", headers=auth_headers(), json=payload)
                if response.status_code == 200:
                    st.success("Tâche créée avec succès")
                else:
                    st.error(f"Erreur création: {response.json().get('detail', 'Inconnue')}")
        
        # Liste des tâches
        response = requests.get("http://localhost:8000/tasks", headers=auth_headers())
        response.raise_for_status()
        tasks = response.json()
        
        if not tasks:
            st.info("Aucune tâche trouvée")
            return
            
        df = pd.DataFrame(tasks)
        st.subheader("Liste des tâches")
        st.dataframe(df[["title", "status", "due_date"]])
        
        # Actions par tâche
        for task in tasks:
            with st.expander(f"{task['title']} ({task['status']})"):
                if st.button(f"Modifier {task['id']}", key=f"edit_{task['id']}"):
                    st.session_state.edit_task_id = task["id"]
                    st.session_state.edit_title = task["title"]
                    st.session_state.edit_status = task["status"]
                    st.session_state.edit_due_date = task["due_date"]
                
                if st.button(f"Supprimer {task['id']}", key=f"delete_{task['id']}"):
                    if st.checkbox(f"Confirmer suppression {task['id']}", key=f"confirm_delete_{task['id']}"):
                        response = requests.delete(f"http://localhost:8000/tasks/{task['id']}", headers=auth_headers())
                        if response.status_code == 200:
                            st.success("Tâche supprimée")
                            st.experimental_rerun()
                        else:
                            st.error(f"Erreur suppression: {response.json().get('detail', 'Inconnue')}")
        
        # Formulaire de modification
        if "edit_task_id" in st.session_state:
            task_id = st.session_state.edit_task_id
            with st.form(f"edit_form_{task_id}", clear_on_submit=True):
                st.subheader(f"Modifier la tâche #{task_id}")
                title = st.text_input("Titre", value=st.session_state.edit_title, key=f"edit_title_{task_id}")
                status = st.selectbox("Statut", ["À faire", "En cours", "Terminé"], 
                                    index=["À faire", "En cours", "Terminé"].index(st.session_state.edit_status),
                                    key=f"edit_status_{task_id}")
                due_date = st.date_input("Date échéance", value=st.session_state.edit_due_date,
                                        key=f"edit_due_date_{task_id}")
                
                submitted = st.form_submit_button("Mettre à jour")
                
                if submitted:
                    payload = {
                        "title": title,
                        "status": status,
                        "due_date": str(due_date)
                    }
                    response = requests.put(f"http://localhost:8000/tasks/{task_id}", 
                                           headers=auth_headers(), json=payload)
                    if response.status_code == 200:
                        st.success("Tâche mise à jour")
                        del st.session_state.edit_task_id
                        st.session_state.edit_title = ""
                        st.session_state.edit_status = ""
                        st.session_state.edit_due_date = ""
                        st.experimental_rerun()
                    else:
                        st.error(f"Erreur modification: {response.json().get('detail', 'Inconnue')}")
    
    except requests.exceptions.ConnectionError:
        st.error("Backend non disponible — vérifiez que le serveur tourne.")
    except Exception as e:
        st.error(f"Erreur lors de l'opération: {str(e)}")

def app():
    """Application principale avec navigation entre modules."""
    if "current_page" not in st.session_state:
        st.session_state.current_page = "dashboard"
    
    # Navigation sidebar
    MODULES = [("Tableau de bord", "dashboard"), ("Gestion des tâches", "tasks")]
    labels = [m[0] for m in MODULES]
    values = [m[1] for m in MODULES]
    
    current_idx = values.index(st.session_state.current_page) if st.session_state.current_page in values else 0
    selected = st.sidebar.radio("Navigation", labels, index=current_idx)
    st.session_state.current_page = values[labels.index(selected)]
    
    # Contenu principal
    if st.session_state.current_page == "dashboard":
        dashboard_module()
    elif st.session_state.current_page == "tasks":
        tasks_module()

if __name__ == "__main__":
    app()