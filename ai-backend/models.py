from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

# Enums pour les types de données
class UserRole(str, Enum):
    ADMIN = "admin"
    RECRUITER = "recruiter"
    CANDIDATE = "candidate"

class ExperienceLevel(str, Enum):
    ENTRY_LEVEL = "entry_level"
    JUNIOR = "junior"
    MID_LEVEL = "mid_level"
    SENIOR = "senior"
    LEAD = "lead"
    MANAGER = "manager"

class JobStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    FILLED = "filled"
    DRAFT = "draft"

class ApplicationStatus(str, Enum):
    PENDING = "pending"
    REVIEWING = "reviewing"
    SHORTLISTED = "shortlisted"
    INTERVIEW_SCHEDULED = "interview_scheduled"
    INTERVIEWED = "interviewed"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    WITHDRAWN = "withdrawn"

class InterviewStatus(str, Enum):
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

# --- User Models ---
class UserCreate(BaseModel):
    """Modèle pour la création d'utilisateur"""
    email: str
    password: str = Field(..., min_length=6, description="Mot de passe (min 6 caractères)")
    first_name: str = Field(..., min_length=1, description="Prénom")
    last_name: Optional[str] = Field(None, description="Nom de famille")
    role: UserRole = Field(..., description="Rôle de l'utilisateur")
    phone: Optional[str] = Field(None, description="Numéro de téléphone")
    location: Optional[str] = Field(None, description="Localisation")

class UserLogin(BaseModel):
    """Modèle pour la connexion utilisateur"""
    email: str
    password: str

class UserResponse(BaseModel):
    """Modèle pour la réponse utilisateur (sans mot de passe)"""
    id: str
    email: EmailStr
    first_name: str
    last_name: str
    role: UserRole
    phone: Optional[str] = None
    location: Optional[str] = None
    avatar: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime] = None

class UserUpdate(BaseModel):
    """Modèle pour la mise à jour utilisateur"""
    first_name: Optional[str] = Field(None, min_length=2)
    last_name: Optional[str] = Field(None, min_length=2)
    phone: Optional[str] = None
    location: Optional[str] = None
    avatar: Optional[str] = None

# --- CV Models ---
class ExperienceItem(BaseModel):
    """Modèle pour une expérience professionnelle"""
    title: str = Field(..., description="Titre du poste")
    company: str = Field(..., description="Nom de l'entreprise")
    start_date: datetime = Field(..., description="Date de début")
    end_date: Optional[datetime] = Field(None, description="Date de fin")
    description: str = Field(..., description="Description du poste")
    skills: List[str] = Field(default_factory=list, description="Compétences utilisées")

class EducationItem(BaseModel):
    """Modèle pour une formation"""
    degree: str = Field(..., description="Diplôme obtenu")
    institution: str = Field(..., description="Nom de l'institution")
    start_date: datetime = Field(..., description="Date de début")
    end_date: Optional[datetime] = Field(None, description="Date de fin")
    field_of_study: str = Field(..., description="Domaine d'étude")
    gpa: Optional[float] = Field(None, ge=0, le=4, description="Moyenne générale")

class CVCreate(BaseModel):
    """Modèle pour la création de CV"""
    user_id: str
    title: str = Field(..., description="Titre du CV")
    summary: Optional[str] = Field(None, description="Résumé du CV")
    experience: List[ExperienceItem] = Field(default_factory=list)
    education: List[EducationItem] = Field(default_factory=list)
    skills: List[str] = Field(default_factory=list, description="Liste des compétences")
    languages: List[Dict[str, str]] = Field(default_factory=list, description="Langues parlées")
    certifications: List[str] = Field(default_factory=list, description="Certifications")
    is_default: bool = Field(False, description="CV par défaut")

class CVResponse(BaseModel):
    """Modèle pour la réponse CV"""
    id: str
    user_id: str
    title: str
    summary: Optional[str]
    experience: List[ExperienceItem]
    education: List[EducationItem]
    skills: List[str]
    languages: List[Dict[str, str]]
    certifications: List[str]
    is_default: bool
    completeness_score: float
    created_at: datetime
    updated_at: datetime

# --- Job Models ---
class JobCreate(BaseModel):
    """Modèle pour la création d'offre d'emploi"""
    title: str = Field(..., min_length=5, description="Titre du poste")
    description: str = Field(..., min_length=50, description="Description détaillée")
    requirements: str = Field(..., min_length=20, description="Exigences du poste")
    skills: List[str] = Field(..., min_items=1, description="Compétences requises")
    experience_level: ExperienceLevel = Field(..., description="Niveau d'expérience requis")
    employment_type: str = Field(..., description="Type de contrat")
    work_location: str = Field(..., description="Lieu de travail")
    remote_policy: str = Field(..., description="Politique de télétravail")
    salary_min: Optional[int] = Field(None, ge=0, description="Salaire minimum")
    salary_max: Optional[int] = Field(None, ge=0, description="Salaire maximum")
    currency: str = Field("EUR", description="Devise")
    department: Optional[str] = Field(None, description="Département")
    team: Optional[str] = Field(None, description="Équipe")
    benefits: List[str] = Field(default_factory=list, description="Avantages")
    application_deadline: Optional[datetime] = Field(None, description="Date limite de candidature")
    is_active: bool = Field(True, description="Offre active")

class JobResponse(BaseModel):
    """Modèle pour la réponse offre d'emploi"""
    id: str
    title: str
    description: str
    requirements: str
    skills: List[str]
    experience_level: ExperienceLevel
    employment_type: str
    work_location: str
    remote_policy: str
    salary_min: Optional[int]
    salary_max: Optional[int]
    currency: str
    department: Optional[str]
    team: Optional[str]
    benefits: List[str]
    application_deadline: Optional[datetime]
    status: JobStatus
    created_by: str
    created_at: datetime
    updated_at: datetime

# --- Application Models ---
class ApplicationCreate(BaseModel):
    """Modèle pour la création de candidature"""
    job_id: str
    cv_id: str
    cover_letter: Optional[str] = Field(None, min_length=50, description="Lettre de motivation")
    salary_expectation: Optional[int] = Field(None, ge=0, description="Prétention salariale")
    availability: Optional[str] = Field(None, description="Disponibilité")
    location_preference: Optional[str] = Field(None, description="Préférence de localisation")

class ApplicationResponse(BaseModel):
    """Modèle pour la réponse candidature"""
    id: str
    job_id: str
    cv_id: str
    candidate_id: str
    cover_letter: Optional[str]
    salary_expectation: Optional[int]
    availability: Optional[str]
    location_preference: Optional[str]
    status: ApplicationStatus
    created_at: datetime
    updated_at: datetime

# --- Interview Models ---
class InterviewQuestion(BaseModel):
    """Modèle pour une question d'entretien"""
    id: int
    type: str
    question: str
    keywords: List[str]
    difficulty: str
    time_limit: int
    category: str

class InterviewCreate(BaseModel):
    """Modèle pour la création d'entretien"""
    job_id: str
    candidate_id: str
    cv_id: str
    scheduled_at: datetime = Field(..., description="Date prévue de l'entretien")
    duration_minutes: int = Field(60, ge=15, le=180, description="Durée en minutes")
    interview_type: str = Field("technical", description="Type d'entretien")
    interviewer_ids: List[str] = Field(default_factory=list, description="IDs des interviewers")
    notes: Optional[str] = Field(None, description="Notes internes")

class InterviewResponse(BaseModel):
    """Modèle pour la réponse entretien"""
    id: str
    job_id: str
    candidate_id: str
    cv_id: str
    scheduled_at: datetime
    duration_minutes: int
    interview_type: str
    interviewer_ids: List[str]
    status: InterviewStatus
    questions: List[InterviewQuestion]
    overall_score: Optional[float]
    recommendation: Optional[str]
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime

# --- Match Models ---
class MatchRequest(BaseModel):
    """Modèle pour la demande de matching"""
    cv_id: str
    job_id: str
    cv_text: str
    job_description: Dict[str, Any]

class MatchResponse(BaseModel):
    """Modèle pour la réponse matching"""
    id: str
    cv_id: str
    job_id: str
    overall_score: float
    skills_score: float
    experience_score: float
    education_score: float
    tools_score: float
    matched_skills: List[str]
    missing_skills: List[str]
    recommendations: List[str]
    created_at: datetime

# --- Analytics Models ---
class AnalyticsEvent(BaseModel):
    """Modèle pour un événement analytics"""
    event_type: str
    timestamp: datetime
    user_id: Optional[str]
    session_id: Optional[str]
    data: Dict[str, Any] = Field(default_factory=dict)

class DashboardResponse(BaseModel):
    """Modèle pour la réponse du dashboard"""
    overview: Dict[str, Any]
    performance_trends: Dict[str, Any]
    matching_analytics: Dict[str, Any]
    interview_analytics: Dict[str, Any]
    recommendation_analytics: Dict[str, Any]
    skill_trends: Dict[str, Any]
    time_range: str
    generated_at: datetime

# --- JWT Token Models ---
class Token(BaseModel):
    """Modèle pour le token JWT"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int

class TokenData(BaseModel):
    """Modèle pour les données du token"""
    sub: str  # user_id
    email: str
    role: UserRole
    is_active: bool
    exp: datetime

# --- API Response Models ---
class APIResponse(BaseModel):
    """Modèle de réponse API standard"""
    success: bool
    message: str
    data: Optional[Any] = None
    errors: Optional[List[str]] = None

class PaginatedResponse(BaseModel):
    """Modèle pour les réponses paginées"""
    items: List[Any]
    total: int
    page: int
    per_page: int
    pages: int
    has_next: bool
    has_prev: bool

# --- Validation Functions ---
@validator('password')
def validate_password(cls, v):
    """Validateur pour le mot de passe"""
    if len(v) < 8:
        raise ValueError('Le mot de passe doit contenir au moins 8 caractères')
    if not any(c.isupper() for c in v):
        raise ValueError('Le mot de passe doit contenir au moins une majuscule')
    if not any(c.islower() for c in v):
        raise ValueError('Le mot de passe doit contenir au moins une minuscule')
    if not any(c.isdigit() for c in v):
        raise ValueError('Le mot de passe doit contenir au moins un chiffre')
    return v

@validator('salary_max')
def validate_salary_range(cls, v, values):
    """Validateur pour la plage salariale"""
    if 'salary_min' in values and v and v <= values['salary_min']:
        raise ValueError('Le salaire maximum doit être supérieur au salaire minimum')
    return v

@validator('application_deadline')
def validate_deadline(cls, v):
    """Validateur pour la date limite"""
    if v and v <= datetime.utcnow():
        raise ValueError('La date limite doit être dans le futur')
    return v

@validator('scheduled_at')
def validate_interview_date(cls, v):
    """Validateur pour la date d'entretien"""
    if v and v <= datetime.utcnow():
        raise ValueError('La date d\'entretien doit être dans le futur')
    return v
