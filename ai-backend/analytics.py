import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict, Counter
import json

class AnalyticsSystem:
    def __init__(self):
        """Initialiser le système d'analytics"""
        # Métriques par défaut
        self.metrics = {
            'total_cvs_processed': 0,
            'total_matches_calculated': 0,
            'total_interviews_conducted': 0,
            'total_recommendations_generated': 0,
            'average_matching_score': 0.0,
            'conversion_rate': 0.0
        }
        
        # Données historiques
        self.historical_data = []
        
    def track_cv_processing(self, cv_data: Dict[str, Any], processing_time: float) -> Dict[str, Any]:
        """Suivre le traitement de CV"""
        try:
            self.metrics['total_cvs_processed'] += 1
            
            # Extraire des métriques du CV
            skills_count = len(cv_data.get('skills', []))
            experience_count = len(cv_data.get('experience', []))
            education_count = len(cv_data.get('education', []))
            completeness_score = cv_data.get('completeness_score', 0)
            
            # Enregistrer l'événement
            event = {
                'event_type': 'cv_processed',
                'timestamp': datetime.now().isoformat(),
                'processing_time': processing_time,
                'metrics': {
                    'skills_count': skills_count,
                    'experience_count': experience_count,
                    'education_count': education_count,
                    'completeness_score': completeness_score
                }
            }
            
            self.historical_data.append(event)
            
            return {
                'event_id': len(self.historical_data),
                'metrics_tracked': True,
                'processing_time': processing_time,
                'cv_metrics': event['metrics']
            }
            
        except Exception as e:
            raise Exception(f"Erreur tracking CV: {str(e)}")

    def track_matching_calculation(self, cv_id: str, job_id: str, 
                                match_result: Dict[str, Any], 
                                processing_time: float) -> Dict[str, Any]:
        """Suivre le calcul de matching"""
        try:
            self.metrics['total_matches_calculated'] += 1
            
            # Mettre à jour le score moyen
            current_avg = self.metrics['average_matching_score']
            total_matches = self.metrics['total_matches_calculated']
            new_score = match_result.get('overall_score', 0)
            
            self.metrics['average_matching_score'] = (
                (current_avg * (total_matches - 1) + new_score) / total_matches
            )
            
            # Catégoriser le score
            score_category = self._categorize_score(new_score)
            
            # Enregistrer l'événement
            event = {
                'event_type': 'match_calculated',
                'timestamp': datetime.now().isoformat(),
                'processing_time': processing_time,
                'entities': {
                    'cv_id': cv_id,
                    'job_id': job_id
                },
                'metrics': {
                    'overall_score': new_score,
                    'skills_score': match_result.get('skills_score', 0),
                    'experience_score': match_result.get('experience_score', 0),
                    'education_score': match_result.get('education_score', 0),
                    'tools_score': match_result.get('tools_score', 0),
                    'score_category': score_category,
                    'matched_skills_count': len(match_result.get('matched_skills', [])),
                    'missing_skills_count': len(match_result.get('missing_skills', []))
                }
            }
            
            self.historical_data.append(event)
            
            return {
                'event_id': len(self.historical_data),
                'match_tracked': True,
                'score_category': score_category,
                'processing_time': processing_time
            }
            
        except Exception as e:
            raise Exception(f"Erreur tracking matching: {str(e)}")

    def track_interview_session(self, candidate_id: str, job_id: str,
                              interview_results: Dict[str, Any],
                              session_duration: float) -> Dict[str, Any]:
        """Suivre une session d'entretien"""
        try:
            self.metrics['total_interviews_conducted'] += 1
            
            overall_score = interview_results.get('overall_score', 0)
            recommendation = interview_results.get('recommendation', '')
            
            # Enregistrer l'événement
            event = {
                'event_type': 'interview_conducted',
                'timestamp': datetime.now().isoformat(),
                'session_duration': session_duration,
                'entities': {
                    'candidate_id': candidate_id,
                    'job_id': job_id
                },
                'metrics': {
                    'overall_score': overall_score,
                    'recommendation': recommendation,
                    'technical_score': interview_results.get('detailed_scores', {}).get('technical', 0),
                    'communication_score': interview_results.get('detailed_scores', {}).get('communication', 0),
                    'questions_count': interview_results.get('total_questions', 0),
                    'session_duration_minutes': session_duration / 60
                }
            }
            
            self.historical_data.append(event)
            
            return {
                'event_id': len(self.historical_data),
                'interview_tracked': True,
                'recommendation': recommendation,
                'session_duration_minutes': session_duration / 60
            }
            
        except Exception as e:
            raise Exception(f"Erreur tracking entretien: {str(e)}")

    def track_recommendation(self, recommendation_type: str, entities: List[str],
                          recommendation_results: Dict[str, Any]) -> Dict[str, Any]:
        """Suivre les recommandations générées"""
        try:
            self.metrics['total_recommendations_generated'] += 1
            
            # Enregistrer l'événement
            event = {
                'event_type': 'recommendation_generated',
                'timestamp': datetime.now().isoformat(),
                'entities': entities,
                'metrics': {
                    'recommendation_type': recommendation_type,
                    'total_recommendations': len(recommendation_results.get('recommendations', [])),
                    'average_score': np.mean([r.get('overall_score', 0) 
                                           for r in recommendation_results.get('recommendations', [])]) if recommendation_results.get('recommendations') else 0
                }
            }
            
            self.historical_data.append(event)
            
            return {
                'event_id': len(self.historical_data),
                'recommendation_tracked': True,
                'type': recommendation_type,
                'count': len(recommendation_results.get('recommendations', []))
            }
            
        except Exception as e:
            raise Exception(f"Erreur tracking recommandation: {str(e)}")

    def generate_performance_dashboard(self, time_range: str = '30d') -> Dict[str, Any]:
        """Générer le tableau de bord de performance"""
        try:
            # Filtrer les données selon la période
            filtered_data = self._filter_data_by_time_range(time_range)
            
            # Métriques générales
            dashboard = {
                'overview': self._generate_overview_metrics(filtered_data),
                'performance_trends': self._generate_performance_trends(filtered_data),
                'matching_analytics': self._generate_matching_analytics(filtered_data),
                'interview_analytics': self._generate_interview_analytics(filtered_data),
                'recommendation_analytics': self._generate_recommendation_analytics(filtered_data),
                'skill_trends': self._generate_skill_trends(filtered_data),
                'time_range': time_range,
                'generated_at': datetime.now().isoformat()
            }
            
            return dashboard
            
        except Exception as e:
            raise Exception(f"Erreur génération dashboard: {str(e)}")

    def generate_recruitment_funnel(self, time_range: str = '30d') -> Dict[str, Any]:
        """Générer l'analyse du funnel de recrutement"""
        try:
            filtered_data = self._filter_data_by_time_range(time_range)
            
            # Étapes du funnel
            funnel_stages = {
                'cvs_processed': 0,
                'matches_calculated': 0,
                'interviews_conducted': 0,
                'recommendations_generated': 0,
                'high_scores': 0,
                'conversions': 0  # À calculer basé sur les données
            }
            
            # Compter les événements par type
            for event in filtered_data:
                event_type = event['event_type']
                if event_type == 'cv_processed':
                    funnel_stages['cvs_processed'] += 1
                elif event_type == 'match_calculated':
                    funnel_stages['matches_calculated'] += 1
                    # Compter les scores élevés
                    if event['metrics']['overall_score'] >= 7.5:
                        funnel_stages['high_scores'] += 1
                elif event_type == 'interview_conducted':
                    funnel_stages['interviews_conducted'] += 1
                elif event_type == 'recommendation_generated':
                    funnel_stages['recommendations_generated'] += 1
            
            # Calculer les taux de conversion
            total_cv = funnel_stages['cvs_processed']
            conversion_rates = {}
            
            if total_cv > 0:
                conversion_rates['cv_to_match'] = (funnel_stages['matches_calculated'] / total_cv) * 100
                conversion_rates['match_to_interview'] = (funnel_stages['interviews_conducted'] / funnel_stages['matches_calculated']) * 100 if funnel_stages['matches_calculated'] > 0 else 0
                conversion_rates['interview_to_recommendation'] = (funnel_stages['recommendations_generated'] / funnel_stages['interviews_conducted']) * 100 if funnel_stages['interviews_conducted'] > 0 else 0
                conversion_rates['high_score_rate'] = (funnel_stages['high_scores'] / funnel_stages['matches_calculated']) * 100 if funnel_stages['matches_calculated'] > 0 else 0
            
            return {
                'funnel_stages': funnel_stages,
                'conversion_rates': conversion_rates,
                'bottlenecks': self._identify_funnel_bottlenecks(funnel_stages, conversion_rates),
                'time_range': time_range,
                'generated_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            raise Exception(f"Erreur génération funnel: {str(e)}")

    def generate_skill_demand_analysis(self, time_range: str = '30d') -> Dict[str, Any]:
        """Analyser la demande de compétences"""
        try:
            filtered_data = self._filter_data_by_time_range(time_range)
            
            # Extraire les compétences des données de matching
            all_skills = []
            job_skills = []
            missing_skills = []
            
            for event in filtered_data:
                if event['event_type'] == 'match_calculated':
                    metrics = event['metrics']
                    all_skills.extend(metrics.get('matched_skills', []))
                    missing_skills.extend(metrics.get('missing_skills', []))
            
            # Analyser les tendances de compétences
            skill_frequency = Counter(all_skills)
            missing_skill_frequency = Counter(missing_skills)
            
            # Compétences les plus demandées
            top_skills = skill_frequency.most_common(20)
            top_missing = missing_skill_frequency.most_common(20)
            
            # Catégoriser les compétences
            skill_categories = self._categorize_skills(top_skills)
            
            # Tendances temporelles
            skill_trends = self._analyze_skill_trends_over_time(filtered_data)
            
            return {
                'top_demand_skills': [{'skill': skill, 'frequency': freq, 'demand_level': self._calculate_demand_level(freq)} for skill, freq in top_skills],
                'skill_gaps': [{'skill': skill, 'gap_frequency': freq} for skill, freq in top_missing],
                'skill_categories': skill_categories,
                'trends': skill_trends,
                'total_unique_skills': len(skill_frequency),
                'time_range': time_range,
                'generated_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            raise Exception(f"Erreur analyse compétences: {str(e)}")

    def export_analytics_data(self, format_type: str = 'json', 
                           time_range: str = '30d') -> Dict[str, Any]:
        """Exporter les données analytics"""
        try:
            filtered_data = self._filter_data_by_time_range(time_range)
            
            if format_type == 'json':
                export_data = {
                    'metadata': {
                        'export_date': datetime.now().isoformat(),
                        'time_range': time_range,
                        'total_events': len(filtered_data),
                        'format': 'json'
                    },
                    'metrics': self.metrics,
                    'events': filtered_data,
                    'summary': self._generate_export_summary(filtered_data)
                }
                
                return {
                    'data': export_data,
                    'filename': f'analytics_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json',
                    'format': 'json'
                }
            
            elif format_type == 'csv':
                # Convertir en format CSV-friendly
                csv_data = []
                for event in filtered_data:
                    row = {
                        'timestamp': event['timestamp'],
                        'event_type': event['event_type'],
                        'processing_time': event.get('processing_time', 0),
                        'metrics': json.dumps(event.get('metrics', {}))
                    }
                    csv_data.append(row)
                
                return {
                    'data': csv_data,
                    'filename': f'analytics_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv',
                    'format': 'csv'
                }
            
            else:
                raise ValueError(f"Format non supporté: {format_type}")
                
        except Exception as e:
            raise Exception(f"Erreur export données: {str(e)}")

    def _categorize_score(self, score: float) -> str:
        """Catégoriser un score de matching"""
        if score >= 8.5:
            return 'excellent'
        elif score >= 7.0:
            return 'good'
        elif score >= 5.5:
            return 'average'
        elif score >= 4.0:
            return 'below_average'
        else:
            return 'poor'

    def _filter_data_by_time_range(self, time_range: str) -> List[Dict[str, Any]]:
        """Filtrer les données selon la période"""
        if not self.historical_data:
            return []
        
        # Déterminer la date de début
        now = datetime.now()
        if time_range == '7d':
            start_date = now - timedelta(days=7)
        elif time_range == '30d':
            start_date = now - timedelta(days=30)
        elif time_range == '90d':
            start_date = now - timedelta(days=90)
        elif time_range == '1y':
            start_date = now - timedelta(days=365)
        else:
            start_date = now - timedelta(days=30)  # Défaut
        
        # Filtrer les événements
        filtered = []
        for event in self.historical_data:
            event_date = datetime.fromisoformat(event['timestamp'].replace('Z', '+00:00'))
            if event_date >= start_date:
                filtered.append(event)
        
        return filtered

    def _generate_overview_metrics(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Générer les métriques d'overview"""
        if not data:
            return self.metrics
        
        # Compter les événements par type
        event_counts = Counter(event['event_type'] for event in data)
        
        # Calculer les moyennes
        processing_times = [event.get('processing_time', 0) for event in data if 'processing_time' in event]
        avg_processing_time = np.mean(processing_times) if processing_times else 0
        
        # Scores moyens par type
        match_scores = [event['metrics']['overall_score'] for event in data 
                       if event['event_type'] == 'match_calculated']
        avg_match_score = np.mean(match_scores) if match_scores else 0
        
        return {
            'total_events': len(data),
            'event_breakdown': dict(event_counts),
            'average_processing_time': round(avg_processing_time, 3),
            'average_match_score': round(avg_match_score, 2),
            'system_health': self._calculate_system_health(data)
        }

    def _generate_performance_trends(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Générer les tendances de performance"""
        # Grouper par jour
        daily_metrics = defaultdict(lambda: {'events': 0, 'avg_score': 0, 'scores': []})
        
        for event in data:
            date = event['timestamp'][:10]  # YYYY-MM-DD
            daily_metrics[date]['events'] += 1
            
            if event['event_type'] == 'match_calculated':
                score = event['metrics']['overall_score']
                daily_metrics[date]['scores'].append(score)
        
        # Calculer les moyennes quotidiennes
        trends = []
        for date, metrics in daily_metrics.items():
            avg_score = np.mean(metrics['scores']) if metrics['scores'] else 0
            trends.append({
                'date': date,
                'events_count': metrics['events'],
                'average_score': round(avg_score, 2)
            })
        
        # Trier par date
        trends.sort(key=lambda x: x['date'])
        
        return {
            'daily_trends': trends[-30:],  # 30 derniers jours
            'trend_direction': self._calculate_trend_direction([t['average_score'] for t in trends]),
            'peak_day': max(trends, key=lambda x: x['events_count']) if trends else None
        }

    def _generate_matching_analytics(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Générer les analytics de matching"""
        match_events = [event for event in data if event['event_type'] == 'match_calculated']
        
        if not match_events:
            return {'message': 'Aucune donnée de matching'}
        
        # Distribution des scores
        scores = [event['metrics']['overall_score'] for event in match_events]
        score_distribution = self._calculate_score_distribution(scores)
        
        # Scores par catégorie
        score_categories = Counter(self._categorize_score(score) for score in scores)
        
        # Compétences les plus communes
        all_matched_skills = []
        all_missing_skills = []
        
        for event in match_events:
            all_matched_skills.extend(event['metrics'].get('matched_skills', []))
            all_missing_skills.extend(event['metrics'].get('missing_skills', []))
        
        top_matched = Counter(all_matched_skills).most_common(10)
        top_missing = Counter(all_missing_skills).most_common(10)
        
        return {
            'total_matches': len(match_events),
            'score_statistics': {
                'mean': round(np.mean(scores), 2),
                'median': round(np.median(scores), 2),
                'std': round(np.std(scores), 2),
                'min': round(min(scores), 2),
                'max': round(max(scores), 2)
            },
            'score_distribution': score_distribution,
            'score_categories': dict(score_categories),
            'top_matched_skills': top_matched,
            'most_missing_skills': top_missing
        }

    def _generate_interview_analytics(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Générer les analytics d'entretien"""
        interview_events = [event for event in data if event['event_type'] == 'interview_conducted']
        
        if not interview_events:
            return {'message': 'Aucune donnée d\'entretien'}
        
        # Scores d'entretien
        overall_scores = [event['metrics']['overall_score'] for event in interview_events]
        technical_scores = [event['metrics'].get('technical_score', 0) for event in interview_events]
        communication_scores = [event['metrics'].get('communication_score', 0) for event in interview_events]
        
        # Recommandations
        recommendations = [event['metrics']['recommendation'] for event in interview_events]
        recommendation_counts = Counter(recommendations)
        
        # Durées de session
        durations = [event['metrics']['session_duration_minutes'] for event in interview_events]
        
        return {
            'total_interviews': len(interview_events),
            'score_statistics': {
                'overall_mean': round(np.mean(overall_scores), 2),
                'technical_mean': round(np.mean(technical_scores), 2),
                'communication_mean': round(np.mean(communication_scores), 2)
            },
            'recommendation_distribution': dict(recommendation_counts),
            'session_statistics': {
                'average_duration_minutes': round(np.mean(durations), 2),
                'total_interview_hours': round(sum(durations) / 60, 2)
            }
        }

    def _generate_recommendation_analytics(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Générer les analytics de recommandation"""
        recommendation_events = [event for event in data if event['event_type'] == 'recommendation_generated']
        
        if not recommendation_events:
            return {'message': 'Aucune donnée de recommandation'}
        
        # Types de recommandations
        rec_types = [event['metrics']['recommendation_type'] for event in recommendation_events]
        type_counts = Counter(rec_types)
        
        # Nombre de recommandations par événement
        rec_counts = [event['metrics']['total_recommendations'] for event in recommendation_events]
        
        return {
            'total_recommendation_events': len(recommendation_events),
            'recommendation_types': dict(type_counts),
            'statistics': {
                'avg_recommendations_per_event': round(np.mean(rec_counts), 2),
                'total_recommendations_generated': sum(rec_counts)
            }
        }

    def _generate_skill_trends(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Générer les tendances de compétences"""
        # Compétences par mois
        monthly_skills = defaultdict(lambda: Counter())
        
        for event in data:
            if event['event_type'] == 'match_calculated':
                month = event['timestamp'][:7]  # YYYY-MM
                skills = event['metrics'].get('matched_skills', [])
                monthly_skills[month].update(skills)
        
        # Identifier les tendances (croissance/déclin)
        trends = {}
        all_skills = set()
        for month_counter in monthly_skills.values():
            all_skills.update(month_counter.keys())
        
        for skill in list(all_skills)[:20]:  # Limiter aux 20 principales
            monthly_counts = [monthly_skills[month].get(skill, 0) for month in sorted(monthly_skills.keys())]
            if len(monthly_counts) > 1:
                trend = 'increasing' if monthly_counts[-1] > monthly_counts[0] else 'decreasing'
                trends[skill] = {
                    'trend': trend,
                    'frequency': sum(monthly_counts)
                }
        
        return {
            'skill_trends': trends,
            'monthly_data': {month: dict(counter) for month, counter in monthly_skills.items()}
        }

    def _identify_funnel_bottlenecks(self, stages: Dict[str, int], 
                                   rates: Dict[str, float]) -> List[str]:
        """Identifier les goulots d'étranglement dans le funnel"""
        bottlenecks = []
        
        # Taux de conversion faibles
        if rates.get('cv_to_match', 0) < 50:
            bottlenecks.append("Faible taux de conversion CV → Matching")
        
        if rates.get('match_to_interview', 0) < 30:
            bottlenecks.append("Faible taux de conversion Matching → Entretien")
        
        if rates.get('interview_to_recommendation', 0) < 60:
            bottlenecks.append("Faible taux de conversion Entretien → Recommandation")
        
        # Scores faibles
        if rates.get('high_score_rate', 0) < 25:
            bottlenecks.append("Taux de scores élevés trop faible")
        
        return bottlenecks

    def _categorize_skills(self, skills: List[Tuple[str, int]]) -> Dict[str, List[str]]:
        """Catégoriser les compétences"""
        categories = {
            'programming': [],
            'web_development': [],
            'databases': [],
            'cloud_devops': [],
            'data_science': [],
            'mobile': [],
            'tools': []
        }
        
        # Catégories simplifiées
        programming_keywords = ['python', 'java', 'javascript', 'c++', 'c#', 'php', 'ruby', 'go']
        web_keywords = ['react', 'angular', 'vue', 'html', 'css', 'node', 'django', 'flask']
        db_keywords = ['sql', 'mysql', 'postgresql', 'mongodb', 'redis']
        cloud_keywords = ['aws', 'azure', 'gcp', 'docker', 'kubernetes']
        data_keywords = ['machine learning', 'ai', 'data science', 'tensorflow', 'pytorch']
        mobile_keywords = ['android', 'ios', 'react native', 'flutter']
        tools_keywords = ['git', 'github', 'jenkins', 'jira']
        
        for skill, freq in skills:
            skill_lower = skill.lower()
            if any(keyword in skill_lower for keyword in programming_keywords):
                categories['programming'].append(skill)
            elif any(keyword in skill_lower for keyword in web_keywords):
                categories['web_development'].append(skill)
            elif any(keyword in skill_lower for keyword in db_keywords):
                categories['databases'].append(skill)
            elif any(keyword in skill_lower for keyword in cloud_keywords):
                categories['cloud_devops'].append(skill)
            elif any(keyword in skill_lower for keyword in data_keywords):
                categories['data_science'].append(skill)
            elif any(keyword in skill_lower for keyword in mobile_keywords):
                categories['mobile'].append(skill)
            elif any(keyword in skill_lower for keyword in tools_keywords):
                categories['tools'].append(skill)
        
        return categories

    def _analyze_skill_trends_over_time(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyser les tendances de compétences dans le temps"""
        # Implémentation simplifiée
        return {'trend_analysis': 'Implementé dans _generate_skill_trends'}

    def _calculate_demand_level(self, frequency: int) -> str:
        """Calculer le niveau de demande d'une compétence"""
        if frequency >= 50:
            return 'very_high'
        elif frequency >= 20:
            return 'high'
        elif frequency >= 10:
            return 'medium'
        elif frequency >= 5:
            return 'low'
        else:
            return 'very_low'

    def _calculate_score_distribution(self, scores: List[float]) -> Dict[str, int]:
        """Calculer la distribution des scores"""
        distribution = {
            '0-2': 0,
            '2-4': 0,
            '4-6': 0,
            '6-8': 0,
            '8-10': 0
        }
        
        for score in scores:
            if score < 2:
                distribution['0-2'] += 1
            elif score < 4:
                distribution['2-4'] += 1
            elif score < 6:
                distribution['4-6'] += 1
            elif score < 8:
                distribution['6-8'] += 1
            else:
                distribution['8-10'] += 1
        
        return distribution

    def _calculate_system_health(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculer la santé du système"""
        if not data:
            return {'status': 'no_data'}
        
        # Temps de traitement moyen
        processing_times = [event.get('processing_time', 0) for event in data if 'processing_time' in event]
        avg_processing_time = np.mean(processing_times) if processing_times else 0
        
        # Taux d'erreurs (simplifié)
        error_events = [event for event in data if 'error' in event.get('metrics', {})]
        error_rate = len(error_events) / len(data) if data else 0
        
        # Score de santé
        health_score = 100
        if avg_processing_time > 5.0:  # 5 secondes
            health_score -= 20
        if error_rate > 0.05:  # 5% d'erreurs
            health_score -= 30
        
        status = 'excellent'
        if health_score < 70:
            status = 'good'
        if health_score < 50:
            status = 'poor'
        
        return {
            'status': status,
            'health_score': health_score,
            'average_processing_time': round(avg_processing_time, 3),
            'error_rate': round(error_rate * 100, 2)
        }

    def _calculate_trend_direction(self, values: List[float]) -> str:
        """Calculer la direction de tendance"""
        if len(values) < 2:
            return 'stable'
        
        recent_avg = np.mean(values[-5:]) if len(values) >= 5 else np.mean(values)
        older_avg = np.mean(values[:5]) if len(values) >= 5 else np.mean(values[:len(values)//2])
        
        if recent_avg > older_avg * 1.1:
            return 'increasing'
        elif recent_avg < older_avg * 0.9:
            return 'decreasing'
        else:
            return 'stable'

    def _generate_export_summary(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Générer le résumé pour l'export"""
        event_types = Counter(event['event_type'] for event in data)
        
        return {
            'total_events': len(data),
            'event_types': dict(event_types),
            'date_range': {
                'start': min(event['timestamp'] for event in data) if data else None,
                'end': max(event['timestamp'] for event in data) if data else None
            }
        }
