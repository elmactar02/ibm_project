# Documentation d'Architecture - Todo App Test10

## Vue d'ensemble
Todo App Test10 est une application full-stack de gestion de tâches avec authentification sécurisée. Le système permet aux utilisateurs de créer, modifier, supprimer et filtrer leurs tâches par statut et priorité. L'architecture suit une approche moderne avec séparation claire des responsabilités entre frontend (React), backend (FastAPI) et base de données (PostgreSQL).

Le projet intègre un pipeline CI/CD pour automatiser les tests et le déploiement. L'authentification est gérée via JWT avec une durée de validité de 30 minutes, sans refresh tokens pour simplifier l'implémentation initiale. L'application est conçue pour être responsive et accessible depuis différents appareils.

## Décisions d'architecture

### Choix technologiques
1. **Backend (FastAPI)**:
   - Sélectionné pour sa performance, sa documentation automatique (OpenAPI) et son écosystème Python mature.
   - Permet une implémentation rapide des endpoints REST avec validation automatique des données.
   - Intégration native avec SQLAlchemy pour la couche ORM.

2. **Frontend (React + TypeScript)**:
   - React offre une approche component-based idéale pour une application de gestion de tâches.
   - TypeScript apporte la sécurité de typage pour réduire les erreurs runtime.
   - Vite comme bundler pour des temps de build optimisés.

3. **Base de données (PostgreSQL)**:
   - Choix robuste pour la gestion des relations entre utilisateurs et tâches.
   - Support natif des types Enum pour les champs status et priority.
   - Performances optimisées avec des indexes sur les champs fréquemment filtrés.

4. **Authentification (JWT)**:
   - Implémentation stateless pour une meilleure scalabilité.
   - python-jose pour la génération/validation des tokens.
   - passlib avec bcrypt pour le hashage sécurisé des mots de passe.

### Structure modulaire
L'application est organisée en modules distincts:
- **Auth Module**: Gestion de l'inscription, connexion et validation des tokens.
- **Tasks Module**: Logique métier pour la gestion des tâches (CRUD + filtres).
- **Database Layer**: Abstraction de la base de données avec SQLAlchemy.

Cette séparation permet une maintenance facilitée et une évolutivité accrue.

## Flux de données

### Parcours utilisateur principal
1. **Authentification**:
   - L'utilisateur s'inscrit ou se connecte via `/auth/register` ou `/auth/login`.
   - Le backend valide les credentials et retourne un JWT.
   - Le frontend stocke le token dans le contexte React.

2. **Gestion des tâches**:
   - Le frontend envoie des requêtes authentifiées aux endpoints `/tasks`.
   - Le backend valide le JWT, récupère les données de l'utilisateur et exécute les opérations demandées.
   - Les résultats sont retournés au frontend pour affichage.

3. **Filtrage des tâches**:
   - Les paramètres de filtre (status, priority) sont envoyés en query parameters.
   - Le backend applique les filtres via des indexes PostgreSQL optimisés.

### Pipeline CI/CD
1. **Déclenchement**:
   - Push sur la branche principale ou création d'une pull request.
   - GitHub Actions exécute le workflow défini.

2. **Étapes**:
   - Installation des dépendances (frontend et backend).
   - Exécution des tests unitaires et d'intégration.
   - Build des images Docker.
   - Déploiement sur l'environnement cible (AWS ECS/Vercel).

## Sécurité

### Mesures implémentées
1. **Authentification**:
   - JWT avec signature JWS pour garantir l'intégrité des tokens.
   - Hashage des mots de passe avec bcrypt (coût de travail 12).
   - Tokens avec durée de vie limitée (30 minutes).

2. **Protection des endpoints**:
   - Tous les endpoints `/tasks` nécessitent un JWT valide.
   - Vérification systématique de l'appartenance des tâches à l'utilisateur connecté.

3. **Validation des données**:
   - Validation des entrées côté backend (Pydantic) et frontend (Zod).
   - Protection contre les injections SQL via SQLAlchemy ORM.

4. **Sécurité des dépendances**:
   - Analyse des vulnérabilités via GitHub Dependabot.
   - Mises à jour régulières des dépendances.

### Bonnes pratiques
- Utilisation de variables d'environnement pour les secrets (SECRET_KEY, DATABASE_URL).
- HTTPS obligatoire en production.
- Headers de sécurité (CORS, CSP) configurés dans FastAPI.

## Scalabilité

### Approche horizontale
1. **Backend**:
   - FastAPI est conçu pour la scalabilité avec son modèle asynchrone.
   - Possibilité de déployer plusieurs instances derrière un load balancer.
   - Stateless design permettant une mise à l'échelle horizontale facile.

2. **Base de données**:
   - PostgreSQL supporte le sharding pour distribuer les données.
   - Lecture/écriture séparées avec réplicas en lecture.
   - Indexes optimisés pour les requêtes fréquentes.

3. **Frontend**:
   - Application SPA permettant un déploiement statique.
   - Possibilité de servir les assets via CDN.

### Optimisations
1. **Cache**:
   - Bien que non implémenté initialement, Redis pourrait être ajouté pour:
     - Cacher les résultats des requêtes fréquentes (liste des tâches).
     - Stocker les sessions utilisateurs si nécessaire.

2. **Pagination**:
   - Implémentation de la pagination côté backend pour limiter la charge.
   - Limite par défaut de 10 tâches par requête.

3. **Monitoring**:
   - Intégration de Prometheus et Grafana pour surveiller:
     - Temps de réponse des endpoints.
     - Charge de la base de données.
     - Utilisation mémoire/CPU.

### Perspectives d'évolution
1. **Microservices**:
   - Séparation possible du service d'authentification.
   - Service dédié pour les notifications (email/rappels).

2. **Fonctionnalités avancées**:
   - Ajout de collaborateurs sur les tâches.
   - Synchronisation multi-appareils.
   - Intégration avec des calendriers externes.

3. **Performance**:
   - Implémentation de GraphQL pour réduire les surcharges réseau.
   - Optimisation des requêtes SQL avec des requêtes batch.

Cette architecture fournit une base solide pour une application de gestion de tâches tout en permettant des évolutions futures selon les besoins métiers.

---