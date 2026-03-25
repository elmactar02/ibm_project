# Documentation d'Architecture — todo-app-test2

## Vue d'ensemble
**todo-app-test2** est une application full-stack de gestion de tâches avec authentification sécurisée. Le système permet aux utilisateurs de s'inscrire, se connecter, et gérer leurs tâches avec des filtres par statut et priorité. L'architecture suit une approche **modulaire** et **scalable**, avec une séparation claire entre frontend (React), backend (FastAPI), et base de données (SQLite/PostgreSQL).

**Objectifs clés** :
- Authentification sécurisée avec JWT.
- Interface réactive avec filtres dynamiques.
- Pipeline CI/CD pour déploiement automatisé.
- Adaptabilité entre développement (SQLite) et production (PostgreSQL).

## Décisions d'architecture
1. **Backend (FastAPI)** :
   - Choix de FastAPI pour ses performances (ASGI) et sa documentation automatique (OpenAPI).
   - Structure modulaire avec routers/services pour une maintenabilité accrue.
   - Utilisation de **SQLAlchemy** pour l'abstraction de la base de données (compatibilité SQLite/PostgreSQL).

2. **Frontend (React + TypeScript)** :
   - React 18 pour les hooks et le rendu concurrent.
   - TypeScript pour la robustesse du code et la détection précoce d'erreurs.
   - **React Query** pour la gestion des états serveur (cache, synchronisation).

3. **Base de données** :
   - **SQLite** en développement pour sa simplicité (fichier local).
   - **PostgreSQL** en production pour sa fiabilité et ses fonctionnalités avancées (indexation, transactions).
   - **Alembic** pour les migrations de schéma.

4. **Authentification** :
   - JWT avec **HttpOnly cookies** pour éviter les attaques XSS.
   - Double token (access/refresh) pour un équilibre sécurité/expérience utilisateur.
   - Hashage des mots de passe avec **bcrypt** (via passlib).

5. **CI/CD** :
   - Pipeline GitHub Actions/GitLab CI pour :
     - Tests automatisés (pytest pour backend, vitest pour frontend).
     - Build Docker et déploiement sur AWS ECS/Render.

## Flux de données
1. **Authentification** :
   - L'utilisateur soumet ses identifiants via `/auth/login`.
   - Le backend valide les données, génère un JWT, et le retourne dans un cookie HttpOnly.
   - Le frontend stocke le token dans un contexte React pour les requêtes authentifiées.

2. **Gestion des tâches** :
   - Le frontend envoie une requête GET `/tasks?status=todo&priority=high` avec le JWT.
   - Le backend vérifie le token, récupère les tâches filtrées via SQLAlchemy, et retourne les données.
   - Le frontend affiche les tâches dans une liste avec des composants Material-UI.

3. **Création/Modification** :
   - L'utilisateur remplit un formulaire (React Hook Form + Zod).
   - Le frontend envoie une requête POST/PUT `/tasks` avec les données validées.
   - Le backend met à jour la base de données et retourne la tâche mise à jour.

## Sécurité
- **JWT** : Tokens signés avec HS256, durée de vie courte (15min pour access_token).
- **Cookies** : Flags `HttpOnly`, `Secure`, et `SameSite=Strict` pour les tokens.
- **Hashage** : Mots de passe hashés avec bcrypt (coût 12).
- **Validation** :
  - Backend : Pydantic pour les modèles d'entrée.
  - Frontend : Zod pour les formulaires.
- **CORS** : Restreint aux origines autorisées (configuré dans FastAPI).
- **SQL Injection** : Prévenu par SQLAlchemy (requêtes paramétrées).

## Scalabilité
1. **Backend** :
   - FastAPI supporte le scaling horizontal (plusieurs workers Uvicorn).
   - PostgreSQL peut être mis à l'échelle avec des réplicas en lecture.
   - Cache Redis optionnel pour les tâches fréquemment accédées.

2. **Frontend** :
   - Code optimisé avec Vite (build rapide, lazy loading des routes).
   - CDN pour les assets statiques (images, CSS).

3. **Base de données** :
   - Indexation des colonnes `status`, `priority`, et `user_id` pour les requêtes filtrées.
   - Partitionnement possible par `user_id` si le nombre d'utilisateurs explose.

4. **Déploiement** :
   - Docker multi-stage pour réduire la taille des images.
   - CI/CD pour des déploiements sans downtime (blue-green ou rolling updates).

---