# Documentation d'Architecture — todo-app-test7

## Vue d'ensemble
**todo-app-test7** est une application full-stack de gestion de tâches (To-Do list) avec authentification sécurisée. L'architecture suit une approche **modulaire** et **scalable**, séparant clairement les responsabilités entre frontend (React), backend (FastAPI) et base de données (PostgreSQL). Le projet intègre un pipeline CI/CD pour automatiser les déploiements sur GitHub.

### Objectifs principaux
1. **Authentification sécurisée** : Inscription/connexion via JWT pour protéger les données utilisateur.
2. **Gestion avancée des tâches** : CRUD complet avec filtres par statut (`todo`, `in_progress`, `done`) et priorité (`low`, `medium`, `high`).
3. **Expérience utilisateur fluide** : Interface SPA réactive avec React et gestion d'état centralisée (Zustand).
4. **Déploiement automatisé** : Pipeline CI/CD avec GitHub Actions pour tester et déployer le code.

---

## Décisions d'architecture

### 1. Choix technologiques
- **Backend (FastAPI)** :
  - **Pourquoi FastAPI** : Framework Python moderne avec support natif de l'asynchrone, idéal pour les APIs REST. Intègre nativement OpenAPI/Swagger pour la documentation.
  - **Authentification** : JWT avec `python-jose` et hachage bcrypt (`passlib`) pour une sécurité robuste sans surcharge.
  - **ORM** : SQLAlchemy pour une abstraction propre de PostgreSQL, avec migrations gérées par Alembic.

- **Frontend (React + TypeScript)** :
  - **Pourquoi React** : Bibliothèque dominante pour les SPAs, avec un écosystème riche (React Router, Zustand).
  - **TypeScript** : Ajoute une couche de typage statique pour réduire les bugs et améliorer la maintenabilité.
  - **Gestion d'état** : Zustand choisi pour sa simplicité (alternative légère à Redux) pour gérer l'état des tâches et de l'utilisateur.

- **Base de données (PostgreSQL)** :
  - **Pourquoi PostgreSQL** : Base relationnelle robuste avec support des types JSON/Enum, idéale pour les relations utilisateur-tâche.
  - **Indexation** : Indexes sur `user_id`, `status`, et `priority` pour optimiser les requêtes de filtrage.

- **CI/CD (GitHub Actions)** :
  - **Workflow** : Tests automatisés (pytest pour le backend, Jest pour le frontend) + déploiement conditionnel sur la branche `main`.

### 2. Structure modulaire
- **Backend** :
  - Séparation claire entre **routes** (FastAPI Routers), **services** (logique métier), et **couche database** (SQLAlchemy).
  - Exemple : Le `TasksRouter` délègue la logique métier au `TasksService`, qui utilise le `DatabaseLayer` pour interagir avec PostgreSQL.

- **Frontend** :
  - **Pages** : `/login`, `/register`, `/dashboard` (avec layout commun via `AuthLayout`).
  - **Composants réutilisables** : `TaskForm` (modal pour création/modification), `TaskFilters` (boutons radio pour les filtres).

### 3. Sécurité
- **JWT** :
  - Tokens signés avec HS256, durée de validité courte (15 minutes).
  - Stockage sécurisé dans le frontend (HTTP-only cookies pour éviter les XSS).
- **Hachage des mots de passe** : bcrypt avec un coût de 12 rounds.
- **Validation des entrées** :
  - Backend : Pydantic pour valider les schemas (ex: `TaskCreate`, `UserRegister`).
  - Frontend : React Hook Form pour valider les formulaires avant envoi.

### 4. Scalabilité
- **Backend** :
  - FastAPI supporte nativement l'asynchrone, permettant de gérer des milliers de requêtes concurrentes.
  - La couche database peut être optimisée avec des **requêtes batch** pour les listes de tâches.
- **Frontend** :
  - Chargement paresseux des composants (React.lazy) pour réduire le bundle initial.
  - Zustand permet de scaler la gestion d'état sans complexité excessive.
- **Base de données** :
  - PostgreSQL supporte le sharding et la réplication pour une scalabilité horizontale.
  - Les indexes sur `user_id`, `status`, et `priority` garantissent des performances constantes même avec des millions de tâches.

---

## Flux de données

### 1. Authentification
1. **Inscription** :
   - Frontend → `POST /auth/register` (email + mot de passe) → Backend hache le mot de passe → Stocke l'utilisateur en base.
2. **Connexion** :
   - Frontend → `POST /auth/login` (email + mot de passe) → Backend vérifie les credentials → Retourne un JWT.
   - Frontend stocke le JWT dans un cookie HTTP-only et le transmet dans les headers `Authorization: Bearer <token>` pour les requêtes protégées.

### 2. Gestion des tâches
1. **Création d'une tâche** :
   - Frontend → `POST /tasks/` (titre, description, status, priority) → Backend valide le JWT → Crée la tâche en base avec `user_id`.
2. **Liste des tâches** :
   - Frontend → `GET /tasks/?status=todo&priority=high` → Backend filtre les tâches par `user_id` (extrait du JWT) + paramètres de filtre → Retourne les résultats paginés.
3. **Modification/Suppression** :
   - Frontend → `PUT /tasks/{id}` ou `DELETE /tasks/{id}` → Backend vérifie que la tâche appartient à l'utilisateur (via `user_id`) → Met à jour/supprime en base.

### 3. CI/CD
1. **Push sur GitHub** :
   - Déclenche un workflow GitHub Actions qui :
     - Installe les dépendances (backend + frontend).
     - Exécute les tests (pytest + Jest).
     - Construit les images Docker (si les tests passent).
     - Déploie sur GitHub Pages (frontend) et Render/Heroku (backend) si la branche est `main`.

---

## Sécurité

### 1. Menaces et contre-mesures
| Menace                  | Contre-mesure                                                                 |
|-------------------------|------------------------------------------------------------------------------|
| Injection SQL           | Utilisation de SQLAlchemy (ORM) pour éviter les requêtes raw.               |
| XSS                     | React escape automatiquement les données. Cookies HTTP-only pour le JWT.    |
| CSRF                    | Double soumission de cookies (non implémenté dans cette version, mais possible avec des tokens CSRF). |
| Attaques par force brute| Limitation de taux sur `/auth/login` (non implémenté, mais recommandé).     |
| Fuites de données       | JWT avec durée de validité courte. Hachage bcrypt pour les mots de passe.   |

### 2. Bonnes pratiques
- **Backend** :
  - Ne jamais retourner le `hashed_password` dans les réponses API.
  - Utiliser des variables d'environnement pour les secrets (`SECRET_KEY`, `DATABASE_URL`).
- **Frontend** :
  - Ne pas stocker le JWT dans `localStorage` (vulnérable aux XSS). Préférer les cookies HTTP-only.
  - Valider toutes les entrées utilisateur côté client **et** serveur.

---

## Scalabilité

### 1. Backend
- **Stateless** : FastAPI est stateless, permettant de scaler horizontalement avec un load balancer (ex: Nginx).
- **Cache** : Ajout possible de Redis pour cacher les listes de tâches fréquemment accédées.
- **Base de données** :
  - Lecture/écriture séparées avec réplicas PostgreSQL.
  - Partitionnement des tables si le volume de tâches devient trop important.

### 2. Frontend
- **Code splitting** : Chargement paresseux des pages (ex: `Dashboard` chargé uniquement après connexion).
- **Optimisation des images** : Utilisation de `next/image` (si migration vers Next.js) ou compression manuelle.
- **CDN** : Déploiement du frontend sur un CDN (ex: Cloudflare) pour réduire la latence.

### 3. CI/CD
- **Tests parallèles** : Exécution des tests backend/frontend en parallèle dans GitHub Actions.
- **Déploiement bleu-vert** : Pour minimiser les temps d'arrêt lors des mises à jour (nécessite une infrastructure cloud comme AWS ECS).

---

## Améliorations futures
1. **Refresh Tokens** : Implémenter un mécanisme de refresh tokens pour éviter les déconnexions fréquentes.
2. **Notifications** : Ajouter des notifications en temps réel avec WebSockets (ex: tâche assignée).
3. **Collaboration** : Permettre le partage de tâches entre utilisateurs (nécessite un modèle `TaskSharing`).
4. **Offline-first** : Utiliser IndexedDB pour synchroniser les tâches lorsque l'utilisateur est hors ligne.

---