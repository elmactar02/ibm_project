# Documentation d'Architecture — Todo App Test15

## Vue d'ensemble
**todo-app-test15** est une application full-stack de gestion de tâches (To-Do list) avec authentification sécurisée et pipeline CI/CD. L'architecture suit une approche **modulaire** et **scalable**, séparant clairement les responsabilités entre frontend (React), backend (FastAPI) et base de données (PostgreSQL). Le système est conçu pour être déployé en conteneurs Docker avec une automatisation CI/CD via GitHub Actions.

## Décisions d'architecture
1. **Backend (FastAPI)**:
   - Choix de FastAPI pour sa **performance** (basé sur Starlette) et sa **documentation automatique** (OpenAPI/Swagger).
   - Structuration en **routers** (auth/tasks) et **services** (users/tasks) pour une séparation claire des préoccupations.
   - Utilisation de **SQLAlchemy** comme ORM pour une abstraction flexible de PostgreSQL.

2. **Frontend (React + TypeScript)**:
   - Adoption de **React 18** avec **TypeScript** pour une meilleure maintenabilité et détection précoce des erreurs.
   - Gestion d'état hybride: **React Context** pour l'authentification et **Zustand** pour les tâches (évite la complexité de Redux).
   - **Vite** comme bundler pour des builds rapides et un développement fluide.

3. **Authentification**:
   - **JWT** avec tokens courts (30 minutes) pour un équilibre entre sécurité et expérience utilisateur.
   - Stockage du token dans **localStorage** (frontend) avec renouvellement via endpoint dédié (non implémenté dans cette version).
   - Hachage des mots de passe avec **bcrypt** (via passlib).

4. **Base de données**:
   - **PostgreSQL** pour sa fiabilité et son support des types avancés (enum pour status/priority).
   - Indexes sur les champs fréquemment filtrés (`user_id`, `status`, `priority`) pour optimiser les performances.

5. **CI/CD**:
   - Pipeline GitHub Actions avec étapes:
     - **Tests** (pytest pour le backend, Jest pour le frontend).
     - **Build** des images Docker.
     - **Déploiement** automatique sur le dépôt Git (simulé dans cette version).

## Flux de données
1. **Authentification**:
   - L'utilisateur soumet ses identifiants via le formulaire de login.
   - Le frontend envoie une requête POST à `/auth/login` avec email/mot de passe.
   - Le backend vérifie les credentials, génère un JWT et le retourne au frontend.
   - Le frontend stocke le token dans localStorage et l'inclut dans les headers des requêtes suivantes.

2. **Gestion des tâches**:
   - **Création**: L'utilisateur remplit le formulaire TaskForm → requête POST `/tasks` avec le token JWT.
   - **Lecture**: Le frontend appelle GET `/tasks` avec des query params pour les filtres (status/priority).
   - **Mise à jour/Suppression**: Requêtes PUT/DELETE vers `/tasks/{task_id}` avec le token JWT.

3. **CI/CD**:
   - Un push sur la branche `main` déclenche le pipeline GitHub Actions.
   - Les tests sont exécutés, puis les images Docker sont buildées et poussées vers le registre (simulé).

## Sécurité
1. **Authentification**:
   - JWT signés avec **HS256** et une clé secrète stockée dans les variables d'environnement.
   - Mots de passe hachés avec **bcrypt** (coût de 12 rounds).
   - Protection contre les attaques CSRF via des headers `Origin` et `X-Requested-With`.

2. **Backend**:
   - Validation des entrées avec **Pydantic** pour tous les endpoints.
   - CORS configuré pour n'autoriser que le domaine du frontend.
   - Middleware pour vérifier la présence du token JWT sur les routes protégées.

3. **Frontend**:
   - Stockage du token dans **localStorage** (avec risques XSS atténués par des headers CSP).
   - Routes protégées redirigeant vers `/login` si non authentifié.

4. **Base de données**:
   - Connexions chiffrées (SSL) en production.
   - Utilisateur PostgreSQL avec permissions minimales (lecture/écriture uniquement sur les tables nécessaires).

## Scalabilité
1. **Backend**:
   - FastAPI est **asynchrone** par défaut, permettant de gérer un grand nombre de requêtes concurrentes.
   - Possibilité de **scaler horizontalement** en ajoutant des instances derrière un load balancer (ex: Nginx).
   - Cache possible avec **Redis** pour les tâches fréquemment accédées (non implémenté dans cette version).

2. **Base de données**:
   - PostgreSQL supporte le **sharding** et la réplication pour une scalabilité horizontale.
   - Indexes optimisés pour les requêtes de filtrage (status/priority).

3. **Frontend**:
   - Code **modulaire** et **lazy loading** des composants pour réduire le temps de chargement initial.
   - Possibilité de déployer le frontend sur un CDN pour une distribution mondiale.

4. **CI/CD**:
   - Pipeline GitHub Actions scalable avec des runners auto-hébergés pour les projets plus larges.
   - Déploiement en **blue-green** ou **canary** pour minimiser les downtimes (non implémenté dans cette version).

---