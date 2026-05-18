import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import MinMaxScaler
import re
import nltk
from typing import Dict, List, Any, Optional
from collections import Counter

class AI_Matcher:
    def __init__(self):
        """Initialiser le moteur de matching IA"""
        # Initialiser le vectorizer TF-IDF
        self.tfidf_vectorizer = TfidfVectorizer(
            max_features=5000,
            stop_words='english',
            ngram_range=(1, 2),  # Unigrammes et bigrammes
            min_df=1,
            max_df=0.8
        )
        
        # Poids pour chaque catégorie de score
        self.weights = {
            'skills': 0.35,      # 35% pour les compétences
            'experience': 0.25,   # 25% pour l'expérience
            'education': 0.20,    # 20% pour l'éducation
            'tools': 0.20         # 20% pour les outils/technologies
        }
        
        # Compétences par catégorie
        self.skill_categories = {
            'programming': [
                'python', 'java', 'javascript', 'c++', 'c#', 'php', 'ruby', 'go', 'rust', 'swift', 'kotlin',
                'typescript', 'scala', 'perl', 'r', 'matlab', 'dart', 'objective-c', 'lua', 'haskell'
            ],
            'web_development': [
                'html', 'css', 'react', 'angular', 'vue.js', 'node.js', 'express', 'django', 'flask', 'spring',
                'laravel', 'rails', 'next.js', 'gatsby', 'nuxt.js', 'svelte', 'bootstrap', 'tailwind', 'webpack'
            ],
            'databases': [
                'sql', 'nosql', 'mysql', 'postgresql', 'mongodb', 'redis', 'elasticsearch', 'cassandra',
                'sqlite', 'oracle', 'sql server', 'firebase', 'supabase', 'dynamodb', 'neo4j', 'influxdb'
            ],
            'cloud_devops': [
                'aws', 'azure', 'gcp', 'docker', 'kubernetes', 'terraform', 'ansible', 'jenkins', 'gitlab',
                'circleci', 'travis ci', 'github actions', 'heroku', 'digitalocean', 'vagrant', 'packer'
            ],
            'data_science': [
                'machine learning', 'data science', 'ai', 'deep learning', 'nlp', 'computer vision',
                'tensorflow', 'pytorch', 'scikit-learn', 'pandas', 'numpy', 'spark', 'hadoop', 'tableau'
            ],
            'mobile': [
                'android', 'ios', 'react native', 'flutter', 'swift', 'kotlin', 'objective-c', 'xamarin',
                'cordova', 'ionic', 'unity', 'xcode', 'android studio'
            ],
            'tools': [
                'git', 'github', 'gitlab', 'bitbucket', 'jira', 'confluence', 'slack', 'trello', 'asana',
                'vs code', 'intellij', 'eclipse', 'vim', 'emacs', 'postman', 'swagger', 'api'
            ]
        }
        
        # Niveaux d'expérience
        self.experience_levels = {
            'entry_level': 0,
            'junior': 1,
            'mid_level': 2,
            'senior': 3,
            'lead': 4,
            'manager': 5
        }
        
        # Types de diplômes
        self.education_weights = {
            'phd': 1.0,
            'master': 0.9,
            'bachelor': 0.8,
            'licence': 0.8,
            'certificat': 0.6,
            'bootcamp': 0.5,
            'autodidacte': 0.3
        }

    def calculate_match(self, cv_text: str, job_description: Dict[str, Any], cv_data: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Calculer le score de matching global entre CV et offre d'emploi
        
        Args:
            cv_text: Texte complet du CV
            job_description: Dictionnaire avec description de l'offre
            cv_data: Données structurées du CV (optionnel)
            
        Returns:
            Dictionnaire avec scores détaillés
        """
        try:
            # Extraire les informations de l'offre
            job_title = job_description.get('title', '')
            job_description_text = job_description.get('description', '')
            job_requirements = job_description.get('requirements', '')
            job_skills = job_description.get('skills', [])
            job_experience_level = job_description.get('experience_level', 'mid_level')
            job_location = job_description.get('location', '')
            
            # Combiner le texte de l'offre pour l'analyse
            full_job_text = f"{job_title} {job_description_text} {job_requirements} {' '.join(job_skills)}"
            
            # Calculer les scores individuels
            skills_score, matched_skills, missing_skills = self._calculate_skills_score(cv_text, job_skills, cv_data)
            experience_score = self._calculate_experience_score(cv_text, job_experience_level, cv_data)
            education_score = self._calculate_education_score(cv_text, cv_data)
            tools_score = self._calculate_tools_score(cv_text, cv_data)
            
            # Calculer le score global avec TF-IDF
            semantic_score = self._calculate_semantic_similarity(cv_text, full_job_text)
            
            # Score final pondéré
            overall_score = (
                skills_score * self.weights['skills'] +
                experience_score * self.weights['experience'] +
                education_score * self.weights['education'] +
                tools_score * self.weights['tools'] +
                semantic_score * 0.1  # Bonus de similarité sémantique
            )
            
            # Générer des recommandations
            recommendations = self._generate_recommendations(
                skills_score, experience_score, education_score, tools_score,
                matched_skills, missing_skills, cv_data
            )
            
            return {
                'overall_score': min(round(overall_score, 1), 100),
                'skills_score': round(skills_score, 1),
                'experience_score': round(experience_score, 1),
                'education_score': round(education_score, 1),
                'tools_score': round(tools_score, 1),
                'semantic_score': round(semantic_score, 1),
                'matched_skills': matched_skills,
                'missing_skills': missing_skills,
                'recommendations': recommendations
            }
            
        except Exception as e:
            raise Exception(f"Erreur calcul matching: {str(e)}")

    def _calculate_skills_score(self, cv_text: str, job_skills: List[str], cv_data: Optional[Dict] = None) -> tuple:
        """Calculer le score de matching des compétences"""
        cv_text_lower = cv_text.lower()
        
        # Extraire les compétences du CV
        if cv_data and 'skills' in cv_data:
            cv_skills = [skill.lower() for skill in cv_data['skills']]
        else:
            cv_skills = self._extract_skills_from_text(cv_text)
        
        # Normaliser les compétences de l'offre
        job_skills_normalized = [skill.lower() for skill in job_skills]
        
        # Calculer le matching
        matched_skills = []
        missing_skills = []
        
        for job_skill in job_skills_normalized:
            # Vérifier si la compétence est présente
            found = False
            for cv_skill in cv_skills:
                if job_skill in cv_skill or cv_skill in job_skill:
                    matched_skills.append(job_skill)
                    found = True
                    break
            
            if not found:
                missing_skills.append(job_skill)
        
        # Calculer le score
        if len(job_skills) == 0:
            return 50, [], []  # Score neutre si pas de compétences requises
        
        score = (len(matched_skills) / len(job_skills)) * 100
        
        return score, matched_skills, missing_skills

    def _calculate_experience_score(self, cv_text: str, job_experience_level: str, cv_data: Optional[Dict] = None) -> float:
        """Calculer le score basé sur l'expérience"""
        target_level = self.experience_levels.get(job_experience_level.lower(), 2)
        
        # Extraire les années d'expérience
        if cv_data and 'experience' in cv_data:
            years_experience = self._extract_years_from_experience(cv_data['experience'])
        else:
            years_experience = self._extract_years_from_text(cv_text)
        
        # Calculer le score basé sur les années d'expérience
        if years_experience >= 10:
            candidate_level = 5  # Manager/Lead
        elif years_experience >= 7:
            candidate_level = 4  # Lead
        elif years_experience >= 5:
            candidate_level = 3  # Senior
        elif years_experience >= 3:
            candidate_level = 2  # Mid-level
        elif years_experience >= 1:
            candidate_level = 1  # Junior
        else:
            candidate_level = 0  # Entry-level
        
        # Calculer le score de matching
        level_diff = abs(candidate_level - target_level)
        if level_diff == 0:
            return 100
        elif level_diff == 1:
            return 80
        elif level_diff == 2:
            return 60
        else:
            return max(40 - (level_diff - 2) * 10, 20)

    def _calculate_education_score(self, cv_text: str, cv_data: Optional[Dict] = None) -> float:
        """Calculer le score basé sur l'éducation"""
        # Extraire l'éducation
        if cv_data and 'education' in cv_data:
            education_list = cv_data['education']
        else:
            education_list = self._extract_education_from_text(cv_text)
        
        if not education_list:
            return 30  # Score faible si pas d'éducation mentionnée
        
        # Calculer le score basé sur le plus haut diplôme
        max_score = 0
        for edu in education_list:
            edu_text = str(edu).lower()
            edu_score = 30  # Score de base
            
            for degree, weight in self.education_weights.items():
                if degree in edu_text:
                    edu_score = weight * 100
                    break
            
            max_score = max(max_score, edu_score)
        
        return max_score

    def _calculate_tools_score(self, cv_text: str, cv_data: Optional[Dict] = None) -> float:
        """Calculer le score basé sur les outils et technologies"""
        cv_text_lower = cv_text.lower()
        
        # Liste d'outils courants
        tools = [
            'git', 'github', 'gitlab', 'docker', 'kubernetes', 'jenkins', 'aws', 'azure', 'gcp',
            'jira', 'confluence', 'slack', 'vs code', 'intellij', 'postman', 'swagger',
            'webpack', 'npm', 'yarn', 'linux', 'ubuntu', 'windows', 'macos'
        ]
        
        found_tools = 0
        for tool in tools:
            if tool in cv_text_lower:
                found_tools += 1
        
        # Score basé sur le nombre d'outils trouvés
        score = (found_tools / len(tools)) * 100
        return min(score, 100)

    def _calculate_semantic_similarity(self, cv_text: str, job_text: str) -> float:
        """Calculer la similarité sémantique avec TF-IDF et cosine similarity"""
        try:
            # Préparer les documents
            documents = [cv_text, job_text]
            
            # Vectorizer TF-IDF
            tfidf_matrix = self.tfidf_vectorizer.fit_transform(documents)
            
            # Calculer la similarité cosinus
            similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
            
            # Convertir en score sur 100
            return similarity * 100
            
        except Exception as e:
            print(f"Erreur similarité sémantique: {e}")
            return 50  # Score par défaut

    def _extract_skills_from_text(self, text: str) -> List[str]:
        """Extraire les compétences du texte"""
        skills = set()
        text_lower = text.lower()
        
        # Extraire de toutes les catégories
        for category, skill_list in self.skill_categories.items():
            for skill in skill_list:
                if skill in text_lower:
                    skills.add(skill)
        
        return list(skills)

    def _extract_years_from_experience(self, experience_list: List[Dict]) -> int:
        """Extraire le nombre total d'années d'expérience"""
        total_years = 0
        
        for exp in experience_list:
            if isinstance(exp, dict):
                # Chercher des patterns de dates
                description = str(exp.get('description', '')).lower()
                years = self._extract_years_from_text(description)
                total_years = max(total_years, years)
        
        return total_years

    def _extract_years_from_text(self, text: str) -> int:
        """Extraire les années d'expérience du texte"""
        text_lower = text.lower()
        
        # Patterns pour les années d'expérience
        patterns = [
            r'(\d+)\s*(?:years?|ans?)\s*(?:of\s*)?(?:experience|exp[ée]rience)',
            r'(\d+)\s*(?:\+|plus)\s*(?:years?|ans?)',
            r'experience\s*(?:of\s*)?(\d+)\s*(?:years?|ans?)',
            r'exp[ée]rience\s*(?:de\s*)?(\d+)\s*(?:ans?|years?)',
        ]
        
        max_years = 0
        for pattern in patterns:
            matches = re.findall(pattern, text_lower)
            for match in matches:
                try:
                    years = int(match)
                    max_years = max(max_years, years)
                except ValueError:
                    continue
        
        return max_years

    def _extract_education_from_text(self, text: str) -> List[str]:
        """Extraire l'éducation du texte"""
        education = []
        text_lower = text.lower()
        
        # Patterns pour les diplômes
        patterns = [
            r'(phd|doctorat|ph\.d)\.?\s*(?:in\s*)?([^.]+)',
            r'(master|master\'s|m\.sc|m\.s)\.?\s*(?:in\s*)?([^.]+)',
            r'(bachelor|bachelor\'s|b\.sc|b\.s)\.?\s*(?:in\s*)?([^.]+)',
            r'(licence|license)\s*(?:en\s*)?([^.]+)',
            r'(certificat|certificate|certification)\s*(?:in\s*)?([^.]+)'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text_lower)
            for match in matches:
                if isinstance(match, tuple):
                    degree = match[0]
                    field = match[1] if len(match) > 1 else ""
                    education.append(f"{degree} in {field}")
                else:
                    education.append(match)
        
        return education

    def _generate_recommendations(self, skills_score: float, experience_score: float, 
                                education_score: float, tools_score: float,
                                matched_skills: List[str], missing_skills: List[str],
                                cv_data: Optional[Dict] = None) -> List[str]:
        """Générer des recommandations pour améliorer le matching"""
        recommendations = []
        
        # Recommandations basées sur les scores
        if skills_score < 70:
            recommendations.append(f"Développer les compétences manquantes: {', '.join(missing_skills[:3])}")
        
        if experience_score < 70:
            recommendations.append("Acquérir plus d'expérience pertinente dans le domaine")
        
        if education_score < 60:
            recommendations.append("Considérer une formation ou certification supplémentaire")
        
        if tools_score < 70:
            recommendations.append("Se familiariser avec les outils et technologies courants")
        
        # Recommandations basées sur les compétences
        if len(matched_skills) >= 3:
            recommendations.append("Excellent matching des compétences techniques")
        
        # Recommandations spécifiques
        if cv_data and 'skills' in cv_data:
            cv_skills = cv_data['skills']
            if len(cv_skills) < 5:
                recommendations.append("Ajouter plus de compétences techniques dans le CV")
        
        # Recommandations générales
        if skills_score > 80 and experience_score > 80:
            recommendations.append("Profil très pertinent pour ce poste")
        elif skills_score > 60 and experience_score > 60:
            recommendations.append("Bon profil, avec quelques améliorations possibles")
        
        return recommendations[:5]  # Limiter à 5 recommandations

    def get_common_skills(self) -> List[str]:
        """Retourner la liste des compétences communes"""
        all_skills = []
        for category_skills in self.skill_categories.values():
            all_skills.extend(category_skills)
        return sorted(all_skills)

    def get_skill_categories(self) -> Dict[str, List[str]]:
        """Retourner les catégories de compétences"""
        return self.skill_categories
