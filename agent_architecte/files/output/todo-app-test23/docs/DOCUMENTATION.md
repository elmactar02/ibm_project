# Documentation d'Architecture — Todo App Test23

## Vue d'ensemble
**todo-app-test23** est une application full-stack de gestion de tâches (To-Do list) avec authentification JWT, permettant aux utilisateurs de créer, modifier, supprimer et filtrer leurs tâches par statut et priorité. L'architecture suit une approche **modulaire et scalable**, séparant clairement les responsabilités entre frontend (React), backend (FastAPI) et base de données (PostgreSQL).

L'application est conçue pour être **déployée automatiquement** via un pipeline CI/CD (GitHub Actions), avec une stack technique moderne et légère. Les utilisateurs interagissent avec une **SPA (Single Page Application)** qui communique avec une API RESTful sécurisée.

---

## Décisions d'architecture

### 1. Séparation des couches (Backend)
Le backend est structuré en **3 couches principales** :
- **Routers (FastAPI)** : Gèrent les requêtes HTTP et les réponses. Chaque route est associée à un service métier.
- **Services** : Contiennent la logique métier (ex: validation des tâches, gestion des utilisateurs). Ils interagissent avec la couche database.
- **Database Layer** : Utilise SQLAlchemy ORM pour abstraire les opérations PostgreSQL. Les migrations sont gérées via Alembic.

**Justification** : Cette séparation permet une maintenance facile et des tests unitaires isolés. Par exemple, les services peuvent être testés sans dépendre de la base de données (mocking).

### 2. Authentification JWT
- **Approche** : JWT (JSON Web Tokens) avec une durée de vie de 30 minutes. Les tokens sont générés côté backend (FastAPI) et stockés côté frontend (localStorage).
- **Sécurité** :
  - Hachage des mots de passe avec **bcrypt** (via passlib).
  - Vérification des tokens à chaque requête protégée (via FastAPI's `Depends`).
  - Utilisation de `python-jose` pour la gestion des tokens (signature/validation).

**Justification** : JWT est léger, scalable et évite les sessions serveur. Le choix de bcrypt offre une protection robuste contre les attaques par force brute.

### 3. Frontend (React + TypeScript)
- **State Management** : React Context + useReducer pour l'état global (authentification et tâches). Évite l'ajout de bibliothèques externes comme Redux pour une complexité réduite.
- **Styling** : Tailwind CSS pour une approche **utility-first**, permettant un développement rapide sans sacrifier la maintenabilité.
- **Routing** : React Router v6 pour la navigation entre pages (avec protection des routes privées).

**Justification** : TypeScript améliore la robustesse du code, tandis que Tailwind CSS accélère le développement des interfaces. React Context est suffisant pour une application de cette taille.

### 4. Base de données (PostgreSQL)
- **Modèles** :
  - `User` : Stocke les emails et mots de passe hachés.
  - `Task` : Contient les champs `title`, `description`, `status`, `priority`, et une relation Many-to-One avec `User`.
- **Index** : Ajout d'index sur `user_id` (Task) et `email` (User) pour optimiser les requêtes.
- **Migrations** : Alembic pour gérer les évolutions du schéma.

**Justification** : PostgreSQL est un choix fiable pour les applications relationnelles. Les indexes améliorent les performances des requêtes fréquentes (ex: liste des tâches d'un utilisateur).

### 5. CI/CD (GitHub Actions)
- **Pipeline** :
  1. **Tests** : Exécution des tests unitaires (backend et frontend) à chaque push.
  2. **Build** : Construction des images Docker (backend et frontend).
  3. **Déploiement** : Déploiement automatique sur des services comme Render (backend) et GitHub Pages (frontend).

**Justification** : Automatiser le déploiement réduit les erreurs humaines et accélère les releases. GitHub Actions est intégré nativement avec les repositories GitHub.

---

## Flux de données

### 1. Authentification
1. L'utilisateur soumet ses identifiants via le formulaire de login (frontend).
2. Le frontend envoie une requête POST à `/auth/login` avec l'email et le mot de passe.
3. Le backend (FastAPI) :
   - Vérifie les identifiants dans la base de données.
   - Génère un token JWT si les identifiants sont valides.
4. Le token est renvoyé au frontend et stocké dans `localStorage`.
5. Pour les requêtes suivantes, le token est ajouté dans l'en-tête `Authorization`.

### 2. Gestion des tâches
1. **Création d'une tâche** :
   - L'utilisateur remplit le formulaire `TaskForm` (frontend).
   - Le frontend envoie une requête POST à `/tasks` avec les données de la tâche + le token JWT.
   - Le backend valide le token, crée la tâche en base de données, et renvoie la tâche créée.
2. **Liste des tâches** :
   - Le frontend envoie une requête GET à `/tasks` avec des filtres optionnels (status, priority).
   - Le backend récupère les tâches de l'utilisateur depuis la base de données et applique les filtres.
   - Les tâches sont affichées dans `TaskList`.
3. **Modification/Suppression** :
   - Similaire à la création, mais avec des requêtes PUT/DELETE vers `/tasks/{id}`.

### 3. CI/CD
1. Un développeur pousse du code sur la branche `main`.
2. GitHub Actions déclenche le pipeline :
   - Exécution des tests (backend: pytest, frontend: vitest).
   - Construction des images Docker.
   - Déploiement sur les services cibles (ex: Render pour le backend).

---

## Sécurité

### 1. Authentification
- **JWT** : Tokens signés avec une clé secrète (générée via `secrets.token_urlsafe(32)`). Durée de vie limitée à 30 minutes.
- **Hachage des mots de passe** : Utilisation de bcrypt (coût de 12) pour stocker les mots de passe en base de données.
- **Protection CSRF** : Désactivée pour une API RESTful (les tokens JWT sont envoyés dans l'en-tête `Authorization`).

### 2. Autorisation
- **Vérification des tokens** : Chaque endpoint protégé utilise FastAPI's `Depends` pour valider le token JWT.
- **Contrôle d'accès** : Les tâches sont associées à un utilisateur (via `user_id`). Le backend vérifie que l'utilisateur authentifié est bien le propriétaire de la tâche avant toute modification/suppression.

### 3. Sécurité des données
- **Base de données** :
  - Les mots de passe sont **jamais stockés en clair** (bcrypt).
  - Les connexions à PostgreSQL sont sécurisées via des variables d'environnement (pas de mots de passe en dur).
- **Frontend** :
  - Les tokens JWT sont stockés dans `localStorage` (risque de XSS, mais acceptable pour une application de cette taille). Pour une sécurité renforcée, `httpOnly cookies` pourraient être utilisés.

### 4. CI/CD
- **Secrets** : Les variables sensibles (ex: `SECRET_KEY`, `DATABASE_URL`) sont stockées dans les secrets GitHub Actions.
- **Tests** : Les tests unitaires incluent des vérifications de sécurité (ex: validation des tokens JWT).

---

## Scalabilité

### 1. Backend (FastAPI)
- **Stateless** : FastAPI est stateless, ce qui permet de scaler horizontalement en ajoutant des instances derrière un load balancer.
- **Base de données** :
  - PostgreSQL supporte le scaling vertical (augmentation des ressources).
  - Pour un scaling horizontal, une réplication maître-esclave pourrait être mise en place.
- **Cache** : Non implémenté pour cette version, mais Redis pourrait être ajouté pour cacher les listes de tâches fréquemment accédées.

### 2. Frontend (React)
- **SPA** : Le frontend est une SPA, ce qui réduit la charge sur le serveur (le code est servi une seule fois).
- **Optimisations** :
  - Code splitting (React.lazy) pour réduire la taille du bundle initial.
  - Utilisation de Tailwind CSS pour des styles optimisés (pas de CSS inutilisé).

### 3. CI/CD
- **Pipeline parallèle** : Les tests backend et frontend peuvent être exécutés en parallèle pour réduire le temps de build.
- **Déploiement bleu-vert** : Pour les mises à jour sans temps d'arrêt, une stratégie de déploiement bleu-vert pourrait être implémentée.

### 4. Monitoring
- **Logs** : Ajout de logs structurés (JSON) pour le backend (ex: via `structlog`).
- **Métriques** : Intégration future avec Prometheus/Grafana pour surveiller les performances.

---

## Contraintes et Limitations

1. **Complexité** : L'application est conçue pour une **complexité moyenne** (gestion des tâches + authentification). Pour des fonctionnalités avancées (ex: collaboration multi-utilisateurs), une refactorisation serait nécessaire.
2. **Stockage des tokens** : `localStorage` est vulnérable aux attaques XSS. Une alternative serait d'utiliser `httpOnly cookies` (mais cela complique le CORS).
3. **Base de données** : PostgreSQL est un choix solide, mais pour des applications avec des millions d'utilisateurs, une base de données NoSQL (ex: MongoDB) pourrait être envisagée pour les tâches.
4. **CI/CD** : Le pipeline actuel est basique. Pour des projets plus grands, des étapes supplémentaires (ex: tests d'intégration, scans de sécurité) seraient nécessaires.

---

## Améliorations futures

1. **Notifications** : Ajout de notifications en temps réel (ex: WebSockets) pour les mises à jour de tâches.
2. **Collaboration** : Permettre à plusieurs utilisateurs de partager des tâches (nécessiterait un modèle `TaskSharing`).
3. **Offline** : Implémenter un mode hors ligne avec synchronisation ultérieure (ex: via Service Workers + IndexedDB).
4. **Tests E2E** : Ajouter des tests end-to-end avec Cypress ou Playwright.
5. **Internationalisation** : Support multilingue pour le frontend (ex: i18next).

---