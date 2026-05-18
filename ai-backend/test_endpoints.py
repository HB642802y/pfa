import requests
import json
import time
from datetime import datetime

class APITester:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
        
    def test_endpoint(self, method, endpoint, data=None, files=None, headers=None):
        """Tester un endpoint spécifique"""
        url = f"{self.base_url}{endpoint}"
        
        try:
            start_time = time.time()
            
            if method.upper() == "GET":
                response = self.session.get(url, headers=headers)
            elif method.upper() == "POST":
                if files:
                    response = self.session.post(url, files=files, headers=headers)
                else:
                    response = self.session.post(url, json=data, headers=headers)
            elif method.upper() == "PUT":
                response = self.session.put(url, json=data, headers=headers)
            elif method.upper() == "DELETE":
                response = self.session.delete(url, headers=headers)
            else:
                return {"error": "Méthode non supportée"}
            
            end_time = time.time()
            response_time = round((end_time - start_time) * 1000, 2)  # en ms
            
            # Analyser la réponse
            result = {
                "endpoint": endpoint,
                "method": method,
                "status_code": response.status_code,
                "response_time_ms": response_time,
                "success": response.status_code < 400,
                "headers": dict(response.headers),
                "content_type": response.headers.get("content-type", ""),
            }
            
            # Essayer de parser le JSON
            try:
                result["response"] = response.json()
            except:
                result["response"] = response.text[:500]  # Limiter la taille de la réponse
                
            return result
            
        except requests.exceptions.RequestException as e:
            return {
                "endpoint": endpoint,
                "method": method,
                "error": str(e),
                "success": False
            }
    
    def test_all_endpoints(self):
        """Tester tous les endpoints principaux"""
        print("🧪 Démarrage des tests API...")
        print(f"🌐 Base URL: {self.base_url}")
        print("=" * 60)
        
        tests = [
            # Endpoints de base
            ("GET", "/", None),
            ("GET", "/health", None),
            
            # Endpoints d'authentification
            ("POST", "/auth/register", {
                "email": "test@example.com",
                "password": "Test123!",
                "first_name": "Test",
                "last_name": "User",
                "role": "candidate"
            }),
            
            # Endpoints de parsing CV (simulé)
            ("POST", "/parse-cv", None),  # Nécessite un fichier
            
            # Endpoints de matching
            ("POST", "/match", {
                "cv_text": "Développeur Python avec expérience en Django et React",
                "job_description": {
                    "title": "Développeur Full Stack",
                    "description": "Nous cherchons un développeur expérimenté",
                    "requirements": "Python, Django, React, PostgreSQL",
                    "skills": ["Python", "Django", "React", "PostgreSQL"],
                    "experience_level": "mid_level"
                }
            }),
            
            # Endpoints d'interview
            ("POST", "/interview/generate-questions", {
                "title": "Développeur Python",
                "description": "Poste de développeur Python",
                "requirements": "5 ans d'expérience",
                "skills": ["Python", "Django", "REST API"],
                "experience_level": "mid_level"
            }),
            
            # Endpoints de recommandations
            ("POST", "/recommendations/candidates", {
                "title": "Développeur Python",
                "description": "Poste de développeur Python",
                "skills": ["Python", "Django"],
                "experience_level": "mid_level"
            }, [
                {"id": "1", "name": "Candidat 1", "skills": ["Python", "Django"]},
                {"id": "2", "name": "Candidat 2", "skills": ["Python", "Flask"]}
            ]),
            
            # Endpoints d'analytics
            ("GET", "/analytics/dashboard", None),
            ("GET", "/analytics/funnel", None),
            ("GET", "/analytics/skills", None),
            
            # Endpoints de compétences
            ("GET", "/skills", None),
        ]
        
        results = []
        success_count = 0
        total_time = 0
        
        for test_data in tests:
            if isinstance(test_data, tuple) and len(test_data) == 2:
                # Cas avec données simples
                method, data = test_data
                endpoint = data[0] if data else None
                payload = data[1] if len(data) > 1 else None
                result = self.test_endpoint(method, endpoint, payload)
            elif isinstance(test_data, tuple) and len(test_data) == 3:
                # Cas avec données supplémentaires (ex: recommandations)
                method, endpoint, additional_data = test_data
                result = self.test_endpoint(method, endpoint, additional_data)
            else:
                # Cas invalide
                result = {"error": "Format de test invalide", "test_data": test_data}
            
            results.append(result)
            
            # Afficher le résultat
            status_icon = "✅" if result.get("success", False) else "❌"
            endpoint_display = endpoint if endpoint else '/'
            print(f"{status_icon} {method} {endpoint_display} - {result.get('status_code', 'N/A')} ({result.get('response_time_ms', 0)}ms)")
            
            if result.get("success", False):
                success_count += 1
            total_time += result.get("response_time_ms", 0)
            
            # Petit délai pour éviter de surcharger le serveur
            time.sleep(0.1)
        
        # Résumé des tests
        print("=" * 60)
        print(f"📊 Résumé des tests:")
        print(f"   Total: {len(results)}")
        print(f"   Succès: {success_count}")
        print(f"   Échecs: {len(results) - success_count}")
        print(f"   Temps moyen: {total_time / len(results):.2f}ms")
        print(f"   Taux de succès: {(success_count / len(results) * 100):.1f}%")
        
        # Détails des erreurs
        failed_tests = [r for r in results if not r["success"]]
        if failed_tests:
            print("\n❌ Tests échoués:")
            for test in failed_tests:
                print(f"   {test['method']} {test['endpoint']}: {test.get('error', 'Erreur inconnue')}")
        
        return results
    
    def generate_report(self, results):
        """Générer un rapport détaillé des tests"""
        report = {
            "test_date": datetime.now().isoformat(),
            "base_url": self.base_url,
            "summary": {
                "total_tests": len(results),
                "successful_tests": len([r for r in results if r["success"]]),
                "failed_tests": len([r for r in results if not r["success"]]),
                "average_response_time": sum(r.get("response_time_ms", 0) for r in results) / len(results)
            },
            "results": results
        }
        
        # Sauvegarder le rapport
        with open("api_test_report.json", "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"\n📄 Rapport sauvegardé dans 'api_test_report.json'")
        return report

if __name__ == "__main__":
    tester = APITester()
    results = tester.test_all_endpoints()
    tester.generate_report(results)
