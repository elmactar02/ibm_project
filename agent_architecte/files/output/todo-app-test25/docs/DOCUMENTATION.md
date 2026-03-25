# Documentation d'Architecture — todo-app-test25

## Vue d'ensemble
**todo-app-test25** est une application full-stack de gestion de tâches (To-Do list) avec authentification sécurisée et fonctionnalités de filtrage avancées. Le système suit une architecture **client-serveur** avec :
- **Frontend** : SPA React (TypeScript) pour une expérience utilisateur réactive.
- **Backend** : API REST FastAPI (Python) pour la logique métier et l'authentification JWT.
- **Base de données** : PostgreSQL pour le stockage persistant des utilisateurs et tâches.
- **CI/CD** : Pipeline GitHub Actions pour l'automatisation des tests et déploiements.

L'application cible des utilisateurs individuels souhaitant organiser leurs tâches quotidiennes avec des filtres par statut (`todo`, `in_progress`, `done`) et priorité (`low`, `medium`, `high`).

---

## Décisions d'architecture

### 1. **Choix technologiques**
- **Frontend** :
  - **React 18 + TypeScript** : Pour une base solide avec typage statique et une communauté active.
  - **Vite** : Bundler ultra-rapide pour le développement et la production.
  - **Tailwind CSS** : Design système utilitaire pour une UI cohérente sans CSS personnalisé lourd.
  - **React Router v6** : Gestion des routes avec protection des pages privées.

- **Backend** :
  - **FastAPI** : Framework Python moderne pour des APIs performantes avec documentation automatique (OpenAPI/Swagger).
  - **SQLAlchemy ORM** : Abstraction de la base de données avec support PostgreSQL.
  - **Pydantic** : Validation des données et gestion des configurations.
  - **JWT** : Authentification stateless avec tokens courts (30 minutes) pour la sécurité.

- **Base de données** :
  - **PostgreSQL 15** : SGBD relationnel robuste avec support des enums et des indexes pour les filtres.
  - **Alembic** : Outil de migration pour gérer l'évolution du schéma.

- **CI/CD** :
  - **GitHub Actions** : Intégration native avec le dépôt Git pour des workflows automatisés (tests, build, déploiement).

### 2. **Séparation des responsabilités**
L'architecture suit le principe **SOLID** avec :
- **Frontend** : Gère uniquement la présentation et les interactions utilisateur.
- **Backend** : Centralise la logique métier, l'authentification et l'accès aux données.
- **Base de données** : Stocke les données de manière structurée avec des relations claires (ex: `User` 1-N `Task`).

### 3. **Modularité**
- **Backend** :
  - **Routers** : Séparation des routes par domaine (`/auth`, `/tasks`).
  - **Services** : Logique métier découplée des routes (ex: `users_service.py`, `tasks_service.py`).
  - **Database Layer** : Couche d'accès aux données réutilisable (SQLAlchemy).

- **Frontend** :
  - **Composants atomiques** : `TaskItem`, `FilterBar` pour une réutilisabilité maximale.
  - **Contextes React** : Gestion centralisée de l'état (authentification, tâches).

---

## Flux de données

### 1. **Authentification**
1. L'utilisateur soumet ses identifiants via le formulaire de login (`/login`).
2. Le frontend envoie une requête `POST /auth/login` avec `email` et `password`.
3. Le backend :
   - Vérifie les identifiants en base (via `users_service`).
   - Génère un JWT avec `python-jose` (payload: `user_id`, `exp`).
   - Retourne le token au frontend.
4. Le frontend stocke le token dans un **React Context** et l'inclut dans les headers des requêtes suivantes (`Authorization: Bearer <token>`).

### 2. **Gestion des tâches**
1. **Lecture** :
   - Le frontend appelle `GET /tasks?status=todo&priority=high` avec le JWT.
   - Le backend :
     - Valide le token (via `get_current_user`).
     - Récupère les tâches filtrées depuis PostgreSQL (avec indexes sur `user_id`, `status`, `priority`).
     - Retourne les données au frontend.
   - Le frontend affiche les tâches dans `TaskList`.

2. **Création/Modification** :
   - Le formulaire `TaskForm` envoie une requête `POST /tasks` ou `PUT /tasks/{id}`.
   - Le backend valide les données (Pydantic) et met à jour la base via `tasks_service`.
   - Le frontend met à jour son état local ou redirige vers le dashboard.

3. **Suppression** :
   - L'utilisateur clique sur "Supprimer" dans `TaskItem`.
   - Le frontend envoie `DELETE /tasks/{id}`.
   - Le backend supprime la tâche et confirme au frontend.

---

## Sécurité

### 1. **Authentification**
- **JWT** :
  - Tokens signés avec **HS256** (algorithme symétrique).
  - Durée de vie courte (30 minutes) pour limiter les risques de vol.
  - Stockage côté frontend dans un **React Context** (pas de `localStorage` pour éviter les XSS).
- **Hachage des mots de passe** :
  - Utilisation de **bcrypt** (via `passlib`) avec un coût de 12.
  - Les mots de passe ne sont jamais stockés en clair.

### 2. **Autorisation**
- **Middleware FastAPI** :
  - Vérification du JWT pour toutes les routes protégées (via dépendance `get_current_user`).
  - Vérification que l'utilisateur possède bien la tâche avant modification/suppression.
- **CORS** :
  - Configuration stricte pour n'autoriser que le domaine du frontend en production.

### 3. **Protection des données**
- **Base de données** :
  - Connexion chiffrée (SSL) entre l'API et PostgreSQL.
  - Indexes sur les champs fréquemment filtrés (`user_id`, `status`, `priority`) pour éviter les full scans.
- **Validation des entrées** :
  - Pydantic côté backend pour valider les données des requêtes.
  - Zod côté frontend pour une validation précoce.

### 4. **CI/CD**
- **GitHub Actions** :
  - Workflow déclenché sur `push` vers `main` :
    1. Exécution des tests unitaires (pytest pour le backend, Jest pour le frontend).
    2. Build des conteneurs Docker.
    3. Déploiement conditionnel (seulement si les tests passent).

---

## Scalabilité

### 1. **Backend**
- **Stateless** :
  - L'API FastAPI est stateless, ce qui permet de la scaler horizontalement avec un load balancer (ex: Nginx).
- **Base de données** :
  - PostgreSQL supporte le scaling vertical (ajout de ressources) et horizontal (réplication en lecture).
  - Les indexes sur `user_id`, `status`, et `priority` optimisent les requêtes même avec des millions de tâches.
- **Cache** :
  - **Option future** : Ajout de Redis pour cacher les listes de tâches fréquemment accédées (ex: dashboard).

### 2. **Frontend**
- **Code splitting** :
  - React Router permet de charger les pages dynamiquement (ex: `TaskFormPage` seulement quand nécessaire).
- **Optimisation des images** :
  - Utilisation de Vite pour optimiser les assets statiques.

### 3. **Déploiement**
- **Conteneurs** :
  - Docker pour l'API et PostgreSQL, avec Docker Compose pour le développement local.
  - En production, déploiement sur des services comme **Render** ou **Heroku** pour le backend, et **GitHub Pages** ou **Vercel** pour le frontend.
- **CI/CD** :
  - Pipeline GitHub Actions pour des déploiements automatisés et reproductibles.

### 4. **Monitoring**
- **Logs** :
  - Structurés (JSON) pour une intégration facile avec des outils comme ELK ou Datadog.
- **Métriques** :
  - **Option future** : Ajout de Prometheus pour surveiller les performances de l'API.

---

## Perspectives d'évolution
1. **Notifications** :
   - Ajout d'un système de notifications (ex: email pour les tâches en retard) avec un **message broker** (RabbitMQ).
2. **Collaboration** :
   - Extension pour permettre le partage de tâches entre utilisateurs (modèle `TaskSharing`).
3. **Mobile** :
   - Développement d'une application mobile avec React Native, réutilisant la même API backend.
4. **Analytics** :
   - Ajout de tableaux de bord analytiques (ex: nombre de tâches complétées par semaine).

---