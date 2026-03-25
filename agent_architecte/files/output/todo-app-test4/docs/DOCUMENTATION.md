# Documentation d'Architecture - Todo App Test4

## Vue d'ensemble
**todo-app-test4** est une application full-stack de gestion de tâches (To-Do list) avec authentification sécurisée, permettant aux utilisateurs de créer, organiser et suivre leurs tâches quotidiennes. Le projet suit une architecture moderne **SPA (Single Page Application)** avec un backend RESTful en Python et un frontend React, le tout containerisé pour une portabilité optimale.

L'application cible des utilisateurs individuels cherchant à organiser leur productivité personnelle, avec des fonctionnalités avancées comme le filtrage par statut/priorité et une authentification robuste via JWT.

## Décisions d'architecture

### Choix technologiques
1. **Backend (FastAPI)**:
   - Sélectionné pour sa performance native (async), sa documentation automatique (OpenAPI) et son écosystème Python mature.
   - Structure modulaire avec séparation claire entre routes, services et couche de données.
   - Utilisation de **SQLAlchemy** pour l'abstraction de la base de données (SQLite en dev, PostgreSQL en prod).

2. **Frontend (React + TypeScript)**:
   - React 18 pour les performances et le support des hooks.
   - TypeScript pour la sécurité de typage et la maintenabilité.
   - **Vite** comme bundler pour un développement rapide et des builds optimisés.

3. **Base de données**:
   - **SQLite** en développement pour sa simplicité et son intégration native avec Python.
   - **PostgreSQL** en production pour sa fiabilité, ses performances et son support des index avancés.
   - **Alembic** pour les migrations de schéma, permettant une évolution fluide du modèle de données.

4. **Authentification**:
   - **JWT (JSON Web Tokens)** avec stockage dans des cookies httpOnly pour une sécurité renforcée contre les XSS.
   - Hashing des mots de passe avec **bcrypt** (via passlib) pour une protection optimale.
   - Durée de validité des tokens limitée à 30 minutes pour réduire les risques de vol.

5. **Containerisation**:
   - **Docker** pour isoler les environnements et garantir la reproductibilité.
   - **Docker Compose** pour orchestrer les services (frontend, backend, base de données) en développement.
   - Multi-stage builds pour réduire la taille des images finales.

### Structure modulaire
- **Backend**:
  - **Routers**: Séparation des préoccupations (auth vs tasks).
  - **Services**: Logique métier encapsulée (ex: `TasksService` pour les opérations CRUD).
  - **Database Layer**: Couche d'abstraction avec SQLAlchemy pour une indépendance vis-à-vis du SGBD.

- **Frontend**:
  - **Layouts**: Composants de haut niveau pour gérer les routes protégées/non protégées.
  - **Pages**: Composants spécifiques à chaque route (ex: `DashboardPage`).
  - **UI Components**: Composants réutilisables (ex: `TaskItem`, `FilterBar`).

## Flux de données

### Flux principal (Création de tâche)
1. **Utilisateur** → **Frontend**: Soumet un formulaire de tâche via `TaskForm`.
2. **Frontend** → **Backend**: Envoie une requête POST `/tasks` avec le JWT dans les headers.
3. **Backend**:
   - Valide le JWT via `AuthService`.
   - Traite la requête via `TasksService` qui applique la logique métier.
   - Persiste la tâche via `Database Layer` (SQLAlchemy).
4. **Backend** → **Frontend**: Retourne la tâche créée avec un code 201.
5. **Frontend**: Met à jour l'état local et affiche la tâche dans `TaskList`.

### Flux d'authentification
1. **Utilisateur** → **Frontend**: Soumet ses identifiants via `AuthForm`.
2. **Frontend** → **Backend**: Envoie une requête POST `/auth/login`.
3. **Backend**:
   - Vérifie les identifiants via `UsersService`.
   - Génère un JWT via `AuthService`.
4. **Backend** → **Frontend**: Retourne le JWT dans un cookie httpOnly.
5. **Frontend**: Redirige vers `/dashboard` et stocke l'état d'authentification dans un contexte React.

## Sécurité

### Mesures implémentées
1. **Authentification**:
   - JWT avec signature HS256 et secret généré dynamiquement.
   - Cookies httpOnly pour éviter les attaques XSS.
   - Durée de vie limitée des tokens (30 minutes).

2. **Protection des données**:
   - Hashing des mots de passe avec bcrypt (coût de travail élevé).
   - Validation des entrées côté backend (Pydantic) et frontend (Zod).
   - Requêtes API protégées par middleware vérifiant la présence et la validité du JWT.

3. **Base de données**:
   - PostgreSQL en production avec connexion sécurisée (SSL).
   - Variables d'environnement pour les secrets (via `python-dotenv`).
   - Sauvegardes régulières (à configurer en production).

4. **Infrastructure**:
   - Docker avec utilisateurs non-root pour les conteneurs.
   - Réseau isolé pour les services (via Docker Compose).
   - CI/CD avec tests automatisés avant déploiement.

### Risques et mitigations
| Risque                          | Mitigation                                                                 |
|---------------------------------|----------------------------------------------------------------------------|
| Vol de JWT                      | Durée de vie courte + cookies httpOnly + rotation des secrets.             |
| Injection SQL                   | Utilisation de SQLAlchemy (ORM) pour éviter les requêtes brutes.          |
| Attaques CSRF                   | Cookies SameSite=Lax + vérification des headers Origin/Referer.           |
| Fuites de données sensibles     | Variables d'environnement + .gitignore pour les fichiers locaux.          |
| Déni de service (DoS)           | Limitation du taux de requêtes (à implémenter via FastAPI middleware).    |

## Scalabilité

### Évolutivité horizontale
1. **Backend**:
   - FastAPI supporte nativement l'async, permettant de gérer un grand nombre de connexions simultanées.
   - Possibilité de déployer plusieurs instances derrière un load balancer (ex: Nginx).
   - Cache Redis pour les tâches fréquemment accédées (à ajouter en v2).

2. **Base de données**:
   - PostgreSQL supporte le sharding et la réplication pour distribuer la charge.
   - Pool de connexions (via `asyncpg`) pour optimiser les performances.
   - Indexes sur les champs fréquemment filtrés (`user_id`, `status`, `priority`).

3. **Frontend**:
   - Build statique optimisé (Vite) pour un chargement rapide.
   - Lazy loading des composants pour réduire le bundle initial.
   - CDN pour les assets statiques (à configurer en production).

### Améliorations futures
1. **Fonctionnalités**:
   - Notifications en temps réel (via WebSockets ou Server-Sent Events).
   - Synchronisation multi-appareils.
   - Intégration avec des calendriers externes (Google Calendar, etc.).

2. **Performance**:
   - Cache des tâches avec Redis pour les utilisateurs actifs.
   - Pagination avancée pour les listes de tâches volumineuses.
   - Optimisation des requêtes SQL avec des vues matérialisées.

3. **Observabilité**:
   - Logging centralisé (ELK Stack ou Loki).
   - Monitoring des performances (Prometheus + Grafana).
   - Traces distribuées (OpenTelemetry).

4. **Déploiement**:
   - Kubernetes pour une orchestration avancée en production.
   - Blue-Green deployments pour des mises à jour sans downtime.
   - Infrastructure as Code (Terraform) pour une gestion reproductible.

---