# Documentation d'Architecture - todo-app-test13

## Vue d'ensemble
**todo-app-test13** est une application de gestion de tâches (To-Do list) conçue pour permettre aux utilisateurs de créer, organiser et suivre leurs tâches quotidiennes. L'application offre des fonctionnalités d'authentification sécurisée (JWT), un tableau de bord avec filtres avancés (statut et priorité), et une interface réactive construite avec React. Le backend est développé avec FastAPI pour une performance optimale et une intégration fluide avec PostgreSQL.

L'architecture suit une approche **modulaire et scalable**, séparant clairement les responsabilités entre frontend, backend et base de données. Le système est conçu pour être déployé via un pipeline CI/CD automatisé, assurant des mises à jour fréquentes et fiables.

## Décisions d'architecture

### Choix technologiques
1. **Backend (FastAPI)** :
   - **Pourquoi FastAPI ?** : Framework moderne pour Python, offrant une performance native (basé sur Starlette et Pydantic), une documentation automatique (OpenAPI/Swagger), et une intégration facile avec les bases de données asynchrones.
   - **Authentification JWT** : Utilisation de `python-jose` pour la génération/validation des tokens et `passlib` pour le hachage sécurisé des mots de passe (bcrypt).
   - **ORM** : SQLAlchemy pour une abstraction propre de la base de données, avec Alembic pour les migrations.

2. **Frontend (React + TypeScript)** :
   - **Pourquoi React ?** : Bibliothèque dominante pour les SPAs, avec un écosystème riche (React Router, Context API, etc.).
   - **TypeScript** : Ajoute une couche de typage statique pour réduire les erreurs et améliorer la maintenabilité.
   - **State Management** : Utilisation de React Context + useReducer pour une gestion d'état légère et scalable, évitant des bibliothèques externes comme Redux pour ce projet de taille moyenne.
   - **Styling** : Tailwind CSS pour un développement rapide et cohérent, avec des classes utilitaires.

3. **Base de données (PostgreSQL)** :
   - **Pourquoi PostgreSQL ?** : Base de données relationnelle robuste, supportant les transactions, les indexes avancés, et les types de données complexes (comme les enums pour le statut et la priorité des tâches).
   - **Indexation** : Indexes sur `user_id`, `status`, et `priority` pour optimiser les requêtes de filtrage.

4. **CI/CD (GitHub Actions)** :
   - Automatisation des tests (unitaires et d'intégration) et du déploiement. Le pipeline est déclenché à chaque push sur la branche principale.

### Structure modulaire
- **Backend** :
  - **Routers** : Séparation des routes `/auth` et `/tasks` pour une meilleure organisation.
  - **Services** : Logique métier encapsulée dans des modules dédiés (`users.py`, `tasks.py`).
  - **Utils** : Fonctions réutilisables (JWT, sécurité) isolées pour une maintenance facile.

- **Frontend** :
  - **Pages** : Composants de haut niveau pour chaque route (`LoginPage`, `DashboardPage`).
  - **Composants réutilisables** : `TaskList`, `TaskForm`, `ProtectedRoute` pour une cohérence UI/UX.
  - **Contextes** : `AuthContext` et `TaskContext` pour partager l'état global sans prop drilling.

## Flux de données

### Authentification
1. L'utilisateur s'inscrit ou se connecte via `/auth/register` ou `/auth/login`.
2. Le backend valide les credentials, génère un token JWT, et le retourne au frontend.
3. Le frontend stocke le token dans `localStorage` et l'ajoute aux headers des requêtes authentifiées.
4. Pour chaque requête protégée, le backend valide le token JWT avant de traiter la demande.

### Gestion des tâches
1. L'utilisateur accède au tableau de bord (`/`), protégé par `ProtectedRoute`.
2. Le frontend récupère les tâches via `GET /tasks` avec les filtres appliqués (statut, priorité).
3. Les tâches sont affichées dans `TaskList`, avec des options pour les modifier ou supprimer.
4. Les actions CRUD (Create, Read, Update, Delete) sont envoyées au backend via les endpoints `/tasks`.
5. Le backend met à jour la base de données et retourne la réponse au frontend, qui met à jour l'UI en conséquence.

### CI/CD
1. Un push sur la branche principale déclenche le pipeline GitHub Actions.
2. Les tests unitaires (backend et frontend) sont exécutés.
3. Si les tests passent, le code est déployé sur l'environnement de production (ex: Render, Railway).

## Sécurité

### Authentification
- **JWT** : Tokens signés avec HS256, expirant après 30 minutes. Stockés dans `localStorage` côté frontend (avec gestion des tokens expirés via interceptors Axios).
- **Mots de passe** : Hachés avec bcrypt (coût de 12) avant stockage en base de données.
- **CORS** : Configuré pour n'autoriser que les requêtes depuis le domaine du frontend.

### Protection des données
- **Validation des entrées** : Utilisation de Pydantic (backend) et React Hook Form (frontend) pour valider les données avant traitement.
- **SQL Injection** : Prévenue par l'utilisation de SQLAlchemy ORM (requêtes paramétrées).
- **CSRF** : Non applicable pour une API REST (le frontend est une SPA séparée).

### Sécurité des endpoints
- Tous les endpoints nécessitant une authentification sont protégés par un middleware JWT.
- Les endpoints sensibles (`/tasks`) vérifient que l'utilisateur est propriétaire de la ressource avant toute modification/suppression.

## Scalabilité

### Backend
- **Stateless** : Le backend est stateless, permettant une mise à l'échelle horizontale facile (ajout de serveurs FastAPI derrière un load balancer).
- **Base de données** :
  - Indexes sur les champs fréquemment interrogés (`user_id`, `status`, `priority`).
  - Possibilité de sharding par `user_id` si le nombre d'utilisateurs explose.
- **Cache** : Bien que non implémenté initialement, Redis pourrait être ajouté pour cacher les tâches fréquemment accédées.

### Frontend
- **Code splitting** : React Router permet un chargement paresseux des pages pour réduire le temps de chargement initial.
- **Optimisation des images** : Utilisation de formats modernes (WebP) et lazy loading.
- **Bundle size** : Vite est configuré pour produire des bundles optimisés avec tree-shaking.

### Déploiement
- **Conteneurisation** : Docker permet un déploiement cohérent sur n'importe quel environnement (local, cloud).
- **CI/CD** : GitHub Actions permet un déploiement continu et reproductible.
- **Cloud** : L'architecture est compatible avec des plateformes comme Render, Railway, ou AWS ECS pour une mise à l'échelle automatique.

### Monitoring
- **Logs** : Structurés (JSON) pour une intégration facile avec des outils comme ELK ou Datadog.
- **Health checks** : Endpoint `/health` pour surveiller l'état du backend.
- **Metrics** : Possibilité d'ajouter Prometheus pour surveiller les performances.

---