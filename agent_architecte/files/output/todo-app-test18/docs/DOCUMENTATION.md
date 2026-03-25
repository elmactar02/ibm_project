# Documentation d'Architecture — todo-app-test18

## Vue d'ensemble
**todo-app-test18** est une application web de gestion de tâches (To-Do list) permettant aux utilisateurs de s'inscrire, se connecter, et gérer leurs tâches avec des fonctionnalités de filtrage par statut et priorité. L'application suit une architecture **client-serveur** avec :
- Un **frontend** en React 18 (SPA) pour l'interface utilisateur.
- Un **backend** en FastAPI (Python) pour la logique métier et l'authentification.
- Une **base de données** PostgreSQL pour le stockage persistant.
- Un **pipeline CI/CD** avec GitHub Actions pour l'automatisation des tests et déploiements.

L'application est conçue pour être **modulaire**, **scalable**, et **sécurisée**, avec une séparation claire des responsabilités entre les couches.

---

## Décisions d'architecture

### 1. Choix technologiques
- **Frontend** : React 18 + TypeScript pour une expérience développeur robuste et une maintenance facilitée. Vite est utilisé comme bundler pour des builds rapides.
- **Backend** : FastAPI pour sa performance, sa simplicité, et sa compatibilité native avec les standards OpenAPI/Swagger. Python 3.10 est choisi pour sa stabilité et son écosystème mature.
- **Base de données** : PostgreSQL pour sa fiabilité, ses fonctionnalités avancées (JSON, full-text search), et sa compatibilité avec SQLAlchemy (ORM).
- **Authentification** : JWT (JSON Web Tokens) pour une authentification stateless, sécurisée, et scalable. Les tokens sont signés avec JWS et ont une durée de validité limitée (1 heure).
- **CI/CD** : GitHub Actions pour son intégration native avec GitHub et sa flexibilité. Le pipeline inclut des étapes de test, build, et déploiement.

### 2. Architecture modulaire
L'application suit une **architecture en couches** :
- **Frontend** : Composants React organisés par fonctionnalité (authentification, tâches) avec un état global géré via Context API.
- **Backend** : Séparation en routers (routes FastAPI), services (logique métier), et couche de base de données (SQLAlchemy). Les dépendances sont injectées explicitement.
- **Base de données** : Modèles SQLAlchemy avec des relations claires (ex: `User` 1-N `Task`). Les migrations sont gérées avec Alembic.

### 3. Sécurité
- **Authentification** : JWT avec hachage des mots de passe (bcrypt) et tokens signés. Les routes protégées vérifient la présence et la validité du token.
- **Validation des données** : Utilisation de Pydantic (backend) et de formulaires contrôlés (frontend) pour valider les entrées utilisateur.
- **Protection CSRF** : Désactivée pour une API stateless (JWT est suffisant), mais les tokens sont stockés dans le `localStorage` avec des mesures pour limiter les risques de XSS (ex: Content Security Policy).

### 4. Scalabilité
- **Backend** : FastAPI est asynchrone par défaut, ce qui permet de gérer un grand nombre de requêtes concurrentes. La base de données PostgreSQL peut être mise à l'échelle verticalement ou horizontalement (réplication).
- **Frontend** : Le bundle React est optimisé avec Vite (code splitting, lazy loading). Les assets statiques peuvent être servis via un CDN en production.
- **Déploiement** : L'application est conteneurisée avec Docker, ce qui permet un déploiement cohérent sur n'importe quel environnement (local, cloud, etc.). Le pipeline CI/CD permet des déploiements fréquents et automatisés.

---

## Flux de données

### 1. Authentification
1. **Inscription** :
   - L'utilisateur soumet un formulaire (email + mot de passe) via le frontend.
   - Le backend valide les données, hache le mot de passe (bcrypt), et crée un utilisateur en base.
   - Un token JWT est généré et renvoyé au frontend, où il est stocké dans le `localStorage`.

2. **Connexion** :
   - L'utilisateur soumet ses identifiants.
   - Le backend vérifie le mot de passe (bcrypt), génère un token JWT, et le renvoie.
   - Le frontend stocke le token et redirige vers le dashboard.

3. **Accès aux routes protégées** :
   - Le frontend envoie le token JWT dans l'en-tête `Authorization` pour chaque requête.
   - Le backend valide le token et autorise/refuse l'accès à la ressource.

### 2. Gestion des tâches
1. **Création d'une tâche** :
   - L'utilisateur remplit un formulaire (titre, description, statut, priorité) et soumet.
   - Le frontend envoie les données au backend avec le token JWT.
   - Le backend valide le token, crée la tâche en base (liée à l'utilisateur), et renvoie la tâche créée.
   - Le frontend met à jour l'état global et affiche la tâche dans la liste.

2. **Filtrage des tâches** :
   - L'utilisateur sélectionne des filtres (ex: statut = "todo", priorité = "high").
   - Le frontend envoie une requête GET avec les paramètres de filtre.
   - Le backend filtre les tâches en base et renvoie les résultats.
   - Le frontend met à jour la liste des tâches affichées.

3. **Modification/Suppression** :
   - L'utilisateur clique sur un bouton "Modifier" ou "Supprimer" pour une tâche.
   - Le frontend envoie une requête PUT/DELETE avec l'ID de la tâche et le token JWT.
   - Le backend valide le token, met à jour/supprime la tâche en base, et renvoie une confirmation.
   - Le frontend met à jour l'état global et la liste des tâches.

---

## Sécurité

### 1. Authentification et autorisation
- **JWT** : Les tokens sont signés avec un algorithme sécurisé (HS256) et ont une durée de validité limitée (1 heure). Ils sont stockés dans le `localStorage` du navigateur.
- **Hachage des mots de passe** : Utilisation de bcrypt avec un coût de travail élevé (12 rounds) pour résister aux attaques par force brute.
- **Protection des routes** : Toutes les routes backend nécessitant une authentification sont protégées par une dépendance FastAPI (`OAuth2PasswordBearer`). Le frontend vérifie la présence du token avant d'accéder aux pages protégées.

### 2. Validation des données
- **Backend** : Utilisation de Pydantic pour valider les données d'entrée (ex: format d'email, longueur des champs). Les erreurs sont renvoyées avec un code HTTP 400.
- **Frontend** : Utilisation de formulaires contrôlés avec des validations en temps réel (ex: champ email requis, mot de passe de 8 caractères minimum).

### 3. Protection contre les attaques courantes
- **XSS** : Le frontend utilise React (qui échappe automatiquement les données) et une Content Security Policy (CSP) pour limiter les scripts externes.
- **CSRF** : Désactivé car l'API est stateless (JWT est suffisant). Les tokens sont envoyés dans l'en-tête `Authorization` plutôt que dans les cookies.
- **Injection SQL** : Utilisation de SQLAlchemy (ORM) pour éviter les requêtes SQL brutes. Les paramètres sont toujours passés via des placeholders.

---

## Scalabilité

### 1. Backend
- **Asynchrone** : FastAPI est conçu pour gérer des requêtes asynchrones, ce qui permet de servir un grand nombre d'utilisateurs simultanés avec peu de ressources.
- **Base de données** : PostgreSQL peut être mis à l'échelle verticalement (augmentation des ressources) ou horizontalement (réplication, sharding). Les indexes sont ajoutés sur les champs fréquemment interrogés (ex: `user_id` dans la table `Task`).
- **Cache** : Bien que non implémenté dans cette version, un cache (ex: Redis) pourrait être ajouté pour stocker les tâches fréquemment accédées et réduire la charge sur la base de données.

### 2. Frontend
- **Optimisation des performances** : Utilisation de Vite pour des builds rapides et un code splitting pour charger uniquement les composants nécessaires. Les assets statiques peuvent être servis via un CDN.
- **État global** : Le contexte React est utilisé pour gérer l'état global, mais pour une application plus complexe, une solution comme Redux ou Zustand pourrait être envisagée.

### 3. Déploiement
- **Conteneurisation** : L'application est conteneurisée avec Docker, ce qui permet un déploiement cohérent sur n'importe quel environnement (local, cloud, etc.). Docker Compose est utilisé pour orchestrer les services (backend, frontend, base de données).
- **CI/CD** : GitHub Actions est utilisé pour automatiser les tests, les builds, et les déploiements. Le pipeline peut être étendu pour inclure des tests de charge et des déploiements blue-green.

### 4. Monitoring et logging
- **Backend** : FastAPI intègre des logs natifs qui peuvent être configurés pour envoyer des métriques à des outils comme Prometheus ou Datadog.
- **Frontend** : Les erreurs peuvent être capturées et envoyées à des services comme Sentry pour le monitoring.

---