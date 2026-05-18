import random
from typing import Dict, List, Any, Optional
from datetime import datetime

class InterviewAI:
    def __init__(self):
        """Initialiser le système d'interview AI"""
        # Base de questions par catégorie
        self.question_bank = {
            'technical': {
                'programming': [
                    {
                        'question': 'Expliquez le concept de programmation orientée objet et donnez un exemple pratique.',
                        'keywords': ['objet', 'classe', 'héritage', 'polymorphisme', 'encapsulation'],
                        'difficulty': 'medium',
                        'time_limit': 180
                    },
                    {
                        'question': 'Comment gérez-vous les erreurs et exceptions dans votre code ?',
                        'keywords': ['erreur', 'exception', 'try-catch', 'debugging', 'logging'],
                        'difficulty': 'medium',
                        'time_limit': 120
                    },
                    {
                        'question': 'Décrivez votre expérience avec les bases de données relationnelles.',
                        'keywords': ['sql', 'database', 'relationnel', 'requete', 'index'],
                        'difficulty': 'medium',
                        'time_limit': 150
                    }
                ],
                'web_development': [
                    {
                        'question': 'Quelles sont les meilleures pratiques pour optimiser les performances d\'une application web ?',
                        'keywords': ['performance', 'optimisation', 'cache', 'lazy loading', 'compression'],
                        'difficulty': 'medium',
                        'time_limit': 180
                    },
                    {
                        'question': 'Comment assurez-vous la sécurité d\'une application web ?',
                        'keywords': ['sécurité', 'authentification', 'autorisation', 'https', 'xss', 'csrf'],
                        'difficulty': 'hard',
                        'time_limit': 200
                    }
                ],
                'algorithms': [
                    {
                        'question': 'Expliquez la différence entre complexité temporelle et spatiale.',
                        'keywords': ['complexité', 'temporel', 'spatial', 'big-o', 'algorithme'],
                        'difficulty': 'medium',
                        'time_limit': 120
                    },
                    {
                        'question': 'Comment aborderiez-vous la résolution d\'un problème algorithmique complexe ?',
                        'keywords': ['algorithme', 'résolution', 'approche', 'optimisation', 'structure'],
                        'difficulty': 'hard',
                        'time_limit': 180
                    }
                ]
            },
            'behavioral': [
                {
                    'question': 'Décrivez une situation où vous avez dû gérer un conflit au sein d\'une équipe.',
                    'keywords': ['conflit', 'équipe', 'communication', 'résolution', 'collaboration'],
                    'difficulty': 'medium',
                    'time_limit': 150
                },
                {
                    'question': 'Parlez-moi d\'un projet dont vous êtes particulièrement fier et pourquoi.',
                    'keywords': ['projet', 'fier', 'réalisation', 'impact', 'apprentissage'],
                    'difficulty': 'easy',
                    'time_limit': 180
                },
                {
                    'question': 'Comment gérez-vous les délais serrés et la pression au travail ?',
                    'keywords': ['délai', 'pression', 'prioritisation', 'stress', 'organisation'],
                    'difficulty': 'medium',
                    'time_limit': 120
                },
                {
                    'question': 'Quelle approche adoptez-vous pour apprendre une nouvelle technologie ?',
                    'keywords': ['apprentissage', 'technologie', 'méthodologie', 'documentation', 'pratique'],
                    'difficulty': 'easy',
                    'time_limit': 120
                }
            ],
            'situational': [
                {
                    'question': 'Si vous découvriez une erreur critique dans le code d\'un collègue, comment réagiriez-vous ?',
                    'keywords': ['erreur', 'collègue', 'communication', 'professionnalisme', 'solution'],
                    'difficulty': 'medium',
                    'time_limit': 150
                },
                {
                    'question': 'Un client change les exigences du projet en dernière minute. Que faites-vous ?',
                    'keywords': ['client', 'exigences', 'changement', 'adaptation', 'négociation'],
                    'difficulty': 'hard',
                    'time_limit': 180
                },
                {
                    'question': 'Comment aborderiez-vous la refonte d\'un système legacy complexe ?',
                    'keywords': ['refonte', 'legacy', 'migration', 'planification', 'risques'],
                    'difficulty': 'hard',
                    'time_limit': 200
                }
            ],
            'experience': [
                {
                    'question': 'Quelle a été votre plus grande réussite professionnelle et qu\'avez-vous appris ?',
                    'keywords': ['réussite', 'professionnel', 'apprentissage', 'croissance', 'leçons'],
                    'difficulty': 'medium',
                    'time_limit': 180
                },
                {
                    'question': 'Décrivez votre expérience dans la gestion de projets ou d\'équipes.',
                    'keywords': ['gestion', 'projet', 'équipe', 'leadership', 'coordination'],
                    'difficulty': 'medium',
                    'time_limit': 150
                }
            ]
        }
        
        # Critères d'évaluation
        self.evaluation_criteria = {
            'technical_accuracy': 0.3,      # Précision technique
            'communication': 0.25,           # Clarté de communication
            'problem_solving': 0.25,         # Capacité de résolution
            'relevance': 0.2                 # Pertinence de la réponse
        }

    def generate_interview_questions(self, job_description: Dict[str, Any], cv_data: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Générer des questions d'entretien personnalisées selon le poste et le CV
        
        Args:
            job_description: Description du poste
            cv_data: Données du CV du candidat
            
        Returns:
            Dictionnaire avec les questions générées
        """
        try:
            job_title = job_description.get('title', '').lower()
            job_skills = job_description.get('skills', [])
            experience_level = job_description.get('experience_level', 'mid_level')
            
            # Déterminer les catégories de questions pertinentes
            categories = self._determine_question_categories(job_title, job_skills, experience_level)
            
            # Générer les questions
            questions = []
            question_id = 1
            
            # Questions techniques (adaptées au poste)
            technical_questions = self._generate_technical_questions(job_title, job_skills, cv_data)
            for q in technical_questions[:4]:  # Max 4 questions techniques
                questions.append({
                    'id': question_id,
                    'type': 'technical',
                    'question': q['question'],
                    'keywords': q['keywords'],
                    'difficulty': q['difficulty'],
                    'time_limit': q['time_limit'],
                    'category': q.get('category', 'general')
                })
                question_id += 1
            
            # Questions comportementales
            behavioral_questions = random.sample(self.question_bank['behavioral'], min(3, len(self.question_bank['behavioral'])))
            for q in behavioral_questions:
                questions.append({
                    'id': question_id,
                    'type': 'behavioral',
                    'question': q['question'],
                    'keywords': q['keywords'],
                    'difficulty': q['difficulty'],
                    'time_limit': q['time_limit'],
                    'category': 'behavioral'
                })
                question_id += 1
            
            # Questions situationnelles
            situational_questions = random.sample(self.question_bank['situational'], min(2, len(self.question_bank['situational'])))
            for q in situational_questions:
                questions.append({
                    'id': question_id,
                    'type': 'situational',
                    'question': q['question'],
                    'keywords': q['keywords'],
                    'difficulty': q['difficulty'],
                    'time_limit': q['time_limit'],
                    'category': 'situational'
                })
                question_id += 1
            
            # Question d'expérience
            experience_questions = random.sample(self.question_bank['experience'], min(1, len(self.question_bank['experience'])))
            for q in experience_questions:
                questions.append({
                    'id': question_id,
                    'type': 'experience',
                    'question': q['question'],
                    'keywords': q['keywords'],
                    'difficulty': q['difficulty'],
                    'time_limit': q['time_limit'],
                    'category': 'experience'
                })
                question_id += 1
            
            # Mélanger les questions (sauf la première technique)
            if len(questions) > 1:
                first_question = questions[0]
                remaining_questions = questions[1:]
                random.shuffle(remaining_questions)
                questions = [first_question] + remaining_questions
            
            # Calculer la durée totale
            total_duration = sum(q['time_limit'] for q in questions)
            
            return {
                'job_title': job_description.get('title'),
                'experience_level': experience_level,
                'questions': questions,
                'total_questions': len(questions),
                'total_duration': total_duration,
                'estimated_duration_minutes': total_duration // 60,
                'instructions': self._generate_interview_instructions(experience_level),
                'generated_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            raise Exception(f"Erreur génération questions: {str(e)}")

    def analyze_answer(self, question: Dict[str, Any], answer: str, response_time: Optional[int] = None) -> Dict[str, Any]:
        """
        Analyser la réponse d'un candidat à une question
        
        Args:
            question: Question posée
            answer: Réponse du candidat
            response_time: Temps de réponse en secondes (optionnel)
            
        Returns:
            Dictionnaire avec l'analyse de la réponse
        """
        try:
            # Nettoyer la réponse
            clean_answer = self._clean_text(answer)
            
            # Analyser les différents aspects
            technical_score = self._analyze_technical_content(question, clean_answer)
            communication_score = self._analyze_communication_quality(clean_answer)
            problem_solving_score = self._analyze_problem_solving(question, clean_answer)
            relevance_score = self._analyze_relevance(question, clean_answer)
            
            # Calculer le score global
            overall_score = (
                technical_score * self.evaluation_criteria['technical_accuracy'] +
                communication_score * self.evaluation_criteria['communication'] +
                problem_solving_score * self.evaluation_criteria['problem_solving'] +
                relevance_score * self.evaluation_criteria['relevance']
            )
            
            # Analyser les mots-clés trouvés
            found_keywords = self._find_keywords(question['keywords'], clean_answer)
            
            # Générer du feedback
            feedback = self._generate_feedback(overall_score, question['type'], found_keywords)
            
            # Vérifier le temps de réponse
            time_analysis = None
            if response_time and 'time_limit' in question:
                time_ratio = response_time / question['time_limit']
                time_analysis = {
                    'response_time': response_time,
                    'time_limit': question['time_limit'],
                    'time_usage_ratio': time_ratio,
                    'time_rating': self._rate_time_usage(time_ratio)
                }
            
            return {
                'question_id': question['id'],
                'question_type': question['type'],
                'overall_score': round(overall_score, 1),
                'technical_score': round(technical_score, 1),
                'communication_score': round(communication_score, 1),
                'problem_solving_score': round(problem_solving_score, 1),
                'relevance_score': round(relevance_score, 1),
                'found_keywords': found_keywords,
                'missing_keywords': [kw for kw in question['keywords'] if kw not in found_keywords],
                'feedback': feedback,
                'time_analysis': time_analysis,
                'answer_length': len(clean_answer),
                'analyzed_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            raise Exception(f"Erreur analyse réponse: {str(e)}")

    def generate_interview_summary(self, answers_analyses: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Générer un résumé complet de l'entretien
        
        Args:
            answers_analyses: Liste des analyses de réponses
            
        Returns:
            Résumé complet de l'entretien
        """
        try:
            if not answers_analyses:
                return {'error': 'Aucune analyse à résumer'}
            
            # Calculer les scores moyens
            avg_scores = {
                'overall': sum(a['overall_score'] for a in answers_analyses) / len(answers_analyses),
                'technical': sum(a['technical_score'] for a in answers_analyses) / len(answers_analyses),
                'communication': sum(a['communication_score'] for a in answers_analyses) / len(answers_analyses),
                'problem_solving': sum(a['problem_solving_score'] for a in answers_analyses) / len(answers_analyses),
                'relevance': sum(a['relevance_score'] for a in answers_analyses) / len(answers_analyses)
            }
            
            # Analyser les performances par type de question
            performance_by_type = {}
            for analysis in answers_analyses:
                q_type = analysis['question_type']
                if q_type not in performance_by_type:
                    performance_by_type[q_type] = []
                performance_by_type[q_type].append(analysis['overall_score'])
            
            # Calculer les moyennes par type
            avg_by_type = {}
            for q_type, scores in performance_by_type.items():
                avg_by_type[q_type] = sum(scores) / len(scores)
            
            # Identifier les forces et faiblesses
            strengths = []
            weaknesses = []
            
            for criterion, score in avg_scores.items():
                if criterion != 'overall':
                    if score >= 7.5:
                        strengths.append(f"Excellent en {criterion} ({score:.1f}/10)")
                    elif score >= 6.0:
                        strengths.append(f"Bon en {criterion} ({score:.1f}/10)")
                    elif score < 5.0:
                        weaknesses.append(f"À améliorer en {criterion} ({score:.1f}/10)")
            
            # Générer la recommandation finale
            recommendation = self._generate_final_recommendation(avg_scores['overall'], avg_by_type)
            
            # Analyser les tendances
            trends = self._analyze_trends(answers_analyses)
            
            return {
                'overall_score': round(avg_scores['overall'], 1),
                'detailed_scores': {k: round(v, 1) for k, v in avg_scores.items()},
                'performance_by_type': {k: round(v, 1) for k, v in avg_by_type.items()},
                'strengths': strengths,
                'weaknesses': weaknesses,
                'recommendation': recommendation,
                'trends': trends,
                'total_questions': len(answers_analyses),
                'interview_date': datetime.now().isoformat(),
                'next_steps': self._suggest_next_steps(avg_scores['overall'])
            }
            
        except Exception as e:
            raise Exception(f"Erreur génération résumé: {str(e)}")

    def _determine_question_categories(self, job_title: str, job_skills: List[str], experience_level: str) -> List[str]:
        """Déterminer les catégories de questions pertinentes"""
        categories = ['technical', 'behavioral', 'situational']
        
        # Adapter selon le niveau d'expérience
        if experience_level in ['entry_level', 'junior']:
            categories.append('experience')  # Moins d'expérience, plus de questions sur le potentiel
        elif experience_level in ['senior', 'lead', 'manager']:
            categories.extend(['leadership', 'architecture'])  # Plus senior, plus de questions sur leadership
        
        # Adapter selon le type de poste
        if any(keyword in job_title for keyword in ['manager', 'lead', 'director']):
            categories.append('leadership')
        
        return categories

    def _generate_technical_questions(self, job_title: str, job_skills: List[str], cv_data: Optional[Dict]) -> List[Dict[str, Any]]:
        """Générer des questions techniques personnalisées"""
        questions = []
        
        # Questions basées sur les compétences requises
        for skill in job_skills[:3]:  # Limiter à 3 compétences
            skill_lower = skill.lower()
            
            if any(keyword in skill_lower for keyword in ['python', 'java', 'javascript', 'react', 'node']):
                questions.append({
                    'question': f'Décrivez votre expérience avec {skill} et les projets où vous l\'avez utilisé.',
                    'keywords': [skill.lower(), 'expérience', 'projet', 'implémentation'],
                    'difficulty': 'medium',
                    'time_limit': 150,
                    'category': 'skill_specific'
                })
            elif any(keyword in skill_lower for keyword in ['database', 'sql', 'mongodb']):
                questions.append({
                    'question': f'Quelle est votre approche pour concevoir et optimiser des bases de données ?',
                    'keywords': ['database', 'conception', 'optimisation', 'performance'],
                    'difficulty': 'medium',
                    'time_limit': 180,
                    'category': 'database'
                })
        
        # Questions génériques si pas assez de questions spécifiques
        if len(questions) < 2:
            questions.extend([
                {
                    'question': 'Comment assurez-vous la qualité et la maintenabilité de votre code ?',
                    'keywords': ['qualité', 'maintenabilité', 'code review', 'tests', 'documentation'],
                    'difficulty': 'medium',
                    'time_limit': 150,
                    'category': 'best_practices'
                },
                {
                    'question': 'Quelles méthodologies de développement avez-vous utilisées ?',
                    'keywords': ['méthodologie', 'agile', 'scrum', 'waterfall', 'devops'],
                    'difficulty': 'easy',
                    'time_limit': 120,
                    'category': 'methodology'
                }
            ])
        
        return questions

    def _generate_interview_instructions(self, experience_level: str) -> str:
        """Générer les instructions pour l'entretien"""
        instructions = {
            'entry_level': 'Prenez votre temps pour répondre clairement. Nous valorisons la pensée logique et la volonté d\'apprendre.',
            'junior': 'Montrez votre compréhension des concepts fondamentaux et votre enthousiasme pour apprendre.',
            'mid_level': 'Démontrez votre expérience pratique et votre capacité à résoudre des problèmes de manière autonome.',
            'senior': 'Partagez votre expertise technique et votre vision architecturale.',
            'lead': 'Expliquez comment vous guidez les équipes et prenez des décisions techniques importantes.',
            'manager': 'Focus sur le leadership, la stratégie et la gestion d\'équipe.'
        }
        
        return instructions.get(experience_level, instructions['mid_level'])

    def _clean_text(self, text: str) -> str:
        """Nettoyer le texte pour l'analyse"""
        return text.strip().lower()

    def _analyze_technical_content(self, question: Dict[str, Any], answer: str) -> float:
        """Analyser le contenu technique de la réponse"""
        if question['type'] != 'technical':
            return 5.0  # Score neutre pour les questions non techniques
        
        # Compter les mots-clés techniques trouvés
        keyword_count = len([kw for kw in question['keywords'] if kw in answer])
        keyword_ratio = keyword_count / len(question['keywords']) if question['keywords'] else 0
        
        # Évaluer la longueur et la structure
        length_score = min(len(answer) / 100, 5)  # Max 5 points pour la longueur
        
        # Score technique combiné
        technical_score = (keyword_ratio * 5) + length_score
        
        return min(technical_score, 10)

    def _analyze_communication_quality(self, answer: str) -> float:
        """Analyser la qualité de communication"""
        score = 5.0  # Score de base
        
        # Structure de la réponse
        if any(indicator in answer for indicator in ['premièrement', 'deuxièmement', 'enfin', 'conclusion']):
            score += 1
        
        # Clarté (longueur appropriée)
        if 50 <= len(answer) <= 500:
            score += 1
        elif len(answer) > 500:
            score += 0.5
        
        # Grammaire et orthographe (simplifié)
        if not any(error in answer for error in ['...', '??', '!!!']):
            score += 1
        
        return min(score, 10)

    def _analyze_problem_solving(self, question: Dict[str, Any], answer: str) -> float:
        """Analyser la capacité de résolution de problèmes"""
        score = 5.0  # Score de base
        
        # Indicateurs de démarche structurée
        problem_solving_indicators = [
            'analyse', 'problème', 'solution', 'approche', 'méthode',
            'étapes', 'processus', 'résultat', 'amélioration'
        ]
        
        indicator_count = sum(1 for indicator in problem_solving_indicators if indicator in answer)
        score += min(indicator_count * 0.5, 3)
        
        # Exemples concrets
        if any(example in answer for example in ['par exemple', 'exemple', 'concrètement', 'cas']):
            score += 1
        
        return min(score, 10)

    def _analyze_relevance(self, question: Dict[str, Any], answer: str) -> float:
        """Analyser la pertinence de la réponse par rapport à la question"""
        # Simplification : vérifier si les mots-clés de la question sont présents
        question_words = question['question'].lower().split()
        answer_words = answer.split()
        
        common_words = set(question_words) & set(answer_words)
        relevance_ratio = len(common_words) / len(question_words) if question_words else 0
        
        # Score de pertinence
        relevance_score = 5.0 + (relevance_ratio * 5)
        
        return min(relevance_score, 10)

    def _find_keywords(self, keywords: List[str], text: str) -> List[str]:
        """Trouver les mots-clés dans le texte"""
        found = []
        for keyword in keywords:
            if keyword.lower() in text:
                found.append(keyword)
        return found

    def _generate_feedback(self, score: float, question_type: str, found_keywords: List[str]) -> str:
        """Générer du feedback pour la réponse"""
        if score >= 8.0:
            return "Excellente réponse ! Très complète et pertinente."
        elif score >= 6.5:
            return "Bonne réponse avec des points pertinents."
        elif score >= 5.0:
            return "Réponse correcte mais pourrait être plus détaillée."
        else:
            return "Réponse incomplète. Essayez d'être plus spécifique."

    def _rate_time_usage(self, ratio: float) -> str:
        """Évaluer l'utilisation du temps"""
        if ratio <= 0.5:
            return "Très rapide"
        elif ratio <= 0.8:
            return "Bon rythme"
        elif ratio <= 1.0:
            return "Temps bien utilisé"
        else:
            return "Temps dépassé"

    def _generate_final_recommendation(self, overall_score: float, performance_by_type: Dict[str, float]) -> str:
        """Générer la recommandation finale"""
        if overall_score >= 8.0:
            return "Candidat excellent - Fortement recommandé pour le poste"
        elif overall_score >= 6.5:
            return "Bon candidat - Recommandé avec quelques points à surveiller"
        elif overall_score >= 5.0:
            return "Candidat moyen - À considérer avec évaluation complémentaire"
        else:
            return "Candidat faible - Non recommandé pour le poste actuel"

    def _analyze_trends(self, answers_analyses: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyser les tendances dans les réponses"""
        trends = {
            'average_response_length': sum(a['answer_length'] for a in answers_analyses) / len(answers_analyses),
            'consistency': self._calculate_consistency(answers_analyses),
            'improvement_areas': []
        }
        
        # Identifier les domaines d'amélioration
        scores_by_type = {}
        for analysis in answers_analyses:
            q_type = analysis['question_type']
            if q_type not in scores_by_type:
                scores_by_type[q_type] = []
            scores_by_type[q_type].append(analysis['overall_score'])
        
        for q_type, scores in scores_by_type.items():
            avg_score = sum(scores) / len(scores)
            if avg_score < 6.0:
                trends['improvement_areas'].append(f"{q_type} (score: {avg_score:.1f})")
        
        return trends

    def _calculate_consistency(self, answers_analyses: List[Dict[str, Any]]) -> float:
        """Calculer la cohérence des réponses"""
        if len(answers_analyses) < 2:
            return 1.0
        
        scores = [a['overall_score'] for a in answers_analyses]
        mean_score = sum(scores) / len(scores)
        
        # Calculer l'écart-type
        variance = sum((s - mean_score) ** 2 for s in scores) / len(scores)
        std_dev = variance ** 0.5
        
        # Cohérence inverse de l'écart-type
        consistency = max(0, 1 - (std_dev / 10))
        
        return consistency

    def _suggest_next_steps(self, overall_score: float) -> List[str]:
        """Suggérer les prochaines étapes"""
        if overall_score >= 8.0:
            return [
                "Passer à l'entretien technique avec l'équipe",
                "Vérifier les références",
                "Préparer une offre"
            ]
        elif overall_score >= 6.5:
            return [
                "Entretien technique complémentaire",
                "Test pratique",
                "Évaluation par un senior"
            ]
        elif overall_score >= 5.0:
            return [
                "Mettre en attente",
                "Considérer pour d'autres postes",
                "Retour constructif au candidat"
            ]
        else:
            return [
                "Rejeter la candidature",
                "Considérer pour un poste plus junior",
                "Fournir du feedback détaillé"
            ]
