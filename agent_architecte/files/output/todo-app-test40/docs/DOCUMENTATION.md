# Documentation d'Architecture - todo-app-test40

## Vue d'ensemble
**todo-app-test40** est une application full-stack de gestion de tâches avec authentification sécurisée. Le système permet aux utilisateurs de créer, modifier et supprimer des tâches tout en appliquant des filtres par statut (todo/in_progress/done) et priorité (low/medium/high). L'architecture suit une approche moderne avec séparation claire des responsabilités entre frontend (React) et backend (FastAPI), utilisant JWT pour l'authentification.

## Décisions d'architecture
1. **Choix technologiques**:
   - **Backend**: FastAPI pour ses performances natives (async) et sa documentation automatique (OpenAPI/Swagger).
   - **Frontend**: React avec TypeScript pour une meilleure maintenabilité et détection précoce des erreurs.
   - **Base de données**: SQLite en développement pour sa simplicité, PostgreSQL en production pour sa robustesse et scalabilité.

2. **Authentification**:
   - Implémentation JWT avec refresh tokens pour éviter les reconnexions fréquentes.
   - Stockage des tokens en HTTP-only cookies pour mitiger les attaques XSS.
   - Hashage des mots de passe avec bcrypt (coût 12).

3. **CI/CD**:
   - Pipeline GitHub Actions/GitLab CI pour:
     - Exécution des tests (pytest pour backend, Jest pour frontend)
     - Build des images Docker
     - Déploiement automatique sur la plateforme cible

4. **Séparation des environnements**:
   - Fichiers de configuration distincts pour dev/prod (Pydantic Settings pour le backend, variables d'environnement pour le frontend).
   - Migration automatique des modèles SQLAlchemy via Alembic.

## Flux de données
1. **Authentification**:
   - L'utilisateur soumet ses identifiants via le formulaire de login (frontend).
   - Le backend valide les credentials, génère un JWT (access + refresh tokens) et les retourne en cookies.
   - Le frontend stocke les tokens et les envoie automatiquement avec chaque requête protégée.

2. **Gestion des tâches**:
   - Le frontend envoie une requête GET `/tasks` avec les filtres (status/priority) et le JWT.
   - Le backend vérifie le JWT, récupère les tâches de l'utilisateur depuis la BDD et retourne les résultats paginés.
   - Pour les modifications (POST/PUT/DELETE), le backend valide les permissions avant toute opération.

3. **Synchronisation BDD**:
   - SQLite en développement utilise un fichier local (`dev.db`).
   - PostgreSQL en production utilise un volume Docker persistant.
   - Les modèles SQLAlchemy sont identiques entre les deux environnements.

## Sécurité
1. **Authentification**:
   - JWT signés avec RS256 (asymétrique) pour éviter la falsification.
   - Refresh tokens avec rotation (invalidation après utilisation).
   - Durée de vie limitée pour les access tokens (15 minutes).

2. **Protection des données**:
   - Mots de passe hashés avec bcrypt (coût 12).
   - CORS configuré pour n'autoriser que les origines du frontend.
   - Validation des entrées côté backend (Pydantic) et frontend (Zod).

3. **Infrastructure**:
   - Base de données PostgreSQL avec authentification par mot de passe.
   - Variables d'environnement pour les secrets (JWT_SECRET, DB_PASSWORD).
   - HTTPS obligatoire en production (via reverse proxy comme Nginx).

## Scalabilité
1. **Backend**:
   - FastAPI supporte nativement l'async/await pour des performances élevées.
   - Possibilité d'ajouter des workers (Gunicorn/Uvicorn) pour gérer plus de requêtes.
   - Cache Redis optionnel pour les tâches fréquemment accédées.

2. **Base de données**:
   - PostgreSQL supporte le sharding et la réplication pour la scalabilité horizontale.
   - Indexes sur les champs fréquemment filtrés (user_id, status).

3. **Frontend**:
   - Code splitté avec React.lazy pour réduire le bundle initial.
   - Pagination des tâches pour éviter de charger trop de données.

4. **Déploiement**:
   - Conteneurisation avec Docker pour une portabilité maximale.
   - Déploiement possible sur AWS ECS, Kubernetes ou plateformes serverless (Render, Vercel).

---