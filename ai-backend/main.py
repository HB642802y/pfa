from fastapi import FastAPI, File, UploadFile, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import uvicorn
import os
from dotenv import load_dotenv

# Importer nos modules personnalisés
from cv_parser import CVParser
from matcher import AI_Matcher
from database import DatabaseManager
from interview_ai import InterviewAI
from auth import auth_service, get_current_user, require_recruiter, require_candidate
from models import (
    UserCreate, UserLogin, UserResponse, UserUpdate,
    CVCreate, CVResponse,
    JobCreate, JobResponse,
    ApplicationCreate, ApplicationResponse,
    InterviewCreate, InterviewResponse,
    MatchRequest as MatchRequestModel, MatchResponse as MatchResponseModel,
    UserRole, JobStatus, ApplicationStatus, InterviewStatus
)

# Charger les variables d'environnement
load_dotenv()

# Initialiser le gestionnaire de base de données MongoDB
db_manager = DatabaseManager()

# Initialiser l'application FastAPI
app = FastAPI(
    title="AI Matching Backend",
    description="Backend IA pour le matching CV et offres d'emploi",
    version="1.0.0"
)

# Configuration CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174", "http://localhost:3000"],  # Frontend URLs
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Événements de démarrage et arrêt ---
async def ensure_default_admin():
    """Créer un compte admin par défaut si aucun admin n'existe."""
    try:
        existing_admin = await db_manager.get_user_by_email("admin@pfam.local")
        if existing_admin:
            return

        admin_password = auth_service.get_password_hash("admin123")
        admin_data = {
            "first_name": "Admin",
            "last_name": "PFA",
            "email": "admin@pfam.local",
            "password": admin_password,
            "role": UserRole.ADMIN.value,
            "is_active": True,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        await db_manager.create_user(admin_data)
        print("✅ Compte admin par défaut créé: admin@pfam.local / admin123")
    except Exception as e:
        print(f"⚠️ Impossible de créer l'admin par défaut: {e}")

@app.on_event("startup")
async def startup_event():
    """Initialiser la connexion à MongoDB au démarrage du serveur"""
    print("🚀 Démarrage du serveur...")
    try:
        await db_manager.connect()
        await ensure_default_admin()
        print("✅ MongoDB initialisé avec succès")
    except Exception as e:
        print(f"⚠️ Attention: MongoDB non accessible: {e}")
        print("📝 Le serveur fonctionne en mode lecture seule sans persistance")
        print("\n💡 Pour activer MongoDB:")
        print("   1. Installez MongoDB Community Edition: https://www.mongodb.com/try/download/community")
        print("   2. OU utilisez Docker: docker run -d --name mongodb -p 27017:27017 mongo:latest")
        print("   3. OU utilisez MongoDB Atlas: https://www.mongodb.com/cloud/atlas\n")

@app.on_event("shutdown")
async def shutdown_event():
    """Fermer la connexion à MongoDB à l'arrêt du serveur"""
    print("🛑 Arrêt du serveur...")
    try:
        await db_manager.disconnect()
        print("✅ MongoDB déconnecté avec succès")
    except Exception as e:
        print(f"❌ Erreur déconnexion MongoDB: {e}")

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

# Routes principales
@app.get("/")
async def root():
    return {
        "message": "AI Matching Backend - FastAPI",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "parse_cv": "/parse-cv",
            "match": "/match",
            "health": "/health"
        }
    }

@app.get("/health")
async def health_check():
    """Vérifier l'état du serveur et de MongoDB"""
    try:
        # Vérifier la connexion à MongoDB
        await db_manager.database.client.admin.command('ping')
        db_status = "connected"
    except Exception as e:
        db_status = f"disconnected: {str(e)}"
    
    return {
        "status": "healthy",
        "service": "AI Matching Backend",
        "version": "1.0.0",
        "database": {
            "type": "MongoDB",
            "status": db_status,
            "url": os.getenv("MONGODB_URL", "mongodb://localhost:27017")
        }
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

# --- Authentication Endpoints ---

@app.post("/auth/register")
async def register_candidate(user: UserCreate):
    """
    Enregistrer un nouveau candidat
    """
    try:
        # Vérifier si l'utilisateur existe déjà
        existing_user = await db_manager.get_user_by_email(user.email)
        if existing_user:
            raise HTTPException(status_code=400, detail="Email déjà utilisé")
        
        # Hasher le mot de passe
        hashed_password = auth_service.get_password_hash(user.password)
        
        # Créer l'utilisateur
        user_data = user.dict()
        user_data["password"] = hashed_password
        user_data["role"] = UserRole.CANDIDATE.value
        
        user_id = await db_manager.create_user(user_data)
        
        # Créer le token
        token_data = {
            "sub": user_id,
            "email": user.email,
            "role": UserRole.CANDIDATE.value,
            "is_active": True
        }
        access_token = auth_service.create_access_token(token_data)
        
        return {
            "success": True,
            "message": "Compte créé avec succès",
            "user_id": user_id,
            "access_token": access_token,
            "token_type": "bearer"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de l'inscription: {str(e)}")

@app.post("/auth/login")
async def login_candidate(credentials: UserLogin):
    """
    Connecter un candidat
    """
    try:
        # Récupérer l'utilisateur
        user = await db_manager.get_user_by_email(credentials.email)
        if not user:
            raise HTTPException(status_code=401, detail="Email ou mot de passe incorrect")
        
        # Vérifier le mot de passe
        if not auth_service.verify_password(credentials.password, user.get("password")):
            raise HTTPException(status_code=401, detail="Email ou mot de passe incorrect")
        
        # Vérifier si le compte est actif
        if not user.get("is_active", True):
            raise HTTPException(status_code=403, detail="Compte désactivé")
        
        # Créer le token
        token_data = {
            "sub": str(user.get("_id")),
            "email": user.get("email"),
            "role": user.get("role"),
            "is_active": user.get("is_active", True)
        }
        access_token = auth_service.create_access_token(token_data)
        
        # Mettre à jour last_login
        await db_manager.update_user(str(user.get("_id")), {"last_login": datetime.utcnow()})
        
        return {
            "success": True,
            "message": "Connexion réussie",
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": str(user.get("_id")),
                "email": user.get("email"),
                "first_name": user.get("first_name"),
                "last_name": user.get("last_name"),
                "role": user.get("role")
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la connexion: {str(e)}")

@app.post("/auth/logout")
async def logout_candidate(current_user: Dict[str, Any] = Depends(get_current_user)):
    """
    Déconnecter un candidat
    """
    try:
        # Dans une implémentation avec JWT stateless, le logout est côté client
        # Mais nous pouvons ajouter le token à une blacklist si nécessaire
        return {
            "success": True,
            "message": "Déconnexion réussie"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la déconnexion: {str(e)}")

@app.post("/auth/refresh")
async def refresh_token(current_user: Dict[str, Any] = Depends(get_current_user)):
    """
    Rafraîchir le token d'accès
    """
    try:
        token_data = {
            "sub": current_user.get("user_id"),
            "email": current_user.get("email"),
            "role": current_user.get("role"),
            "is_active": current_user.get("is_active", True)
        }
        new_token = auth_service.create_access_token(token_data)
        
        return {
            "success": True,
            "access_token": new_token,
            "token_type": "bearer"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors du rafraîchissement du token: {str(e)}")

@app.post("/auth/forgot-password")
async def forgot_password(email: str):
    """
    Demander la réinitialisation du mot de passe
    """
    try:
        user = await db_manager.get_user_by_email(email)
        if not user:
            # Pour des raisons de sécurité, ne pas révéler si l'email existe
            return {
                "success": True,
                "message": "Si l'email existe, un lien de réinitialisation sera envoyé"
            }
        
        # Générer un token de réinitialisation
        reset_token = auth_service.create_access_token(
            {"sub": str(user.get("_id")), "type": "password_reset"},
            expires_delta=timedelta(hours=1)
        )
        
        # Sauvegarder le token dans la base de données
        await db_manager.database["password_resets"].insert_one({
            "user_id": str(user.get("_id")),
            "token": reset_token,
            "created_at": datetime.utcnow(),
            "expires_at": datetime.utcnow() + timedelta(hours=1),
            "used": False
        })
        
        # Ici, vous enverriez un email avec le lien de réinitialisation
        # Pour l'instant, nous retournons le token pour le développement
        
        return {
            "success": True,
            "message": "Lien de réinitialisation envoyé",
            "reset_token": reset_token  # En production, ne pas retourner le token
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la demande de réinitialisation: {str(e)}")

@app.post("/auth/reset-password")
async def reset_password(token: str, new_password: str):
    """
    Réinitialiser le mot de passe avec un token
    """
    try:
        # Vérifier le token
        payload = auth_service.verify_token(token)
        if not payload or payload.get("type") != "password_reset":
            raise HTTPException(status_code=400, detail="Token invalide ou expiré")
        
        # Vérifier si le token existe et n'a pas été utilisé
        reset_record = await db_manager.database["password_resets"].find_one({
            "token": token,
            "used": False
        })
        
        if not reset_record:
            raise HTTPException(status_code=400, detail="Token invalide ou déjà utilisé")
        
        # Hasher le nouveau mot de passe
        hashed_password = auth_service.get_password_hash(new_password)
        
        # Mettre à jour le mot de passe de l'utilisateur
        await db_manager.update_user(reset_record["user_id"], {"password": hashed_password})
        
        # Marquer le token comme utilisé
        await db_manager.database["password_resets"].update_one(
            {"_id": reset_record["_id"]},
            {"$set": {"used": True}}
        )
        
        return {
            "success": True,
            "message": "Mot de passe réinitialisé avec succès"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la réinitialisation du mot de passe: {str(e)}")

# --- Candidat Endpoints ---

@app.post("/candidate/cv/upload")
async def upload_cv(
    file: UploadFile = File(...),
    user_id: str = None,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Uploader un CV et le sauvegarder dans MongoDB
    """
    try:
        # Vérifier que l'utilisateur est un candidat
        if current_user.get("role") != "candidate":
            raise HTTPException(status_code=403, detail="Accès réservé aux candidats")
        
        # Vérifier le type de fichier
        if not file.filename.lower().endswith(('.pdf', '.docx')):
            raise HTTPException(status_code=400, detail="Format de fichier non supporté. Utilisez PDF ou DOCX.")
        
        # Lire le contenu du fichier
        contents = await file.read()
        
        # Parser le CV
        parsed_data = cv_parser.parse_cv(contents, file.filename)
        
        # Sauvegarder dans MongoDB
        cv_data = {
            "user_id": user_id or current_user.get("user_id"),
            "title": file.filename,
            "text": parsed_data.text,
            "skills": parsed_data.skills,
            "experience": parsed_data.experience,
            "education": parsed_data.education,
            "contact_info": parsed_data.contact_info,
            "completeness_score": parsed_data.completeness_score,
            "filename": file.filename
        }
        
        cv_id = await db_manager.save_cv(cv_data)
        
        return {
            "success": True,
            "message": "CV uploadé avec succès",
            "cv_id": cv_id,
            "parsed_data": parsed_data.dict()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de l'upload du CV: {str(e)}")

@app.put("/candidate/cv/{cv_id}")
async def update_cv(
    cv_id: str,
    cv_update: CVCreate,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Mettre à jour un CV
    """
    try:
        # Vérifier que l'utilisateur est un candidat
        if current_user.get("role") != "candidate":
            raise HTTPException(status_code=403, detail="Accès réservé aux candidats")
        
        # Récupérer le CV existant
        existing_cv = await db_manager.get_cv_by_id(cv_id)
        if not existing_cv:
            raise HTTPException(status_code=404, detail="CV non trouvé")
        
        # Vérifier que le CV appartient à l'utilisateur
        if existing_cv.get("user_id") != current_user.get("user_id"):
            raise HTTPException(status_code=403, detail="CV non autorisé")
        
        # Mettre à jour le CV
        update_data = cv_update.dict()
        update_data["updated_at"] = datetime.utcnow()
        
        result = await db_manager.update_cv(cv_id, update_data)
        
        if result:
            return {
                "success": True,
                "message": "CV mis à jour avec succès"
            }
        else:
            raise HTTPException(status_code=400, detail="Erreur lors de la mise à jour")
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la mise à jour du CV: {str(e)}")

@app.delete("/candidate/cv/{cv_id}")
async def delete_cv(
    cv_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Supprimer un CV
    """
    try:
        # Vérifier que l'utilisateur est un candidat
        if current_user.get("role") != "candidate":
            raise HTTPException(status_code=403, detail="Accès réservé aux candidats")
        
        # Récupérer le CV existant
        existing_cv = await db_manager.get_cv_by_id(cv_id)
        if not existing_cv:
            raise HTTPException(status_code=404, detail="CV non trouvé")
        
        # Vérifier que le CV appartient à l'utilisateur
        if existing_cv.get("user_id") != current_user.get("user_id"):
            raise HTTPException(status_code=403, detail="CV non autorisé")
        
        # Supprimer le CV
        result = await db_manager.database["cvs"].delete_one({"_id": cv_id})
        
        if result.deleted_count > 0:
            return {
                "success": True,
                "message": "CV supprimé avec succès"
            }
        else:
            raise HTTPException(status_code=400, detail="Erreur lors de la suppression")
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la suppression du CV: {str(e)}")

@app.get("/candidate/cv/{cv_id}/download")
async def download_cv(
    cv_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Télécharger un CV
    """
    try:
        # Récupérer le CV
        cv = await db_manager.get_cv_by_id(cv_id)
        if not cv:
            raise HTTPException(status_code=404, detail="CV non trouvé")
        
        # Vérifier les autorisations
        if current_user.get("role") == "candidate":
            if cv.get("user_id") != current_user.get("user_id"):
                raise HTTPException(status_code=403, detail="CV non autorisé")
        elif current_user.get("role") == "recruiter":
            # Les recruteurs peuvent voir les CVs des candidats qui ont postulé
            pass
        else:
            raise HTTPException(status_code=403, detail="Accès non autorisé")
        
        return {
            "success": True,
            "cv": cv
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors du téléchargement du CV: {str(e)}")

# --- AI CV Analysis Endpoints ---

@app.post("/cv/analyze")
async def analyze_cv_endpoint(
    cv_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Analyser un CV avec l'IA
    """
    try:
        # Récupérer le CV
        cv = await db_manager.get_cv_by_id(cv_id)
        if not cv:
            raise HTTPException(status_code=404, detail="CV non trouvé")
        
        # Vérifier les autorisations
        if current_user.get("role") == "candidate":
            if cv.get("user_id") != current_user.get("user_id"):
                raise HTTPException(status_code=403, detail="CV non autorisé")
        
        # Analyser le CV
        analysis_result = {
            "cv_id": cv_id,
            "text": cv.get("text", ""),
            "skills": cv.get("skills", []),
            "experience": cv.get("experience", []),
            "education": cv.get("education", []),
            "completeness_score": cv.get("completeness_score", 0),
            "contact_info": cv.get("contact_info", {}),
            "analysis_summary": {
                "total_skills": len(cv.get("skills", [])),
                "total_experience": len(cv.get("experience", [])),
                "total_education": len(cv.get("education", [])),
                "has_contact_info": bool(cv.get("contact_info")),
                "is_complete": cv.get("completeness_score", 0) >= 0.8
            }
        }
        
        return {
            "success": True,
            "analysis": analysis_result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de l'analyse du CV: {str(e)}")

@app.post("/cv/extract-text")
async def extract_text_from_pdf(
    file: UploadFile = File(...),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Extraire le texte d'un fichier PDF
    """
    try:
        # Vérifier le type de fichier
        if not file.filename.lower().endswith(('.pdf', '.docx')):
            raise HTTPException(status_code=400, detail="Format de fichier non supporté")
        
        # Lire le contenu
        contents = await file.read()
        
        # Parser le CV
        parsed_data = cv_parser.parse_cv(contents, file.filename)
        
        return {
            "success": True,
            "text": parsed_data.text,
            "filename": file.filename
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de l'extraction du texte: {str(e)}")

@app.post("/cv/extract-skills")
async def extract_skills(
    text: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Extraire les compétences d'un texte
    """
    try:
        # Utiliser le parser pour extraire les compétences
        skills = cv_parser._extract_skills(text)
        
        return {
            "success": True,
            "skills": skills,
            "total": len(skills)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de l'extraction des compétences: {str(e)}")

@app.post("/cv/extract-experience")
async def extract_experience(
    text: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Extraire l'expérience d'un texte
    """
    try:
        # Utiliser le parser pour extraire l'expérience
        experience = cv_parser._extract_experience(text)
        
        return {
            "success": True,
            "experience": experience,
            "total": len(experience)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de l'extraction de l'expérience: {str(e)}")

@app.post("/cv/extract-education")
async def extract_education(
    text: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Extraire la formation d'un texte
    """
    try:
        # Utiliser le parser pour extraire la formation
        education = cv_parser._extract_education(text)
        
        return {
            "success": True,
            "education": education,
            "total": len(education)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de l'extraction de la formation: {str(e)}")

@app.post("/cv/clean")
async def clean_cv_text(
    text: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Nettoyer le texte d'un CV
    """
    try:
        # Nettoyer le texte
        cleaned_text = cv_parser._clean_text(text)
        
        return {
            "success": True,
            "original_text": text,
            "cleaned_text": cleaned_text,
            "original_length": len(text),
            "cleaned_length": len(cleaned_text)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors du nettoyage du texte: {str(e)}")

# --- Matching Score Endpoints ---

@app.post("/matching/calculate")
async def calculate_matching_score(
    cv_id: str,
    job_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Calculer le score de matching entre un CV et une offre
    """
    try:
        # Récupérer le CV
        cv = await db_manager.get_cv_by_id(cv_id)
        if not cv:
            raise HTTPException(status_code=404, detail="CV non trouvé")
        
        # Récupérer l'offre
        job = await db_manager.get_job_by_id(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Offre non trouvée")
        
        # Calculer le score de matching
        match_result = ai_matcher.calculate_match(
            cv_text=cv.get("text", ""),
            job_description=job,
            cv_data={
                "skills": cv.get("skills", []),
                "experience": cv.get("experience", []),
                "education": cv.get("education", [])
            }
        )
        
        # Sauvegarder le résultat
        match_data = {
            "cv_id": cv_id,
            "job_id": job_id,
            "overall_score": match_result["overall_score"],
            "skills_score": match_result["skills_score"],
            "experience_score": match_result["experience_score"],
            "education_score": match_result["education_score"],
            "tools_score": match_result["tools_score"],
            "matched_skills": match_result["matched_skills"],
            "missing_skills": match_result["missing_skills"],
            "recommendations": match_result["recommendations"]
        }
        
        await db_manager.save_match(match_data)
        
        return {
            "success": True,
            "match_result": match_result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors du calcul du matching: {str(e)}")

@app.post("/matching/compare-skills")
async def compare_skills(
    cv_skills: List[str],
    job_skills: List[str],
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Comparer les compétences d'un CV avec celles d'une offre
    """
    try:
        # Convertir en minuscules pour la comparaison
        cv_skills_lower = [skill.lower() for skill in cv_skills]
        job_skills_lower = [skill.lower() for skill in job_skills]
        
        # Trouver les compétences correspondantes
        matched_skills = []
        missing_skills = []
        
        for job_skill in job_skills_lower:
            if any(job_skill in cv_skill for cv_skill in cv_skills_lower):
                matched_skills.append(job_skill)
            else:
                missing_skills.append(job_skill)
        
        # Calculer le ratio
        match_ratio = len(matched_skills) / len(job_skills) if job_skills else 0
        
        return {
            "success": True,
            "matched_skills": matched_skills,
            "missing_skills": missing_skills,
            "match_ratio": match_ratio,
            "match_percentage": round(match_ratio * 100, 2)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la comparaison des compétences: {str(e)}")

@app.post("/matching/compare-experience")
async def compare_experience(
    cv_experience: List[Dict[str, Any]],
    job_requirements: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Comparer l'expérience d'un CV avec les exigences du poste
    """
    try:
        # Analyser l'expérience
        total_years = 0
        relevant_experience = []
        
        for exp in cv_experience:
            # Calculer les années d'expérience (simplifié)
            if "start_date" in exp and "end_date" in exp:
                start = exp["start_date"]
                end = exp["end_date"] if exp["end_date"] else datetime.utcnow()
                years = (end - start).days / 365.25
                total_years += years
                relevant_experience.append({
                    "title": exp.get("title", ""),
                    "company": exp.get("company", ""),
                    "years": round(years, 1)
                })
        
        # Analyser les exigences (simplifié)
        required_years = 0
        if "année" in job_requirements.lower():
            # Extraire le nombre d'années requis (simplifié)
            import re
            years_match = re.search(r'(\d+)\s*année', job_requirements.lower())
            if years_match:
                required_years = int(years_match.group(1))
        
        # Comparer
        experience_match = total_years >= required_years if required_years > 0 else True
        
        return {
            "success": True,
            "total_years_experience": round(total_years, 1),
            "required_years": required_years,
            "experience_match": experience_match,
            "relevant_experience": relevant_experience
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la comparaison de l'expérience: {str(e)}")

@app.get("/matching/rank-candidates/{job_id}")
async def rank_candidates(
    job_id: str,
    limit: int = 20,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Classer les candidats pour une offre selon leur score de matching
    """
    try:
        # Récupérer l'offre
        job = await db_manager.get_job_by_id(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Offre non trouvée")
        
        # Récupérer tous les matches pour cette offre
        matches = await db_manager.get_matches_for_job(job_id, limit)
        
        # Trier par score décroissant
        matches.sort(key=lambda x: x.get("overall_score", 0), reverse=True)
        
        # Enrichir avec les détails des candidats
        ranked_candidates = []
        for i, match in enumerate(matches, 1):
            cv = await db_manager.get_cv_by_id(match.get("cv_id"))
            if cv:
                user = await db_manager.get_user_by_id(cv.get("user_id"))
                ranked_candidates.append({
                    "rank": i,
                    "match_score": match.get("overall_score"),
                    "candidate": {
                        "user_id": cv.get("user_id"),
                        "email": user.get("email") if user else "",
                        "first_name": user.get("first_name") if user else "",
                        "last_name": user.get("last_name") if user else ""
                    },
                    "cv_id": match.get("cv_id"),
                    "matched_skills": match.get("matched_skills"),
                    "missing_skills": match.get("missing_skills")
                })
        
        return {
            "success": True,
            "job_title": job.get("title"),
            "ranked_candidates": ranked_candidates,
            "total": len(ranked_candidates)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors du classement des candidats: {str(e)}")

@app.get("/matching/report/{job_id}")
async def generate_matching_report(
    job_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Générer un rapport de matching pour une offre
    """
    try:
        # Récupérer l'offre
        job = await db_manager.get_job_by_id(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Offre non trouvée")
        
        # Récupérer tous les matches
        matches = await db_manager.get_matches_for_job(job_id, 100)
        
        # Calculer les statistiques
        if matches:
            scores = [m.get("overall_score", 0) for m in matches]
            avg_score = sum(scores) / len(scores)
            max_score = max(scores)
            min_score = min(scores)
            
            # Analyser les compétences
            all_matched_skills = []
            all_missing_skills = []
            for match in matches:
                all_matched_skills.extend(match.get("matched_skills", []))
                all_missing_skills.extend(match.get("missing_skills", []))
            
            # Compter les compétences
            from collections import Counter
            matched_skills_count = Counter(all_matched_skills)
            missing_skills_count = Counter(all_missing_skills)
        else:
            avg_score = max_score = min_score = 0
            matched_skills_count = {}
            missing_skills_count = {}
        
        report = {
            "job_title": job.get("title"),
            "total_candidates": len(matches),
            "average_score": round(avg_score, 2),
            "max_score": round(max_score, 2),
            "min_score": round(min_score, 2),
            "top_matched_skills": dict(matched_skills_count.most_common(10)),
            "top_missing_skills": dict(missing_skills_count.most_common(10)),
            "job_requirements": job.get("skills", []),
            "generated_at": datetime.utcnow().isoformat()
        }
        
        return {
            "success": True,
            "report": report
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la génération du rapport: {str(e)}")

@app.post("/candidate/apply")
async def apply_to_job(
    application: ApplicationCreate,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Postuler à une offre d'emploi
    """
    try:
        # Vérifier que l'utilisateur est un candidat
        if current_user.get("role") != "candidate":
            raise HTTPException(status_code=403, detail="Accès réservé aux candidats")
        
        # Récupérer le CV
        cv = await db_manager.get_cv_by_id(application.cv_id)
        if not cv:
            raise HTTPException(status_code=404, detail="CV non trouvé")
        
        # Vérifier que le CV appartient à l'utilisateur
        if cv.get("user_id") != current_user.get("user_id"):
            raise HTTPException(status_code=403, detail="CV non autorisé")
        
        # Récupérer l'offre
        job = await db_manager.get_job_by_id(application.job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Offre non trouvée")
        
        # Créer la candidature
        application_data = application.dict()
        application_data["candidate_id"] = current_user.get("user_id")
        application_data["status"] = ApplicationStatus.PENDING.value
        
        # Calculer le score de matching
        match_result = ai_matcher.calculate_match(
            cv_text=cv.get("text", ""),
            job_description=job,
            cv_data={
                "skills": cv.get("skills", []),
                "experience": cv.get("experience", []),
                "education": cv.get("education", [])
            }
        )
        
        application_data["match_score"] = match_result["overall_score"]
        
        # Sauvegarder la candidature
        application_id = await db_manager.database["applications"].insert_one(application_data)
        
        # Sauvegarder le résultat du matching
        match_data = {
            "cv_id": application.cv_id,
            "job_id": application.job_id,
            "candidate_id": current_user.get("user_id"),
            "overall_score": match_result["overall_score"],
            "skills_score": match_result["skills_score"],
            "experience_score": match_result["experience_score"],
            "education_score": match_result["education_score"],
            "tools_score": match_result["tools_score"],
            "matched_skills": match_result["matched_skills"],
            "missing_skills": match_result["missing_skills"],
            "recommendations": match_result["recommendations"]
        }
        await db_manager.save_match(match_data)
        
        return {
            "success": True,
            "message": "Candidature envoyée avec succès",
            "application_id": str(application_id.inserted_id),
            "match_score": match_result["overall_score"],
            "match_details": match_result
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la candidature: {str(e)}")

@app.post("/candidate/interview/start")
async def start_interview(
    job_id: str,
    cv_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Démarrer un entretien AI pour un candidat
    """
    try:
        # Vérifier que l'utilisateur est un candidat
        if current_user.get("role") != "candidate":
            raise HTTPException(status_code=403, detail="Accès réservé aux candidats")
        
        # Récupérer l'offre
        job = await db_manager.get_job_by_id(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Offre non trouvée")
        
        # Récupérer le CV
        cv = await db_manager.get_cv_by_id(cv_id)
        if not cv:
            raise HTTPException(status_code=404, detail="CV non trouvé")
        
        # Générer les questions d'entretien
        interview_questions = interview_ai.generate_interview_questions(
            job_description=job,
            cv_data=cv
        )
        
        # Créer l'entretien
        interview_data = {
            "job_id": job_id,
            "candidate_id": current_user.get("user_id"),
            "cv_id": cv_id,
            "status": InterviewStatus.IN_PROGRESS.value,
            "questions": interview_questions["questions"],
            "total_questions": interview_questions["total_questions"],
            "estimated_duration_minutes": interview_questions["estimated_duration_minutes"],
            "instructions": interview_questions["instructions"]
        }
        
        interview_id = await db_manager.save_interview(interview_data)
        
        return {
            "success": True,
            "message": "Entretien démarré avec succès",
            "interview_id": interview_id,
            "questions": interview_questions["questions"],
            "total_questions": interview_questions["total_questions"],
            "estimated_duration_minutes": interview_questions["estimated_duration_minutes"],
            "instructions": interview_questions["instructions"]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors du démarrage de l'entretien: {str(e)}")

@app.post("/candidate/interview/answer")
async def submit_answer(
    interview_id: str,
    question_id: int,
    answer: str,
    response_time: Optional[int] = None,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Soumettre une réponse à une question d'entretien
    """
    try:
        # Récupérer l'entretien
        interview = await db_manager.get_interview_by_id(interview_id)
        if not interview:
            raise HTTPException(status_code=404, detail="Entretien non trouvé")
        
        # Vérifier que l'utilisateur est le candidat
        if interview.get("candidate_id") != current_user.get("user_id"):
            raise HTTPException(status_code=403, detail="Accès non autorisé")
        
        # Trouver la question
        question = None
        for q in interview.get("questions", []):
            if q["id"] == question_id:
                question = q
                break
        
        if not question:
            raise HTTPException(status_code=404, detail="Question non trouvée")
        
        # Analyser la réponse
        answer_analysis = interview_ai.analyze_answer(question, answer, response_time)
        
        # Sauvegarder la réponse
        if "answers" not in interview:
            interview["answers"] = []
        
        interview["answers"].append({
            "question_id": question_id,
            "answer": answer,
            "analysis": answer_analysis,
            "submitted_at": datetime.utcnow().isoformat()
        })
        
        # Mettre à jour l'entretien
        await db_manager.database["interviews"].update_one(
            {"_id": interview_id},
            {"$set": {"answers": interview["answers"]}}
        )
        
        return {
            "success": True,
            "message": "Réponse soumise avec succès",
            "analysis": answer_analysis
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la soumission de la réponse: {str(e)}")

@app.post("/candidate/interview/complete")
async def complete_interview(
    interview_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Compléter l'entretien et obtenir le score final
    """
    try:
        # Récupérer l'entretien
        interview = await db_manager.get_interview_by_id(interview_id)
        if not interview:
            raise HTTPException(status_code=404, detail="Entretien non trouvé")
        
        # Vérifier que l'utilisateur est le candidat
        if interview.get("candidate_id") != current_user.get("user_id"):
            raise HTTPException(status_code=403, detail="Accès non autorisé")
        
        # Analyser toutes les réponses
        answers_analyses = [a["analysis"] for a in interview.get("answers", [])]
        
        if not answers_analyses:
            raise HTTPException(status_code=400, detail="Aucune réponse à analyser")
        
        # Générer le résumé de l'entretien
        interview_summary = interview_ai.generate_interview_summary(answers_analyses)
        
        # Mettre à jour l'entretien avec le score final
        await db_manager.database["interviews"].update_one(
            {"_id": interview_id},
            {
                "$set": {
                    "status": InterviewStatus.COMPLETED.value,
                    "overall_score": interview_summary["overall_score"],
                    "detailed_scores": interview_summary["detailed_scores"],
                    "strengths": interview_summary["strengths"],
                    "weaknesses": interview_summary["weaknesses"],
                    "recommendation": interview_summary["recommendation"],
                    "completed_at": datetime.utcnow().isoformat()
                }
            }
        )
        
        return {
            "success": True,
            "message": "Entretien complété avec succès",
            "interview_summary": interview_summary
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la complétion de l'entretien: {str(e)}")

@app.post("/interview/validate-invitation")
async def validate_interview_invitation(
    interview_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Valider une invitation d'entretien"""
    try:
        interview = await db_manager.get_interview_by_id(interview_id)
        if not interview:
            raise HTTPException(status_code=404, detail="Entretien non trouvé")
        
        if interview.get("candidate_id") != current_user.get("user_id"):
            raise HTTPException(status_code=403, detail="Entretien non autorisé")
        
        if interview.get("status") != InterviewStatus.SCHEDULED.value:
            raise HTTPException(status_code=400, detail="Entretien pas en attente")
        
        await db_manager.database["interviews"].update_one(
            {"_id": interview_id},
            {"$set": {"status": InterviewStatus.IN_PROGRESS.value}}
        )
        
        return {"success": True, "message": "Invitation validée avec succès"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur: {str(e)}")

@app.post("/interview/end")
async def end_interview(
    interview_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Terminer un entretien"""
    try:
        interview = await db_manager.get_interview_by_id(interview_id)
        if not interview:
            raise HTTPException(status_code=404, detail="Entretien non trouvé")
        
        if current_user.get("role") == "candidate":
            if interview.get("candidate_id") != current_user.get("user_id"):
                raise HTTPException(status_code=403, detail="Entretien non autorisé")
        elif current_user.get("role") == "recruiter":
            job = await db_manager.get_job_by_id(interview.get("job_id"))
            if not job or job.get("created_by") != current_user.get("user_id"):
                raise HTTPException(status_code=403, detail="Entretien non autorisé")
        
        await db_manager.database["interviews"].update_one(
            {"_id": interview_id},
            {"$set": {"status": InterviewStatus.CANCELLED.value}}
        )
        
        return {"success": True, "message": "Entretien terminé"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur: {str(e)}")

@app.post("/interview/generate-questions")
async def generate_questions_endpoint(
    job_id: str,
    cv_id: Optional[str] = None,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Générer des questions d'entretien"""
    try:
        job = await db_manager.get_job_by_id(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Offre non trouvée")
        
        cv = None
        if cv_id:
            cv = await db_manager.get_cv_by_id(cv_id)
        
        interview_questions = interview_ai.generate_interview_questions(
            job_description=job,
            cv_data=cv
        )
        
        return {
            "success": True,
            "questions": interview_questions["questions"],
            "total_questions": interview_questions["total_questions"],
            "estimated_duration_minutes": interview_questions["estimated_duration_minutes"]
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur: {str(e)}")

@app.post("/interview/detect-confidence")
async def detect_confidence(
    answer: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Détecter le niveau de confiance dans une réponse"""
    try:
        confidence_indicators = ["je suis sûr", "certainement", "absolument", "je confirme", "sans aucun doute"]
        uncertainty_indicators = ["je pense", "peut-être", "probablement", "je ne suis pas sûr", "il me semble"]
        
        answer_lower = answer.lower()
        confidence_score = 5.0
        
        for indicator in confidence_indicators:
            if indicator in answer_lower:
                confidence_score += 1
        
        for indicator in uncertainty_indicators:
            if indicator in answer_lower:
                confidence_score -= 1
        
        confidence_score = max(0, min(10, confidence_score))
        confidence_level = "high" if confidence_score >= 7 else "medium" if confidence_score >= 4 else "low"
        
        return {"success": True, "confidence_score": confidence_score, "confidence_level": confidence_level}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur: {str(e)}")

@app.get("/interview/feedback/{interview_id}")
async def get_interview_feedback(
    interview_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Obtenir le feedback complet d'un entretien"""
    try:
        interview = await db_manager.get_interview_by_id(interview_id)
        if not interview:
            raise HTTPException(status_code=404, detail="Entretien non trouvé")
        
        if current_user.get("role") == "candidate":
            if interview.get("candidate_id") != current_user.get("user_id"):
                raise HTTPException(status_code=403, detail="Entretien non autorisé")
        elif current_user.get("role") == "recruiter":
            job = await db_manager.get_job_by_id(interview.get("job_id"))
            if not job or job.get("created_by") != current_user.get("user_id"):
                raise HTTPException(status_code=403, detail="Entretien non autorisé")
        
        answers_analyses = [a["analysis"] for a in interview.get("answers", [])]
        
        if not answers_analyses:
            raise HTTPException(status_code=400, detail="Aucune réponse à analyser")
        
        interview_summary = interview_ai.generate_interview_summary(answers_analyses)
        
        return {"success": True, "interview_summary": interview_summary, "interview": interview}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur: {str(e)}")

# --- Recruteur Endpoints ---

@app.post("/recruiter/job/create")
async def create_job(
    job: JobCreate,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Créer une nouvelle offre d'emploi
    """
    try:
        # Vérifier que l'utilisateur est un recruteur
        if current_user.get("role") != "recruiter":
            raise HTTPException(status_code=403, detail="Accès réservé aux recruteurs")
        
        # Créer les données de l'offre
        job_data = job.dict()
        job_data["created_by"] = current_user.get("user_id")
        job_data["status"] = JobStatus.DRAFT.value
        
        # Sauvegarder l'offre
        job_id = await db_manager.create_job(job_data)
        
        return {
            "success": True,
            "message": "Offre créée avec succès",
            "job_id": job_id
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la création de l'offre: {str(e)}")

@app.get("/recruiter/job/{job_id}/applications")
async def get_job_applications(
    job_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Récupérer toutes les candidatures pour une offre
    """
    try:
        # Vérifier que l'utilisateur est un recruteur
        if current_user.get("role") != "recruiter":
            raise HTTPException(status_code=403, detail="Accès réservé aux recruteurs")
        
        # Récupérer l'offre
        job = await db_manager.get_job_by_id(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Offre non trouvée")
        
        # Vérifier que l'offre appartient au recruteur
        if job.get("created_by") != current_user.get("user_id"):
            raise HTTPException(status_code=403, detail="Offre non autorisée")
        
        # Récupérer les candidatures
        cursor = db_manager.database["applications"].find(
            {"job_id": job_id}
        ).sort("created_at", -1)
        
        applications = await cursor.to_list(length=None)
        
        # Récupérer les scores de matching
        for app in applications:
            match = await db_manager.database["matches"].find_one({
                "cv_id": app.get("cv_id"),
                "job_id": job_id
            })
            if match:
                app["match_score"] = match.get("overall_score")
                app["match_details"] = match
        
        return {
            "success": True,
            "applications": applications,
            "total": len(applications)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la récupération des candidatures: {str(e)}")

@app.put("/recruiter/job/{job_id}")
async def update_job(
    job_id: str,
    job_update: JobCreate,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Modifier une offre d'emploi
    """
    try:
        # Vérifier que l'utilisateur est un recruteur
        if current_user.get("role") != "recruiter":
            raise HTTPException(status_code=403, detail="Accès réservé aux recruteurs")
        
        # Récupérer l'offre existante
        existing_job = await db_manager.get_job_by_id(job_id)
        if not existing_job:
            raise HTTPException(status_code=404, detail="Offre non trouvée")
        
        # Vérifier que l'offre appartient au recruteur
        if existing_job.get("created_by") != current_user.get("user_id"):
            raise HTTPException(status_code=403, detail="Offre non autorisée")
        
        # Mettre à jour l'offre
        update_data = job_update.dict()
        update_data["updated_at"] = datetime.utcnow()
        
        result = await db_manager.database["jobs"].update_one(
            {"_id": job_id},
            {"$set": update_data}
        )
        
        if result.modified_count == 0:
            raise HTTPException(status_code=400, detail="Aucune modification effectuée")
        
        return {
            "success": True,
            "message": "Offre modifiée avec succès"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la modification de l'offre: {str(e)}")

@app.delete("/recruiter/job/{job_id}")
async def delete_job(
    job_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Supprimer une offre d'emploi
    """
    try:
        # Vérifier que l'utilisateur est un recruteur
        if current_user.get("role") != "recruiter":
            raise HTTPException(status_code=403, detail="Accès réservé aux recruteurs")
        
        # Récupérer l'offre existante
        existing_job = await db_manager.get_job_by_id(job_id)
        if not existing_job:
            raise HTTPException(status_code=404, detail="Offre non trouvée")
        
        # Vérifier que l'offre appartient au recruteur
        if existing_job.get("created_by") != current_user.get("user_id"):
            raise HTTPException(status_code=403, detail="Offre non autorisée")
        
        # Supprimer l'offre
        result = await db_manager.database["jobs"].delete_one({"_id": job_id})
        
        if result.deleted_count == 0:
            raise HTTPException(status_code=400, detail="Erreur lors de la suppression")
        
        return {
            "success": True,
            "message": "Offre supprimée avec succès"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la suppression de l'offre: {str(e)}")

@app.put("/recruiter/job/{job_id}/publish")
async def publish_job(
    job_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Publier une offre d'emploi
    """
    try:
        # Vérifier que l'utilisateur est un recruteur
        if current_user.get("role") != "recruiter":
            raise HTTPException(status_code=403, detail="Accès réservé aux recruteurs")
        
        # Récupérer l'offre existante
        existing_job = await db_manager.get_job_by_id(job_id)
        if not existing_job:
            raise HTTPException(status_code=404, detail="Offre non trouvée")
        
        # Vérifier que l'offre appartient au recruteur
        if existing_job.get("created_by") != current_user.get("user_id"):
            raise HTTPException(status_code=403, detail="Offre non autorisée")
        
        # Publier l'offre
        result = await db_manager.database["jobs"].update_one(
            {"_id": job_id},
            {
                "$set": {
                    "status": JobStatus.ACTIVE.value,
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        if result.modified_count == 0:
            raise HTTPException(status_code=400, detail="Erreur lors de la publication")
        
        return {
            "success": True,
            "message": "Offre publiée avec succès"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la publication de l'offre: {str(e)}")

@app.get("/recruiter/jobs")
async def get_recruiter_jobs(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Récupérer toutes les offres d'un recruteur
    """
    try:
        # Vérifier que l'utilisateur est un recruteur
        if current_user.get("role") != "recruiter":
            raise HTTPException(status_code=403, detail="Accès réservé aux recruteurs")
        
        # Récupérer les offres du recruteur
        cursor = db_manager.database["jobs"].find(
            {"created_by": current_user.get("user_id")}
        ).sort("created_at", -1)
        
        jobs = await cursor.to_list(length=None)
        
        return {
            "success": True,
            "jobs": jobs,
            "total": len(jobs)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la récupération des offres: {str(e)}")

@app.put("/recruiter/job/{job_id}/archive")
async def archive_offer(
    job_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Archiver une offre"""
    try:
        if current_user.get("role") != "recruiter":
            raise HTTPException(status_code=403, detail="Accès réservé aux recruteurs")
        
        existing_job = await db_manager.get_job_by_id(job_id)
        if not existing_job:
            raise HTTPException(status_code=404, detail="Offre non trouvée")
        
        if existing_job.get("created_by") != current_user.get("user_id"):
            raise HTTPException(status_code=403, detail="Offre non autorisée")
        
        result = await db_manager.database["jobs"].update_one(
            {"_id": job_id},
            {"$set": {"status": JobStatus.INACTIVE.value, "updated_at": datetime.utcnow()}}
        )
        
        if result.modified_count == 0:
            raise HTTPException(status_code=400, detail="Erreur lors de l'archivage")
        
        return {"success": True, "message": "Offre archivée avec succès"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur: {str(e)}")

@app.put("/recruiter/job/{job_id}/unpublish")
async def unpublish_offer(
    job_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Dépublier une offre"""
    try:
        if current_user.get("role") != "recruiter":
            raise HTTPException(status_code=403, detail="Accès réservé aux recruteurs")
        
        existing_job = await db_manager.get_job_by_id(job_id)
        if not existing_job:
            raise HTTPException(status_code=404, detail="Offre non trouvée")
        
        if existing_job.get("created_by") != current_user.get("user_id"):
            raise HTTPException(status_code=403, detail="Offre non autorisée")
        
        result = await db_manager.database["jobs"].update_one(
            {"_id": job_id},
            {"$set": {"status": JobStatus.DRAFT.value, "updated_at": datetime.utcnow()}}
        )
        
        if result.modified_count == 0:
            raise HTTPException(status_code=400, detail="Erreur lors de la dépublication")
        
        return {"success": True, "message": "Offre dépubliée avec succès"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur: {str(e)}")

@app.get("/jobs/all")
async def get_all_offers(
    limit: int = 50,
    skip: int = 0,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Récupérer toutes les offres actives"""
    try:
        cursor = db_manager.database["jobs"].find(
            {"status": JobStatus.ACTIVE.value}
        ).sort("created_at", -1).skip(skip).limit(limit)
        
        jobs = await cursor.to_list(length=None)
        
        return {"success": True, "jobs": jobs, "total": len(jobs)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur: {str(e)}")

@app.get("/jobs/{job_id}")
async def get_offer_by_id(
    job_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Récupérer une offre par ID"""
    try:
        job = await db_manager.get_job_by_id(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Offre non trouvée")
        
        return {"success": True, "job": job}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur: {str(e)}")

@app.get("/jobs/search")
async def search_offers(
    query: str,
    limit: int = 20,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Rechercher des offres"""
    try:
        jobs = await db_manager.search_jobs(query, limit)
        
        return {"success": True, "jobs": jobs, "total": len(jobs), "query": query}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur: {str(e)}")

# --- Talent Recommendation Endpoints ---

@app.get("/recommendation/candidates/{job_id}")
async def recommend_candidates(
    job_id: str,
    limit: int = 20,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Recommander des candidats pour une offre"""
    try:
        if current_user.get("role") != "recruiter":
            raise HTTPException(status_code=403, detail="Accès réservé aux recruteurs")
        
        job = await db_manager.get_job_by_id(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Offre non trouvée")
        
        if job.get("created_by") != current_user.get("user_id"):
            raise HTTPException(status_code=403, detail="Offre non autorisée")
        
        matches = await db_manager.get_matches_for_job(job_id, limit)
        matches.sort(key=lambda x: x.get("overall_score", 0), reverse=True)
        
        recommendations = []
        for match in matches:
            cv = await db_manager.get_cv_by_id(match.get("cv_id"))
            if cv:
                user = await db_manager.get_user_by_id(cv.get("user_id"))
                recommendations.append({
                    "match_score": match.get("overall_score"),
                    "candidate": {
                        "user_id": cv.get("user_id"),
                        "email": user.get("email") if user else "",
                        "first_name": user.get("first_name") if user else "",
                        "last_name": user.get("last_name") if user else ""
                    },
                    "cv_id": match.get("cv_id"),
                    "matched_skills": match.get("matched_skills")
                })
        
        return {"success": True, "recommendations": recommendations, "total": len(recommendations)}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur: {str(e)}")

@app.get("/recommendation/jobs/{candidate_id}")
async def recommend_jobs(
    candidate_id: str,
    limit: int = 20,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Recommander des offres pour un candidat"""
    try:
        if current_user.get("role") == "candidate":
            if candidate_id != current_user.get("user_id"):
                raise HTTPException(status_code=403, detail="Accès non autorisé")
        
        cvs = await db_manager.get_cvs_by_user(candidate_id)
        if not cvs:
            raise HTTPException(status_code=404, detail="Aucun CV trouvé")
        
        cv = cvs[0]
        jobs = await db_manager.get_active_jobs(limit * 2)
        
        recommendations = []
        for job in jobs:
            match_result = ai_matcher.calculate_match(
                cv_text=cv.get("text", ""),
                job_description=job,
                cv_data={
                    "skills": cv.get("skills", []),
                    "experience": cv.get("experience", []),
                    "education": cv.get("education", [])
                }
            )
            
            if match_result["overall_score"] >= 5.0:
                recommendations.append({
                    "job_id": job.get("_id"),
                    "job_title": job.get("title"),
                    "match_score": match_result["overall_score"],
                    "matched_skills": match_result["matched_skills"]
                })
        
        recommendations.sort(key=lambda x: x["match_score"], reverse=True)
        recommendations = recommendations[:limit]
        
        return {"success": True, "recommendations": recommendations, "total": len(recommendations)}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur: {str(e)}")

@app.get("/recommendation/best-match/{cv_id}")
async def find_best_match(
    cv_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Trouver la meilleure offre pour un CV"""
    try:
        cv = await db_manager.get_cv_by_id(cv_id)
        if not cv:
            raise HTTPException(status_code=404, detail="CV non trouvé")
        
        if current_user.get("role") == "candidate":
            if cv.get("user_id") != current_user.get("user_id"):
                raise HTTPException(status_code=403, detail="CV non autorisé")
        
        jobs = await db_manager.get_active_jobs(100)
        
        best_match = None
        best_score = 0
        
        for job in jobs:
            match_result = ai_matcher.calculate_match(
                cv_text=cv.get("text", ""),
                job_description=job,
                cv_data={
                    "skills": cv.get("skills", []),
                    "experience": cv.get("experience", []),
                    "education": cv.get("education", [])
                }
            )
            
            if match_result["overall_score"] > best_score:
                best_score = match_result["overall_score"]
                best_match = {
                    "job": job,
                    "match_score": match_result["overall_score"],
                    "matched_skills": match_result["matched_skills"],
                    "missing_skills": match_result["missing_skills"]
                }
        
        return {"success": True, "best_match": best_match}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur: {str(e)}")

@app.get("/recommendation/filter-candidates")
async def filter_candidates(
    job_id: str,
    min_score: float = 5.0,
    skills: Optional[List[str]] = None,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Filtrer les candidats par score et compétences"""
    try:
        if current_user.get("role") != "recruiter":
            raise HTTPException(status_code=403, detail="Accès réservé aux recruteurs")
        
        job = await db_manager.get_job_by_id(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Offre non trouvée")
        
        matches = await db_manager.get_matches_for_job(job_id, 100)
        
        filtered_candidates = []
        for match in matches:
            if match.get("overall_score", 0) >= min_score:
                if not skills or all(skill in match.get("matched_skills", []) for skill in skills):
                    cv = await db_manager.get_cv_by_id(match.get("cv_id"))
                    if cv:
                        user = await db_manager.get_user_by_id(cv.get("user_id"))
                        filtered_candidates.append({
                            "match_score": match.get("overall_score"),
                            "candidate": {
                                "user_id": cv.get("user_id"),
                                "email": user.get("email") if user else "",
                                "first_name": user.get("first_name") if user else "",
                                "last_name": user.get("last_name") if user else ""
                            },
                            "cv_id": match.get("cv_id")
                        })
        
        return {"success": True, "filtered_candidates": filtered_candidates, "total": len(filtered_candidates)}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur: {str(e)}")

@app.get("/recommendation/sort-candidates/{job_id}")
async def sort_candidates_by_score(
    job_id: str,
    order: str = "desc",
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Trier les candidats par score"""
    try:
        if current_user.get("role") != "recruiter":
            raise HTTPException(status_code=403, detail="Accès réservé aux recruteurs")
        
        matches = await db_manager.get_matches_for_job(job_id, 100)
        
        reverse = order.lower() == "desc"
        matches.sort(key=lambda x: x.get("overall_score", 0), reverse=reverse)
        
        sorted_candidates = []
        for match in matches:
            cv = await db_manager.get_cv_by_id(match.get("cv_id"))
            if cv:
                user = await db_manager.get_user_by_id(cv.get("user_id"))
                sorted_candidates.append({
                    "match_score": match.get("overall_score"),
                    "candidate": {
                        "user_id": cv.get("user_id"),
                        "email": user.get("email") if user else "",
                        "first_name": user.get("first_name") if user else "",
                        "last_name": user.get("last_name") if user else ""
                    },
                    "cv_id": match.get("cv_id")
                })
        
        return {"success": True, "sorted_candidates": sorted_candidates, "total": len(sorted_candidates)}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur: {str(e)}")

# --- Score Consultation Endpoints ---

@app.get("/scores/candidate/{candidate_id}")
async def get_candidate_score(
    candidate_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Obtenir les scores d'un candidat"""
    try:
        if current_user.get("role") == "candidate":
            if candidate_id != current_user.get("user_id"):
                raise HTTPException(status_code=403, detail="Accès non autorisé")
        
        cvs = await db_manager.get_cvs_by_user(candidate_id)
        if not cvs:
            raise HTTPException(status_code=404, detail="Aucun CV trouvé")
        
        cv = cvs[0]
        matches = await db_manager.get_matches_for_cv(cv.get("_id"), 50)
        
        return {"success": True, "candidate_id": candidate_id, "matches": matches, "total": len(matches)}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur: {str(e)}")

@app.get("/scores/all")
async def get_all_scores(
    limit: int = 100,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Obtenir tous les scores de matching"""
    try:
        if current_user.get("role") not in ["recruiter", "admin"]:
            raise HTTPException(status_code=403, detail="Accès réservé aux recruteurs et admins")
        
        cursor = db_manager.database["matches"].find().sort("overall_score", -1).limit(limit)
        scores = await cursor.to_list(length=None)
        
        return {"success": True, "scores": scores, "total": len(scores)}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur: {str(e)}")

@app.get("/scores/top-candidates/{job_id}")
async def get_top_candidates(
    job_id: str,
    limit: int = 10,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Obtenir les meilleurs candidats pour une offre"""
    try:
        if current_user.get("role") != "recruiter":
            raise HTTPException(status_code=403, detail="Accès réservé aux recruteurs")
        
        job = await db_manager.get_job_by_id(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Offre non trouvée")
        
        if job.get("created_by") != current_user.get("user_id"):
            raise HTTPException(status_code=403, detail="Offre non autorisée")
        
        matches = await db_manager.get_matches_for_job(job_id, limit)
        matches.sort(key=lambda x: x.get("overall_score", 0), reverse=True)
        
        top_candidates = []
        for match in matches:
            cv = await db_manager.get_cv_by_id(match.get("cv_id"))
            if cv:
                user = await db_manager.get_user_by_id(cv.get("user_id"))
                top_candidates.append({
                    "rank": len(top_candidates) + 1,
                    "match_score": match.get("overall_score"),
                    "candidate": {
                        "user_id": cv.get("user_id"),
                        "email": user.get("email") if user else "",
                        "first_name": user.get("first_name") if user else "",
                        "last_name": user.get("last_name") if user else ""
                    },
                    "cv_id": match.get("cv_id")
                })
        
        return {"success": True, "top_candidates": top_candidates, "total": len(top_candidates)}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur: {str(e)}")

@app.get("/scores/statistics")
async def get_matching_statistics(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Obtenir les statistiques de matching"""
    try:
        if current_user.get("role") not in ["recruiter", "admin"]:
            raise HTTPException(status_code=403, detail="Accès réservé aux recruteurs et admins")
        
        stats = await db_manager.get_database_stats()
        
        # Calculer les statistiques de matching
        cursor = db_manager.database["matches"].find()
        all_matches = await cursor.to_list(length=None)
        
        if all_matches:
            scores = [m.get("overall_score", 0) for m in all_matches]
            avg_score = sum(scores) / len(scores)
            max_score = max(scores)
            min_score = min(scores)
            
            # Distribution des scores
            high_scores = len([s for s in scores if s >= 7.0])
            medium_scores = len([s for s in scores if 5.0 <= s < 7.0])
            low_scores = len([s for s in scores if s < 5.0])
        else:
            avg_score = max_score = min_score = 0
            high_scores = medium_scores = low_scores = 0
        
        statistics = {
            "total_matches": len(all_matches),
            "average_score": round(avg_score, 2),
            "max_score": round(max_score, 2),
            "min_score": round(min_score, 2),
            "score_distribution": {
                "high": high_scores,
                "medium": medium_scores,
                "low": low_scores
            },
            "database_stats": stats
        }
        
        return {"success": True, "statistics": statistics}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur: {str(e)}")

# --- Recruiter Management Endpoints ---

@app.post("/recruiter/validate-candidate")
async def validate_candidate(
    application_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Valider un candidat"""
    try:
        if current_user.get("role") != "recruiter":
            raise HTTPException(status_code=403, detail="Accès réservé aux recruteurs")
        
        application = await db_manager.database["applications"].find_one({"_id": application_id})
        if not application:
            raise HTTPException(status_code=404, detail="Candidature non trouvée")
        
        job = await db_manager.get_job_by_id(application.get("job_id"))
        if not job or job.get("created_by") != current_user.get("user_id"):
            raise HTTPException(status_code=403, detail="Offre non autorisée")
        
        await db_manager.database["applications"].update_one(
            {"_id": application_id},
            {"$set": {"status": ApplicationStatus.SHORTLISTED.value, "updated_at": datetime.utcnow()}}
        )
        
        return {"success": True, "message": "Candidat validé avec succès"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur: {str(e)}")

@app.post("/recruiter/reject-candidate")
async def reject_candidate(
    application_id: str,
    reason: Optional[str] = None,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Rejeter un candidat"""
    try:
        if current_user.get("role") != "recruiter":
            raise HTTPException(status_code=403, detail="Accès réservé aux recruteurs")
        
        application = await db_manager.database["applications"].find_one({"_id": application_id})
        if not application:
            raise HTTPException(status_code=404, detail="Candidature non trouvée")
        
        job = await db_manager.get_job_by_id(application.get("job_id"))
        if not job or job.get("created_by") != current_user.get("user_id"):
            raise HTTPException(status_code=403, detail="Offre non autorisée")
        
        update_data = {
            "status": ApplicationStatus.REJECTED.value,
            "updated_at": datetime.utcnow()
        }
        if reason:
            update_data["rejection_reason"] = reason
        
        await db_manager.database["applications"].update_one(
            {"_id": application_id},
            {"$set": update_data}
        )
        
        return {"success": True, "message": "Candidat rejeté avec succès"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur: {str(e)}")

@app.post("/recruiter/send-interview-invitation")
async def send_interview_invitation(
    application_id: str,
    scheduled_at: datetime,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Envoyer une invitation d'entretien"""
    try:
        if current_user.get("role") != "recruiter":
            raise HTTPException(status_code=403, detail="Accès réservé aux recruteurs")
        
        application = await db_manager.database["applications"].find_one({"_id": application_id})
        if not application:
            raise HTTPException(status_code=404, detail="Candidature non trouvée")
        
        job = await db_manager.get_job_by_id(application.get("job_id"))
        if not job or job.get("created_by") != current_user.get("user_id"):
            raise HTTPException(status_code=403, detail="Offre non autorisée")
        
        # Créer l'entretien
        interview_data = {
            "job_id": application.get("job_id"),
            "candidate_id": application.get("candidate_id"),
            "cv_id": application.get("cv_id"),
            "scheduled_at": scheduled_at,
            "status": InterviewStatus.SCHEDULED.value,
            "created_by": current_user.get("user_id")
        }
        
        interview_id = await db_manager.save_interview(interview_data)
        
        # Mettre à jour la candidature
        await db_manager.database["applications"].update_one(
            {"_id": application_id},
            {"$set": {"status": ApplicationStatus.INTERVIEW_SCHEDULED.value, "updated_at": datetime.utcnow()}}
        )
        
        return {"success": True, "message": "Invitation d'entretien envoyée", "interview_id": interview_id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur: {str(e)}")

@app.post("/recruiter/shortlist-candidate")
async def shortlist_candidate(
    application_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Ajouter un candidat à la shortlist"""
    try:
        if current_user.get("role") != "recruiter":
            raise HTTPException(status_code=403, detail="Accès réservé aux recruteurs")
        
        application = await db_manager.database["applications"].find_one({"_id": application_id})
        if not application:
            raise HTTPException(status_code=404, detail="Candidature non trouvée")
        
        job = await db_manager.get_job_by_id(application.get("job_id"))
        if not job or job.get("created_by") != current_user.get("user_id"):
            raise HTTPException(status_code=403, detail="Offre non autorisée")
        
        await db_manager.database["applications"].update_one(
            {"_id": application_id},
            {"$set": {"status": ApplicationStatus.SHORTLISTED.value, "updated_at": datetime.utcnow()}}
        )
        
        return {"success": True, "message": "Candidat ajouté à la shortlist"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur: {str(e)}")

# --- Administration Endpoints ---

@app.post("/admin/create-recruiter")
async def create_recruiter(
    user: UserCreate,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Créer un compte recruteur"""
    try:
        if current_user.get("role") != "admin":
            raise HTTPException(status_code=403, detail="Accès réservé aux administrateurs")
        
        existing_user = await db_manager.get_user_by_email(user.email)
        if existing_user:
            raise HTTPException(status_code=400, detail="Email déjà utilisé")
        
        hashed_password = auth_service.get_password_hash(user.password)
        user_data = user.dict(exclude_none=True)
        user_data["password"] = hashed_password
        user_data["role"] = UserRole.RECRUITER.value
        if not user_data.get("last_name"):
            user_data["last_name"] = user_data.get("first_name", "")
        
        user_id = await db_manager.create_user(user_data)
        
        return {"success": True, "message": "Recruteur créé avec succès", "user_id": user_id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur: {str(e)}")

@app.put("/admin/update-recruiter/{user_id}")
async def update_recruiter(
    user_id: str,
    user_update: UserUpdate,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Mettre à jour un recruteur"""
    try:
        if current_user.get("role") != "admin":
            raise HTTPException(status_code=403, detail="Accès réservé aux administrateurs")
        
        existing_user = await db_manager.get_user_by_id(user_id)
        if not existing_user:
            raise HTTPException(status_code=404, detail="Utilisateur non trouvé")
        
        if existing_user.get("role") != UserRole.RECRUITER.value:
            raise HTTPException(status_code=400, detail="L'utilisateur n'est pas un recruteur")
        
        update_data = user_update.dict(exclude_unset=True)
        update_data["updated_at"] = datetime.utcnow()
        
        await db_manager.update_user(user_id, update_data)
        
        return {"success": True, "message": "Recruteur mis à jour avec succès"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur: {str(e)}")

@app.delete("/admin/delete-recruiter/{user_id}")
async def delete_recruiter(
    user_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Supprimer un recruteur"""
    try:
        if current_user.get("role") != "admin":
            raise HTTPException(status_code=403, detail="Accès réservé aux administrateurs")
        
        existing_user = await db_manager.get_user_by_id(user_id)
        if not existing_user:
            raise HTTPException(status_code=404, detail="Utilisateur non trouvé")
        
        if existing_user.get("role") != UserRole.RECRUITER.value:
            raise HTTPException(status_code=400, detail="L'utilisateur n'est pas un recruteur")
        
        result = await db_manager.database["users"].delete_one({"_id": user_id})
        
        if result.deleted_count == 0:
            raise HTTPException(status_code=400, detail="Erreur lors de la suppression")
        
        return {"success": True, "message": "Recruteur supprimé avec succès"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur: {str(e)}")

@app.put("/admin/assign-role/{user_id}")
async def assign_roles(
    user_id: str,
    role: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Assigner un rôle à un utilisateur"""
    try:
        if current_user.get("role") != "admin":
            raise HTTPException(status_code=403, detail="Accès réservé aux administrateurs")
        
        if role not in [UserRole.CANDIDATE.value, UserRole.RECRUITER.value, UserRole.ADMIN.value]:
            raise HTTPException(status_code=400, detail="Rôle invalide")
        
        existing_user = await db_manager.get_user_by_id(user_id)
        if not existing_user:
            raise HTTPException(status_code=404, detail="Utilisateur non trouvé")
        
        await db_manager.update_user(user_id, {"role": role})
        
        return {"success": True, "message": f"Rôle {role} assigné avec succès"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur: {str(e)}")

@app.get("/admin/dashboard-stats")
async def get_dashboard_stats(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Obtenir les statistiques du dashboard"""
    try:
        if current_user.get("role") != "admin":
            raise HTTPException(status_code=403, detail="Accès réservé aux administrateurs")
        
        stats = await db_manager.get_database_stats()
        
        # Statistiques supplémentaires
        total_candidates = await db_manager.database["users"].count_documents({"role": UserRole.CANDIDATE.value})
        total_recruiters = await db_manager.database["users"].count_documents({"role": UserRole.RECRUITER.value})
        total_jobs = await db_manager.database["jobs"].count_documents({})
        total_interviews = await db_manager.database["interviews"].count_documents({})
        total_applications = await db_manager.database["applications"].count_documents({})
        
        dashboard_stats = {
            "total_candidates": total_candidates,
            "total_recruiters": total_recruiters,
            "total_jobs": total_jobs,
            "total_interviews": total_interviews,
            "total_applications": total_applications,
            "database_stats": stats
        }
        
        return {"success": True, "dashboard_stats": dashboard_stats}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur: {str(e)}")

@app.get("/admin/ai-accuracy")
async def get_ai_accuracy(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Obtenir les statistiques de précision de l'IA"""
    try:
        if current_user.get("role") != "admin":
            raise HTTPException(status_code=403, detail="Accès réservé aux administrateurs")
        
        # Calculer la précision de l'IA basée sur les entretiens complétés
        cursor = db_manager.database["interviews"].find({"status": InterviewStatus.COMPLETED.value})
        completed_interviews = await cursor.to_list(length=None)
        
        if completed_interviews:
            scores = [i.get("overall_score", 0) for i in completed_interviews]
            avg_score = sum(scores) / len(scores)
            high_score_rate = len([s for s in scores if s >= 7.0]) / len(scores) * 100
        else:
            avg_score = 0
            high_score_rate = 0
        
        ai_stats = {
            "total_completed_interviews": len(completed_interviews),
            "average_score": round(avg_score, 2),
            "high_score_rate": round(high_score_rate, 2),
            "ai_services_status": {
                "cv_parser": "active",
                "ai_matcher": "active",
                "interview_ai": "active"
            }
        }
        
        return {"success": True, "ai_stats": ai_stats}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur: {str(e)}")

@app.get("/admin/system-monitor")
async def monitor_system(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Surveiller le système"""
    try:
        if current_user.get("role") != "admin":
            raise HTTPException(status_code=403, detail="Accès réservé aux administrateurs")
        
        stats = await db_manager.get_database_stats()
        
        system_status = {
            "database": "connected",
            "database_stats": stats,
            "ai_services": {
                "cv_parser": "operational",
                "ai_matcher": "operational",
                "interview_ai": "operational"
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
        return {"success": True, "system_status": system_status}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur: {str(e)}")

@app.get("/admin/ai-services-monitor")
async def monitor_ai_services(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Surveiller les services IA"""
    try:
        if current_user.get("role") != "admin":
            raise HTTPException(status_code=403, detail="Accès réservé aux administrateurs")
        
        ai_services_status = {
            "cv_parser": {
                "status": "operational",
                "last_used": datetime.utcnow().isoformat()
            },
            "ai_matcher": {
                "status": "operational",
                "last_used": datetime.utcnow().isoformat()
            },
            "interview_ai": {
                "status": "operational",
                "last_used": datetime.utcnow().isoformat()
            }
        }
        
        return {"success": True, "ai_services_status": ai_services_status}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur: {str(e)}")

@app.get("/admin/logs")
async def view_logs(
    limit: int = 100,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Voir les logs système"""
    try:
        if current_user.get("role") != "admin":
            raise HTTPException(status_code=403, detail="Accès réservé aux administrateurs")
        
        # Pour l'instant, retourner des logs simulés
        logs = [
            {"timestamp": datetime.utcnow().isoformat(), "level": "INFO", "message": "Système opérationnel"},
            {"timestamp": datetime.utcnow().isoformat(), "level": "INFO", "message": "Base de données connectée"},
            {"timestamp": datetime.utcnow().isoformat(), "level": "INFO", "message": "Services IA actifs"}
        ]
        
        return {"success": True, "logs": logs[:limit], "total": len(logs)}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur: {str(e)}")

@app.post("/admin/backup-database")
async def backup_database(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Sauvegarder la base de données"""
    try:
        if current_user.get("role") != "admin":
            raise HTTPException(status_code=403, detail="Accès réservé aux administrateurs")
        
        # Pour l'instant, simuler la sauvegarde
        backup_info = {
            "timestamp": datetime.utcnow().isoformat(),
            "status": "success",
            "message": "Sauvegarde simulée - à implémenter avec mongodump"
        }
        
        return {"success": True, "backup_info": backup_info}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur: {str(e)}")

@app.post("/admin/restore-database")
async def restore_database(
    backup_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Restaurer la base de données"""
    try:
        if current_user.get("role") != "admin":
            raise HTTPException(status_code=403, detail="Accès réservé aux administrateurs")
        
        # Pour l'instant, simuler la restauration
        restore_info = {
            "timestamp": datetime.utcnow().isoformat(),
            "status": "success",
            "message": "Restauration simulée - à implémenter avec mongorestore",
            "backup_id": backup_id
        }
        
        return {"success": True, "restore_info": restore_info}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur: {str(e)}")

# --- AI Analysis Endpoints ---

@app.post("/ai/analyze-cv")
async def analyze_cv(
    cv_id: str,
    job_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Analyser un CV avec l'IA et calculer le score de matching
    """
    try:
        # Récupérer le CV
        cv = await db_manager.get_cv_by_id(cv_id)
        if not cv:
            raise HTTPException(status_code=404, detail="CV non trouvé")
        
        # Récupérer l'offre
        job = await db_manager.get_job_by_id(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Offre non trouvée")
        
        # Analyser le CV avec l'IA
        match_result = ai_matcher.calculate_match(
            cv_text=cv.get("text", ""),
            job_description=job,
            cv_data={
                "skills": cv.get("skills", []),
                "experience": cv.get("experience", []),
                "education": cv.get("education", [])
            }
        )
        
        # Sauvegarder le résultat du matching
        match_data = {
            "cv_id": cv_id,
            "job_id": job_id,
            "overall_score": match_result["overall_score"],
            "skills_score": match_result["skills_score"],
            "experience_score": match_result["experience_score"],
            "education_score": match_result["education_score"],
            "tools_score": match_result["tools_score"],
            "matched_skills": match_result["matched_skills"],
            "missing_skills": match_result["missing_skills"],
            "recommendations": match_result["recommendations"]
        }
        
        await db_manager.save_match(match_data)
        
        return {
            "success": True,
            "message": "CV analysé avec succès",
            "analysis": match_result
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de l'analyse du CV: {str(e)}")

@app.get("/recruiter/matches/{job_id}")
async def get_job_matches(
    job_id: str,
    limit: int = 20,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Récupérer les scores de matching pour une offre (pour les recruteurs)
    """
    try:
        # Vérifier que l'utilisateur est un recruteur
        if current_user.get("role") != "recruiter":
            raise HTTPException(status_code=403, detail="Accès réservé aux recruteurs")
        
        # Récupérer l'offre
        job = await db_manager.get_job_by_id(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Offre non trouvée")
        
        # Vérifier que l'offre appartient au recruteur
        if job.get("created_by") != current_user.get("user_id"):
            raise HTTPException(status_code=403, detail="Offre non autorisée")
        
        # Récupérer les matches
        matches = await db_manager.get_matches_for_job(job_id, limit)
        
        # Enrichir avec les détails des CVs et candidats
        for match in matches:
            cv = await db_manager.get_cv_by_id(match.get("cv_id"))
            if cv:
                match["cv_details"] = cv
                user = await db_manager.get_user_by_id(cv.get("user_id"))
                if user:
                    match["candidate_details"] = {
                        "email": user.get("email"),
                        "first_name": user.get("first_name"),
                        "last_name": user.get("last_name")
                    }
        
        return {
            "success": True,
            "matches": matches,
            "total": len(matches),
            "job_title": job.get("title")
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la récupération des matches: {str(e)}")

@app.get("/recruiter/interview/{interview_id}")
async def get_interview_details(
    interview_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Récupérer les détails d'un entretien avec le score et le feedback
    """
    try:
        # Vérifier que l'utilisateur est un recruteur
        if current_user.get("role") != "recruiter":
            raise HTTPException(status_code=403, detail="Accès réservé aux recruteurs")
        
        # Récupérer l'entretien
        interview = await db_manager.get_interview_by_id(interview_id)
        if not interview:
            raise HTTPException(status_code=404, detail="Entretien non trouvé")
        
        # Récupérer l'offre pour vérifier l'autorisation
        job = await db_manager.get_job_by_id(interview.get("job_id"))
        if not job or job.get("created_by") != current_user.get("user_id"):
            raise HTTPException(status_code=403, detail="Entretien non autorisé")
        
        return {
            "success": True,
            "interview": interview
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la récupération de l'entretien: {str(e)}")

@app.get("/candidate/my-applications")
async def get_my_applications(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Récupérer les candidatures du candidat connecté
    """
    try:
        # Vérifier que l'utilisateur est un candidat
        if current_user.get("role") != "candidate":
            raise HTTPException(status_code=403, detail="Accès réservé aux candidats")
        
        # Récupérer les candidatures
        cursor = db_manager.database["applications"].find(
            {"candidate_id": current_user.get("user_id")}
        ).sort("created_at", -1)
        
        applications = await cursor.to_list(length=None)
        
        # Enrichir avec les détails des offres
        for app in applications:
            job = await db_manager.get_job_by_id(app.get("job_id"))
            if job:
                app["job_details"] = job
            
            match = await db_manager.database["matches"].find_one({
                "cv_id": app.get("cv_id"),
                "job_id": app.get("job_id")
            })
            if match:
                app["match_score"] = match.get("overall_score")
        
        return {
            "success": True,
            "applications": applications,
            "total": len(applications)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la récupération des candidatures: {str(e)}")

@app.get("/candidate/my-cvs")
async def get_my_cvs(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Récupérer les CVs du candidat connecté
    """
    try:
        # Vérifier que l'utilisateur est un candidat
        if current_user.get("role") != "candidate":
            raise HTTPException(status_code=403, detail="Accès réservé aux candidats")
        
        # Récupérer les CVs
        cvs = await db_manager.get_cvs_by_user(current_user.get("user_id"))
        
        return {
            "success": True,
            "cvs": cvs,
            "total": len(cvs)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la récupération des CVs: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
