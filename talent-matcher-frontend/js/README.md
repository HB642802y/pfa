# Organisation des modules frontend

Ce dossier contient la logique JavaScript de l'interface. Les fichiers sont separes par responsabilite pour rendre le projet plus facile a lire et modifier.

## Fichiers partages

- `state.js`: etat global de l'application et donnees persistantes.
- `utils.js`: fonctions utilitaires reutilisables.
- `components.js`: fragments HTML et composants simples.
- `domain.js`: fonctions metier communes.
- `api.js`: appels HTTP vers le backend FastAPI.
- `sync.js`: synchronisation des donnees entre frontend, backend et mode demo.

## Fonctionnalites

- `auth.js`: connexion, inscription et deconnexion.
- `jobs.js`: creation, modification, selection et suppression d'offres.
- `applications.js`: depot de candidature et analyse CV.
- `interview.js`: generation de questions et analyse des reponses.
- `admin.js`: gestion des recruteurs et supervision.

## Rendu des pages

- `page-shared.js`: rendu commun a plusieurs vues.
- `page-candidate.js`: espace candidat.
- `page-interview.js`: page entretien IA.
- `page-recruiter.js`: espace recruteur.
- `page-admin.js`: espace administrateur.
- `pages.js`: orchestration du rendu global.

## Point d'entree

Le fichier `../app.js` initialise l'application, recupere les elements du DOM, branche les evenements et appelle les fonctions de rendu.
