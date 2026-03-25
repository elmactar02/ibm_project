# Documentation d'Architecture — todo-app-test6

## Vue d'ensemble
**todo-app-test6** est une application full-stack de gestion de tâches (To-Do list) avec authentification JWT, permettant aux utilisateurs de créer, modifier, supprimer et filtrer leurs tâches par statut et priorité. L'application suit une architecture **client-serveur** avec :
- Un **frontend** en React 18 (TypeScript) pour l'interface utilisateur.
- Un **backend** en FastAPI (Python) pour la logique métier et l'authentification.
- Une **base de données** PostgreSQL pour le stockage persistant.
- Un **pipeline CI/CD** (GitHub Actions) pour l'automatisation des tests et déploiements.

L'objectif est de fournir une solution **modulaire**, **scalable** et **sécurisée**, avec une séparation claire des responsabilités entre les couches.

---

## Décisions d'architecture

### 1. Choix technologiques
- **Frontend** : React 18 + TypeScript pour une expérience développeur robuste et une maintenabilité accrue. Vite pour le bundling (performances optimisées).
- **Backend** : FastAPI pour sa simplicité, sa performance (basé sur Starlette) et sa documentation automatique (OpenAPI/Swagger). Python 3.10 pour la compatibilité avec les bibliothèques modernes.
- **Base de données** : PostgreSQL pour sa fiabilité, ses fonctionnalités avancées (ex: JSONB, indexes) et sa compatibilité avec SQLAlchemy.
- **Authentification** : JWT (JSON Web Tokens) avec `python-jose` pour la signature et `passlib` pour le hachage des mots de passe (bcrypt). Durée de validité du token limitée à 1 heure pour réduire les risques de sécurité.
- **CI/CD** : GitHub Actions pour son intégration native avec GitHub et sa simplicité de configuration.

### 2. Architecture modulaire
- **Backend** :
  - **Routers** : Séparation des endpoints par domaine (`/auth` pour l'authentification, `/tasks` pour les tâches).
  - **Services** : Logique métier isolée dans des services réutilisables (ex: `AuthService`, `TasksService`).
  - **Database Layer** : SQLAlchemy pour l'ORM, avec des sessions gérées via des dépendances FastAPI.
- **Frontend** :
  - **Pages** : Routing basé sur React Router v6, avec des layouts dédiés pour les pages publiques/privées.
  - **Composants** : Composants réutilisables (ex: `TaskForm`, `TaskFilters`) avec une logique d'état gérée via React Context et SWR.
  - **State Management** : SWR pour le caching des données des tâches (évite les requêtes redondantes) et React Context pour l'authentification.

### 3. Sécurité
- **Authentification** :
  - Mots de passe hachés avec bcrypt (coût de travail élevé pour résister aux attaques par force brute).
  - Tokens JWT signés avec HS256 (clé secrète stockée dans des variables d'environnement).
  - Middleware FastAPI pour valider les tokens sur les endpoints protégés.
- **Frontend** :
  - Stockage du token JWT dans le `localStorage` (avec expiration gérée par le backend).
  - Middleware React pour rediriger vers `/login` si l'utilisateur n'est pas authentifié.
- **Base de données** :
  - Indexes sur les champs fréquemment interrogés (ex: `user_id` dans `Task`, `email` dans `User`).
  - Contraintes de validation (ex: email unique, champs obligatoires).

### 4. Scalabilité
- **Backend** :
  - FastAPI est asynchrone par défaut, ce qui permet de gérer un grand nombre de requêtes concurrentes avec peu de ressources.
  - La séparation des services (`AuthService`, `TasksService`) facilite l'ajout de nouvelles fonctionnalités ou le remplacement de composants.
- **Base de données** :
  - PostgreSQL supporte le sharding et la réplication pour une scalabilité horizontale.
  - Les indexes optimisent les requêtes fréquentes (ex: filtrage des tâches par statut/priorité).
- **Frontend** :
  - SWR permet de réduire la charge sur le backend en cachant les données côté client.
  - Le bundling avec Vite optimise les performances de chargement.

### 5. CI/CD
- **Pipeline GitHub Actions** :
  - **Tests** : Exécution des tests unitaires (pytest) et d'intégration à chaque push.
  - **Build** : Construction des images Docker pour le frontend et le backend.
  - **Déploiement** : Déploiement automatique sur Render/Railway après validation des tests.
- **Docker** :
  - Images multi-stage pour réduire la taille des images de production.
  - Docker Compose pour le développement local (avec PostgreSQL en conteneur).

---

## Flux de données

### 1. Authentification
1. **Inscription** :
   - L'utilisateur soumet un email et un mot de passe via le formulaire de `RegisterPage`.
   - Le frontend envoie une requête `POST /auth/register` au backend.
   - Le backend hache le mot de passe (bcrypt), crée l'utilisateur en base de données, et retourne un token JWT.
   - Le frontend stocke le token dans le `localStorage` et redirige vers `/`.

2. **Connexion** :
   - Similaire à l'inscription, mais via `POST /auth/login`.
   - Le backend vérifie le mot de passe haché et retourne un token JWT.

### 2. Gestion des tâches
1. **Création d'une tâche** :
   - L'utilisateur remplit le formulaire `TaskForm` et soumet les données.
   - Le frontend envoie une requête `POST /tasks` avec le token JWT dans les headers.
   - Le backend valide le token, crée la tâche en base de données (liée à l'utilisateur), et retourne la tâche créée.
   - Le frontend met à jour l'interface en temps réel (via SWR).

2. **Filtrage des tâches** :
   - L'utilisateur sélectionne des filtres (statut/priorité) via `TaskFilters`.
   - Le frontend met à jour l'URL avec les query params (ex: `?status=done&priority=high`).
   - SWR déclenche une requête `GET /tasks` avec les filtres, et le backend retourne les tâches correspondantes.

3. **Modification/Suppression** :
   - Pour la modification, le frontend envoie une requête `PUT /tasks/{task_id}` avec les champs à mettre à jour.
   - Pour la suppression, une requête `DELETE /tasks/{task_id}` est envoyée.
   - Le backend valide les permissions (l'utilisateur doit être propriétaire de la tâche) avant d'exécuter l'action.

---

## Sécurité

### 1. Authentification et autorisation
- **JWT** :
  - Les tokens sont signés avec une clé secrète (HS256) stockée dans des variables d'environnement.
  - Durée de validité limitée à 1 heure pour réduire les risques en cas de vol de token.
  - Les tokens sont transmis via les headers `Authorization: Bearer <token>`.
- **Permissions** :
  - Le backend vérifie que l'utilisateur est propriétaire d'une tâche avant de permettre sa modification/suppression (via `user_id` dans la table `Task`).
  - Les endpoints protégés utilisent un middleware FastAPI pour valider le token avant d'exécuter la logique métier.

### 2. Protection contre les attaques courantes
- **CSRF** : Non applicable car l'application utilise JWT (pas de cookies).
- **XSS** :
  - Le frontend utilise React (qui échappe automatiquement les données) et évite le `dangerouslySetInnerHTML`.
  - Les headers CSP (Content Security Policy) sont configurés pour limiter les sources de scripts.
- **Injection SQL** :
  - SQLAlchemy utilise des requêtes paramétrées pour éviter les injections.
  - Les entrées utilisateur sont validées via Pydantic avant d'être traitées par le backend.
- **Brute Force** :
  - Les mots de passe sont hachés avec bcrypt (coût de travail élevé).
  - Le backend peut implémenter un rate limiting (ex: avec `slowapi`) pour limiter les tentatives de connexion.

### 3. Stockage des données sensibles
- **Mots de passe** : Jamais stockés en clair. Hachés avec bcrypt avant d'être enregistrés en base de données.
- **Tokens JWT** : Stockés dans le `localStorage` du navigateur (avec expiration gérée par le backend). Alternative possible : `httpOnly` cookies pour une sécurité accrue (mais moins pratique pour les apps SPA).
- **Variables d'environnement** : Les clés secrètes (ex: `SECRET_KEY`, `DATABASE_URL`) sont stockées dans des fichiers `.env` (exclus du versioning via `.gitignore`).

---

## Scalabilité

### 1. Backend
- **Asynchrone** : FastAPI est conçu pour gérer des milliers de requêtes concurrentes avec peu de ressources.
- **Stateless** : Les sessions utilisateur sont gérées via JWT, ce qui permet de scaler horizontalement le backend sans état.
- **Cache** : Bien que non implémenté dans cette version, un cache Redis pourrait être ajouté pour réduire la charge sur la base de données (ex: pour les tâches fréquemment accédées).

### 2. Base de données
- **Indexing** : Les indexes sur `user_id` (Task) et `email` (User) optimisent les requêtes fréquentes.
- **Partitionnement** : Pour une scalabilité future, la table `Task` pourrait être partitionnée par `user_id` ou `created_at`.
- **Réplication** : PostgreSQL supporte la réplication maître-esclave pour distribuer la charge de lecture.

### 3. Frontend
- **Caching** : SWR réduit le nombre de requêtes vers le backend en cachant les données côté client.
- **Lazy Loading** : Les composants React peuvent être chargés dynamiquement (ex: `React.lazy`) pour réduire le temps de chargement initial.
- **Optimisation des assets** : Vite optimise automatiquement les assets (minification, tree-shaking).

### 4. Déploiement
- **Conteneurs** : Docker permet de déployer l'application de manière cohérente sur différents environnements.
- **Orchestration** : Pour une scalabilité avancée, Kubernetes pourrait être utilisé pour gérer les conteneurs (ex: auto-scaling en fonction de la charge).
- **CDN** : Les assets statiques du frontend pourraient être servis via un CDN (ex: Cloudflare) pour réduire la latence.

---

## Améliorations futures
1. **Notifications** : Ajouter des notifications en temps réel (ex: WebSockets) pour les rappels de tâches.
2. **Collaboration** : Permettre le partage de tâches entre utilisateurs (avec des rôles comme "lecteur" ou "éditeur").
3. **Offline** : Implémenter un mode hors ligne avec synchronisation automatique lorsque la connexion est rétablie (ex: via IndexedDB).
4. **Analytics** : Ajouter des tableaux de bord pour suivre la productivité (ex: nombre de tâches terminées par jour).

---