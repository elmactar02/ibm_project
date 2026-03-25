# Documentation d'Architecture — TodoApp (todo-app-test11)

## Vue d'ensemble
TodoApp est une application full-stack de gestion de tâches avec authentification JWT, conçue pour permettre aux utilisateurs de créer, modifier, supprimer et filtrer leurs tâches par statut et priorité. L'architecture suit une approche **modulaire** et **scalable**, avec une séparation claire entre frontend (React), backend (FastAPI) et base de données (PostgreSQL). Le projet intègre un pipeline CI/CD pour automatiser les déploiements sur GitHub.

## Décisions d'architecture
1. **Backend (FastAPI)** :
   - Choix de FastAPI pour sa performance, sa documentation automatique (Swagger/OpenAPI) et son support natif de l'asynchrone.
   - Structure en **routers** (`/auth`, `/tasks`) et **services** (`UsersService`, `TasksService`) pour isoler la logique métier.
   - Authentification JWT avec tokens courts (30 minutes) pour équilibrer sécurité et expérience utilisateur.

2. **Frontend (React + TypeScript)** :
   - Utilisation de **React 18** avec **TypeScript** pour une meilleure maintenabilité et détection précoce des erreurs.
   - Architecture basée sur des **composants réutilisables** (ex: `TaskForm`, `TaskList`) et un **contexte d'authentification** (`AuthProvider`).
   - Routing protégé avec **React Router v6** pour gérer les accès aux pages.

3. **Base de données (PostgreSQL)** :
   - Modèle relationnel avec deux tables principales : `users` et `tasks` (relation Many-to-One).
   - Indexes sur `user_id`, `status` et `priority` pour optimiser les requêtes de filtrage.
   - Migrations gérées avec **Alembic** pour une évolution contrôlée du schéma.

4. **CI/CD (GitHub Actions)** :
   - Pipeline déclenché sur `push` vers `main`, incluant :
     - Tests unitaires (backend) et linting (frontend/backend).
     - Build des images Docker.
     - Déploiement automatique sur GitHub Pages (frontend) et Render/Heroku (backend).

5. **Sécurité** :
   - Hashing des mots de passe avec **bcrypt** (via `passlib`).
   - Validation des entrées côté backend (Pydantic) et frontend (React Hook Form).
   - CORS configuré pour n'accepter que les requêtes du frontend.

## Flux de données
1. **Authentification** :
   - L'utilisateur s'inscrit (`POST /auth/register`) ou se connecte (`POST /auth/login`).
   - Le backend génère un **JWT** signé avec une clé secrète (stockée dans les variables d'environnement).
   - Le frontend stocke le token dans `localStorage` et l'ajoute aux en-têtes des requêtes API.

2. **Gestion des tâches** :
   - Le frontend envoie une requête `GET /tasks` avec des filtres optionnels (`status`, `priority`).
   - Le backend vérifie le JWT, récupère les tâches de l'utilisateur depuis PostgreSQL, et les retourne.
   - Pour les opérations CRUD, le backend valide les permissions (ex: un utilisateur ne peut modifier que ses propres tâches).

3. **Déploiement** :
   - Le pipeline CI/CD build les images Docker pour le frontend et le backend.
   - Les images sont poussées vers un registry (GitHub Container Registry) et déployées sur des services cloud.

## Sécurité
- **JWT** : Tokens signés avec HS256, expirant après 30 minutes. Stockage côté client dans `localStorage` (avec risques XSS atténués par des headers CSP).
- **Mots de passe** : Hashés avec bcrypt (coût de 12 rounds).
- **Validation** : Double validation des données (frontend + backend) pour éviter les injections SQL ou XSS.
- **Environnement** : Variables sensibles (clé JWT, credentials DB) stockées dans `.env` (exclu de Git).

## Scalabilité
1. **Backend** :
   - FastAPI supporte l'asynchrone, permettant de gérer des milliers de requêtes concurrentes.
   - Possibilité d'ajouter un **cache Redis** pour les tâches fréquemment accédées.
   - Déploiement horizontal possible avec un load balancer (ex: Nginx).

2. **Base de données** :
   - PostgreSQL supporte le sharding et la réplication pour une haute disponibilité.
   - Les indexes sur `user_id`, `status` et `priority` optimisent les requêtes de filtrage.

3. **Frontend** :
   - Chargement paresseux des composants (`React.lazy`) pour réduire le bundle initial.
   - Pagination des tâches pour éviter de charger trop de données en une fois.

4. **CI/CD** :
   - Le pipeline peut être étendu pour inclure des tests de charge (ex: Locust) et des scans de sécurité (ex: Snyk).

---