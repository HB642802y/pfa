from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext
import os
from dotenv import load_dotenv

load_dotenv()

# Configuration JWT
SECRET_KEY = os.getenv("JWT_SECRET", "votre_secret_key_ici")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30 * 24 * 60  # 30 jours

# Configuration du hash de mot de passe
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

# Configuration du bearer token
security = HTTPBearer()

class AuthService:
    def __init__(self):
        """Initialiser le service d'authentification"""
        self.secret_key = SECRET_KEY
        self.algorithm = ALGORITHM
        self.expire_minutes = ACCESS_TOKEN_EXPIRE_MINUTES

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Vérifier un mot de passe"""
        return pwd_context.verify(plain_password, hashed_password)

    def get_password_hash(self, password: str) -> str:
        """Hasher un mot de passe"""
        return pwd_context.hash(password)

    def create_access_token(self, data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """Créer un token d'accès JWT"""
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=self.expire_minutes)
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        
        return encoded_jwt

    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Vérifier et décoder un token JWT"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except JWTError:
            return None

    def get_current_user(self, credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
        """Obtenir l'utilisateur courant à partir du token"""
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
        try:
            payload = self.verify_token(credentials.credentials)
            if payload is None:
                raise credentials_exception
                
            user_id: str = payload.get("sub")
            if user_id is None:
                raise credentials_exception
                
            # Ajouter les informations de l'utilisateur au payload
            payload.update({
                "user_id": user_id,
                "email": payload.get("email"),
                "role": payload.get("role"),
                "is_active": payload.get("is_active", True)
            })
            
            return payload
            
        except JWTError:
            raise credentials_exception

    def require_role(self, required_role: str):
        """Décorateur pour vérifier le rôle de l'utilisateur"""
        def role_checker(current_user: Dict[str, Any] = Depends(self.get_current_user)):
            if current_user.get("role") != required_role:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Accès refusé. Rôle requis: {required_role}"
                )
            return current_user
        return role_checker

    def require_roles(self, allowed_roles: list):
        """Décorateur pour vérifier plusieurs rôles"""
        def roles_checker(current_user: Dict[str, Any] = Depends(self.get_current_user)):
            user_role = current_user.get("role")
            if user_role not in allowed_roles:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Accès refusé. Rôles autorisés: {', '.join(allowed_roles)}"
                )
            return current_user
        return roles_checker

    def is_active_user(self, current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
        """Vérifier si l'utilisateur est actif"""
        if not current_user.get("is_active", False):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Compte utilisateur désactivé"
            )
        return current_user

# Instance globale du service d'authentification
auth_service = AuthService()

# Dépendances communes
get_current_user = auth_service.get_current_user
require_admin = auth_service.require_role("admin")
require_recruiter = auth_service.require_role("recruiter")
require_candidate = auth_service.require_role("candidate")
require_active_user = auth_service.is_active_user

# Rôles autorisés pour les différentes opérations
ALLOWED_ROLES = {
    "admin": ["admin"],
    "recruiter": ["admin", "recruiter"],
    "candidate": ["admin", "candidate"],
    "all": ["admin", "recruiter", "candidate"]
}

def check_permission(required_permission: str):
    """Vérifier une permission spécifique"""
    def permission_checker(current_user: Dict[str, Any] = Depends(get_current_user)):
        user_role = current_user.get("role")
        
        # Définir les permissions par rôle
        role_permissions = {
            "admin": [
                "manage_users", "manage_system", "view_analytics", 
                "manage_jobs", "manage_interviews", "access_all_data"
            ],
            "recruiter": [
                "create_jobs", "edit_own_jobs", "view_applications", 
                "schedule_interviews", "view_candidates"
            ],
            "candidate": [
                "apply_jobs", "view_own_applications", "edit_own_profile",
                "view_interviews", "upload_cv"
            ]
        }
        
        user_permissions = role_permissions.get(user_role, [])
        
        if required_permission not in user_permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission refusée: {required_permission}"
            )
        
        return current_user
    
    return permission_checker

# Permissions disponibles
PERMISSIONS = {
    # Admin permissions
    "manage_users": "Gérer les utilisateurs",
    "manage_system": "Gérer le système",
    "view_analytics": "Voir les analytics",
    "manage_jobs": "Gérer toutes les offres",
    "manage_interviews": "Gérer tous les entretiens",
    "access_all_data": "Accéder à toutes les données",
    
    # Recruiter permissions
    "create_jobs": "Créer des offres",
    "edit_own_jobs": "Modifier ses offres",
    "view_applications": "Voir les candidatures",
    "schedule_interviews": "Planifier des entretiens",
    "view_candidates": "Voir les candidats",
    
    # Candidate permissions
    "apply_jobs": "Postuler aux offres",
    "view_own_applications": "Voir ses candidatures",
    "edit_own_profile": "Modifier son profil",
    "view_interviews": "Voir ses entretiens",
    "upload_cv": "Uploader un CV"
}
