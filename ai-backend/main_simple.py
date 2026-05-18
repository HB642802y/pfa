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

class CVData(BaseModel):
    text: str = ""
    skills: List[str] = []
    experience: List[Dict[str, Any]] = []
    education: List[Dict[str, Any]] = []

class MatchRequest(BaseModel):
    cv_text: str
    job_description: JobDescription
    cv_data: Optional[CVData] = None

class AnswerAnalysisRequest(BaseModel):
    question: Dict[str, Any]
    answer: str
    response_time: Optional[int] = None

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
async def calculate_match(request: MatchRequest):
    """Calculer le matching CV-Job"""
    try:
        cv_text = request.cv_text.lower()
        job_description = request.job_description
        required_skills = job_description.skills
        matched_skills = [
            skill for skill in required_skills
            if skill.lower() in cv_text
        ]
        missing_skills = [
            skill for skill in required_skills
            if skill.lower() not in cv_text
        ]

        skills_score = (len(matched_skills) / len(required_skills) * 100) if required_skills else 50
        job_words = {
            word.strip(".,;:!?()[]").lower()
            for word in f"{job_description.description} {job_description.requirements}".split()
            if len(word.strip(".,;:!?()[]")) > 3
        }
        cv_words = {
            word.strip(".,;:!?()[]").lower()
            for word in cv_text.split()
            if len(word.strip(".,;:!?()[]")) > 3
        }
        text_overlap = len(job_words & cv_words) / max(len(job_words), 1) * 100
        match_score = min(98, max(20, skills_score * 0.7 + text_overlap * 0.3))
        
        match_result = {
            "overall_score": round(match_score, 2),
            "skills_score": round(skills_score, 2),
            "experience_score": round(min(95, 45 + text_overlap), 2),
            "education_score": 65,
            "tools_score": round(skills_score, 2),
            "matched_skills": matched_skills,
            "missing_skills": missing_skills,
            "recommendations": [
                "Profil recommande pour entretien" if match_score >= 70 else "Profil a verifier manuellement",
                "Competences principales couvertes" if not missing_skills else f"Verifier ou former: {', '.join(missing_skills[:4])}"
            ]
        }
        
        return {
            "success": True,
            "data": match_result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur matching: {str(e)}")

@app.post("/interview/generate-questions")
async def generate_interview_questions(job_description: JobDescription):
    """Generer des questions d'entretien AI simples"""
    try:
        main_skill = job_description.skills[0] if job_description.skills else "vos competences"
        questions = [
            {
                "id": 1,
                "type": "technical",
                "question": f"Expliquez un projet ou vous avez utilise {main_skill}.",
                "keywords": job_description.skills[:4],
                "difficulty": "medium",
                "time_limit": 180,
                "category": "technique"
            },
            {
                "id": 2,
                "type": "problem_solving",
                "question": f"Comment aborderiez-vous une mission similaire a: {job_description.title} ?",
                "keywords": ["analyse", "solution", "priorite"],
                "difficulty": "medium",
                "time_limit": 180,
                "category": "raisonnement"
            },
            {
                "id": 3,
                "type": "behavioral",
                "question": "Donnez un exemple de collaboration avec une equipe pour livrer un resultat.",
                "keywords": ["collaboration", "communication", "resultat"],
                "difficulty": "easy",
                "time_limit": 180,
                "category": "soft skills"
            }
        ]
        return {"success": True, "data": questions}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur questions entretien: {str(e)}")

@app.post("/interview/analyze-answer")
async def analyze_interview_answer(request: AnswerAnalysisRequest):
    """Analyser une reponse d'entretien AI simple"""
    try:
        answer = request.answer.lower()
        keywords = request.question.get("keywords", [])
        matched_keywords = [
            keyword for keyword in keywords
            if keyword.lower() in answer
        ]
        keyword_score = (len(matched_keywords) / len(keywords) * 60) if keywords else 25
        length_score = min(30, len(answer) / 12)
        structure_score = 10 if any(word in answer for word in ["resultat", "impact", "projet", "solution"]) else 4
        score = min(100, round(keyword_score + length_score + structure_score, 2))

        return {
            "success": True,
            "data": {
                "score": score,
                "matched_keywords": matched_keywords,
                "feedback": "Reponse solide et alignee" if score >= 70 else "Ajoutez des exemples concrets, outils et resultats mesurables",
                "recommendation": "continuer" if score >= 70 else "approfondir"
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur analyse reponse: {str(e)}")

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
