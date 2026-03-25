# Documentation d'Architecture - todo-app-test14

## Vue d'ensemble
**todo-app-test14** est une application full-stack de gestion de tâches (To-Do list) avec authentification sécurisée et fonctionnalités de filtrage avancées. Le système suit une architecture moderne **client-serveur** avec :
- **Frontend** : Application SPA en React 18 avec TypeScript
- **Backend** : API RESTful en FastAPI (Python)
- **Base de données** : PostgreSQL pour le stockage persistant
- **CI/CD** : Pipeline GitHub Actions pour automatisation

L'application permet aux utilisateurs de s'inscrire, se connecter, créer/modifier/supprimer des tâches, et les filtrer par statut (todo/in_progress/done) et priorité (low/medium/high).

## Décisions d'architecture

### Choix technologiques
1. **FastAPI** pour le backend :
   - Performance native (ASGI)
   - Documentation automatique (OpenAPI/Swagger)
   - Validation des données intégrée (Pydantic)
   - Support natif de l'asynchrone

2. **React + TypeScript** pour le frontend :
   - Typage statique pour réduire les bugs
   - Écosystème riche (React Hook Form, Zustand)
   - Vite pour un bundling rapide

3. **PostgreSQL** :
   - Fiabilité et ACID
   - Support natif des types JSON et enum
   - Indexes pour optimiser les requêtes de filtrage

4. **JWT** pour l'authentification :
   - Stateless (pas de sessions serveur)
   - Sécurité renforcée avec httpOnly cookies
   - Expiration courte (30 minutes) avec possibilité de rafraîchissement

### Structure modulaire
- **Backend** :
  - Séparation claire entre routers (contrôleurs), services (logique métier) et modèles (données)
  - Injection de dépendances pour les services
  - Middleware pour la gestion des erreurs et CORS

- **Frontend** :
  - Architecture basée sur les composants (Atomic Design)
  - State management hybride (Context pour l'auth, Zustand pour les tâches)
  - Routing protégé pour les pages nécessitant une authentification

## Flux de données

### Flux principal (CRUD tâches)
1. **Frontend** → Envoie une requête HTTP (GET/POST/PUT/DELETE) à l'API avec le JWT dans les cookies
2. **API Backend** :
   - Vérifie le JWT via le middleware d'authentification
   - Valide les données avec Pydantic
   - Exécute la logique métier via le service dédié
   - Interagit avec la base de données via SQLAlchemy
3. **Base de données** → Retourne les données demandées
4. **API Backend** → Formate la réponse et la retourne au frontend
5. **Frontend** → Met à jour l'interface utilisateur

### Flux d'authentification
1. **Frontend** → Envoie les identifiants (email/mot de passe) à `/auth/login`
2. **API Backend** :
   - Vérifie les identifiants en base
   - Génère un JWT avec python-jose
   - Retourne le token dans un httpOnly cookie
3. **Frontend** → Stocke le token dans le contexte React et redirige vers le dashboard

### Flux CI/CD
1. **Développeur** → Pousse du code sur la branche `main`
2. **GitHub Actions** :
   - Exécute les tests (pytest pour backend, Jest pour frontend)
   - Construit les images Docker
   - Déploie sur l'environnement cible (Render/Railway pour backend, Vercel pour frontend)

## Sécurité

### Authentification
- **JWT** :
  - Signé avec HS256 et une clé secrète forte
  - Durée de vie limitée (30 minutes)
  - Stocké dans des httpOnly cookies pour prévenir les XSS
  - Invalidation côté client via le contexte React

- **Mots de passe** :
  - Hachés avec bcrypt (passlib)
  - Salage automatique
  - Validation de complexité côté frontend et backend

### Protection des données
- **CORS** : Restreint aux origines autorisées
- **CSRF** : Protection via les cookies SameSite
- **SQL Injection** : Prévenue par l'utilisation de SQLAlchemy ORM
- **Validation des entrées** : Double validation (frontend avec Zod, backend avec Pydantic)

### Sécurité des conteneurs
- **Backend** :
  - Exécution avec un utilisateur non-root
  - Variables d'environnement pour les secrets
  - Limitation des ressources (CPU/mémoire)

- **Base de données** :
  - Mot de passe fort pour l'utilisateur PostgreSQL
  - Volume chiffré pour le stockage persistant

## Scalabilité

### Backend
- **Stateless** : Permet une mise à l'échelle horizontale facile
- **Base de données** :
  - Indexes sur les champs fréquemment filtrés (user_id, status, priority)
  - Possibilité d'ajouter un cache Redis pour les tâches fréquemment accédées
- **Asynchrone** : FastAPI supporte nativement l'asynchrone pour les I/O bound operations

### Frontend
- **Code splitting** : Chargement paresseux des routes
- **Optimisation des images** : Via Vite
- **Bundle analysis** : Pour identifier les dépendances lourdes

### Déploiement
- **Conteneurisation** : Docker pour une portabilité maximale
- **Orchestration** : Possibilité de migrer vers Kubernetes si besoin
- **CI/CD** : Pipeline GitHub Actions pour des déploiements fréquents et fiables

### Monitoring
- **Backend** : Intégration possible avec Prometheus + Grafana
- **Frontend** : Sentry pour le suivi des erreurs
- **Logs** : Centralisation via ELK Stack (à implémenter en production)

---