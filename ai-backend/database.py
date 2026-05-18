from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import MongoClient
from typing import Optional, Dict, Any, List
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

class DatabaseManager:
    def __init__(self):
        """Initialiser le gestionnaire de base de données"""
        self.mongodb_url = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
        self.database_name = os.getenv("DATABASE_NAME", "ai_matching_db")
        
        # Client MongoDB
        self.client = None
        self.database = None
        
        # Collections
        self.users_collection = "users"
        self.cvs_collection = "cvs"
        self.jobs_collection = "jobs"
        self.matches_collection = "matches"
        self.interviews_collection = "interviews"
        self.analytics_collection = "analytics"

    async def connect(self):
        """Établir la connexion à MongoDB"""
        try:
            self.client = AsyncIOMotorClient(self.mongodb_url)
            self.database = self.client[self.database_name]
            
            # Créer les indexes
            await self._create_indexes()
            
            print(f"✅ Connecté à MongoDB: {self.mongodb_url}")
            print(f"📊 Base de données: {self.database_name}")
            
        except Exception as e:
            print(f"❌ Erreur connexion MongoDB: {e}")
            raise

    async def disconnect(self):
        """Fermer la connexion à MongoDB"""
        if self.client:
            self.client.close()
            print("🔌 Déconnecté de MongoDB")

    async def _create_indexes(self):
        """Créer les indexes pour optimiser les performances"""
        try:
            # Index pour les utilisateurs
            await self.database[self.users_collection].create_index("email", unique=True)
            await self.database[self.users_collection].create_index("role")
            
            # Index pour les CVs
            await self.database[self.cvs_collection].create_index("user_id")
            await self.database[self.cvs_collection].create_index("created_at")
            await self.database[self.cvs_collection].create_index("skills")
            
            # Index pour les jobs
            await self.database[self.jobs_collection].create_index("created_by")
            await self.database[self.jobs_collection].create_index("skills")
            await self.database[self.jobs_collection].create_index("status")
            
            # Index pour les matches
            await self.database[self.matches_collection].create_index([("cv_id", 1), ("job_id", 1)])
            await self.database[self.matches_collection].create_index("score")
            await self.database[self.matches_collection].create_index("created_at")
            
            # Index pour les interviews
            await self.database[self.interviews_collection].create_index("candidate_id")
            await self.database[self.interviews_collection].create_index("job_id")
            await self.database[self.interviews_collection].create_index("created_at")
            
            # Index pour les analytics
            await self.database[self.analytics_collection].create_index("event_type")
            await self.database[self.analytics_collection].create_index("timestamp")
            
            print("📈 Index créés avec succès")
            
        except Exception as e:
            print(f"⚠️ Erreur création indexes: {e}")

    # --- CRUD Operations for Users ---
    async def create_user(self, user_data: Dict[str, Any]) -> str:
        """Créer un nouvel utilisateur"""
        try:
            user_data["created_at"] = datetime.utcnow()
            user_data["updated_at"] = datetime.utcnow()
            user_data["is_active"] = True
            
            result = await self.database[self.users_collection].insert_one(user_data)
            return str(result.inserted_id)
            
        except Exception as e:
            print(f"❌ Erreur création utilisateur: {e}")
            raise

    async def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Récupérer un utilisateur par email"""
        try:
            user = await self.database[self.users_collection].find_one({"email": email})
            return user
            
        except Exception as e:
            print(f"❌ Erreur récupération utilisateur: {e}")
            return None

    async def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Récupérer un utilisateur par ID"""
        try:
            user = await self.database[self.users_collection].find_one({"_id": user_id})
            return user
            
        except Exception as e:
            print(f"❌ Erreur récupération utilisateur: {e}")
            return None

    async def update_user(self, user_id: str, update_data: Dict[str, Any]) -> bool:
        """Mettre à jour un utilisateur"""
        try:
            update_data["updated_at"] = datetime.utcnow()
            result = await self.database[self.users_collection].update_one(
                {"_id": user_id},
                {"$set": update_data}
            )
            return result.modified_count > 0
            
        except Exception as e:
            print(f"❌ Erreur mise à jour utilisateur: {e}")
            return False

    # --- CRUD Operations for CVs ---
    async def save_cv(self, cv_data: Dict[str, Any]) -> str:
        """Sauvegarder un CV"""
        try:
            cv_data["created_at"] = datetime.utcnow()
            cv_data["updated_at"] = datetime.utcnow()
            
            result = await self.database[self.cvs_collection].insert_one(cv_data)
            return str(result.inserted_id)
            
        except Exception as e:
            print(f"❌ Erreur sauvegarde CV: {e}")
            raise

    async def get_cv_by_id(self, cv_id: str) -> Optional[Dict[str, Any]]:
        """Récupérer un CV par ID"""
        try:
            cv = await self.database[self.cvs_collection].find_one({"_id": cv_id})
            return cv
            
        except Exception as e:
            print(f"❌ Erreur récupération CV: {e}")
            return None

    async def get_cvs_by_user(self, user_id: str) -> List[Dict[str, Any]]:
        """Récupérer tous les CVs d'un utilisateur"""
        try:
            cursor = self.database[self.cvs_collection].find({"user_id": user_id})
            cvs = await cursor.to_list(length=None)
            return cvs
            
        except Exception as e:
            print(f"❌ Erreur récupération CVs utilisateur: {e}")
            return []

    async def update_cv(self, cv_id: str, update_data: Dict[str, Any]) -> bool:
        """Mettre à jour un CV"""
        try:
            update_data["updated_at"] = datetime.utcnow()
            result = await self.database[self.cvs_collection].update_one(
                {"_id": cv_id},
                {"$set": update_data}
            )
            return result.modified_count > 0
            
        except Exception as e:
            print(f"❌ Erreur mise à jour CV: {e}")
            return False

    # --- CRUD Operations for Jobs ---
    async def create_job(self, job_data: Dict[str, Any]) -> str:
        """Créer une offre d'emploi"""
        try:
            job_data["created_at"] = datetime.utcnow()
            job_data["updated_at"] = datetime.utcnow()
            job_data["status"] = "active"
            
            result = await self.database[self.jobs_collection].insert_one(job_data)
            return str(result.inserted_id)
            
        except Exception as e:
            print(f"❌ Erreur création offre: {e}")
            raise

    async def get_job_by_id(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Récupérer une offre par ID"""
        try:
            job = await self.database[self.jobs_collection].find_one({"_id": job_id})
            return job
            
        except Exception as e:
            print(f"❌ Erreur récupération offre: {e}")
            return None

    async def get_active_jobs(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Récupérer les offres actives"""
        try:
            cursor = self.database[self.jobs_collection].find(
                {"status": "active"}
            ).sort("created_at", -1).limit(limit)
            
            jobs = await cursor.to_list(length=None)
            return jobs
            
        except Exception as e:
            print(f"❌ Erreur récupération offres actives: {e}")
            return []

    async def search_jobs(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Rechercher des offres"""
        try:
            search_filter = {
                "$or": [
                    {"title": {"$regex": query, "$options": "i"}},
                    {"description": {"$regex": query, "$options": "i"}},
                    {"skills": {"$in": [query]}}
                ],
                "status": "active"
            }
            
            cursor = self.database[self.jobs_collection].find(search_filter).limit(limit)
            jobs = await cursor.to_list(length=None)
            return jobs
            
        except Exception as e:
            print(f"❌ Erreur recherche offres: {e}")
            return []

    # --- CRUD Operations for Matches ---
    async def save_match(self, match_data: Dict[str, Any]) -> str:
        """Sauvegarder un résultat de matching"""
        try:
            match_data["created_at"] = datetime.utcnow()
            
            result = await self.database[self.matches_collection].insert_one(match_data)
            return str(result.inserted_id)
            
        except Exception as e:
            print(f"❌ Erreur sauvegarde match: {e}")
            raise

    async def get_matches_for_cv(self, cv_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Récupérer les matches pour un CV"""
        try:
            cursor = self.database[self.matches_collection].find(
                {"cv_id": cv_id}
            ).sort("score", -1).limit(limit)
            
            matches = await cursor.to_list(length=None)
            return matches
            
        except Exception as e:
            print(f"❌ Erreur récupération matches CV: {e}")
            return []

    async def get_matches_for_job(self, job_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Récupérer les matches pour une offre"""
        try:
            cursor = self.database[self.matches_collection].find(
                {"job_id": job_id}
            ).sort("score", -1).limit(limit)
            
            matches = await cursor.to_list(length=None)
            return matches
            
        except Exception as e:
            print(f"❌ Erreur récupération matches offre: {e}")
            return []

    # --- CRUD Operations for Interviews ---
    async def save_interview(self, interview_data: Dict[str, Any]) -> str:
        """Sauvegarder un entretien"""
        try:
            interview_data["created_at"] = datetime.utcnow()
            
            result = await self.database[self.interviews_collection].insert_one(interview_data)
            return str(result.inserted_id)
            
        except Exception as e:
            print(f"❌ Erreur sauvegarde entretien: {e}")
            raise

    async def get_interview_by_id(self, interview_id: str) -> Optional[Dict[str, Any]]:
        """Récupérer un entretien par ID"""
        try:
            interview = await self.database[self.interviews_collection].find_one({"_id": interview_id})
            return interview
            
        except Exception as e:
            print(f"❌ Erreur récupération entretien: {e}")
            return None

    async def get_interviews_by_candidate(self, candidate_id: str) -> List[Dict[str, Any]]:
        """Récupérer les entretiens d'un candidat"""
        try:
            cursor = self.database[self.interviews_collection].find(
                {"candidate_id": candidate_id}
            ).sort("created_at", -1)
            
            interviews = await cursor.to_list(length=None)
            return interviews
            
        except Exception as e:
            print(f"❌ Erreur récupération entretiens candidat: {e}")
            return []

    # --- Analytics Operations ---
    async def save_analytics_event(self, event_data: Dict[str, Any]) -> str:
        """Sauvegarder un événement analytics"""
        try:
            event_data["timestamp"] = datetime.utcnow()
            
            result = await self.database[self.analytics_collection].insert_one(event_data)
            return str(result.inserted_id)
            
        except Exception as e:
            print(f"❌ Erreur sauvegarde analytics: {e}")
            raise

    async def get_analytics_events(self, event_type: str = None, 
                                time_range: int = 30) -> List[Dict[str, Any]]:
        """Récupérer les événements analytics"""
        try:
            from datetime import timedelta
            
            start_date = datetime.utcnow() - timedelta(days=time_range)
            
            filter_query = {"timestamp": {"$gte": start_date}}
            if event_type:
                filter_query["event_type"] = event_type
            
            cursor = self.database[self.analytics_collection].find(filter_query).sort("timestamp", -1)
            events = await cursor.to_list(length=None)
            return events
            
        except Exception as e:
            print(f"❌ Erreur récupération analytics: {e}")
            return []

    # --- Statistics Operations ---
    async def get_database_stats(self) -> Dict[str, Any]:
        """Obtenir les statistiques de la base de données"""
        try:
            stats = {}
            
            # Compter les documents dans chaque collection
            stats["users_count"] = await self.database[self.users_collection].count_documents({})
            stats["cvs_count"] = await self.database[self.cvs_collection].count_documents({})
            stats["jobs_count"] = await self.database[self.jobs_collection].count_documents({})
            stats["matches_count"] = await self.database[self.matches_collection].count_documents({})
            stats["interviews_count"] = await self.database[self.interviews_collection].count_documents({})
            stats["analytics_events_count"] = await self.database[self.analytics_collection].count_documents({})
            
            # Statistiques récentes (7 derniers jours)
            from datetime import timedelta
            recent_date = datetime.utcnow() - timedelta(days=7)
            
            stats["recent_matches"] = await self.database[self.matches_collection].count_documents({
                "created_at": {"$gte": recent_date}
            })
            stats["recent_interviews"] = await self.database[self.interviews_collection].count_documents({
                "created_at": {"$gte": recent_date}
            })
            
            return stats
            
        except Exception as e:
            print(f"❌ Erreur statistiques base: {e}")
            return {}

# Instance globale du gestionnaire de base de données
db_manager = DatabaseManager()
