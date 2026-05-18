import PyPDF2
import pdfplumber
import re
import nltk
from typing import Dict, List, Any, Optional
from io import BytesIO
import spacy

# Télécharger les modèles NLTK nécessaires (une seule fois)
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords')

class CVParser:
    def __init__(self):
        """Initialiser le parser de CV"""
        # Charger le modèle spaCy pour le NLP (si disponible)
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            print("Modèle spaCy non trouvé, utilisation du traitement basique")
            self.nlp = None
        
        # Patterns pour extraire les informations
        self.email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        self.phone_pattern = r'(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'
        self.linkedin_pattern = r'linkedin\.com/in/[\w-]+'
        
        # Sections communes dans les CV
        self.section_patterns = {
            'experience': [
                r'(?:experience|exp[ée]rience|work\s+history|professional\s+experience)',
                r'(?:emploi|carri[èe]re|parcours)',
                r'(?:professional\s+background|career\s+summary)'
            ],
            'education': [
                r'(?:education|formation|dipl[ôo]me)',
                r'(?:academic|university|college)',
                r'(?:études|scolarit[ée])'
            ],
            'skills': [
                r'(?:skills|comp[ée]tences|abilities)',
                r'(?:technical\s+skills|technologies)',
                r'(?:langages|outils|software)'
            ]
        }
        
        # Liste de compétences techniques communes
        self.technical_skills = [
            'python', 'java', 'javascript', 'react', 'node.js', 'angular', 'vue.js',
            'html', 'css', 'sql', 'nosql', 'mongodb', 'postgresql', 'mysql',
            'docker', 'kubernetes', 'aws', 'azure', 'gcp', 'git', 'ci/cd',
            'machine learning', 'data science', 'ai', 'deep learning', 'nlp',
            'tensorflow', 'pytorch', 'scikit-learn', 'pandas', 'numpy',
            'c++', 'c#', '.net', 'php', 'ruby', 'swift', 'kotlin',
            'linux', 'ubuntu', 'windows', 'macos', 'bash', 'powershell',
            'rest api', 'graphql', 'microservices', 'devops', 'agile'
        ]

    def parse_cv(self, file_content: bytes, filename: str) -> Dict[str, Any]:
        """
        Parser un fichier CV et extraire les informations
        
        Args:
            file_content: Contenu du fichier en bytes
            filename: Nom du fichier
            
        Returns:
            Dictionnaire contenant les informations parsées
        """
        try:
            # Extraire le texte du fichier
            text = self._extract_text(file_content, filename)
            
            if not text or len(text.strip()) < 50:
                raise ValueError("Le fichier ne contient pas assez de texte")
            
            # Nettoyer le texte
            cleaned_text = self._clean_text(text)
            
            # Extraire les informations
            parsed_data = {
                'text': cleaned_text,
                'skills': self._extract_skills(cleaned_text),
                'experience': self._extract_experience(cleaned_text),
                'education': self._extract_education(cleaned_text),
                'contact_info': self._extract_contact_info(cleaned_text),
                'completeness_score': self._calculate_completeness(cleaned_text)
            }
            
            return parsed_data
            
        except Exception as e:
            raise Exception(f"Erreur lors du parsing du CV: {str(e)}")

    def _extract_text(self, file_content: bytes, filename: str) -> str:
        """Extraire le texte du fichier PDF ou DOCX"""
        try:
            if filename.lower().endswith('.pdf'):
                return self._extract_from_pdf(file_content)
            elif filename.lower().endswith('.docx'):
                return self._extract_from_docx(file_content)
            else:
                raise ValueError("Format de fichier non supporté")
        except Exception as e:
            raise Exception(f"Erreur extraction texte: {str(e)}")

    def _extract_from_pdf(self, file_content: bytes) -> str:
        """Extraire le texte d'un fichier PDF"""
        text = ""
        
        # Essayer d'abord avec pdfplumber (meilleur pour les tableaux)
        try:
            with pdfplumber.open(BytesIO(file_content)) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
        except Exception as e:
            print(f"pdfplumber a échoué: {e}")
        
        # Si pdfplumber échoue, utiliser PyPDF2
        if not text.strip():
            try:
                pdf_reader = PyPDF2.PdfReader(BytesIO(file_content))
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
            except Exception as e:
                print(f"PyPDF2 a échoué: {e}")
        
        return text

    def _extract_from_docx(self, file_content: bytes) -> str:
        """Extraire le texte d'un fichier DOCX (placeholder)"""
        # Pour l'instant, retourner un message
        # En production, installer python-docx et implémenter
        return "DOCX parsing non implémenté - utilisez PDF"

    def _clean_text(self, text: str) -> str:
        """Nettoyer et normaliser le texte"""
        # Supprimer les caractères spéciaux excessifs
        text = re.sub(r'[^\w\s@.-]', ' ', text)
        
        # Normaliser les espaces
        text = re.sub(r'\s+', ' ', text)
        
        # Supprimer les lignes vides
        text = '\n'.join(line.strip() for line in text.split('\n') if line.strip())
        
        return text.strip()

    def _extract_skills(self, text: str) -> List[str]:
        """Extraire les compétences du texte"""
        found_skills = set()
        text_lower = text.lower()
        
        # Rechercher les compétences techniques
        for skill in self.technical_skills:
            if skill in text_lower:
                found_skills.add(skill)
        
        # Utiliser spaCy si disponible pour une meilleure extraction
        if self.nlp:
            doc = self.nlp(text_lower)
            # Extraire les noms propres et les entités
            for ent in doc.ents:
                if ent.label_ in ['ORG', 'PRODUCT', 'PERSON']:
                    found_skills.add(ent.text.lower())
        
        # Rechercher des patterns spécifiques
        # Frameworks et technologies
        framework_patterns = [
            r'\breact\b', r'\bangular\b', r'\bvue\b', r'\bdjango\b', r'\bflask\b',
            r'\bspring\b', r'\blaravel\b', r'\bexpress\b', r'\bfastapi\b'
        ]
        
        for pattern in framework_patterns:
            matches = re.findall(pattern, text_lower)
            found_skills.update(matches)
        
        # Bases de données
        db_patterns = [
            r'\bmongodb\b', r'\bpostgresql\b', r'\bmysql\b', r'\bsqlite\b',
            r'\bredis\b', r'\belasticsearch\b', r'\bcassandra\b'
        ]
        
        for pattern in db_patterns:
            matches = re.findall(pattern, text_lower)
            found_skills.update(matches)
        
        # Cloud et DevOps
        cloud_patterns = [
            r'\baws\b', r'\bazure\b', r'\bgcp\b', r'\bdocker\b', r'\bkubernetes\b',
            r'\bterraform\b', r'\bjenkins\b', r'\bgitlab\b', r'\bcircleci\b'
        ]
        
        for pattern in cloud_patterns:
            matches = re.findall(pattern, text_lower)
            found_skills.update(matches)
        
        return sorted(list(found_skills))

    def _extract_experience(self, text: str) -> List[Dict[str, Any]]:
        """Extraire l'expérience professionnelle"""
        experiences = []
        
        # Pattern pour détecter les expériences
        exp_patterns = [
            r'(\d{4}\s*-\s*(?:\d{4}|present))\s*[:\-]\s*(.+?)(?=\n\d{4}|\n[A-Z]|\Z)',
            r'(\d{1,2}/\d{4}\s*-\s*(?:\d{1,2}/\d{4}|present))\s*[:\-]\s*(.+?)(?=\n\d|\n[A-Z]|\Z)',
            r'([A-Z][a-z]+\s+\d{4}\s*-\s*(?:[A-Z][a-z]+\s+\d{4}|present))\s*[:\-]\s*(.+?)(?=\n[A-Z]|\Z)'
        ]
        
        for pattern in exp_patterns:
            matches = re.findall(pattern, text, re.MULTILINE | re.DOTALL)
            for match in matches:
                if len(match) >= 2:
                    period = match[0].strip()
                    description = match[1].strip()
                    
                    # Extraire le titre et l'entreprise
                    lines = description.split('\n')[:3]  # Prendre les 3 premières lignes
                    title = lines[0] if lines else ""
                    company = lines[1] if len(lines) > 1 else ""
                    
                    # Nettoyer
                    title = re.sub(r'^[\W]+', '', title).strip()
                    company = re.sub(r'^[\W]+', '', company).strip()
                    
                    if title and len(title) > 3:
                        experiences.append({
                            'period': period,
                            'title': title,
                            'company': company,
                            'description': description[:200]  # Limiter la description
                        })
        
        return experiences[:5]  # Limiter à 5 expériences

    def _extract_education(self, text: str) -> List[Dict[str, Any]]:
        """Extraire la formation académique"""
        education = []
        
        # Patterns pour détecter l'éducation
        edu_patterns = [
            r'(\d{4}\s*-\s*\d{4})\s*[:\-]\s*(.+?)(?=\n\d{4}|\n[A-Z]|\Z)',
            r'(?:dipl[ôo]me|certificat|master|bachelor|licence|phd|doctorat)\s*[:\-]?\s*(.+?)(?=\n|\Z)',
            r'([A-Z][^,\n]*(?:university|universit[ée]|school|école|institute|institut)[^,\n]*)',
        ]
        
        for pattern in edu_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE | re.MULTILINE | re.DOTALL)
            for match in matches:
                if isinstance(match, tuple):
                    match = match[0] if match[0] else match[1]
                
                match = match.strip()
                if len(match) > 10:  # Éviter les trop courts
                    # Détecter le type de diplôme
                    degree_type = "Autre"
                    if any(word in match.lower() for word in ['master', 'm.sc']):
                        degree_type = "Master"
                    elif any(word in match.lower() for word in ['bachelor', 'b.sc', 'licence']):
                        degree_type = "Bachelor/Licence"
                    elif any(word in match.lower() for word in ['phd', 'doctorat', 'ph.d']):
                        degree_type = "PhD/Doctorat"
                    elif any(word in match.lower() for word in ['certificat', 'certificate']):
                        degree_type = "Certificat"
                    
                    education.append({
                        'degree': degree_type,
                        'description': match[:150]  # Limiter la description
                    })
        
        return education[:3]  # Limiter à 3 formations

    def _extract_contact_info(self, text: str) -> Dict[str, str]:
        """Extraire les informations de contact"""
        contact_info = {}
        
        # Extraire l'email
        emails = re.findall(self.email_pattern, text)
        if emails:
            contact_info['email'] = emails[0]
        
        # Extraire le téléphone
        phones = re.findall(self.phone_pattern, text)
        if phones:
            contact_info['phone'] = phones[0]
        
        # Extraire LinkedIn
        linkedin_urls = re.findall(self.linkedin_pattern, text)
        if linkedin_urls:
            contact_info['linkedin'] = f"https://www.linkedin.com/in/{linkedin_urls[0]}"
        
        # Extraire le nom (première ligne du CV)
        lines = text.split('\n')
        if lines:
            first_line = lines[0].strip()
            if len(first_line.split()) <= 4 and len(first_line) > 3:  # Probablement un nom
                contact_info['name'] = first_line
        
        return contact_info

    def _calculate_completeness(self, text: str) -> float:
        """Calculer un score de complétude du CV (0-100)"""
        score = 0
        
        # Longueur du texte (max 30 points)
        text_length = len(text)
        if text_length > 500:
            score += 30
        elif text_length > 200:
            score += 20
        elif text_length > 100:
            score += 10
        
        # Présence d'email (10 points)
        if re.search(self.email_pattern, text):
            score += 10
        
        # Présence de téléphone (10 points)
        if re.search(self.phone_pattern, text):
            score += 10
        
        # Présence d'expérience (20 points)
        exp_keywords = ['experience', 'expériences', 'exp', 'work', 'emploi', 'carrière']
        if any(keyword in text.lower() for keyword in exp_keywords):
            score += 20
        
        # Présence de formation (15 points)
        edu_keywords = ['education', 'formation', 'diplôme', 'université', 'école', 'études']
        if any(keyword in text.lower() for keyword in edu_keywords):
            score += 15
        
        # Présence de compétences (15 points)
        skills_keywords = ['skills', 'compétences', 'technologies', 'outils', 'langages']
        if any(keyword in text.lower() for keyword in skills_keywords):
            score += 15
        
        return min(score, 100)
