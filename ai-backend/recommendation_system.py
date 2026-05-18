import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import json

class RecommendationSystem:
    def __init__(self):
        """Initialiser le système de recommandation"""
        # Poids pour différents facteurs de recommandation
        self.recommendation_weights = {
            'matching_score': 0.4,      # 40% pour le score de matching
            'experience_fit': 0.2,       # 20% pour l'adéquation expérience
            'skills_relevance': 0.2,     # 20% pour la pertinence des compétences
            'education_match': 0.1,       # 10% pour le matching éducation
            'location_preference': 0.1      # 10% pour la préférence de localisation
        }
        
        # Seuils de recommandation
        self.thresholds = {
            'highly_recommended': 8.5,
            'recommended': 7.0,
            'consider': 6.0,
            'maybe': 5.0
        }

    def recommend_candidates_for_job(self, candidates: List[Dict[str, Any]], 
                                 job_description: Dict[str, Any],
                                 limit: int = 10) -> Dict[str, Any]:
        """
        Recommander des candidats pour une offre d'emploi
        
        Args:
            candidates: Liste des candidats avec leurs données
            job_description: Description de l'offre
            limit: Nombre maximum de recommandations
            
        Returns:
            Dictionnaire avec les recommandations
        """
        try:
            recommendations = []
            
            for candidate in candidates:
                # Calculer le score de recommandation
                rec_score = self._calculate_candidate_recommendation_score(
                    candidate, job_description
                )
                
                # Déterminer la catégorie de recommandation
                category = self._categorize_recommendation(rec_score['overall_score'])
                
                # Créer l'objet recommandation
                recommendation = {
                    'candidate_id': candidate.get('id'),
                    'candidate_name': candidate.get('name', 'Candidat Anonyme'),
                    'candidate_email': candidate.get('email', ''),
                    'overall_score': rec_score['overall_score'],
                    'recommendation_score': rec_score['recommendation_score'],
                    'category': category,
                    'breakdown': rec_score['breakdown'],
                    'strengths': rec_score['strengths'],
                    'weaknesses': rec_score['weaknesses'],
                    'matched_skills': rec_score['matched_skills'],
                    'missing_skills': rec_score['missing_skills'],
                    'recommendation_reason': self._generate_recommendation_reason(rec_score, category),
                    'next_steps': self._suggest_candidate_next_steps(rec_score['overall_score'], category)
                }
                
                recommendations.append(recommendation)
            
            # Trier par score de recommandation
            recommendations.sort(key=lambda x: x['recommendation_score'], reverse=True)
            
            # Limiter le nombre de résultats
            recommendations = recommendations[:limit]
            
            # Analyser les tendances
            trends = self._analyze_recommendation_trends(recommendations)
            
            return {
                'job_title': job_description.get('title'),
                'job_id': job_description.get('id'),
                'recommendations': recommendations,
                'total_candidates': len(candidates),
                'recommended_count': len(recommendations),
                'trends': trends,
                'generated_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            raise Exception(f"Erreur recommandation candidats: {str(e)}")

    def recommend_jobs_for_candidate(self, candidate: Dict[str, Any], 
                                  jobs: List[Dict[str, Any]], 
                                  limit: int = 10) -> Dict[str, Any]:
        """
        Recommander des offres d'emploi pour un candidat
        
        Args:
            candidate: Données du candidat
            jobs: Liste des offres d'emploi
            limit: Nombre maximum de recommandations
            
        Returns:
            Dictionnaire avec les recommandations
        """
        try:
            recommendations = []
            
            for job in jobs:
                # Calculer le score de matching
                match_score = self._calculate_job_candidate_match(candidate, job)
                
                # Calculer le score de recommandation
                rec_score = self._calculate_job_recommendation_score(candidate, job, match_score)
                
                # Déterminer la catégorie
                category = self._categorize_recommendation(rec_score['overall_score'])
                
                # Créer l'objet recommandation
                recommendation = {
                    'job_id': job.get('id'),
                    'job_title': job.get('title'),
                    'company': job.get('company', {}).get('name', 'Entreprise'),
                    'location': job.get('location', 'Remote'),
                    'experience_level': job.get('experience_level'),
                    'overall_score': rec_score['overall_score'],
                    'recommendation_score': rec_score['recommendation_score'],
                    'category': category,
                    'breakdown': rec_score['breakdown'],
                    'matched_skills': rec_score['matched_skills'],
                    'missing_skills': rec_score['missing_skills'],
                    'salary_range': {
                        'min': job.get('salary_min'),
                        'max': job.get('salary_max'),
                        'currency': job.get('currency', 'EUR')
                    },
                    'recommendation_reason': self._generate_job_recommendation_reason(rec_score, category),
                    'application_suggestions': self._suggest_application_steps(rec_score['overall_score'])
                }
                
                recommendations.append(recommendation)
            
            # Trier par score de recommandation
            recommendations.sort(key=lambda x: x['recommendation_score'], reverse=True)
            
            # Limiter les résultats
            recommendations = recommendations[:limit]
            
            # Analyser les tendances
            trends = self._analyze_job_recommendation_trends(recommendations)
            
            return {
                'candidate_name': candidate.get('name', 'Candidat'),
                'recommendations': recommendations,
                'total_jobs': len(jobs),
                'recommended_count': len(recommendations),
                'trends': trends,
                'generated_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            raise Exception(f"Erreur recommandation emplois: {str(e)}")

    def get_similar_candidates(self, target_candidate: Dict[str, Any], 
                            candidates: List[Dict[str, Any]], 
                            limit: int = 5) -> Dict[str, Any]:
        """
        Trouver des candidats similaires à un candidat cible
        
        Args:
            target_candidate: Candidat de référence
            candidates: Liste des autres candidats
            limit: Nombre maximum de résultats
            
        Returns:
            Candidats similaires avec scores de similarité
        """
        try:
            similarities = []
            
            for candidate in candidates:
                if candidate.get('id') == target_candidate.get('id'):
                    continue  # Ignorer le candidat cible
                
                # Calculer la similarité
                similarity_score = self._calculate_candidate_similarity(target_candidate, candidate)
                
                similarity = {
                    'candidate_id': candidate.get('id'),
                    'candidate_name': candidate.get('name'),
                    'similarity_score': similarity_score['overall_similarity'],
                    'breakdown': similarity_score['breakdown'],
                    'common_skills': similarity_score['common_skills'],
                    'similarity_reason': self._generate_similarity_reason(similarity_score)
                }
                
                similarities.append(similarity)
            
            # Trier par similarité
            similarities.sort(key=lambda x: x['similarity_score'], reverse=True)
            
            return {
                'target_candidate': target_candidate.get('name'),
                'similar_candidates': similarities[:limit],
                'total_compared': len(candidates),
                'generated_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            raise Exception(f"Erreur recherche candidats similaires: {str(e)}")

    def optimize_matching_algorithm(self, historical_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Optimiser l'algorithme de matching basé sur les données historiques
        
        Args:
            historical_data: Données historiques de matching
            
        Returns:
            Recommandations d'optimisation
        """
        try:
            if len(historical_data) < 10:
                return {'error': 'Pas assez de données pour l\'optimisation'}
            
            # Analyser les performances historiques
            performance_analysis = self._analyze_historical_performance(historical_data)
            
            # Identifier les tendances
            trends = self._identify_performance_trends(historical_data)
            
            # Générer des recommandations d'optimisation
            optimizations = self._generate_optimization_recommendations(performance_analysis, trends)
            
            return {
                'performance_analysis': performance_analysis,
                'trends': trends,
                'optimizations': optimizations,
                'data_points': len(historical_data),
                'analysis_date': datetime.now().isoformat()
            }
            
        except Exception as e:
            raise Exception(f"Erreur optimisation algorithme: {str(e)}")

    def _calculate_candidate_recommendation_score(self, candidate: Dict[str, Any], 
                                           job_description: Dict[str, Any]) -> Dict[str, Any]:
        """Calculer le score de recommandation pour un candidat"""
        
        # Score de matching (déjà calculé ou à calculer)
        if 'matching_score' in candidate:
            matching_score = candidate['matching_score']
        else:
            # Simulation de calcul de matching
            matching_score = np.random.uniform(4.0, 9.5)
        
        # Score d'adéquation expérience
        experience_score = self._calculate_experience_fit(candidate, job_description)
        
        # Score de pertinence des compétences
        skills_score = self._calculate_skills_relevance(candidate, job_description)
        
        # Score d'éducation
        education_score = self._calculate_education_match(candidate, job_description)
        
        # Score de localisation
        location_score = self._calculate_location_preference(candidate, job_description)
        
        # Score de recommandation pondéré
        recommendation_score = (
            matching_score * self.recommendation_weights['matching_score'] +
            experience_score * self.recommendation_weights['experience_fit'] +
            skills_score * self.recommendation_weights['skills_relevance'] +
            education_score * self.recommendation_weights['education_match'] +
            location_score * self.recommendation_weights['location_preference']
        )
        
        # Identifier forces et faiblesses
        breakdown = {
            'matching_score': matching_score,
            'experience_fit': experience_score,
            'skills_relevance': skills_score,
            'education_match': education_score,
            'location_preference': location_score
        }
        
        strengths = []
        weaknesses = []
        
        for criterion, score in breakdown.items():
            if score >= 7.5:
                strengths.append(f"Excellent en {criterion}")
            elif score >= 6.0:
                strengths.append(f"Bon en {criterion}")
            elif score < 5.0:
                weaknesses.append(f"À améliorer en {criterion}")
        
        return {
            'overall_score': recommendation_score,
            'recommendation_score': recommendation_score,  # Même valeur pour compatibilité
            'breakdown': breakdown,
            'strengths': strengths,
            'weaknesses': weaknesses,
            'matched_skills': candidate.get('skills', [])[:5],  # Top 5 compétences
            'missing_skills': []  # À calculer basé sur les exigences du poste
        }

    def _calculate_job_candidate_match(self, candidate: Dict[str, Any], 
                                   job: Dict[str, Any]) -> Dict[str, Any]:
        """Calculer le matching entre candidat et offre"""
        # Simulation de calcul de matching
        return {
            'overall_score': np.random.uniform(4.0, 9.5),
            'matched_skills': [],
            'missing_skills': []
        }

    def _calculate_job_recommendation_score(self, candidate: Dict[str, Any], 
                                        job: Dict[str, Any], 
                                        match_score: Dict[str, Any]) -> Dict[str, Any]:
        """Calculer le score de recommandation pour une offre"""
        
        # Facteurs additionnels pour les recommandations d'emplois
        career_alignment = self._calculate_career_alignment(candidate, job)
        growth_potential = self._calculate_growth_potential(candidate, job)
        salary_alignment = self._calculate_salary_alignment(candidate, job)
        
        # Score pondéré
        recommendation_score = (
            match_score['overall_score'] * 0.5 +
            career_alignment * 0.2 +
            growth_potential * 0.2 +
            salary_alignment * 0.1
        )
        
        return {
            'overall_score': recommendation_score,
            'recommendation_score': recommendation_score,
            'breakdown': {
                'job_match': match_score['overall_score'],
                'career_alignment': career_alignment,
                'growth_potential': growth_potential,
                'salary_alignment': salary_alignment
            },
            'matched_skills': match_score.get('matched_skills', []),
            'missing_skills': match_score.get('missing_skills', [])
        }

    def _calculate_candidate_similarity(self, candidate1: Dict[str, Any], 
                                   candidate2: Dict[str, Any]) -> Dict[str, Any]:
        """Calculer la similarité entre deux candidats"""
        
        # Similarité des compétences
        skills1 = set(candidate1.get('skills', []))
        skills2 = set(candidate2.get('skills', []))
        
        if len(skills1) == 0 and len(skills2) == 0:
            skills_similarity = 1.0
        elif len(skills1) == 0 or len(skills2) == 0:
            skills_similarity = 0.0
        else:
            common_skills = skills1 & skills2
            skills_similarity = len(common_skills) / len(skills1 | skills2)
        
        # Similarité d'expérience
        exp1 = candidate1.get('experience_years', 0)
        exp2 = candidate2.get('experience_years', 0)
        
        max_exp = max(exp1, exp2)
        exp_similarity = 1.0 - (abs(exp1 - exp2) / max_exp) if max_exp > 0 else 1.0
        
        # Similarité d'éducation
        edu1 = candidate1.get('education_level', 0)
        edu2 = candidate2.get('education_level', 0)
        
        edu_similarity = 1.0 - abs(edu1 - edu2) / 5  # 5 niveaux max
        
        # Score de similarité global
        overall_similarity = (skills_similarity * 0.5 + exp_similarity * 0.3 + edu_similarity * 0.2)
        
        return {
            'overall_similarity': overall_similarity,
            'breakdown': {
                'skills_similarity': skills_similarity,
                'experience_similarity': exp_similarity,
                'education_similarity': edu_similarity
            },
            'common_skills': list(skills1 & skills2)
        }

    def _calculate_experience_fit(self, candidate: Dict[str, Any], job: Dict[str, Any]) -> float:
        """Calculer l'adéquation d'expérience"""
        candidate_exp = candidate.get('experience_years', 0)
        job_level = job.get('experience_level', 'mid_level')
        
        # Mapping des niveaux
        level_requirements = {
            'entry_level': 0,
            'junior': 2,
            'mid_level': 4,
            'senior': 6,
            'lead': 8,
            'manager': 10
        }
        
        required_exp = level_requirements.get(job_level, 4)
        
        if candidate_exp >= required_exp:
            return min(10, 10 - (candidate_exp - required_exp) * 0.1)
        else:
            return max(0, candidate_exp / required_exp * 10)

    def _calculate_skills_relevance(self, candidate: Dict[str, Any], job: Dict[str, Any]) -> float:
        """Calculer la pertinence des compétences"""
        candidate_skills = set(candidate.get('skills', []))
        job_skills = set(job.get('required_skills', []))
        
        if len(job_skills) == 0:
            return 5.0  # Score neutre
        
        common_skills = candidate_skills & job_skills
        relevance = len(common_skills) / len(job_skills)
        
        return relevance * 10

    def _calculate_education_match(self, candidate: Dict[str, Any], job: Dict[str, Any]) -> float:
        """Calculer le matching d'éducation"""
        candidate_edu = candidate.get('education_level', 0)
        required_edu = job.get('education_requirement', 2)  # Bachelor par défaut
        
        if candidate_edu >= required_edu:
            return 10.0
        else:
            return (candidate_edu / required_edu) * 10

    def _calculate_location_preference(self, candidate: Dict[str, Any], job: Dict[str, Any]) -> float:
        """Calculer la préférence de localisation"""
        candidate_location = candidate.get('location', '').lower()
        job_location = job.get('location', '').lower()
        
        if job_location == 'remote' or candidate_location == 'remote':
            return 10.0
        elif candidate_location == job_location:
            return 10.0
        elif candidate_location and job_location:
            # Similarité basique de localisation
            return 5.0
        else:
            return 3.0

    def _calculate_career_alignment(self, candidate: Dict[str, Any], job: Dict[str, Any]) -> float:
        """Calculer l'alignement de carrière"""
        # Simulation basée sur les titres précédents
        candidate_titles = [t.lower() for t in candidate.get('previous_titles', [])]
        job_title = job.get('title', '').lower()
        
        if any(job_title in title for title in candidate_titles):
            return 9.0
        elif any(word in job_title for title in candidate_titles for word in title.split()):
            return 6.0
        else:
            return 3.0

    def _calculate_growth_potential(self, candidate: Dict[str, Any], job: Dict[str, Any]) -> float:
        """Calculer le potentiel de croissance"""
        # Basé sur le niveau de l'offre par rapport à l'expérience actuelle
        candidate_exp = candidate.get('experience_years', 0)
        job_level = job.get('experience_level', 'mid_level')
        
        # Potentiel de croissance si le poste est un peu au-dessus
        level_map = {'entry_level': 1, 'junior': 2, 'mid_level': 3, 'senior': 4, 'lead': 5, 'manager': 6}
        
        candidate_level = 1
        if candidate_exp >= 8:
            candidate_level = 5
        elif candidate_exp >= 5:
            candidate_level = 4
        elif candidate_exp >= 3:
            candidate_level = 3
        elif candidate_exp >= 1:
            candidate_level = 2
        
        job_level_value = level_map.get(job_level, 3)
        
        if job_level_value == candidate_level + 1:
            return 9.0  # Bon potentiel de croissance
        elif job_level_value > candidate_level:
            return 7.0  # Croissance significative
        elif job_level_value == candidate_level:
            return 6.0  # Stabilité
        else:
            return 3.0  # Pas de croissance

    def _calculate_salary_alignment(self, candidate: Dict[str, Any], job: Dict[str, Any]) -> float:
        """Calculer l'alignement salarial"""
        candidate_salary = candidate.get('current_salary', 0)
        job_salary_min = job.get('salary_min', 0)
        job_salary_max = job.get('salary_max', 0)
        
        if job_salary_min == 0:
            return 5.0  # Score neutre
        
        job_salary_avg = (job_salary_min + job_salary_max) / 2
        
        if candidate_salary >= job_salary_min and candidate_salary <= job_salary_max:
            return 10.0  # Parfait alignement
        elif candidate_salary < job_salary_min:
            ratio = candidate_salary / job_salary_min
            return ratio * 10
        else:
            ratio = job_salary_max / candidate_salary
            return ratio * 10

    def _categorize_recommendation(self, score: float) -> str:
        """Catégoriser la recommandation"""
        if score >= self.thresholds['highly_recommended']:
            return 'highly_recommended'
        elif score >= self.thresholds['recommended']:
            return 'recommended'
        elif score >= self.thresholds['consider']:
            return 'consider'
        elif score >= self.thresholds['maybe']:
            return 'maybe'
        else:
            return 'not_recommended'

    def _generate_recommendation_reason(self, rec_score: Dict[str, Any], category: str) -> str:
        """Générer la raison de recommandation"""
        reasons = {
            'highly_recommended': "Excellent profil avec forte correspondance aux exigences du poste",
            'recommended': "Bon profil avec de bonnes correspondances",
            'consider': "Profil intéressant avec quelques points à vérifier",
            'maybe': "Profil à considérer avec évaluation complémentaire",
            'not_recommended': "Profil ne correspondant pas aux exigences"
        }
        
        base_reason = reasons.get(category, "Profil à évaluer")
        
        # Ajouter des détails spécifiques
        details = []
        if rec_score['breakdown']['matching_score'] >= 8.0:
            details.append("excellent matching technique")
        if rec_score['breakdown']['experience_fit'] >= 7.0:
            details.append("expérience pertinente")
        
        if details:
            return f"{base_reason} ({', '.join(details)})"
        else:
            return base_reason

    def _generate_job_recommendation_reason(self, rec_score: Dict[str, Any], category: str) -> str:
        """Générer la raison de recommandation d'emploi"""
        reasons = {
            'highly_recommended': "Opportunité excellente correspondant parfaitement à votre profil",
            'recommended': "Bonne opportunité avec de fortes correspondances",
            'consider': "Opportunité intéressante à explorer",
            'maybe': "Opportunité possible avec quelques ajustements",
            'not_recommended': "Opportunité ne correspondant pas à votre profil"
        }
        
        return reasons.get(category, "Opportunité à évaluer")

    def _suggest_candidate_next_steps(self, score: float, category: str) -> List[str]:
        """Suggérer les prochaines étapes pour un candidat"""
        if category == 'highly_recommended':
            return ["Contacter immédiatement", "Planifier entretien technique", "Préparer offre"]
        elif category == 'recommended':
            return ["Contacter sous 48h", "Planifier entretien", "Vérifier références"]
        elif category == 'consider':
            return ["Demander documentation complémentaire", "Entretien téléphonique", "Test technique"]
        elif category == 'maybe':
            return ["Mettre en liste d'attente", "Revoir ultérieurement", "Considérer pour autre poste"]
        else:
            return ["Archiver la candidature", "Rejeter poliment", "Garder en contact"]

    def _suggest_application_steps(self, score: float) -> List[str]:
        """Suggérer les étapes de candidature"""
        if score >= 8.0:
            return ["Postuler immédiatement", "Personnaliser la lettre", "Contacter recruteur"]
        elif score >= 6.5:
            return ["Postuler avec lettre personnalisée", "Mettre en avant compétences clés", "Préparer entretien"]
        elif score >= 5.0:
            return ["Postuler en explorant l'opportunité", "Développer compétences manquantes", "Réseau professionnel"]
        else:
            return ["Évaluer pertinence", "Développer compétences", "Chercher alternatives"]

    def _generate_similarity_reason(self, similarity_score: Dict[str, Any]) -> str:
        """Générer la raison de similarité"""
        overall = similarity_score['overall_similarity']
        
        if overall >= 0.8:
            return "Très similaire avec profils comparables"
        elif overall >= 0.6:
            return "Similaire avec quelques différences"
        elif overall >= 0.4:
            return "Partiellement similaire"
        else:
            return "Peu similaire"

    def _analyze_recommendation_trends(self, recommendations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyser les tendances des recommandations"""
        if not recommendations:
            return {}
        
        # Distribution des catégories
        categories = [r['category'] for r in recommendations]
        category_counts = {}
        for cat in categories:
            category_counts[cat] = category_counts.get(cat, 0) + 1
        
        # Scores moyens
        avg_scores = [r['overall_score'] for r in recommendations]
        avg_score = sum(avg_scores) / len(avg_scores)
        
        # Compétences les plus communes
        all_skills = []
        for r in recommendations:
            all_skills.extend(r['matched_skills'])
        
        skill_counts = {}
        for skill in all_skills:
            skill_counts[skill] = skill_counts.get(skill, 0) + 1
        
        top_skills = sorted(skill_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        
        return {
            'category_distribution': category_counts,
            'average_score': round(avg_score, 2),
            'top_common_skills': top_skills,
            'total_recommendations': len(recommendations)
        }

    def _analyze_job_recommendation_trends(self, recommendations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyser les tendances des recommandations d'emplois"""
        if not recommendations:
            return {}
        
        # Distribution des niveaux d'expérience
        experience_levels = [r.get('experience_level', 'mid_level') for r in recommendations]
        level_counts = {}
        for level in experience_levels:
            level_counts[level] = level_counts.get(level, 0) + 1
        
        # Distribution des localisations
        locations = [r.get('location', 'Unknown') for r in recommendations]
        location_counts = {}
        for loc in locations:
            location_counts[loc] = location_counts.get(loc, 0) + 1
        
        # Scores moyens
        avg_scores = [r['overall_score'] for r in recommendations]
        avg_score = sum(avg_scores) / len(avg_scores)
        
        return {
            'experience_level_distribution': level_counts,
            'location_distribution': location_counts,
            'average_score': round(avg_score, 2),
            'total_recommendations': len(recommendations)
        }

    def _analyze_historical_performance(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyser les performances historiques"""
        # Taux de succès par score de matching
        score_ranges = [(0, 4), (4, 6), (6, 8), (8, 10)]
        success_rates = {}
        
        for min_score, max_score in score_ranges:
            range_data = [d for d in data if min_score <= d['matching_score'] < max_score]
            if range_data:
                success_count = sum(1 for d in range_data if d.get('hired', False))
                success_rates[f"{min_score}-{max_score}"] = success_count / len(range_data)
            else:
                success_rates[f"{min_score}-{max_score}"] = 0
        
        return {
            'success_rates_by_score_range': success_rates,
            'total_data_points': len(data),
            'overall_success_rate': sum(1 for d in data if d.get('hired', False)) / len(data)
        }

    def _identify_performance_trends(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Identifier les tendances de performance"""
        # Tendances temporelles
        data_sorted = sorted(data, key=lambda x: x.get('date', ''))
        
        # Tendance du taux de succès
        recent_data = data_sorted[-10:]  # 10 plus récents
        older_data = data_sorted[:-10] if len(data_sorted) > 10 else []
        
        recent_success = sum(1 for d in recent_data if d.get('hired', False)) / len(recent_data) if recent_data else 0
        older_success = sum(1 for d in older_data if d.get('hired', False)) / len(older_data) if older_data else 0
        
        return {
            'recent_success_rate': recent_success,
            'older_success_rate': older_success,
            'trend': 'improving' if recent_success > older_success else 'declining',
            'sample_sizes': {'recent': len(recent_data), 'older': len(older_data)}
        }

    def _generate_optimization_recommendations(self, performance: Dict[str, Any], 
                                             trends: Dict[str, Any]) -> List[str]:
        """Générer des recommandations d'optimisation"""
        recommendations = []
        
        # Basé sur les taux de succès
        success_rates = performance.get('success_rates_by_score_range', {})
        if success_rates:
            best_range = max(success_rates.keys(), key=lambda k: success_rates[k])
            worst_range = min(success_rates.keys(), key=lambda k: success_rates[k])
            
            if success_rates[best_range] > success_rates[worst_range] * 1.5:
                recommendations.append(f"Augmenter le poids des scores dans la range {best_range}")
        
        # Basé sur les tendances
        if trends.get('trend') == 'declining':
            recommendations.append("Réviser l'algorithme de matching")
        
        # Recommandations générales
        if performance.get('overall_success_rate', 0) < 0.3:
            recommendations.append("Revoir les critères d'évaluation")
        
        return recommendations
