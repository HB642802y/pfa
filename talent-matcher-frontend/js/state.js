// ============================================================
// Configuration, state and demo data
// ============================================================

function readStoredJson(key, fallback) {
  try {
    const value = localStorage.getItem(key);
    return value ? JSON.parse(value) : fallback;
  } catch (error) {
    localStorage.removeItem(key);
    return fallback;
  }
}

const state = {
  apiBase: localStorage.getItem("apiBase") || "http://localhost:8000",
  backendOnline: false,
  jobs: readStoredJson("jobs", []),
  applications: readStoredJson("applications", []),
  candidates: readStoredJson("candidates", []),
  recruiters: readStoredJson("recruiters", []),
  session: readStoredJson("session", null),
  editingJobId: null,
  selectedCandidateJobId: localStorage.getItem("selectedCandidateJobId") || null,
  currentInterviewApplicationId: localStorage.getItem("currentInterviewApplicationId") || null,
  cvAnalyses: readStoredJson("cvAnalyses", []),
  questions: [],
  logs: []
};

const INTERVIEW_MIN_SCORE = 60;

const defaultAdmin = {
  id: "admin_default",
  name: "Administrateur",
  email: "admin@pfam.local",
  password: "admin123",
  role: "admin"
};

const demoJobs = [
  {
    id: "job_demo_1",
    title: "Developpeur Full Stack React / FastAPI",
    description: "Construire une plateforme de recrutement avec interface candidat, recruteur et administration.",
    requirements: "React, API REST, Python, FastAPI, MongoDB, bonnes pratiques UI.",
    skills: ["React", "Python", "FastAPI", "MongoDB", "API REST"],
    experience_level: "mid_level",
    salary_min: 10000,
    salary_max: 18000,
    location: "Casablanca",
    status: "active"
  },
  {
    id: "job_demo_2",
    title: "Data Analyst RH",
    description: "Analyser les candidatures, les scores IA et les performances du funnel recrutement.",
    requirements: "Python, SQL, visualisation, statistiques, communication avec recruteurs.",
    skills: ["Python", "SQL", "Analytics", "Dashboard"],
    experience_level: "junior",
    salary_min: 8000,
    salary_max: 13000,
    location: "Rabat",
    status: "active"
  }
];

const demoCandidates = [
  {
    id: "candidate_demo_1",
    name: "Sara El Mansouri",
    cvText: "Developpeuse React avec experience Python FastAPI MongoDB. Projets API REST, dashboards et interfaces RH.",
    skills: ["React", "Python", "FastAPI", "MongoDB", "API REST"]
  },
  {
    id: "candidate_demo_2",
    name: "Youssef Amrani",
    cvText: "Analyste data junior, Python SQL Power BI, suivi KPI et reporting recrutement.",
    skills: ["Python", "SQL", "Analytics", "Power BI"]
  }
];

const els = {};

// ============================================================

