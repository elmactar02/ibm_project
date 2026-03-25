# Documentation d'Architecture — TodoApp (todo-app-test21)

## Vue d'ensemble
TodoApp est une application full-stack de gestion de tâches avec authentification sécurisée, conçue pour permettre aux utilisateurs de créer, organiser et suivre leurs tâches quotidiennes. L'application suit une architecture moderne basée sur des conteneurs avec un frontend React, un backend FastAPI, et une base de données PostgreSQL. Le projet intègre un pipeline CI/CD pour automatiser les tests et le déploiement.

L'application répond aux besoins suivants:
- Authentification sécurisée avec JWT
- Gestion complète des tâches (CRUD)
- Filtrage avancé par statut et priorité
- Interface utilisateur réactive et intuitive
- Déploiement automatisé via CI/CD

## Décisions d'architecture
1. **Séparation des responsabilités**:
   - Frontend (React) gère uniquement l'interface utilisateur et les appels API.
   - Backend (FastAPI) implémente la logique métier et l'accès aux données.
   - Base de données (PostgreSQL) stocke les données de manière relationnelle.

2. **Technologies choisies**:
   - **FastAPI**: Framework Python moderne pour le backend, choisi pour ses performances, sa documentation automatique (OpenAPI), et sa facilité d'intégration avec JWT.
   - **React + TypeScript**: Combinaison robuste pour le frontend avec typage statique et écosystème riche.
   - **PostgreSQL**: Base de données relationnelle pour garantir l'intégrité des données et supporter les requêtes complexes (filtres).
   - **Docker**: Conteneurisation pour une portabilité maximale et une configuration reproductible.

3. **Authentification**:
   - JWT (JSON Web Tokens) pour une authentification stateless.
   - Hachage des mots de passe avec bcrypt pour une sécurité renforcée.
   - Middleware FastAPI pour protéger les routes sensibles.

4. **CI/CD**:
   - GitHub Actions pour automatiser les tests et le déploiement.
   - Pipeline déclenché à chaque push sur la branche principale.

## Flux de données
1. **Authentification**:
   - L'utilisateur soumet ses identifiants via le formulaire de login (frontend).
   - Le backend valide les identifiants, génère un token JWT, et le retourne au frontend.
   - Le frontend stocke le token dans un contexte React et l'ajoute aux headers des requêtes suivantes.

2. **Gestion des tâches**:
   - Le frontend envoie une requête GET `/tasks` avec les filtres (status, priority) en query params.
   - Le backend récupère les tâches de l'utilisateur depuis PostgreSQL, applique les filtres, et retourne les résultats.
   - Pour la création/modification, le frontend envoie une requête POST/PUT avec les données de la tâche.
   - Le backend valide les données, met à jour la base de données, et retourne la tâche mise à jour.

3. **CI/CD**:
   - À chaque push sur la branche principale, GitHub Actions exécute les tests unitaires et d'intégration.
   - Si les tests passent, le pipeline déploie automatiquement l'application sur l'environnement cible.

## Sécurité
1. **Authentification**:
   - Les mots de passe sont hachés avec bcrypt avant stockage.
   - Les tokens JWT ont une durée de validité limitée (24h) et sont signés avec un secret.
   - Les routes sensibles sont protégées par un middleware qui vérifie la présence et la validité du token.

2. **Protection des données**:
   - Les requêtes SQL utilisent des paramètres pour éviter les injections.
   - Les données sensibles (mots de passe, tokens) ne sont jamais exposées dans les logs ou les réponses API.

3. **Frontend**:
   - Les tokens JWT sont stockés dans un contexte React et non dans le localStorage pour éviter les attaques XSS.
   - Les requêtes API utilisent HTTPS pour chiffrer les données en transit.

4. **Infrastructure**:
   - Les conteneurs Docker sont configurés avec des utilisateurs non-root pour limiter les privilèges.
   - Les variables d'environnement sensibles (secrets JWT, mots de passe DB) sont injectées via Docker secrets ou GitHub Secrets.

## Scalabilité
1. **Backend**:
   - FastAPI est conçu pour être asynchrone et peut gérer un grand nombre de requêtes simultanées.
   - La base de données PostgreSQL supporte les index pour optimiser les requêtes de filtrage.
   - Possibilité d'ajouter un cache Redis pour les requêtes fréquentes (ex: liste des tâches).

2. **Frontend**:
   - React permet une mise à jour efficace du DOM avec le Virtual DOM.
   - La pagination côté client réduit la charge sur le backend pour les listes de tâches volumineuses.

3. **Déploiement**:
   - Docker permet de scaler horizontalement en ajoutant des instances du backend.
   - Le pipeline CI/CD peut être étendu pour supporter des environnements multiples (staging, production).
   - Possibilité de migrer vers un orchestrateur comme Kubernetes pour une scalabilité avancée.

4. **Base de données**:
   - PostgreSQL supporte le sharding et la réplication pour distribuer la charge.
   - Les indexes sur les champs fréquemment filtrés (status, priority) optimisent les performances.

---