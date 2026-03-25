import streamlit as st
from theme_runtime import inject_theme, get_auth_handler
import requests
from typing import Optional, Dict, List

# ── Thème client (relu depuis client_config.yaml à chaque refresh) ───────────
_cfg  = inject_theme(st)
_auth = get_auth_handler(_cfg)

# ── Authentification ─────────────────────────────────────────────────────────
_auth.require(st)

def auth_headers() -> dict:
    """Retourne les headers HTTP avec le Bearer token courant."""
    return _auth.headers(st)

# ── Fin du bloc thème / auth — code métier ci-dessous ────────────────────────

# ─────────────────────────────────────────────────────────────────────────────
# ──── CONFIGURATION GLOBALE ───────────────────────────────────────────────────
# ─────────────────────────────────────────────────────────────────────────────

MODULES_INTERNES = ["task_management", "dashboard", "ci_cd"]

if "current_page" not in st.session_state:
    st.session_state.current_page = "task_management"

# ─────────────────────────────────────────────────────────────────────────────
# ──── FONCTIONS DE BASE ───────────────────────────────────────────────────────
# ─────────────────────────────────────────────────────────────────────────────

def get_tasks(filters: Optional[Dict] = None) -> List[Dict]:
    """Récupère la liste des tâches avec filtres optionnels."""
    try:
        params = filters or {}
        response = requests.get("http://localhost:8000/tasks", 
                               headers=auth_headers(), 
                               params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.ConnectionError:
        st.error("Backend non disponible — vérifiez que le serveur tourne.")
        return []
    except requests.exceptions.HTTPError as e:
        st.error(f"Erreur API: {e.response.status_code}")
        return []

def create_task(task_data: Dict) -> Dict:
    """Crée une nouvelle tâche."""
    try:
        response = requests.post("http://localhost:8000/tasks", 
                               headers=auth_headers(), 
                               json=task_data)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.ConnectionError:
        st.error("Backend non disponible — vérifiez que le serveur tourne.")
    except requests.exceptions.HTTPError as e:
        st.error(f"Erreur API: {e.response.status_code}")
    return {}

def update_task(task_id: int, task_data: Dict) -> Dict:
    """Met à jour une tâche existante."""
    try:
        response = requests.put(f"http://localhost:8000/tasks/{task_id}", 
                               headers=auth_headers(), 
                               json=task_data)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.ConnectionError:
        st.error("Backend non disponible — vérifiez que le serveur tourne.")
    except requests.exceptions.HTTPError as e:
        st.error(f"Erreur API: {e.response.status_code}")
    return {}

def delete_task(task_id: int) -> bool:
    """Supprime une tâche."""
    try:
        response = requests.delete(f"http://localhost:8000/tasks/{task_id}", 
                                 headers=auth_headers())
        response.raise_for_status()
        return True
    except requests.exceptions.ConnectionError:
        st.error("Backend non disponible — vérifiez que le serveur tourne.")
    except requests.exceptions.HTTPError as e:
        st.error(f"Erreur API: {e.response.status_code}")
    return False

# ─────────────────────────────────────────────────────────────────────────────
# ──── COMPOSANTS UI ────────────────────────────────────────────────────────────
# ─────────────────────────────────────────────────────────────────────────────

def render_task_management():
    """Affiche l'interface de gestion des tâches."""
    st.title("Gestion des tâches")
    
    # Formulaire de création
    with st.form("create_task_form", clear_on_submit=True):
        st.subheader("Créer une nouvelle tâche")
        title = st.text_input("Titre", key="create_title")
        description = st.text_area("Description", key="create_description")
        priority = st.selectbox("Priorité", ["low", "medium", "high"], key="create_priority")
        status = st.selectbox("Statut", ["pending", "in_progress", "completed"], key="create_status")
        
        if st.form_submit_button("Créer"):
            if title and description:
                task_data = {
                    "title": title,
                    "description": description,
                    "priority": priority,
                    "status": status
                }
                result = create_task(task_data)
                if result:
                    st.success("Tâche créée avec succès!")
                    st.rerun()
            else:
                st.error("Veuillez remplir tous les champs obligatoires")
    
    # Filtres et liste des tâches
    st.subheader("Liste des tâches")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        filter_status = st.selectbox("Filtrer par statut", ["all", "pending", "in_progress", "completed"], 
                                   key="filter_status")
    with col2:
        filter_priority = st.selectbox("Filtrer par priorité", ["all", "low", "medium", "high"], 
                                     key="filter_priority")
    
    filters = {}
    if filter_status != "all":
        filters["status"] = filter_status
    if filter_priority != "all":
        filters["priority"] = filter_priority
    
    tasks = get_tasks(filters)
    
    if not tasks:
        st.info("Aucune tâche trouvée avec ces critères.")
        return
    
    # Tableau des tâches
    st.dataframe(tasks, use_container_width=True)
    
    # Actions par tâche
    for task in tasks:
        st.markdown("---")
        st.write(f"**{task['title']}**")
        st.write(f"Description: {task['description']}")
        st.write(f"Statut: {task['status']}")
        st.write(f"Priorité: {task['priority']}")
        
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            if st.button("Modifier", key=f"edit_{task['id']}"):
                st.session_state[f"edit_task_{task['id']}"] = task
        
        with col2:
            if st.button("Supprimer", key=f"delete_{task['id']}"):
                if st.checkbox("Êtes-vous sûr?", key=f"confirm_delete_{task['id']}"):
                    if delete_task(task["id"]):
                        st.success("Tâche supprimée!")
                        st.rerun()
        
        with col3:
            if st.button("Détails", key=f"details_{task['id']}"):
                st.session_state[f"view_task_{task['id']}"] = task
    
    # Formulaire d'édition
    for task in tasks:
        if f"edit_task_{task['id']}" in st.session_state:
            st.subheader(f"Modifier la tâche #{task['id']}")
            with st.form(f"edit_form_{task['id']}"):
                title = st.text_input("Titre", value=task["title"], key=f"edit_title_{task['id']}")
                description = st.text_area("Description", value=task["description"], 
                                         key=f"edit_description_{task['id']}")
                priority = st.selectbox("Priorité", ["low", "medium", "high"], 
                                      index=["low", "medium", "high"].index(task["priority"]),
                                      key=f"edit_priority_{task['id']}")
                status = st.selectbox("Statut", ["pending", "in_progress", "completed"], 
                                    index=["pending", "in_progress", "completed"].index(task["status"]),
                                    key=f"edit_status_{task['id']}")
                
                if st.form_submit_button("Mettre à jour"):
                    updated_task = {
                        "title": title,
                        "description": description,
                        "priority": priority,
                        "status": status
                    }
                    result = update_task(task["id"], updated_task)
                    if result:
                        st.success("Tâche mise à jour!")
                        st.rerun()
                if st.form_submit_button("Annuler"):
                    del st.session_state[f"edit_task_{task['id']}"]
                    st.rerun()

def render_dashboard():
    """Affiche le tableau de bord."""
    st.title("Tableau de bord")
    
    tasks = get_tasks()
    
    if not tasks:
        st.info("Aucune tâche trouvée.")
        return
    
    # Métriques
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total des tâches", len(tasks))
    with col2:
        st.metric("Tâches en cours", sum(1 for t in tasks if t["status"] == "in_progress"))
    with col3:
        st.metric("Tâches terminées", sum(1 for t in tasks if t["status"] == "completed"))
    
    # Graphiques
    st.subheader("Répartition par priorité")
    priority_counts = {"low": 0, "medium": 0, "high": 0}
    for task in tasks:
        priority_counts[task["priority"]] += 1
    
    st.bar_chart(priority_counts)
    
    st.subheader("Évolution des tâches")
    status_counts = {"pending": 0, "in_progress": 0, "completed": 0}
    for task in tasks:
        status_counts[task["status"]] += 1
    
    st.line_chart(status_counts)

def render_ci_cd():
    """Affiche l'interface CI/CD."""
    st.title("Pipeline CI/CD")
    st.info("Fonctionnalité à implémenter : Intégration avec le système de CI/CD")

# ─────────────────────────────────────────────────────────────────────────────
# ──── NAVIGATION ──────────────────────────────────────────────────────────────
# ─────────────────────────────────────────────────────────────────────────────

pages = [
    ("Gestion des tâches", "task_management"),
    ("Tableau de bord", "dashboard"),
    ("Pipeline CI/CD", "ci_cd")
]

labels = [p[0] for p in pages]
values = [p[1] for p in pages]

current_idx = values.index(st.session_state.current_page) if st.session_state.current_page in values else 0
selected = st.sidebar.radio("Navigation", labels, index=current_idx)
st.session_state.current_page = values[labels.index(selected)]

# ─────────────────────────────────────────────────────────────────────────────
# ──── RENDU DE LA PAGE ACTUELLE ────────────────────────────────────────────────
# ─────────────────────────────────────────────────────────────────────────────

if st.session_state.current_page == "task_management":
    render_task_management()
elif st.session_state.current_page == "dashboard":
    render_dashboard()
elif st.session_state.current_page == "ci_cd":
    render_ci_cd()