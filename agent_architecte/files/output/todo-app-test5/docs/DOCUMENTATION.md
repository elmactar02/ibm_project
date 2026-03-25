# Documentation d'Architecture — todo-app-test5

## Vue d'ensemble
**todo-app-test5** est une application de gestion de tâches (To-Do list) avec authentification sécurisée, permettant aux utilisateurs de créer, modifier, supprimer et filtrer leurs tâches par statut et priorité. L'application suit une architecture **modulaire et scalable**, séparant clairement le frontend (React), le backend (FastAPI), et la base de données (SQLite en dev, PostgreSQL en prod). Le déploiement est automatisé via un pipeline CI/CD.

## Décisions d'architecture
1. **Backend (FastAPI)** :
   - Choix de FastAPI pour sa **performance** (async) et sa **documentation automatique** (OpenAPI/Swagger).
   - Structure modulaire avec **routers** (auth/tasks) et **services** pour séparer les responsabilités.
   - Authentification JWT avec **python-jose** et hachage des mots de passe avec **bcrypt** (via passlib).

2. **Frontend (React + TypeScript)** :
   - Utilisation de **React 18** avec **TypeScript** pour une meilleure maintenabilité.
   - Gestion de l'état avec **React Context + useReducer** pour éviter une dépendance à Redux (complexité inutile pour ce projet).
   - Routing avec **React Router v6** pour une navigation fluide.
   - UI avec **Material-UI (MUI)** pour des composants prêts à l'emploi et responsive.

3. **Base de données** :
   - **SQLite** en développement pour sa simplicité et son intégration native avec SQLAlchemy.
   - **PostgreSQL** en production pour sa robustesse et ses fonctionnalités avancées (ex: requêtes complexes).
   - **Alembic** pour les migrations, assurant une transition fluide entre les environnements.

4. **Déploiement** :
   - **Docker** pour la conteneurisation, avec des images multi-stage pour optimiser la taille.
   - **Docker Compose** pour orchestrer les services en développement (frontend, backend, base de données).
   - **CI/CD** avec GitHub Actions/GitLab CI pour automatiser les tests et le déploiement.

5. **Sécurité** :
   - JWT avec **durée de vie courte** (15 min pour l'access token, 7 jours pour le refresh token).
   - Stockage du JWT dans un **cookie HttpOnly** pour éviter les attaques XSS.
   - Validation des entrées utilisateur avec **Pydantic** (backend) et **TypeScript** (frontend).

## Flux de données
1. **Authentification** :
   - L'utilisateur s'inscrit (`POST /auth/register`) ou se connecte (`POST /auth/login`).
   - Le backend valide les données, hache le mot de passe (si inscription), et génère un JWT.
   - Le JWT est retourné au frontend et stocké dans un cookie HttpOnly.
   - Pour les requêtes protégées (ex: `GET /tasks`), le frontend envoie le JWT dans l'en-tête `Authorization`.

2. **Gestion des tâches** :
   - L'utilisateur crée une tâche (`POST /tasks`), modifie (`PUT /tasks/{id}`), ou supprime (`DELETE /tasks/{id}`).
   - Le backend valide le JWT, vérifie que l'utilisateur est propriétaire de la tâche, puis exécute l'opération.
   - Les filtres (status/priority) sont passés en query parameters (`GET /tasks?status=todo&priority=high`).

3. **Déploiement** :
   - Le code est poussé sur le dépôt Git, déclenchant le pipeline CI/CD.
   - Le pipeline exécute les tests (backend: pytest, frontend: Jest), construit les images Docker, et déploie sur l'environnement cible.

## Sécurité
- **Authentification** :
  - JWT avec signature HS256 et durée de vie limitée.
  - Refresh tokens pour éviter les reconnexions fréquentes.
  - Hachage des mots de passe avec bcrypt (coût de travail élevé pour résister aux attaques par force brute).
- **Protection des données** :
  - Cookies HttpOnly pour le JWT (protection contre XSS).
  - CORS configuré pour n'autoriser que le domaine du frontend.
  - Validation des entrées utilisateur (backend: Pydantic, frontend: TypeScript + MUI).
- **Base de données** :
  - PostgreSQL en production avec chiffrement des données au repos.
  - Sauvegardes automatiques via le pipeline CI/CD.

## Scalabilité
1. **Backend** :
   - FastAPI supporte le **async/await**, permettant de gérer un grand nombre de requêtes concurrentes.
   - Possibilité d'ajouter un **load balancer** (ex: Nginx) devant plusieurs instances du backend.
   - Cache avec **Redis** pour les tâches fréquemment accédées (ex: liste des tâches d'un utilisateur).

2. **Base de données** :
   - PostgreSQL supporte le **sharding** et la **réplication** pour distribuer la charge.
   - Pool de connexions avec **asyncpg** pour optimiser les performances.

3. **Frontend** :
   - React est optimisé pour le rendu côté client, réduisant la charge sur le serveur.
   - Code splitting avec **React.lazy** pour charger uniquement les composants nécessaires.

4. **Déploiement** :
   - Docker permet de **scaler horizontalement** en ajoutant des conteneurs.
   - CI/CD automatisé pour déployer rapidement de nouvelles versions.

---