# Documentation d'Architecture - Todo App Test20

## Vue d'ensemble
Todo App Test20 est une application full-stack de gestion de tâches avec authentification sécurisée. Le système permet aux utilisateurs de créer, modifier et supprimer des tâches, avec des fonctionnalités de filtrage par statut et priorité. L'architecture suit une approche moderne avec séparation claire des responsabilités entre frontend (React) et backend (FastAPI), le tout déployé via des conteneurs Docker.

## Décisions d'architecture

### Choix technologiques
1. **Backend**: FastAPI a été choisi pour sa performance native (async), sa documentation automatique (OpenAPI) et son écosystème Python mature. PostgreSQL offre une solution relationnelle robuste pour les données structurées des tâches et utilisateurs.

2. **Frontend**: React 18 avec TypeScript apporte typage statique et composants réutilisables. Material-UI fournit une base de composants design cohérente. Le state management utilise React Context pour éviter une complexité inutile (Redux non nécessaire pour ce scope).

3. **Authentification**: JWT avec tokens courts (15min) et refresh tokens (7j) offre un équilibre entre sécurité et expérience utilisateur. Les tokens sont stockés dans le localStorage du navigateur avec des mesures de sécurité contre les XSS.

4. **Déploiement**: Docker Compose pour l'environnement local et GitHub Actions pour le CI/CD. La pipeline inclut des tests automatisés et la construction d'images Docker.

### Structure modulaire
- **Backend**: Séparation en routers (auth/tasks), services (auth), et couche database. Chaque module a une responsabilité unique.
- **Frontend**: Organisation par features (auth, tasks) avec des composants réutilisables. Les pages protégées vérifient la présence d'un token JWT.

## Flux de données

### Flux principal
1. L'utilisateur s'authentifie via `/auth/login` → le backend vérifie les credentials et retourne un JWT.
2. Le frontend stocke le token et l'inclut dans les requêtes vers `/tasks`.
3. Le backend valide le token via le `AuthService`, puis interagit avec la base de données via SQLAlchemy.
4. Les données sont retournées au frontend qui les affiche dans le `TaskList`.

### Flux de filtrage
1. L'utilisateur sélectionne des filtres (statut/priorité) dans l'interface.
2. Le frontend envoie une requête GET `/tasks?status=todo&priority=high`.
3. Le backend applique les filtres via SQLAlchemy et retourne les résultats paginés.

## Sécurité

### Authentification
- **JWT**: Tokens signés avec HS256, expirant après 15 minutes. Les refresh tokens sont stockés en base de données avec une durée de 7 jours.
- **Protection CSRF**: Désactivée pour l'API REST (stateless), mais les tokens sont envoyés via Authorization header.
- **Protection XSS**: Les tokens sont stockés dans le localStorage avec des headers HTTP-only pour les cookies (non utilisés ici).

### Base de données
- **Mots de passe**: Hashés avec bcrypt (coût 12) via passlib.
- **Permissions**: Chaque utilisateur n'a accès qu'à ses propres tâches (vérification via `user_id` dans les requêtes).

### Infrastructure
- **Docker**: Les conteneurs backend et frontend sont isolés. PostgreSQL est exposé uniquement au backend.
- **CI/CD**: Les secrets (clés JWT, credentials DB) sont stockés dans les secrets GitHub Actions.

## Scalabilité

### Backend
- **Stateless**: FastAPI est stateless, permettant une mise à l'échelle horizontale facile.
- **Base de données**: PostgreSQL supporte la réplication. Les indexes sur `user_id`, `status` et `priority` optimisent les requêtes de filtrage.
- **Cache**: Redis peut être ajouté pour cacher les listes de tâches fréquemment accédées.

### Frontend
- **Code splitting**: React.lazy() pour charger les pages à la demande.
- **Pagination**: Les listes de tâches sont paginées pour limiter la charge réseau.

### Déploiement
- **Conteneurs**: Les images Docker permettent un déploiement cohérent sur n'importe quel environnement.
- **CI/CD**: La pipeline GitHub Actions peut être étendue pour déployer sur AWS ECS ou Kubernetes.

---