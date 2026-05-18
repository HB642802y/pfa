from fastapi import FastAPI, File, UploadFile, HTTPException, status, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
import uvicorn
import os
from dotenv import load_dotenv
from contextlib import asynccontextmanager

# Importer nos modules personnalisés
from cv_parser import CVParser
from matcher import AI_Matcher
from interview_ai import InterviewAI
from recommendation_system import RecommendationSystem
from analytics import AnalyticsSystem
from database import db_manager
from auth import auth_service, get_current_user, require_admin, require_recruiter, require_candidate
from models import (
    UserCreate, UserLogin, UserResponse, UserUpdate,
    CVCreate, CVResponse,
    JobCreate, JobResponse,
    ApplicationCreate, ApplicationResponse,
    InterviewCreate, InterviewResponse,
    MatchRequest, MatchResponse,
    APIResponse
)

# Charger les variables d'environnement
load_dotenv()

# Context manager pour le cycle de vie de l'application
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gérer le cycle de vie de l'application"""
    # Démarrage
    await db_manager.connect()
    print("🚀 AI Matching Backend démarré avec succès")
    
    yield
    
    # Arrêt
    await db_manager.disconnect()
    print("🔌 AI Matching Backend arrêté")

# Initialiser l'application FastAPI
app = FastAPI(
    title="AI Matching Backend",
    description="Backend IA pour le matching CV et offres d'emploi",
    version="1.0.0",
    lifespan=lifespan
)

# Configuration CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],  # Frontend URLs
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Modèles Pydantic pour les requêtes/réponses
class JobDescription(BaseModel):
    title: str
    description: str
    requirements: str
    skills: List[str]
    experience_level: str
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    location: Optional[str] = None

class CVData(BaseModel):
    text: str
    skills: List[str] = []
    experience: List[Dict[str, Any]] = []
    education: List[Dict[str, Any]] = []

class MatchRequest(BaseModel):
    cv_text: str
    job_description: JobDescription
    cv_data: Optional[CVData] = None

class MatchResponse(BaseModel):
    overall_score: float
    skills_score: float
    experience_score: float
    education_score: float
    tools_score: float
    matched_skills: List[str]
    missing_skills: List[str]
    recommendations: List[str]

class ParsedCV(BaseModel):
    text: str
    skills: List[str]
    experience: List[Dict[str, Any]]
    education: List[Dict[str, Any]]
    contact_info: Dict[str, str]
    completeness_score: float

# Variables globales pour les instances
cv_parser = CVParser()
ai_matcher = AI_Matcher()
interview_ai = InterviewAI()
recommendation_system = RecommendationSystem()
analytics_system = AnalyticsSystem()

# Context manager pour le cycle de vie de l'application
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gérer le cycle de vie de l'application"""
    # Démarrage
    await db_manager.connect()
    print("🚀 AI Matching Backend démarré avec succès")
    
    yield
    
    # Arrêt
    await db_manager.disconnect()
    print("🔌 AI Matching Backend arrêté")

# Routes principales
@app.get("/")
async def root():
    return {
        "message": "AI Matching Backend - FastAPI",
        "version": "1.0.0",
        "status": "running",
        "api_docs": "/docs",
        "redoc": "/redoc",
        "endpoints": {
            "core": {
                "parse_cv": "/parse-cv",
                "match": "/match",
                "batch_match": "/batch-match",
                "health": "/health",
                "skills": "/skills"
            },
            "interview": {
                "generate_questions": "/interview/generate-questions",
                "analyze_answer": "/interview/analyze-answer",
                "summary": "/interview/summary"
            },
            "recommendations": {
                "candidates": "/recommendations/candidates",
                "jobs": "/recommendations/jobs",
                "similar_candidates": "/recommendations/similar-candidates"
            },
            "analytics": {
                "track_cv": "/analytics/track-cv",
                "track_match": "/analytics/track-match",
                "dashboard": "/analytics/dashboard",
                "funnel": "/analytics/funnel",
                "skills": "/analytics/skills",
                "export": "/analytics/export"
            }
        },
        "features": [
            "CV Processing with PyPDF2 & pdfplumber",
            "TF-IDF Matching with scikit-learn",
            "AI Interview System",
            "Smart Recommendations",
            "Real-time Analytics",
            "RESTful API"
        ]
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "AI Matching Backend",
        "version": "1.0.0"
    }

@app.post("/parse-cv", response_model=ParsedCV)
async def parse_cv(file: UploadFile = File(...)):
    """
    Parser un fichier CV (PDF, DOCX) et extraire les informations
    """
    try:
        # Vérifier le type de fichier
        if not file.filename.lower().endswith(('.pdf', '.docx')):
            raise HTTPException(status_code=400, detail="Format de fichier non supporté. Utilisez PDF ou DOCX.")
        
        # Lire le contenu du fichier
        contents = await file.read()
        
        # Parser le CV
        parsed_data = cv_parser.parse_cv(contents, file.filename)
        
        return parsed_data
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors du parsing du CV: {str(e)}")

@app.post("/match", response_model=MatchResponse)
async def match_cv_job(request: MatchRequest):
    """
    Calculer le score de matching entre un CV et une offre d'emploi
    """
    try:
        # Utiliser le moteur IA pour calculer le matching
        match_result = ai_matcher.calculate_match(
            cv_text=request.cv_text,
            job_description=request.job_description.dict(),
            cv_data=request.cv_data.dict() if request.cv_data else None
        )
        
        return match_result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors du calcul du matching: {str(e)}")

@app.post("/batch-match")
async def batch_match(request: Dict[str, Any]):
    """
    Matching multiple CVs contre une offre d'emploi
    """
    try:
        cvs = request.get('cvs', [])
        job_description = request.get('job_description')
        
        if not cvs or not job_description:
            raise HTTPException(status_code=400, detail="CVs et description d'emploi requis")
        
        results = []
        for cv in cvs:
            match_result = ai_matcher.calculate_match(
                cv_text=cv.get('text', ''),
                job_description=job_description,
                cv_data=cv.get('data')
            )
            results.append({
                'cv_id': cv.get('id'),
                'result': match_result
            })
        
        # Trier par score décroissant
        results.sort(key=lambda x: x['result']['overall_score'], reverse=True)
        
        return {
            'job_description': job_description,
            'results': results,
            'total_cvs': len(cvs)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors du batch matching: {str(e)}")

@app.get("/skills")
async def get_common_skills():
    """
    Retourner la liste des compétences communes reconnues par le système
    """
    try:
        return {
            "skills": ai_matcher.get_common_skills(),
            "categories": ai_matcher.get_skill_categories()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur: {str(e)}")

# Interview AI endpoints
@app.post("/interview/generate-questions")
async def generate_interview_questions(job_description: JobDescription, cv_data: Optional[CVData] = None):
    """
    Générer des questions d'entretien personnalisées
    """
    try:
        questions = interview_ai.generate_interview_questions(
            job_description.dict(),
            cv_data.dict() if cv_data else None
        )
        return questions
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur génération questions: {str(e)}")

@app.post("/interview/analyze-answer")
async def analyze_interview_answer(question: Dict[str, Any], answer: str, response_time: Optional[int] = None):
    """
    Analyser la réponse d'un candidat à une question d'entretien
    """
    try:
        analysis = interview_ai.analyze_answer(question, answer, response_time)
        return analysis
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur analyse réponse: {str(e)}")

@app.post("/interview/summary")
async def generate_interview_summary(answers_analyses: List[Dict[str, Any]]):
    """
    Générer un résumé complet de l'entretien
    """
    try:
        summary = interview_ai.generate_interview_summary(answers_analyses)
        return summary
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur génération résumé: {str(e)}")

# Recommendation System endpoints
@app.post("/recommendations/candidates")
async def recommend_candidates_for_job(job_description: JobDescription, candidates: List[Dict[str, Any]], limit: int = 10):
    """
    Recommander des candidats pour une offre d'emploi
    """
    try:
        recommendations = recommendation_system.recommend_candidates_for_job(
            candidates, job_description.dict(), limit
        )
        return recommendations
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur recommandation candidats: {str(e)}")

@app.post("/recommendations/jobs")
async def recommend_jobs_for_candidate(candidate: Dict[str, Any], jobs: List[Dict[str, Any]], limit: int = 10):
    """
    Recommander des offres d'emploi pour un candidat
    """
    try:
        recommendations = recommendation_system.recommend_jobs_for_candidate(
            candidate, jobs, limit
        )
        return recommendations
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur recommandation emplois: {str(e)}")

@app.post("/recommendations/similar-candidates")
async def get_similar_candidates(target_candidate: Dict[str, Any], candidates: List[Dict[str, Any]], limit: int = 5):
    """
    Trouver des candidats similaires
    """
    try:
        similar = recommendation_system.get_similar_candidates(
            target_candidate, candidates, limit
        )
        return similar
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur recherche similaires: {str(e)}")

# --- User Management Endpoints ---
@app.post("/auth/register", response_model=APIResponse)
async def register_user(user_data: UserCreate):
    """Inscrire un nouvel utilisateur"""
    try:
        # Vérifier si l'utilisateur existe déjà
        existing_user = await db_manager.get_user_by_email(user_data.email)
        if existing_user:
            raise HTTPException(status_code=400, detail="Email déjà utilisé")
        
        # Hasher le mot de passe
        hashed_password = auth_service.get_password_hash(user_data.password)
        
        # Créer l'utilisateur
        user_dict = user_data.dict()
        user_dict["password"] = hashed_password
        
        user_id = await db_manager.create_user(user_dict)
        
        # Créer le token
        token_data = {
            "sub": user_id,
            "email": user_data.email,
            "role": user_data.role.value,
            "is_active": True
        }
        
        access_token = auth_service.create_access_token(token_data)
        
        return APIResponse(
            success=True,
            message="Utilisateur créé avec succès",
            data={
                "user_id": user_id,
                "access_token": access_token,
                "token_type": "bearer"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur inscription: {str(e)}")

@app.post("/auth/login", response_model=APIResponse)
async def login_user(user_credentials: UserLogin):
    """Connecter un utilisateur"""
    try:
        # Récupérer l'utilisateur
        user = await db_manager.get_user_by_email(user_credentials.email)
        if not user:
            raise HTTPException(status_code=401, detail="Email ou mot de passe incorrect")
        
        # Vérifier le mot de passe
        if not auth_service.verify_password(user_credentials.password, user["password"]):
            raise HTTPException(status_code=401, detail="Email ou mot de passe incorrect")
        
        # Créer le token
        token_data = {
            "sub": str(user["_id"]),
            "email": user["email"],
            "role": user["role"],
            "is_active": user.get("is_active", True)
        }
        
        access_token = auth_service.create_access_token(token_data)
        
        # Mettre à jour last_login
        await db_manager.update_user(str(user["_id"]), {"last_login": datetime.utcnow()})
        
        return APIResponse(
            success=True,
            message="Connexion réussie",
            data={
                "access_token": access_token,
                "token_type": "bearer",
                "user": {
                    "id": str(user["_id"]),
                    "email": user["email"],
                    "first_name": user["first_name"],
                    "last_name": user["last_name"],
                    "role": user["role"],
                    "is_active": user.get("is_active", True)
                }
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur connexion: {str(e)}")

@app.get("/auth/me", response_model=APIResponse)
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """Obtenir les informations de l'utilisateur courant"""
    return APIResponse(
        success=True,
        message="Informations utilisateur récupérées",
        data=current_user
    )

@app.put("/users/profile", response_model=APIResponse)
async def update_user_profile(
    user_update: UserUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Mettre à jour le profil utilisateur"""
    try:
        user_id = current_user["user_id"]
        
        # Filtrer les champs non vides
        update_data = {k: v for k, v in user_update.dict().items() if v is not None}
        
        if not update_data:
            raise HTTPException(status_code=400, detail="Aucune donnée à mettre à jour")
        
        success = await db_manager.update_user(user_id, update_data)
        
        if not success:
            raise HTTPException(status_code=404, detail="Utilisateur non trouvé")
        
        return APIResponse(
            success=True,
            message="Profil mis à jour avec succès"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur mise à jour profil: {str(e)}")

# --- CV Management Endpoints ---
@app.post("/cvs", response_model=APIResponse)
async def create_cv(
    cv_data: CVCreate,
    current_user: dict = Depends(require_candidate)
):
    """Créer un nouveau CV"""
    try:
        user_id = current_user["user_id"]
        cv_dict = cv_data.dict()
        cv_dict["user_id"] = user_id
        
        cv_id = await db_manager.save_cv(cv_dict)
        
        return APIResponse(
            success=True,
            message="CV créé avec succès",
            data={"cv_id": cv_id}
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur création CV: {str(e)}")

@app.get("/cvs", response_model=APIResponse)
async def get_user_cvs(current_user: dict = Depends(get_current_user)):
    """Récupérer les CVs de l'utilisateur"""
    try:
        user_id = current_user["user_id"]
        cvs = await db_manager.get_cvs_by_user(user_id)
        
        return APIResponse(
            success=True,
            message="CVs récupérés avec succès",
            data=cvs
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur récupération CVs: {str(e)}")

# --- Job Management Endpoints ---
@app.post("/jobs", response_model=APIResponse)
async def create_job(
    job_data: JobCreate,
    current_user: dict = Depends(require_recruiter)
):
    """Créer une nouvelle offre d'emploi"""
    try:
        user_id = current_user["user_id"]
        job_dict = job_data.dict()
        job_dict["created_by"] = user_id
        
        job_id = await db_manager.create_job(job_dict)
        
        return APIResponse(
            success=True,
            message="Offre créée avec succès",
            data={"job_id": job_id}
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur création offre: {str(e)}")

@app.get("/jobs", response_model=APIResponse)
async def get_jobs(limit: int = 20):
    """Récupérer les offres d'emploi actives"""
    try:
        jobs = await db_manager.get_active_jobs(limit)
        
        return APIResponse(
            success=True,
            message="Offres récupérées avec succès",
            data=jobs
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur récupération offres: {str(e)}")

@app.get("/jobs/search", response_model=APIResponse)
async def search_jobs(query: str, limit: int = 20):
    """Rechercher des offres d'emploi"""
    try:
        jobs = await db_manager.search_jobs(query, limit)
        
        return APIResponse(
            success=True,
            message="Recherche effectuée avec succès",
            data=jobs
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur recherche offres: {str(e)}")

# Analytics endpoints
@app.post("/analytics/track-cv")
async def track_cv_processing(cv_data: ParsedCV, processing_time: float):
    """
    Suivre le traitement de CV
    """
    try:
        tracking = analytics_system.track_cv_processing(cv_data.dict(), processing_time)
        return tracking
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur tracking CV: {str(e)}")

@app.post("/analytics/track-match")
async def track_matching_calculation(cv_id: str, job_id: str, match_result: MatchResponse, processing_time: float):
    """
    Suivre le calcul de matching
    """
    try:
        tracking = analytics_system.track_matching_calculation(
            cv_id, job_id, match_result.dict(), processing_time
        )
        return tracking
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur tracking matching: {str(e)}")

@app.get("/analytics/dashboard")
async def get_performance_dashboard(time_range: str = "30d"):
    """
    Obtenir le tableau de bord de performance
    """
    try:
        dashboard = analytics_system.generate_performance_dashboard(time_range)
        return dashboard
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur dashboard: {str(e)}")

@app.get("/analytics/funnel")
async def get_recruitment_funnel(time_range: str = "30d"):
    """
    Obtenir l'analyse du funnel de recrutement
    """
    try:
        funnel = analytics_system.generate_recruitment_funnel(time_range)
        return funnel
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur funnel: {str(e)}")

@app.get("/analytics/skills")
async def get_skill_demand_analysis(time_range: str = "30d"):
    """
    Obtenir l'analyse de la demande de compétences
    """
    try:
        skills_analysis = analytics_system.generate_skill_demand_analysis(time_range)
        return skills_analysis
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur analyse compétences: {str(e)}")

@app.get("/analytics/export")
async def export_analytics_data(format_type: str = "json", time_range: str = "30d"):
    """
    Exporter les données analytics
    """
    try:
        export_data = analytics_system.export_analytics_data(format_type, time_range)
        return export_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur export: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(
        "main_fixed:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
