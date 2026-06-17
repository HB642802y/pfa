# Talent Matcher AI

Plateforme de recrutement assistee par IA. Le projet combine un frontend statique, un backend FastAPI pour le matching CV/offres, et des modules dedies a l'entretien IA, aux recommandations et a l'administration.

## Structure du projet

```text
pfam/
├── ai-backend/                 # API FastAPI, matching, parsing CV, entretien IA
├── ats-backend/                # Espace reserve pour une API ATS separee
├── talent-matcher-frontend/    # Interface web statique HTML/CSS/JS
├── README.md                   # Vue d'ensemble du projet
└── .gitignore                  # Fichiers locaux ignores par Git
```

## Frontend

Le frontend se trouve dans `talent-matcher-frontend/`.

Fichiers principaux:

- `index.html`: structure HTML, vues candidat, recruteur, admin et landing page.
- `styles.css`: design global, responsive, composants visuels.
- `app.js`: initialisation, binding DOM, navigation entre les vues.
- `js/`: logique decoupee par domaine.

Pour lancer rapidement:

```bash
cd talent-matcher-frontend
python -m http.server 5173
```

Puis ouvrir:

```text
http://localhost:5173
```

## Backend IA

Le backend principal se trouve dans `ai-backend/`.

Fichiers principaux:

- `main.py`: backend FastAPI avec persistance MongoDB.
- `main_simple.py`: backend FastAPI simplifié en mémoire pour tests locaux.
- `matcher.py`: scoring et matching entre CV et offres.
- `cv_parser.py`: extraction de contenu CV.
- `interview_ai.py`: generation et analyse des entretiens.
- `recommendation_system.py`: recommandations de talents.
- `auth.py`: logique d'authentification.
- `database.py`: connexion et accès base de données MongoDB.

Installation:

```bash
cd ai-backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

Configuration MongoDB:

1. Installez MongoDB localement ou utilisez Docker :

```bash
docker run -d --name mongodb -p 27017:27017 mongo:latest
```

2. Créez un fichier `ai-backend/.env` avec :

```ini
MONGODB_URL=mongodb://localhost:27017
DATABASE_NAME=ai_matching_db
```

Lancement MongoDB + backend :

```bash
cd ai-backend
.venv\Scripts\activate
uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

Le backend crée automatiquement un compte admin par défaut si aucun admin n'existe :

- Email : `admin@pfam.local`
- Mot de passe : `admin123`

## Flux applicatif

1. L'utilisateur ouvre le frontend.
2. Le frontend tente d'appeler le backend sur `http://localhost:8000`.
3. Le candidat consulte une offre, depose un CV ou colle son texte.
4. Le backend parse le CV et calcule un score de matching.
5. Si le score est suffisant, l'entretien IA peut etre lance.
6. Le recruteur consulte les candidatures, scores et recommandations.
7. L'admin gere les recruteurs et surveille l'etat du systeme.

## Notes de developpement

- Les fichiers `.log`, environnements virtuels, caches Python et variables d'environnement sont ignores par Git.
- Le frontend peut continuer en mode demo local si le backend est indisponible.
- Eviter de renommer les `id` HTML sans mettre a jour `app.js` et les modules dans `js/`.
