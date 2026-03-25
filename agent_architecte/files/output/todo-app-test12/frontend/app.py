import streamlit as st
from theme_runtime import inject_theme, get_auth_handler
import requests
import pandas as pd

# ── Thème client ───────────────────────────────────────────────────────────
_cfg  = inject_theme(st)
_auth = get_auth_handler(_cfg)

# ── Authentification ───────────────────────────────────────────────────────
_auth.require(st)

def auth_headers() -> dict:
    """Retourne les headers HTTP avec le Bearer token courant."""
    return _auth.headers(st)

# ── Fin du bloc thème / auth — code métier ci-dessous ────────────────────────

# ── États de session ─────────────────────────────────────────────────────────
if "current_page" not in st.session_state:
    st.session_state.current_page = "dashboard"

if "editing_task" not in st.session_state:
    st.session_state.editing_task = None

# ── Fonctions API ───────────────────────────────────────────────────────────
def get_tasks(status=None, priority=None):
    params = {}
    if status:
        params["status"] = status
    if priority:
        params["priority"] = priority
    try:
        r = requests.get("http://localhost:8000/tasks", headers=auth_headers(), params=params)
        r.raise_for_status()
        return r.json()
    except requests.exceptions.ConnectionError:
        st.error("Backend non disponible — vérifiez que le serveur tourne.")
        return []
    except Exception as e:
        st.error(f"Erreur lors de la récupération des tâches: {str(e)}")
        return []

def create_task(title, description, status, priority, due_date=None):
    payload = {
        "title": title,
        "description": description,
        "status": status,
        "priority": priority
    }
    if due_date:
        payload["due_date"] = due_date.strftime("%Y-%m-%d")
    try:
        r = requests.post("http://localhost:8000/tasks", headers=auth_headers(), json=payload)
        r.raise_for_status()
        return r.json()
    except requests.exceptions.ConnectionError:
        st.error("Backend non disponible — vérifiez que le serveur tourne.")
        return None
    except Exception as e:
        st.error(f"Erreur lors de la création de la tâche: {str(e)}")
        return None

def update_task(task_id, title, description, status, priority, due_date=None):
    payload = {
        "title": title,
        "description": description,
        "status": status,
        "priority": priority
    }
    if due_date:
        payload["due_date"] = due_date.strftime("%Y-%m-%d")
    try:
        r = requests.put(f"http://localhost:8000/tasks/{task_id}", headers=auth_headers(), json=payload)
        r.raise_for_status()
        return r.json()
    except requests.exceptions.ConnectionError:
        st.error("Backend non disponible — vérifiez que le serveur tourne.")
        return None
    except Exception as e:
        st.error(f"Erreur lors de la mise à jour de la tâche: {str(e)}")
        return None

def delete_task(task_id):
    try:
        r = requests.delete(f"http://localhost:8000/tasks/{task_id}", headers=auth_headers())
        r.raise_for_status()
        return True
    except requests.exceptions.ConnectionError:
        st.error("Backend non disponible — vérifiez que le serveur tourne.")
        return False
    except Exception as e:
        st.error(f"Erreur lors de la suppression de la tâche: {str(e)}")
        return False

# ── Composants UI ───────────────────────────────────────────────────────────
def dashboard_page():
    st.title("Tableau de bord")
    
    # Filtres
    col1, col2 = st.columns(2)
    with col1:
        status_filter = st.selectbox(
            "Statut",
            ["Toutes", "À faire", "En cours", "Terminée"],
            index=0
        )
    with col2:
        priority_filter = st.selectbox(
            "Priorité",
            ["Toutes", "Basse", "Moyenne", "Haute"],
            index=0
        )
    
    # Récupération des tâches
    tasks = get_tasks(
        status=status_filter if status_filter != "Toutes" else None,
        priority=priority_filter if priority_filter != "Toutes" else None
    )
    
    if not tasks:
        st.info("Aucune tâche trouvée avec ces critères.")
        return
    
    # Affichage des tâches
    df = pd.DataFrame(tasks)
    df = df[["id", "title", "status", "priority", "due_date", "created_at"]]
    df.columns = ["ID", "Titre", "Statut", "Priorité", "Échéance", "Créé le"]
    st.dataframe(df)
    
    # Formulaire de création/modification
    if st.session_state.editing_task:
        task = next((t for t in tasks if t["id"] == st.session_state.editing_task), None)
        if task:
            with st.form("edit_task_form", clear_on_submit=True):
                st.subheader(f"Modifier la tâche #{task['id']}")
                title = st.text_input("Titre", task["title"])
                description = st.text_area("Description", task["description"])
                status = st.selectbox("Statut", ["À faire", "En cours", "Terminée"], index=["À faire", "En cours", "Terminée"].index(task["status"]))
                priority = st.selectbox("Priorité", ["Basse", "Moyenne", "Haute"], index=["Basse", "Moyenne", "Haute"].index(task["priority"]))
                due_date = st.date_input("Échéance", value=task["due_date"] if task["due_date"] else None)
                
                submitted = st.form_submit_button("Mettre à jour")
                if submitted:
                    result = update_task(
                        task_id=task["id"],
                        title=title,
                        description=description,
                        status=status,
                        priority=priority,
                        due_date=due_date
                    )
                    if result:
                        st.success("Tâche mise à jour avec succès!")
                        st.session_state.editing_task = None
                        st.rerun()
                    else:
                        st.error("Échec de la mise à jour")
    else:
        with st.form("create_task_form", clear_on_submit=True):
            st.subheader("Créer une nouvelle tâche")
            title = st.text_input("Titre")
            description = st.text_area("Description")
            status = st.selectbox("Statut", ["À faire", "En cours", "Terminée"], index=0)
            priority = st.selectbox("Priorité", ["Basse", "Moyenne", "Haute"], index=0)
            due_date = st.date_input("Échéance")
            
            submitted = st.form_submit_button("Créer")
            if submitted:
                if not title or not description:
                    st.error("Titre et description sont requis")
                    return
                result = create_task(title, description, status, priority, due_date)
                if result:
                    st.success("Tâche créée avec succès!")
                    st.rerun()
                else:
                    st.error("Échec de la création")

    # Actions sur les tâches
    if tasks:
        selected_task_id = st.selectbox(
            "Sélectionner une tâche à modifier",
            [t["id"] for t in tasks],
            format_func=lambda x: f"#{x} - {next(t['title'] for t in tasks if t['id'] == x)}"
        )
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Modifier", key="edit_button"):
                st.session_state.editing_task = selected_task_id
                st.rerun()
        with col2:
            if st.button("Supprimer", key="delete_button"):
                if delete_task(selected_task_id):
                    st.success("Tâche supprimée avec succès!")
                    st.rerun()
                else:
                    st.error("Échec de la suppression")

# ── Navigation ─────────────────────────────────────────────────────────────
pages = [("Tableau de bord", "dashboard")]
labels = [p[0] for p in pages]
values = [p[1] for p in pages]

current_idx = values.index(st.session_state.current_page) if st.session_state.current_page in values else 0
selected = st.sidebar.radio("Navigation", labels, index=current_idx)
st.session_state.current_page = values[labels.index(selected)]

# ── Affichage de la page sélectionnée ─────────────────────────────────────────
if st.session_state.current_page == "dashboard":
    dashboard_page()