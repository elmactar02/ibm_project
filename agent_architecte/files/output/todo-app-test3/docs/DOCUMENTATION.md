# Documentation d'Architecture - todo-app-test3

## Vue d'ensemble
**todo-app-test3** est une application de gestion de tâches (To-Do list) avec authentification sécurisée via JWT. L'application permet aux utilisateurs de s'inscrire, se connecter, et gérer leurs tâches avec des fonctionnalités de filtrage par statut et priorité. Le projet suit une architecture moderne basée sur des conteneurs avec une séparation claire entre frontend (React) et backend (FastAPI), et utilise des bases de données différentes selon l'environnement (SQLite en développement, PostgreSQL en production).

## Décisions d'architecture
1. **Architecture en couches** :
   - **Frontend** : SPA React avec TypeScript pour une meilleure maintenabilité et typage fort.
   - **Backend** : FastAPI pour sa performance et sa compatibilité avec les standards OpenAPI.
   - **Base de données** : SQLite pour le développement (simplicité) et PostgreSQL pour la production (robustesse).

2. **Authentification** :
   - JWT (JSON Web Tokens) pour une authentification stateless, avec une durée de validité de 30 minutes.
   - Hachage des mots de passe avec bcrypt pour une sécurité renforcée.

3. **Gestion des données** :
   - SQLAlchemy comme ORM pour abstraire les différences entre SQLite et PostgreSQL.
   - Alembic pour gérer les migrations de schéma entre les environnements.

4. **CI/CD** :
   - Pipeline GitHub Actions pour automatiser les tests et le déploiement.
   - Déploiement conditionnel selon la branche (ex: `main` pour la production).

5. **Conteneurisation** :
   - Docker pour isoler les services (frontend, backend, base de données).
   - Docker Compose pour orchestrer les conteneurs en développement.

## Flux de données
1. **Authentification** :
   - L'utilisateur soumet ses identifiants via le formulaire de login.
   - Le frontend envoie une requête POST à `/auth/login` avec l'email et le mot de passe.
   - Le backend valide les identifiants, génère un JWT, et le retourne au frontend.
   - Le frontend stocke le JWT dans le localStorage et l'inclut dans les en-têtes des requêtes suivantes.

2. **Gestion des tâches** :
   - Le frontend envoie une requête GET à `/tasks` avec le JWT pour récupérer les tâches de l'utilisateur.
   - Le backend vérifie le JWT, récupère les tâches associées à l'utilisateur depuis la base de données, et les retourne.
   - Pour créer/modifier/supprimer une tâche, le frontend envoie une requête POST/PUT/DELETE à `/tasks` ou `/tasks/{task_id}` avec le JWT et les données de la tâche.

3. **Filtrage** :
   - Le frontend envoie une requête GET à `/tasks?status=todo&priority=high` pour filtrer les tâches.
   - Le backend applique les filtres SQL et retourne les résultats.

## Sécurité
1. **Authentification** :
   - JWT avec une durée de validité limitée (30 minutes) pour réduire les risques de vol de token.
   - Stockage des tokens dans le localStorage du navigateur (avec mise en garde contre les XSS).
   - Hachage des mots de passe avec bcrypt (coût de travail élevé pour résister aux attaques par force brute).

2. **Autorisation** :
   - Middleware FastAPI pour vérifier la présence et la validité du JWT sur les routes protégées.
   - Vérification de l'appartenance des tâches à l'utilisateur avant toute modification/suppression.

3. **Protection des données** :
   - Utilisation de HTTPS pour toutes les communications.
   - Variables d'environnement pour les secrets (JWT_SECRET_KEY, DATABASE_URL).
   - Prévention des injections SQL via SQLAlchemy (requêtes paramétrées).

4. **CI/CD** :
   - Secrets GitHub Actions pour les variables sensibles (clés API, mots de passe de base de données).
   - Tests automatisés avant déploiement pour détecter les régressions.

## Scalabilité
1. **Backend** :
   - FastAPI est conçu pour être scalable grâce à son architecture asynchrone.
   - Possibilité de déployer plusieurs instances du backend derrière un load balancer (ex: Nginx).
   - Ajout de Redis pour le cache des données fréquemment accédées (ex: liste des tâches).

2. **Base de données** :
   - PostgreSQL supporte le scaling vertical (augmentation des ressources) et horizontal (réplication).
   - Indexation des champs fréquemment filtrés (`status`, `priority`, `user_id`) pour améliorer les performances.

3. **Frontend** :
   - React est optimisé pour les performances grâce au Virtual DOM.
   - Code splitting pour réduire la taille des bundles et améliorer le temps de chargement.
   - Utilisation de React Query pour optimiser les requêtes API (cache, retry, pagination).

4. **Déploiement** :
   - Conteneurisation avec Docker permet un déploiement cohérent sur différents environnements.
   - Possibilité de migrer vers Kubernetes pour une orchestration avancée en cas de croissance.

---