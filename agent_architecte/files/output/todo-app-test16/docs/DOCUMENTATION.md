# Documentation d'Architecture - todo-app-test16

## Vue d'ensemble
todo-app-test16 est une application web de gestion de tâches (To-Do list) permettant aux utilisateurs de s'inscrire, se connecter et gérer leurs tâches avec des fonctionnalités de filtrage par statut et priorité. L'application suit une architecture moderne full-stack avec un frontend React, un backend FastAPI et une base de données PostgreSQL.

La complexité du projet est classée comme **medium** en raison des exigences d'authentification sécurisée (JWT), des opérations CRUD avancées avec filtres, et de l'intégration d'un pipeline CI/CD. L'application est conçue pour être scalable horizontalement et sécurisée par design.

## Décisions d'architecture

### Choix technologiques
1. **Backend (FastAPI)**:
   - Sélectionné pour sa performance, sa documentation automatique (OpenAPI/Swagger) et sa compatibilité native avec Python async.
   - Utilisation de Pydantic pour la validation des données et SQLAlchemy pour l'ORM.
   - Structure modulaire avec séparation claire entre routes, services et couche de données.

2. **Frontend (React + TypeScript)**:
   - React 18 pour son écosystème mature et ses performances optimisées.
   - TypeScript pour une meilleure maintenabilité et détection précoce des erreurs.
   - Vite comme bundler pour un développement rapide et une construction optimisée.

3. **Base de données (PostgreSQL)**:
   - Choix motivé par sa fiabilité, ses fonctionnalités avancées (JSONB, full-text search) et sa compatibilité avec SQLAlchemy.
   - Utilisation d'enums pour les champs status et priority afin d'assurer l'intégrité des données.

4. **Authentification (JWT)**:
   - Implémentation avec python-jose pour la génération/validation des tokens et passlib pour le hachage sécurisé des mots de passe.
   - Durée de validité des tokens limitée à 1 heure pour réduire les risques de sécurité.

5. **CI/CD (GitHub Actions)**:
   - Pipeline automatisé pour les tests, la construction et le déploiement sur le dépôt Git spécifié.
   - Intégration des tests unitaires et d'intégration dans le workflow.

### Structure du projet
L'application est divisée en trois conteneurs principaux:
1. **Frontend**: SPA React servie via Nginx en production.
2. **Backend**: API FastAPI avec une architecture en couches (routes → services → repository).
3. **Base de données**: PostgreSQL avec migrations gérées par Alembic.

## Flux de données

### Flux d'authentification
1. L'utilisateur soumet ses identifiants via le formulaire de login (frontend).
2. Le frontend envoie une requête POST à `/auth/login` avec email/mot de passe.
3. Le backend valide les identifiants, génère un token JWT et le retourne.
4. Le frontend stocke le token dans le contexte React et l'ajoute aux headers des requêtes suivantes.
5. Pour chaque requête protégée, le backend valide le token avant de traiter la demande.

### Flux de gestion des tâches
1. L'utilisateur authentifié accède au tableau de bord.
2. Le frontend envoie une requête GET à `/tasks` avec les filtres optionnels (status/priority).
3. Le backend récupère les tâches de l'utilisateur depuis la base de données, applique les filtres et retourne les résultats.
4. Pour les opérations CRUD:
   - **Création**: POST `/tasks` avec les données de la tâche.
   - **Modification**: PUT `/tasks/{id}` avec les champs à mettre à jour.
   - **Suppression**: DELETE `/tasks/{id}`.

### Flux CI/CD
1. Un push sur la branche principale déclenche le workflow GitHub Actions.
2. Le pipeline exécute les tests unitaires et d'intégration.
3. Si les tests passent, le pipeline construit les images Docker pour le frontend et le backend.
4. Les images sont poussées vers le registre Docker (GitHub Container Registry).
5. Le pipeline déploie les nouvelles versions sur l'environnement cible (via SSH ou autre méthode selon la configuration).

## Sécurité

### Mesures de sécurité implémentées
1. **Authentification**:
   - Utilisation de JWT avec une durée de validité limitée (1 heure).
   - Hachage des mots de passe avec bcrypt (coût de travail élevé).
   - Protection des routes sensibles avec FastAPI's OAuth2PasswordBearer.

2. **Protection des données**:
   - Chiffrement des mots de passe avant stockage en base de données.
   - Utilisation de HTTPS pour toutes les communications.
   - Validation stricte des entrées utilisateur (Pydantic pour le backend, TypeScript pour le frontend).

3. **Sécurité de l'API**:
   - Limitation du taux de requêtes (rate limiting) pour prévenir les attaques par force brute.
   - CORS configuré pour n'autoriser que les origines spécifiques.
   - Headers de sécurité (CSP, XSS protection) configurés dans Nginx.

4. **Sécurité de la base de données**:
   - Utilisation de requêtes paramétrées pour prévenir les injections SQL.
   - Isolation des données utilisateur (chaque utilisateur ne voit que ses propres tâches).
   - Sauvegardes régulières de la base de données.

### Bonnes pratiques recommandées
1. **Pour le développement**:
   - Utiliser des variables d'environnement pour les secrets (SECRET_KEY, DATABASE_URL).
   - Ne jamais commiter les fichiers `.env` dans le dépôt Git.
   - Utiliser des tokens d'accès personnels pour GitHub Actions avec des permissions minimales.

2. **Pour la production**:
   - Configurer un WAF (Web Application Firewall) pour protéger contre les attaques courantes.
   - Mettre en place une rotation automatique des secrets.
   - Surveiller les logs pour détecter les activités suspectes.

## Scalabilité

### Scalabilité horizontale
1. **Backend**:
   - FastAPI est conçu pour être scalable horizontalement. Plusieurs instances peuvent être déployées derrière un load balancer.
   - Utilisation de Redis pour le cache (optionnel pour les versions futures) afin de réduire la charge sur la base de données.

2. **Base de données**:
   - PostgreSQL supporte la réplication pour distribuer la charge de lecture.
   - Partitionnement des tables si le volume de données devient important.
   - Utilisation de read replicas pour les requêtes de lecture intensives.

3. **Frontend**:
   - Le frontend statique peut être servi via un CDN pour réduire la latence.
   - Utilisation de service workers pour le caching des assets.

### Optimisations de performance
1. **Backend**:
   - Implémentation de la pagination pour les listes de tâches.
   - Utilisation de requêtes SQL optimisées avec des indexes sur les champs fréquemment filtrés (user_id, status, priority).
   - Mise en cache des résultats des requêtes fréquentes (ex: liste des tâches pour un utilisateur).

2. **Frontend**:
   - Chargement paresseux des composants non critiques.
   - Optimisation des images et assets.
   - Utilisation de React.memo pour éviter les re-renders inutiles.

3. **Base de données**:
   - Indexation des champs utilisés dans les clauses WHERE et JOIN.
   - Utilisation de requêtes batch pour les opérations en masse.
   - Configuration appropriée du pool de connexions.

### Plan de scaling
1. **Phase 1 (1-10k utilisateurs)**:
   - Une seule instance de chaque service (frontend, backend, base de données).
   - Optimisation des requêtes et mise en cache basique.

2. **Phase 2 (10k-100k utilisateurs)**:
   - Déploiement de plusieurs instances du backend derrière un load balancer.
   - Ajout d'une instance Redis pour le caching.
   - Réplication de la base de données avec une read replica.

3. **Phase 3 (100k+ utilisateurs)**:
   - Déploiement multi-région avec CDN pour le frontend.
   - Partitionnement de la base de données.
   - Utilisation d'un message broker (RabbitMQ/Kafka) pour les opérations asynchrones.

---