# Documentation d'Architecture - TodoApp Test24

## Vue d'ensemble
TodoApp Test24 est une application full-stack de gestion de tâches avec authentification sécurisée. Le système permet aux utilisateurs de créer, modifier et supprimer des tâches tout en les filtrant par statut et priorité. L'architecture suit une approche moderne avec séparation claire des responsabilités entre frontend (React) et backend (FastAPI), le tout déployé via une pipeline CI/CD automatisée.

## Décisions d'architecture
1. **Séparation frontend/backend** : Architecture découplée permettant une évolution indépendante des deux parties. Le frontend communique avec le backend via une API REST bien définie.
2. **Authentification JWT** : Choix de JSON Web Tokens pour leur simplicité et leur compatibilité avec les applications SPA. Les tokens sont signés avec HS256 et ont une durée de vie limitée (30 minutes).
3. **Base de données relationnelle** : PostgreSQL pour sa fiabilité et son support des types avancés (ENUM pour status/priority). Les indexes sont optimisés pour les requêtes fréquentes (filtres par utilisateur/status/priority).
4. **CI/CD intégré** : Pipeline GitHub Actions pour automatiser tests et déploiements, garantissant une qualité constante du code.
5. **Conteneurisation** : Docker pour une portabilité maximale entre environnements de développement et production.

## Flux de données
1. **Authentification** :
   - L'utilisateur soumet ses identifiants via le frontend
   - Le backend valide les informations et génère un JWT
   - Le token est stocké dans le localStorage du navigateur
   - Les requêtes suivantes incluent le token dans l'en-tête Authorization

2. **Gestion des tâches** :
   - Le frontend envoie une requête GET /tasks avec des paramètres de filtre
   - Le backend récupère les données via SQLAlchemy avec les filtres appliqués
   - Les résultats sont paginés (implémentation future) et retournés au frontend
   - Pour les modifications, le frontend envoie des requêtes POST/PUT/DELETE avec le JWT

3. **CI/CD** :
   - Un push sur le dépôt déclenche le workflow GitHub Actions
   - Les tests unitaires et d'intégration sont exécutés
   - Si succès, les images Docker sont construites et poussées vers un registry
   - Le déploiement est déclenché sur l'environnement cible

## Sécurité
1. **Authentification** :
   - Mots de passe hachés avec bcrypt (coût 12)
   - JWT signés avec une clé secrète forte (32 caractères aléatoires)
   - Durée de vie limitée des tokens (30 minutes)
   - Refresh tokens non implémentés dans cette version (à ajouter pour la production)

2. **Protection des données** :
   - Toutes les routes protégées vérifient la présence et la validité du JWT
   - Les requêtes de modification/suppression vérifient que l'utilisateur est propriétaire de la tâche
   - CORS configuré pour n'accepter que les requêtes du domaine frontend

3. **Infrastructure** :
   - Base de données avec mot de passe fort et accès restreint
   - Conteneurs isolés avec des réseaux Docker dédiés
   - Secrets gérés via des variables d'environnement (non commités dans le code)

## Scalabilité
1. **Backend** :
   - FastAPI est conçu pour la haute performance (basé sur Starlette)
   - Possibilité d'ajouter des workers ASGI pour gérer plus de requêtes
   - Cache Redis prêt à être implémenté pour les requêtes fréquentes

2. **Base de données** :
   - Index optimisés pour les requêtes de filtrage
   - Possibilité de réplication en lecture pour les environnements de production
   - Partitionnement possible par utilisateur si la base devient trop grande

3. **Frontend** :
   - Code modulaire avec lazy loading des composants
   - State management optimisé pour éviter les re-renders inutiles
   - Possibilité de servir le frontend via un CDN en production

4. **Déploiement** :
   - Architecture conteneurisée permettant un scaling horizontal
   - Pipeline CI/CD prêt pour des déploiements fréquents et sans downtime
   - Monitoring à ajouter pour identifier les goulots d'étranglement

---