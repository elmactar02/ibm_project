# Documentation d'Architecture - Todo App Test9

## Vue d'ensemble
**todo-app-test9** est une application full-stack de gestion de tâches avec authentification sécurisée. Elle permet aux utilisateurs de créer, modifier et supprimer des tâches, tout en les filtrant par statut (todo/in_progress/done) et priorité (low/medium/high). L'architecture suit une approche moderne avec séparation claire des responsabilités entre frontend (React) et backend (FastAPI), le tout containerisé avec Docker et déployé via GitHub Actions.

## Décisions d'architecture
1. **Séparation frontend/backend** : Choix d'une SPA React pour une expérience utilisateur fluide, communiquant avec une API RESTful en FastAPI. Cette séparation permet une évolutivité indépendante des deux parties.

2. **Authentification JWT** : Implémentation de JSON Web Tokens pour une authentification stateless, avec stockage sécurisé des mots de passe via bcrypt. Les tokens ont une durée de vie limitée (1 heure) et sont rafraîchis via un endpoint dédié.

3. **Base de données relationnelle** : PostgreSQL a été choisi pour sa fiabilité et son support des types avancés (ENUM pour statut/priorité). Les indexes sur `user_id`, `status` et `priority` optimisent les requêtes de filtrage.

4. **CI/CD intégré** : Pipeline GitHub Actions pour automatiser les tests et le déploiement. Le workflow inclut :
   - Tests unitaires (pytest pour backend, Jest pour frontend)
   - Build des images Docker
   - Déploiement sur les environnements cibles

5. **Containerisation** : Utilisation de Docker pour garantir la cohérence entre environnements. Le `docker-compose.yml` définit trois services (frontend, backend, database) avec des volumes persistants pour la base de données.

## Flux de données
1. **Authentification** :
   - L'utilisateur soumet ses identifiants via le formulaire React
   - Le frontend envoie une requête POST `/login` au backend
   - FastAPI valide les credentials et génère un JWT
   - Le token est stocké dans le localStorage du navigateur
   - Les requêtes suivantes incluent le token dans l'en-tête Authorization

2. **Gestion des tâches** :
   - Le frontend envoie une requête GET `/tasks` avec les filtres (status/priority)
   - FastAPI récupère les tâches via SQLAlchemy avec les filtres appliqués
   - Les données sont retournées au frontend sous forme de JSON
   - React affiche les tâches dans le tableau de bord avec les composants TaskList/TaskItem

3. **Création/modification** :
   - L'utilisateur remplit un formulaire (TaskForm)
   - Le frontend envoie une requête POST/PUT `/tasks` avec les données
   - FastAPI valide les données via Pydantic et met à jour la base
   - La réponse contient la tâche mise à jour

## Sécurité
1. **Authentification** :
   - Mots de passe hashés avec bcrypt (coût de 12)
   - JWT signés avec HS256 et durée de vie limitée (1h)
   - Middleware FastAPI pour valider les tokens sur les routes protégées
   - Stockage des tokens dans le localStorage (avec HttpOnly pour les cookies en production)

2. **Protection des données** :
   - Requêtes SQL paramétrées via SQLAlchemy pour éviter les injections
   - Validation des entrées avec Pydantic (schemas)
   - CORS configuré pour n'autoriser que le domaine du frontend
   - Variables d'environnement pour les secrets (DATABASE_URL, SECRET_KEY)

3. **Infrastructure** :
   - Base de données isolée dans un conteneur séparé
   - Réseau Docker dédié pour les communications backend-database
   - Secrets gérés via GitHub Secrets pour le CI/CD

## Scalabilité
1. **Backend** :
   - FastAPI est asynchrone par défaut, permettant une bonne scalabilité horizontale
   - Possibilité d'ajouter Redis pour le caching des tâches fréquemment accédées
   - Load balancing possible avec plusieurs instances du backend

2. **Base de données** :
   - PostgreSQL supporte le sharding et la réplication
   - Les indexes existants optimisent les requêtes de filtrage
   - Possibilité de séparer les tables utilisateurs/tâches sur différents schémas

3. **Frontend** :
   - React permet une bonne performance même avec beaucoup de tâches
   - Virtualisation des listes (via react-window) pour les grands jeux de données
   - Déploiement possible sur CDN pour une diffusion mondiale

4. **CI/CD** :
   - Pipeline modulaire permettant d'ajouter des étapes (tests de charge, scans de sécurité)
   - Déploiement blue-green possible pour les mises à jour sans downtime
   - Rollback automatique en cas d'échec des tests

---