# Documentation d'Architecture — todo-app-test12

## Vue d'ensemble
**todo-app-test12** est une application full-stack de gestion de tâches avec authentification sécurisée. L'architecture suit une approche **modulaire** et **scalable**, séparant clairement les responsabilités entre frontend (React), backend (FastAPI) et base de données (PostgreSQL). Le projet intègre un pipeline CI/CD pour automatiser les tests et déploiements.

**Objectifs clés** :
- Offrir une expérience utilisateur fluide avec filtres dynamiques (statut/priorité).
- Sécuriser les données avec JWT et hachage des mots de passe.
- Permettre une évolutivité future (ajout de fonctionnalités comme les équipes ou les rappels).

## Décisions d'architecture
1. **Backend (FastAPI)** :
   - Choix motivé par la **performance** (async natif) et la **documentation automatique** (OpenAPI).
   - Structure en couches : *routers* (contrôleurs) → *services* (logique métier) → *database layer* (ORM).
   - Authentification JWT avec cookies httpOnly pour éviter les XSS.

2. **Frontend (React + TypeScript)** :
   - **TypeScript** pour réduire les bugs en production et améliorer la maintenabilité.
   - **React Router v6** pour une navigation fluide avec routes protégées.
   - **Tailwind CSS** pour un design système cohérent sans surcharge de dépendances.

3. **Base de données (PostgreSQL)** :
   - **SQLAlchemy ORM** pour une abstraction propre et des migrations faciles (Alembic).
   - Indexes sur `user_id` et `status` pour optimiser les requêtes de filtres.

4. **CI/CD (GitHub Actions)** :
   - Pipeline déclenché sur `git push` : tests (pytest + Jest) → build Docker → déploiement.
   - Variables d'environnement sécurisées pour les secrets (clés JWT, DB_URL).

## Flux de données
1. **Authentification** :
   - L'utilisateur s'inscrit/connexion → le backend valide les données → génère un JWT → stocke en cookie httpOnly.
   - Le frontend envoie le JWT dans les headers pour les requêtes protégées.

2. **Gestion des tâches** :
   - Le frontend envoie une requête GET `/tasks?status=todo&priority=high` → le backend filtre les tâches via SQLAlchemy → retourne les résultats paginés.
   - Pour les modifications (POST/PUT/DELETE), le backend vérifie les permissions (tâche appartient à l'utilisateur).

3. **CI/CD** :
   - Un push sur `main` déclenche le pipeline → exécute les tests → build l'image Docker → déploie sur Render/Railway.

## Sécurité
- **Authentification** :
  - Mots de passe hachés avec **bcrypt** (passlib).
  - JWT signés avec **HS256** et durée limitée (1h).
  - Cookies httpOnly pour éviter les attaques XSS.

- **Validation des données** :
  - Backend : Pydantic pour valider les payloads (ex: email format, longueur des champs).
  - Frontend : React Hook Form + Zod pour une validation côté client.

- **Permissions** :
  - Middleware FastAPI vérifie que l'utilisateur est propriétaire de la tâche avant toute modification/suppression.

- **Infrastructure** :
  - Variables d'environnement pour les secrets (`.env` ignoré par Git).
  - PostgreSQL avec connexion chiffrée (SSL).

## Scalabilité
1. **Backend** :
   - FastAPI supporte le **load balancing** grâce à son architecture async.
   - Possibilité d'ajouter **Redis** pour le cache (ex: tâches fréquemment accédées).

2. **Base de données** :
   - PostgreSQL supporte le **sharding** et la réplication pour les gros volumes.
   - Indexes optimisés pour les requêtes de filtres.

3. **Frontend** :
   - Code splitté avec React.lazy pour réduire le bundle initial.
   - Possibilité d'ajouter un **CDN** pour les assets statiques.

4. **CI/CD** :
   - Pipeline modulaire pour ajouter des étapes (ex: tests de charge avec Locust).
   - Déploiement en **blue-green** pour minimiser les downtimes.

---