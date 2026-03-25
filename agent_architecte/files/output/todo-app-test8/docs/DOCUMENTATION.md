# Documentation d'Architecture — TodoApp Test8

## Vue d'ensemble
TodoApp Test8 est une application full-stack de gestion de tâches avec authentification sécurisée. Le système permet aux utilisateurs de créer, modifier et supprimer des tâches, tout en les filtrant par statut (todo/in_progress/done) et priorité (low/medium/high). L'architecture suit une approche moderne avec une séparation claire entre frontend (React) et backend (FastAPI), communiquant via une API REST sécurisée par JWT.

## Décisions d'architecture
1. **Séparation des responsabilités** :
   - Frontend en React pour une expérience utilisateur dynamique (SPA)
   - Backend en FastAPI pour sa performance et son support natif de l'asynchrone
   - Base de données PostgreSQL pour sa fiabilité et son support des types avancés (Enum)

2. **Authentification** :
   - Choix de JWT pour son caractère stateless et sa facilité d'intégration avec les APIs REST
   - Hachage des mots de passe avec bcrypt (via Passlib) pour une sécurité renforcée
   - Tokens avec durée de vie limitée (30 minutes) pour réduire les risques de vol

3. **Modèle de données** :
   - Relation Many-to-One entre tâches et utilisateurs pour permettre une gestion multi-utilisateurs
   - Indexes sur les champs fréquemment filtrés (user_id, status, priority) pour optimiser les performances
   - Utilisation d'Enums pour les champs status et priority afin d'éviter les valeurs incohérentes

4. **CI/CD** :
   - Pipeline GitHub Actions pour automatiser les tests et le déploiement
   - Déploiement séparé du frontend (GitHub Pages) et du backend (VPS) pour une scalabilité future

## Flux de données
1. **Authentification** :
   - L'utilisateur soumet ses identifiants via le formulaire de login (frontend)
   - Le backend valide les credentials et génère un JWT
   - Le frontend stocke le token dans le localStorage et l'inclut dans les headers des requêtes suivantes

2. **Gestion des tâches** :
   - Le frontend envoie une requête GET `/tasks` avec les filtres (status/priority) et le JWT
   - Le backend vérifie le JWT, récupère les tâches de l'utilisateur depuis la base de données
   - Les données sont retournées au frontend qui les affiche dans le tableau de bord

3. **Création de tâche** :
   - L'utilisateur remplit le formulaire et soumet les données
   - Le frontend envoie une requête POST `/tasks` avec le JWT et les données
   - Le backend crée la tâche en base de données et retourne l'objet créé

## Sécurité
1. **Authentification** :
   - JWT avec signature HS256 et secret stocké en variable d'environnement
   - Hachage des mots de passe avec bcrypt (coût de 12)
   - Vérification systématique du JWT pour les endpoints protégés

2. **Protection des données** :
   - HTTPS obligatoire en production (via reverse proxy comme Nginx)
   - CORS configuré pour n'autoriser que les requêtes depuis le domaine du frontend
   - Validation des entrées utilisateur (backend et frontend) pour prévenir les injections

3. **Infrastructure** :
   - Variables d'environnement pour les secrets (JWT_SECRET, DB_PASSWORD)
   - Réseau Docker isolé pour les conteneurs
   - Base de données accessible uniquement depuis le backend

## Scalabilité
1. **Backend** :
   - FastAPI supporte nativement l'asynchrone, permettant de gérer de nombreuses connexions simultanées
   - Possibilité d'ajouter un load balancer devant plusieurs instances du backend
   - Cache Redis peut être ajouté ultérieurement pour les tâches fréquemment accédées

2. **Base de données** :
   - PostgreSQL supporte le sharding et la réplication pour une scalabilité horizontale
   - Les indexes sur user_id, status et priority optimisent les requêtes de filtrage

3. **Frontend** :
   - Architecture modulaire avec React permettant d'ajouter facilement de nouvelles fonctionnalités
   - Possibilité de déployer le frontend sur un CDN pour une meilleure performance mondiale

4. **CI/CD** :
   - Pipeline GitHub Actions scalable pour gérer plusieurs environnements (dev, staging, prod)
   - Déploiement blue-green possible pour minimiser les downtimes

---