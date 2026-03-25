# Documentation d'Architecture - todo-app-test19

## Vue d'ensemble
todo-app-test19 est une application de gestion de tâches (To-Do list) avec authentification JWT, permettant aux utilisateurs de créer, modifier, supprimer et filtrer leurs tâches par statut et priorité. L'application suit une architecture moderne full-stack avec un frontend React, un backend FastAPI et une base de données PostgreSQL.

Le système est conçu pour être déployé via un pipeline CI/CD utilisant GitHub Actions, assurant une intégration et un déploiement continus. L'architecture est modulaire, avec une séparation claire entre les couches de présentation, de logique métier et de persistance.

## Décisions d'architecture

1. **Choix technologiques**:
   - **Frontend**: React 18 avec TypeScript pour une meilleure maintenabilité et typage fort. Vite est utilisé comme bundler pour ses performances.
   - **Backend**: FastAPI pour sa rapidité, sa documentation automatique et son support natif de l'asynchrone.
   - **Base de données**: PostgreSQL pour sa fiabilité, ses fonctionnalités avancées (comme les types Enum) et sa compatibilité avec SQLAlchemy.
   - **Authentification**: JWT avec python-jose pour la génération/validation et passlib pour le hachage sécurisé des mots de passe.

2. **Séparation des responsabilités**:
   - Le backend est divisé en routers (auth et tasks) et services (users et tasks) pour une meilleure maintenabilité.
   - Le frontend utilise un contexte d'authentification pour gérer l'état global du JWT.
   - La couche de base de données est abstraite via SQLAlchemy ORM.

3. **CI/CD**:
   - GitHub Actions est utilisé pour automatiser les tests et le déploiement, avec des workflows séparés pour le frontend et le backend.

4. **Scalabilité**:
   - L'architecture stateless du backend permet une scalabilité horizontale facile.
   - Les requêtes SQL sont optimisées avec des indexes sur les champs fréquemment filtrés.

## Flux de données

1. **Authentification**:
   - L'utilisateur soumet ses identifiants via le formulaire de login.
   - Le frontend envoie une requête POST à `/auth/login`.
   - Le backend valide les identifiants, génère un JWT et le retourne.
   - Le frontend stocke le JWT dans un contexte React et l'inclut dans les requêtes suivantes.

2. **Gestion des tâches**:
   - Le frontend récupère les tâches via GET `/tasks` avec les filtres optionnels.
   - Pour créer une tâche, le frontend envoie une requête POST à `/tasks` avec les données de la tâche.
   - Le backend valide le JWT, crée la tâche en base de données et retourne la tâche créée.
   - Les opérations de mise à jour et suppression suivent un flux similaire.

3. **CI/CD**:
   - Les développeurs pushent du code sur la branche principale.
   - GitHub Actions déclenche les tests automatisés.
   - Si les tests passent, le code est déployé sur l'environnement cible.

## Sécurité

1. **Authentification**:
   - Les mots de passe sont hachés avec bcrypt avant stockage.
   - Les JWT ont une expiration courte (30 minutes) et sont signés avec un secret fort.
   - Les endpoints protégés vérifient la présence et la validité du JWT.

2. **Autorisation**:
   - Chaque tâche est associée à un utilisateur (relation Many-to-One).
   - Les endpoints de tâches vérifient que l'utilisateur authentifié est propriétaire de la tâche.

3. **Protection contre les attaques**:
   - CORS est configuré pour n'autoriser que les requêtes depuis le domaine du frontend.
   - Les requêtes sensibles (comme la suppression) utilisent des méthodes HTTP appropriées (DELETE).
   - Les entrées utilisateur sont validées côté backend.

4. **CI/CD**:
   - Les secrets (comme les clés JWT) sont stockés dans les secrets GitHub Actions.
   - Les workflows CI/CD nécessitent des approbations pour les déploiements en production.

## Scalabilité

1. **Backend**:
   - FastAPI est conçu pour gérer un grand nombre de requêtes concurrentes grâce à son support natif de l'asynchrone.
   - La couche de base de données peut être optimisée avec des indexes et des requêtes SQL efficaces.
   - En cas de besoin, le backend peut être déployé sur plusieurs instances derrière un load balancer.

2. **Base de données**:
   - PostgreSQL supporte le sharding et la réplication pour une meilleure scalabilité.
   - Les requêtes sont optimisées avec des indexes sur les champs fréquemment filtrés (status, priority, user_id).

3. **Frontend**:
   - React est optimisé pour les performances avec des techniques comme le lazy loading des composants.
   - Les données sont paginées pour éviter de charger trop de tâches en une seule fois.

4. **CI/CD**:
   - Les workflows GitHub Actions peuvent être parallélisés pour réduire le temps de build.
   - Les artefacts de build sont mis en cache pour accélérer les déploiements futurs.

---