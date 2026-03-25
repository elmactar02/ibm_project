# Documentation d'Architecture — todo-app-test17

## Vue d'ensemble
**todo-app-test17** est une application full-stack de gestion de tâches (To-Do list) avec authentification JWT, permettant aux utilisateurs de créer, modifier, supprimer et filtrer leurs tâches par statut et priorité. L'application suit une architecture **client-serveur** avec :
- Un **frontend** en React 18 (TypeScript) pour l'interface utilisateur.
- Un **backend** en FastAPI (Python) pour la logique métier et l'API REST.
- Une **base de données** PostgreSQL pour le stockage des données.
- Un **pipeline CI/CD** pour l'automatisation des tests et déploiements.

L'objectif est de fournir une solution simple, scalable et sécurisée pour la gestion des tâches quotidiennes.

---

## Décisions d'architecture

### 1. Choix technologiques
- **Frontend** : React 18 avec TypeScript pour une meilleure maintenabilité et typage statique. Vite comme bundler pour des performances optimales en développement.
- **Backend** : FastAPI pour sa rapidité, sa documentation automatique (Swagger/OpenAPI) et sa compatibilité avec Python async. Choix de Python pour sa simplicité et son écosystème mature (SQLAlchemy, Pydantic).
- **Base de données** : PostgreSQL pour sa fiabilité, ses fonctionnalités avancées (JSON, indexes) et sa compatibilité avec SQLAlchemy.
- **Authentification** : JWT (JSON Web Tokens) pour une authentification stateless, sécurisée et scalable. Stockage du token côté client dans le `localStorage`.
- **CI/CD** : GitHub Actions pour son intégration native avec GitHub et sa simplicité de configuration.

### 2. Structure modulaire
- **Backend** :
  - Séparation claire entre **routers** (routes API), **services** (logique métier) et **utils** (fonctions réutilisables comme JWT).
  - Utilisation de **Pydantic** pour la validation des données et la documentation automatique des modèles.
  - **SQLAlchemy** comme ORM pour une abstraction propre de la base de données.
- **Frontend** :
  - Architecture basée sur des **composants réutilisables** (ex: `TaskForm`, `TaskFilters`).
  - Gestion de l'état avec **React Context** pour éviter une complexité inutile (pas de Redux pour ce projet).
  - Routing protégé avec `react-router-dom` pour gérer l'accès aux pages authentifiées.

### 3. Sécurité
- **Authentification** : JWT avec hachage des mots de passe via `bcrypt` (via `passlib`). Durée de validité du token limitée à 1 heure pour réduire les risques en cas de fuite.
- **Protection des routes** : Middleware FastAPI pour vérifier les tokens JWT sur les routes protégées. Côté frontend, vérification de la présence du token avant d'accéder aux pages protégées.
- **Validation des données** : Utilisation de Pydantic côté backend et `react-hook-form` côté frontend pour valider les entrées utilisateur.

### 4. Scalabilité
- **Backend** :
  - Architecture stateless permettant un scaling horizontal facile (ajout de serveurs FastAPI derrière un load balancer).
  - Utilisation de **SQLAlchemy** avec des sessions gérées proprement pour éviter les fuites de mémoire.
- **Base de données** :
  - Indexes sur les champs fréquemment filtrés (`user_id`, `status`, `priority`) pour optimiser les performances.
  - Possibilité de migrer vers une base de données managée (ex: AWS RDS) en production.
- **Frontend** :
  - Code optimisé avec Vite pour des temps de chargement rapides.
  - Lazy loading des composants pour réduire la taille du bundle initial.

### 5. Déploiement
- **Conteneurisation** : Docker pour le développement local et la production. Docker Compose pour orchestrer les services (frontend, backend, base de données).
- **CI/CD** : Pipeline GitHub Actions pour :
  - Exécuter les tests unitaires et d'intégration.
  - Builder les images Docker.
  - Déployer automatiquement sur Render/Railway après un push sur `main`.
- **Environnement** : Variables d'environnement pour gérer les configurations (ex: `SECRET_KEY`, `DATABASE_URL`).

---

## Flux de données

### 1. Authentification
1. **Inscription** :
   - L'utilisateur remplit le formulaire (`RegisterPage`) et envoie ses identifiants au backend (`POST /auth/register`).
   - Le backend hache le mot de passe avec `bcrypt`, crée l'utilisateur en base de données et génère un token JWT.
   - Le token est retourné au frontend et stocké dans le `localStorage`.
2. **Connexion** :
   - Similaire à l'inscription, mais vérifie d'abord les identifiants en base de données (`POST /auth/login`).
3. **Accès aux routes protégées** :
   - Le frontend envoie le token JWT dans le header `Authorization` pour chaque requête API.
   - Le backend vérifie la validité du token avant de traiter la requête.

### 2. Gestion des tâches
1. **Création d'une tâche** :
   - L'utilisateur remplit le formulaire (`TaskForm`) et envoie les données au backend (`POST /tasks`).
   - Le backend valide les données, crée la tâche en base de données (liée à l'utilisateur via `user_id`) et retourne la tâche créée.
   - Le frontend met à jour l'interface en ajoutant la tâche à la liste.
2. **Filtrage des tâches** :
   - L'utilisateur sélectionne des filtres (`TaskFilters`) qui envoient une requête `GET /tasks?status=todo&priority=high`.
   - Le backend filtre les tâches en base de données et retourne les résultats.
   - Le frontend met à jour la liste des tâches affichées.
3. **Modification/Suppression** :
   - Similaire à la création, mais utilise `PUT /tasks/{id}` ou `DELETE /tasks/{id}`.

### 3. CI/CD
1. **Push sur GitHub** :
   - Le développeur pousse du code sur la branche `main`.
2. **Déclenchement du pipeline** :
   - GitHub Actions exécute les étapes définies dans `.github/workflows/deploy.yml`.
3. **Tests et build** :
   - Exécution des tests unitaires (backend) et des tests d'intégration (frontend).
   - Build des images Docker pour le frontend et le backend.
4. **Déploiement** :
   - Les images sont poussées vers un registry (ex: Docker Hub).
   - Déploiement sur Render/Railway avec mise à jour des services.

---

## Sécurité

### 1. Authentification et autorisation
- **JWT** :
  - Tokens signés avec une clé secrète (`SECRET_KEY`) stockée dans les variables d'environnement.
  - Durée de validité limitée (1 heure) pour réduire les risques en cas de vol du token.
  - Stockage du token dans le `localStorage` côté frontend (avec les risques associés, mais acceptable pour ce projet).
- **Protection des routes** :
  - Middleware FastAPI pour vérifier la présence et la validité du token JWT sur les routes protégées.
  - Vérification côté frontend avec `react-router-dom` pour rediriger vers `/login` si le token est absent.
- **Hachage des mots de passe** :
  - Utilisation de `bcrypt` via `passlib` pour un hachage sécurisé des mots de passe.

### 2. Validation des données
- **Backend** :
  - Validation des entrées utilisateur avec Pydantic (ex: format d'email, longueur des champs).
  - Protection contre les injections SQL via SQLAlchemy (ORM).
- **Frontend** :
  - Validation des formulaires avec `react-hook-form` et des règles personnalisées (ex: mot de passe de 8 caractères minimum).

### 3. Sécurité des API
- **CORS** :
  - Configuration stricte des origines autorisées dans FastAPI (`CORSMiddleware`).
- **Rate Limiting** :
  - À implémenter en production pour limiter les attaques par force brute (ex: avec `slowapi`).
- **HTTPS** :
  - Obligatoire en production pour chiffrer les communications.

### 4. Gestion des erreurs
- **Backend** :
  - Utilisation de `HTTPException` pour retourner des codes d'erreur appropriés (401 pour auth, 404 pour ressources introuvables).
  - Logs des erreurs pour le débogage (sans exposer d'informations sensibles).
- **Frontend** :
  - Affichage de messages d'erreur utilisateur-friendly (ex: "Email déjà utilisé" pour une inscription échouée).

---

## Scalabilité

### 1. Backend
- **Stateless** :
  - Le backend est stateless, ce qui permet d'ajouter des instances facilement derrière un load balancer (ex: Nginx).
- **Base de données** :
  - Indexes sur les champs fréquemment filtrés (`user_id`, `status`, `priority`) pour optimiser les performances.
  - Possibilité de partitionner la table `tasks` par `user_id` si le nombre de tâches devient très grand.
- **Cache** :
  - Ajout possible d'un cache Redis pour les tâches fréquemment accédées (non implémenté dans ce projet, mais extensible).

### 2. Frontend
- **Optimisation des performances** :
  - Code splitting avec Vite pour réduire la taille du bundle initial.
  - Lazy loading des composants pour les pages moins critiques.
- **Gestion de l'état** :
  - Utilisation de React Context pour éviter une complexité inutile (pas de Redux pour ce projet).
  - Possibilité de migrer vers une solution plus scalable (ex: Zustand) si l'état devient trop complexe.

### 3. Déploiement
- **Conteneurisation** :
  - Docker permet un déploiement cohérent entre les environnements (dev, staging, prod).
  - Docker Compose pour orchestrer les services localement.
- **CI/CD** :
  - Pipeline GitHub Actions pour automatiser les tests et déploiements.
  - Possibilité de déployer sur des plateformes serverless (ex: AWS Lambda pour le backend) si nécessaire.
- **Monitoring** :
  - À ajouter en production (ex: Sentry pour le frontend, Prometheus/Grafana pour le backend).

---

## Conclusion
**todo-app-test17** est conçu comme une application moderne, sécurisée et scalable pour la gestion des tâches. L'architecture modulaire et les choix technologiques permettent une évolution facile des fonctionnalités. Les décisions prises (JWT, FastAPI, React, PostgreSQL) offrent un équilibre entre simplicité, performance et maintenabilité. Le pipeline CI/CD garantit des déploiements rapides et fiables, essentiels pour un développement agile.

---