# Plateforme AI Recrutement - Frontend

Frontend statique pour relier les roles candidat, recruteur, moteur IA et administration au backend FastAPI.

## Lancer

Ouvrir `index.html` dans le navigateur, ou lancer un petit serveur local:

```bash
python -m http.server 5173
```

Puis ouvrir:

```text
http://localhost:5173
```

## Backend attendu

Par defaut, le frontend appelle:

```text
http://localhost:8000
```

Endpoints utilises si disponibles:

- `GET /health`
- `GET /jobs`
- `POST /jobs`
- `POST /parse-cv`
- `POST /match`
- `POST /interview/generate-questions`
- `POST /interview/analyze-answer`

Si le backend n'est pas lance ou si un endpoint echoue, l'application continue en mode demo local.
