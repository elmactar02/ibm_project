# Documentation d'Architecture - TodoApp Test22

## Vue d'ensemble
TodoApp Test22 est une application full-stack de gestion de tâches avec authentification sécurisée. Le système permet aux utilisateurs de s'inscrire, se connecter, et gérer leurs tâches avec des fonctionnalités de filtrage avancées. L'architecture suit une approche moderne avec séparation claire des responsabilités entre frontend (React), backend (FastAPI) et base de données (PostgreSQL).

La complexité du projet est classée comme **moyenne** en raison:
- De l'intégration d'un système d'authentification JWT
- Des fonctionnalités de filtrage dynamiques
- De la pipeline CI/CD à configurer
- De la nécessité de gérer les relations entre utilisateurs et tâches

## Décisions d'architecture

### Choix technologiques
1. **Backend**: FastAPI a été choisi pour sa performance, sa documentation automatique (OpenAPI) et son support natif de l'asynchrone. Python 3.10 offre une bonne compatibilité avec les bibliothèques modernes.

2. **Frontend**: React 18 avec TypeScript permet une meilleure maintenabilité et détection précoce des erreurs. Vite est utilisé comme bundler pour son démarrage rapide et son HMR efficace.

3. **Base de données**: PostgreSQL 15 a été sélectionné pour sa fiabilité, son support des types JSON et ses performances pour les requêtes complexes (filtres).

4. **Authentification**: JWT avec python-jose et passlib (bcrypt) offre un bon équilibre entre sécurité et simplicité d'implémentation.

5. **CI/CD**: GitHub Actions est utilisé pour sa intégration native avec GitHub et sa flexibilité.

### Structure modulaire
L'application est divisée en plusieurs modules indépendants:
- **Auth Module**: Gère l'inscription, la connexion et la validation des tokens
- **Tasks Module**: Contient toute la logique métier des tâches
- **Database Layer**: Abstraction de la base de données avec SQLAlchemy
- **Frontend Components**: Composants réutilisables avec une séparation claire entre présentation et logique

### Gestion d'état
- **Backend**: L'état est géré via la base de données avec SQLAlchemy ORM
- **Frontend**: React Query pour la gestion des données distantes et React Context pour l'authentification

## Flux de données

### Flux d'authentification
1. L'utilisateur soumet ses identifiants via le formulaire de login
2. Le frontend envoie une requête POST à `/auth/login`
3. Le backend valide les identifiants et génère un JWT
4. Le token est stocké dans le localStorage du navigateur
5. Les requêtes suivantes incluent le token dans l'en-tête Authorization

### Flux de gestion des tâches
1. L'utilisateur accède au tableau de bord
2. Le frontend envoie une requête GET à `/tasks` avec les filtres éventuels
3. Le backend récupère les tâches de l'utilisateur depuis la base de données
4. Les données sont retournées au frontend et affichées
5. Pour les opérations CRUD, des requêtes spécifiques sont envoyées aux endpoints correspondants

### Flux CI/CD
1. Un push sur la branche principale déclenche le pipeline
2. Les tests unitaires et d'intégration sont exécutés
3. Si les tests passent, le code est buildé et déployé
4. Les images Docker sont poussées vers le registry
5. Le déploiement est effectué sur l'environnement cible

## Sécurité

### Authentification
- JWT avec signature HS256 et expiration courte (30 minutes)
- Hachage des mots de passe avec bcrypt (coût 12)
- Protection CSRF via les en-têtes CORS
- Validation des entrées à tous les niveaux (frontend et backend)

### Autorisation
- Vérification du token JWT pour toutes les routes protégées
- Vérification de l'appartenance des tâches à l'utilisateur courant
- Rôles simples (utilisateur standard uniquement pour cette version)

### Protection des données
- Chiffrement des mots de passe en base de données
- Utilisation de HTTPS pour toutes les communications
- Variables d'environnement pour les secrets (JWT_SECRET, DATABASE_URL)
- Prévention des injections SQL via SQLAlchemy ORM

## Scalabilité

### Backend
- FastAPI supporte nativement l'asynchrone pour une meilleure gestion des requêtes concurrentes
- La base de données PostgreSQL peut être mise à l'échelle verticalement
- Possibilité d'ajouter un cache Redis pour les requêtes fréquentes
- Les indexes sur les champs fréquemment filtrés (status, priority) optimisent les performances

### Frontend
- React Query gère efficacement le cache des données
- Le code est modularisé pour faciliter les mises à jour
- Les composants sont conçus pour être réutilisables

### Infrastructure
- L'architecture en conteneurs permet un déploiement facile sur différents environnements
- Docker Compose facilite le scaling horizontal des services
- La pipeline CI/CD permet des déploiements fréquents et fiables

### Améliorations futures
1. Ajout d'un système de rafraîchissement de token
2. Implémentation d'un cache Redis pour les requêtes fréquentes
3. Mise en place d'un système de logging centralisé
4. Ajout de métriques et monitoring
5. Implémentation d'un système de notifications en temps réel (WebSockets)

---