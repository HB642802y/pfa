from fastapi import FastAPI, File, UploadFile, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
import uvicorn
import os
from dotenv import load_dotenv

# Configuration
load_dotenv()

app = FastAPI(
    title="AI Matching Backend (Simple Mode)",
    description="Backend simplifié sans base de données",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Stockage en mémoire (pour développement)
memory_storage = {
    "users": [],
    "cvs": [],
    "jobs": [],
    "matches": [],
    "interviews": []
}

# Modèles
class UserCreate(BaseModel):
    firstName: str
    lastName: str
    email: str
    password: str
    role: str = "candidate"

class UserLogin(BaseModel):
    email: str
    password: str

class JobDescription(BaseModel):
    title: str
    description: str
    requirements: str
    skills: List[str]
    experience_level: str
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    location: Optional[str] = None

# Endpoints Auth
@app.post("/auth/register")
async def register(user_data: UserCreate):
    """Inscription utilisateur"""
    try:
        # Vérifier si l'utilisateur existe déjà
        for user in memory_storage["users"]:
            if user["email"] == user_data.email:
                raise HTTPException(status_code=400, detail="Email déjà utilisé")
        
        # Créer nouvel utilisateur
        new_user = {
            "id": f"user_{len(memory_storage['users']) + 1}",
            "firstName": user_data.firstName,
            "lastName": user_data.lastName,
            "email": user_data.email,
            "role": user_data.role,
            "isActive": True,
            "lastLogin": None,
            "createdAt": datetime.now().isoformat()
        }
        
        memory_storage["users"].append(new_user)
        
        return {
            "success": True,
            "data": {
                "user": new_user,
                "token": f"token_{new_user['id']}"
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur inscription: {str(e)}")

@app.post("/auth/login")
async def login(credentials: UserLogin):
    """Connexion utilisateur"""
    try:
        # Rechercher l'utilisateur
        user = None
        for u in memory_storage["users"]:
            if u["email"] == credentials.email:
                user = u
                break
        
        if not user:
            raise HTTPException(status_code=401, detail="Email ou mot de passe incorrect")
        
        # Mettre à jour lastLogin
        user["lastLogin"] = datetime.now().isoformat()
        
        return {
            "success": True,
            "data": {
                "user": user,
                "token": f"token_{user['id']}"
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur connexion: {str(e)}")

@app.get("/auth/verify")
async def verify_token():
    """Vérification du token"""
    try:
        # Simuler une vérification réussie
        return {
            "success": True,
            "data": {
                "user": {
                    "id": "user_1",
                    "firstName": "Test",
                    "lastName": "User",
                    "email": "test@example.com",
                    "role": "candidate",
                    "isActive": True
                }
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur vérification: {str(e)}")

# Endpoints Jobs
@app.get("/jobs")
async def get_jobs():
    """Récupérer toutes les offres d'emploi"""
    try:
        return {
            "success": True,
            "data": memory_storage["jobs"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur récupération jobs: {str(e)}")

@app.post("/jobs")
async def create_job(job_data: JobDescription):
    """Créer une nouvelle offre d'emploi"""
    try:
        new_job = {
            "id": f"job_{len(memory_storage['jobs']) + 1}",
            **job_data.dict(),
            "createdAt": datetime.now().isoformat(),
            "status": "active"
        }
        
        memory_storage["jobs"].append(new_job)
        
        return {
            "success": True,
            "data": new_job
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur création job: {str(e)}")

# Endpoints CV
@app.post("/parse-cv")
async def parse_cv(file: UploadFile = File(...)):
    """Parser un CV"""
    try:
        # Simuler le parsing de CV
        content = await file.read()
        
        cv_data = {
            "id": f"cv_{len(memory_storage['cvs']) + 1}",
            "filename": file.filename,
            "text": f"Contenu simulé du fichier {file.filename}",
            "skills": ["Python", "JavaScript", "React", "Node.js"],
            "experience": [
                {
                    "company": "Entreprise A",
                    "position": "Développeur",
                    "duration": "2 ans"
                }
            ],
            "education": [
                {
                    "degree": "Master en informatique",
                    "school": "Université X",
                    "year": "2020"
                }
            ],
            "parsedAt": datetime.now().isoformat()
        }
        
        memory_storage["cvs"].append(cv_data)
        
        return {
            "success": True,
            "data": cv_data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur parsing CV: {str(e)}")

# Endpoint Matching
@app.post("/match")
async def calculate_match(cv_text: str, job_description: JobDescription):
    """Calculer le matching CV-Job"""
    try:
        # Simuler un calcul de matching
        match_score = 85.5
        
        match_result = {
            "score": match_score,
            "matched_skills": ["Python", "JavaScript", "React"],
            "missing_skills": ["Docker", "AWS"],
            "recommendation": "Excellent candidat",
            "analysis": "Le candidat correspond bien aux exigences du poste"
        }
        
        return {
            "success": True,
            "data": match_result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur matching: {str(e)}")

# Health check
@app.get("/health")
async def health_check():
    """Vérifier l'état du serveur"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "mode": "simple (no database)"
    }

# Racine
@app.get("/")
async def root():
    """Page d'accueil"""
    return {
        "message": "AI Matching Backend - Mode Simple",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }

if __name__ == "__main__":
    print("🚀 Démarrage du AI Backend en mode simple (sans base de données)")
    print("📊 Stockage en mémoire uniquement")
    print("🔗 API Documentation: http://localhost:8000/docs")
    
    uvicorn.run(
        "main_simple:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
