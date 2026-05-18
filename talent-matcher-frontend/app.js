const state = {
  apiBase: localStorage.getItem("apiBase") || "http://localhost:8000",
  backendOnline: false,
  jobs: JSON.parse(localStorage.getItem("jobs") || "[]"),
  applications: JSON.parse(localStorage.getItem("applications") || "[]"),
  recruiters: JSON.parse(localStorage.getItem("recruiters") || "[]"),
  cvAnalyses: JSON.parse(localStorage.getItem("cvAnalyses") || "[]"),
  questions: [],
  logs: []
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

document.addEventListener("DOMContentLoaded", () => {
  bindElements();
  bindEvents();
  els.apiBase.value = state.apiBase;
  renderAll();
  checkHealth();
});

function bindElements() {
  [
    "apiBase", "saveApi", "apiStatus", "pageTitle", "seedDemo", "refreshData",
    "jobsList", "jobCount", "applicationForm", "applicationJob", "cvFile",
    "cvText", "coverLetter", "candidateResult", "applicationsList",
    "applicationCount", "generateQuestions", "questionsList", "answerText",
    "analyzeAnswer", "answerAnalysis", "jobForm", "jobTitle", "experienceLevel",
    "jobLocation", "salaryMin", "jobSkills", "jobDescription", "jobRequirements",
    "recommendationJob", "recommendTalents", "talentRecommendations",
    "recruiterApplications", "recruiterApplicationCount", "aiCvCount",
    "aiMatchAvg", "aiQuestionCount", "aiLog", "adminJobs", "adminApplications",
    "adminBackend", "recruiterForm", "recruiterName", "recruiterEmail",
    "recruitersList", "systemMonitor"
  ].forEach((id) => {
    els[id] = document.getElementById(id);
  });
}

function bindEvents() {
  document.querySelectorAll(".nav-btn").forEach((button) => {
    button.addEventListener("click", () => switchView(button.dataset.view));
  });

  els.saveApi.addEventListener("click", () => {
    state.apiBase = els.apiBase.value.replace(/\/$/, "");
    localStorage.setItem("apiBase", state.apiBase);
    addLog(`API definie sur ${state.apiBase}`);
    checkHealth();
  });

  els.refreshData.addEventListener("click", syncJobs);
  els.seedDemo.addEventListener("click", seedDemoData);
  els.jobForm.addEventListener("submit", createJob);
  els.applicationForm.addEventListener("submit", submitApplication);
  els.generateQuestions.addEventListener("click", generateQuestions);
  els.analyzeAnswer.addEventListener("click", analyzeAnswer);
  els.recommendTalents.addEventListener("click", recommendTalents);
  els.recruiterForm.addEventListener("submit", addRecruiter);
}

function switchView(view) {
  document.querySelectorAll(".nav-btn").forEach((button) => {
    button.classList.toggle("active", button.dataset.view === view);
  });
  document.querySelectorAll(".view").forEach((section) => {
    section.classList.toggle("active", section.id === `${view}View`);
  });
  const titles = {
    candidate: "Espace candidat",
    recruiter: "Espace recruteur",
    ai: "Moteur IA",
    admin: "Administration"
  };
  els.pageTitle.textContent = titles[view];
}

async function apiFetch(path, options = {}) {
  const headers = options.body instanceof FormData ? {} : { "Content-Type": "application/json" };
  const response = await fetch(`${state.apiBase}${path}`, {
    ...options,
    headers: { ...headers, ...(options.headers || {}) }
  });
  if (!response.ok) {
    const message = await response.text();
    throw new Error(message || `HTTP ${response.status}`);
  }
  return response.json();
}

async function checkHealth() {
  try {
    const health = await apiFetch("/health");
    state.backendOnline = true;
    els.apiStatus.textContent = `Connecte: ${health.status || "ok"}`;
    els.apiStatus.className = "status ok";
    addLog("Backend disponible via /health");
  } catch (error) {
    state.backendOnline = false;
    els.apiStatus.textContent = "Backend indisponible, mode demo actif";
    els.apiStatus.className = "status bad";
    addLog("Mode demo actif: backend non disponible");
  }
  renderAdmin();
}

async function syncJobs() {
  await checkHealth();
  if (!state.backendOnline) {
    renderAll();
    return;
  }

  try {
    const payload = await apiFetch("/jobs");
    const jobs = normalizeList(payload);
    if (jobs.length) {
      state.jobs = mergeById(state.jobs, jobs);
      persist();
      addLog(`${jobs.length} offres synchronisees depuis /jobs`);
    }
  } catch (error) {
    addLog(`Synchronisation /jobs impossible: ${cleanError(error)}`);
  }
  renderAll();
}

async function createJob(event) {
  event.preventDefault();
  const job = {
    id: `job_${Date.now()}`,
    title: els.jobTitle.value.trim(),
    description: els.jobDescription.value.trim(),
    requirements: els.jobRequirements.value.trim(),
    skills: splitCsv(els.jobSkills.value),
    experience_level: els.experienceLevel.value,
    salary_min: numberOrNull(els.salaryMin.value),
    salary_max: null,
    location: els.jobLocation.value.trim() || "Non precise",
    status: "active"
  };

  let savedJob = job;
  if (state.backendOnline) {
    try {
      const payload = await apiFetch("/jobs", { method: "POST", body: JSON.stringify(job) });
      savedJob = normalizeObject(payload) || job;
      addLog(`Offre creee cote backend: ${savedJob.title}`);
    } catch (error) {
      addLog(`Creation backend echouee, sauvegarde locale: ${cleanError(error)}`);
    }
  }

  state.jobs = mergeById(state.jobs, [savedJob]);
  persist();
  event.target.reset();
  renderAll();
}

async function submitApplication(event) {
  event.preventDefault();
  const job = state.jobs.find((item) => item.id === els.applicationJob.value) || state.jobs[0];
  if (!job) {
    showResult(els.candidateResult, "Creez ou chargez une offre avant de postuler.", true);
    return;
  }

  let parsedCv = null;
  let cvText = els.cvText.value.trim();
  const file = els.cvFile.files[0];

  if (file && state.backendOnline) {
    const formData = new FormData();
    formData.append("file", file);
    try {
      parsedCv = normalizeObject(await apiFetch("/parse-cv", { method: "POST", body: formData }));
      cvText = parsedCv.text || cvText || `CV importe: ${file.name}`;
      addLog(`CV analyse par le backend: ${file.name}`);
    } catch (error) {
      addLog(`Analyse CV backend echouee: ${cleanError(error)}`);
    }
  }

  if (!cvText) {
    cvText = "React Python FastAPI MongoDB API REST recrutement analytics";
  }

  const match = await calculateMatch(cvText, job, parsedCv);
  const application = {
    id: `app_${Date.now()}`,
    candidateName: "Candidat demo",
    jobId: job.id,
    jobTitle: job.title,
    cvText,
    coverLetter: els.coverLetter.value.trim(),
    match,
    status: "reviewing",
    createdAt: new Date().toISOString()
  };

  state.applications.unshift(application);
  state.cvAnalyses.push({ id: application.id, cvText, parsedCv, match });
  persist();
  renderAll();
  showResult(els.candidateResult, renderMatchSummary(match, "Candidature envoyee et analysee."));
}

async function calculateMatch(cvText, job, parsedCv) {
  const request = {
    cv_text: cvText,
    job_description: normalizeJobForApi(job),
    cv_data: parsedCv
      ? {
          text: parsedCv.text || cvText,
          skills: parsedCv.skills || [],
          experience: parsedCv.experience || [],
          education: parsedCv.education || []
        }
      : null
  };

  if (state.backendOnline) {
    try {
      const match = normalizeObject(await apiFetch("/match", {
        method: "POST",
        body: JSON.stringify(request)
      }));
      addLog(`Matching backend calcule pour ${job.title}`);
      return normalizeMatch(match);
    } catch (error) {
      addLog(`Matching backend echoue, calcul local: ${cleanError(error)}`);
    }
  }

  return localMatch(cvText, job);
}

async function generateQuestions() {
  const job = selectedJob() || state.jobs[0] || demoJobs[0];
  let questions = [];

  if (state.backendOnline) {
    try {
      const payload = await apiFetch("/interview/generate-questions", {
        method: "POST",
        body: JSON.stringify(normalizeJobForApi(job))
      });
      questions = Array.isArray(payload) ? payload : normalizeList(payload);
      addLog(`Questions entretien generees par backend pour ${job.title}`);
    } catch (error) {
      addLog(`Generation questions backend echouee: ${cleanError(error)}`);
    }
  }

  if (!questions.length) {
    questions = localQuestions(job);
  }

  state.questions = questions.slice(0, 5);
  renderQuestions();
  renderAi();
}

async function analyzeAnswer() {
  const selected = document.querySelector("input[name='question']:checked");
  const question = state.questions[Number(selected?.value || 0)] || state.questions[0];
  const answer = els.answerText.value.trim();
  if (!question || !answer) {
    showResult(els.answerAnalysis, "Choisissez une question et ecrivez une reponse.", true);
    return;
  }

  if (state.backendOnline) {
    try {
      const analysis = await apiFetch("/interview/analyze-answer", {
        method: "POST",
        body: JSON.stringify({ question, answer, response_time: 90 })
      });
      showResult(els.answerAnalysis, formatObject(analysis));
      addLog("Reponse entretien analysee par backend");
      return;
    } catch (error) {
      try {
        const params = new URLSearchParams({ answer, response_time: "90" });
        const analysis = await apiFetch(`/interview/analyze-answer?${params}`, {
          method: "POST",
          body: JSON.stringify(question)
        });
        showResult(els.answerAnalysis, formatObject(analysis));
        addLog("Reponse entretien analysee par backend");
        return;
      } catch (fallbackError) {
        addLog(`Analyse reponse backend echouee: ${cleanError(fallbackError)}`);
      }
    }
  }

  const score = Math.min(96, 45 + overlapScore(answer, (question.keywords || []).join(" ")) + answer.length / 12);
  showResult(els.answerAnalysis, `<strong>Score feedback:</strong> ${Math.round(score)}%<br>${score > 70 ? "Reponse solide, claire et alignee." : "Reponse a renforcer avec exemples, outils et resultats mesurables."}`);
}

async function recommendTalents() {
  const job = selectedJob() || state.jobs[0];
  if (!job) {
    showResult(els.talentRecommendations, "Aucune offre disponible.", true);
    return;
  }

  const candidates = [
    ...demoCandidates,
    ...state.applications.map((app) => ({
      id: app.id,
      name: app.candidateName,
      cvText: app.cvText,
      skills: extractSkills(app.cvText)
    }))
  ];

  const recommendations = candidates
    .map((candidate) => ({ candidate, match: localMatch(candidate.cvText, job) }))
    .sort((a, b) => b.match.overall_score - a.match.overall_score);

  els.talentRecommendations.innerHTML = recommendations.map(({ candidate, match }) => `
    <article class="item">
      <h3>${escapeHtml(candidate.name)}</h3>
      <p><span class="score">${Math.round(match.overall_score)}%</span> de compatibilite avec ${escapeHtml(job.title)}</p>
      <div class="tag-row">${match.matched_skills.map((skill) => `<span class="tag">${escapeHtml(skill)}</span>`).join("")}</div>
    </article>
  `).join("");
  addLog(`Recommandation talents calculee pour ${job.title}`);
}

function addRecruiter(event) {
  event.preventDefault();
  const name = els.recruiterName.value.trim();
  const email = els.recruiterEmail.value.trim();
  if (!name || !email) return;
  state.recruiters.unshift({ id: `rec_${Date.now()}`, name, email, status: "actif" });
  persist();
  event.target.reset();
  renderAdmin();
}

function seedDemoData() {
  state.jobs = mergeById(state.jobs, demoJobs);
  if (!state.applications.length) {
    state.applications = [{
      id: "app_demo_1",
      candidateName: "Sara El Mansouri",
      jobId: "job_demo_1",
      jobTitle: "Developpeur Full Stack React / FastAPI",
      cvText: demoCandidates[0].cvText,
      coverLetter: "Je souhaite rejoindre votre equipe pour construire des interfaces utiles et des APIs solides.",
      match: localMatch(demoCandidates[0].cvText, demoJobs[0]),
      status: "reviewing",
      createdAt: new Date().toISOString()
    }];
  }
  persist();
  renderAll();
  addLog("Donnees demo chargees");
}

function renderAll() {
  renderJobs();
  renderApplications();
  renderRecruiter();
  renderAi();
  renderAdmin();
}

function renderJobs() {
  els.jobCount.textContent = `${state.jobs.length} offres`;
  renderOptions(els.applicationJob, state.jobs);
  renderOptions(els.recommendationJob, state.jobs);

  if (!state.jobs.length) {
    els.jobsList.innerHTML = emptyHtml();
    return;
  }

  els.jobsList.innerHTML = state.jobs.map((job) => `
    <article class="item">
      <h3>${escapeHtml(job.title)}</h3>
      <p>${escapeHtml(job.location || job.work_location || "Lieu non precise")} · ${escapeHtml(job.experience_level || "niveau non precise")}</p>
      <p>${escapeHtml(trimText(job.description, 150))}</p>
      <div class="tag-row">${(job.skills || []).map((skill) => `<span class="tag">${escapeHtml(skill)}</span>`).join("")}</div>
    </article>
  `).join("");
}

function renderApplications() {
  els.applicationCount.textContent = String(state.applications.length);
  if (!state.applications.length) {
    els.applicationsList.innerHTML = emptyHtml();
    return;
  }

  els.applicationsList.innerHTML = state.applications.map((app) => `
    <article class="item">
      <h3>${escapeHtml(app.jobTitle)}</h3>
      <p>Statut: ${escapeHtml(app.status)} · Score: <span class="score">${Math.round(app.match.overall_score)}%</span></p>
      <p>${escapeHtml(trimText(app.coverLetter || "Sans lettre de motivation", 120))}</p>
    </article>
  `).join("");
}

function renderRecruiter() {
  els.recruiterApplicationCount.textContent = String(state.applications.length);
  if (!state.applications.length) {
    els.recruiterApplications.innerHTML = emptyHtml();
    return;
  }

  els.recruiterApplications.innerHTML = `
    <table>
      <thead>
        <tr>
          <th>Candidat</th>
          <th>Offre</th>
          <th>Score</th>
          <th>Competences detectees</th>
          <th>Statut</th>
        </tr>
      </thead>
      <tbody>
        ${state.applications.map((app) => `
          <tr>
            <td>${escapeHtml(app.candidateName)}</td>
            <td>${escapeHtml(app.jobTitle)}</td>
            <td><span class="score">${Math.round(app.match.overall_score)}%</span></td>
            <td>${(app.match.matched_skills || []).map(escapeHtml).join(", ") || "Aucune"}</td>
            <td>${escapeHtml(app.status)}</td>
          </tr>
        `).join("")}
      </tbody>
    </table>
  `;
}

function renderQuestions() {
  if (!state.questions.length) {
    els.questionsList.innerHTML = emptyHtml();
    return;
  }

  els.questionsList.innerHTML = state.questions.map((question, index) => `
    <label class="item question">
      <input type="radio" name="question" value="${index}" ${index === 0 ? "checked" : ""} />
      <span>${escapeHtml(question.question || question.text || String(question))}</span>
    </label>
  `).join("");
}

function renderAi() {
  const avg = state.applications.length
    ? state.applications.reduce((sum, app) => sum + Number(app.match.overall_score || 0), 0) / state.applications.length
    : 0;
  els.aiCvCount.textContent = String(state.cvAnalyses.length);
  els.aiMatchAvg.textContent = `${Math.round(avg)}%`;
  els.aiQuestionCount.textContent = String(state.questions.length);
  els.aiLog.innerHTML = state.logs.slice(-12).map((line) => `<div>${escapeHtml(line)}</div>`).join("") || "Aucun evenement IA.";
}

function renderAdmin() {
  els.adminJobs.textContent = String(state.jobs.length);
  els.adminApplications.textContent = String(state.applications.length);
  els.adminBackend.textContent = state.backendOnline ? "ON" : "OFF";
  els.systemMonitor.innerHTML = `
    <strong>API:</strong> ${escapeHtml(state.apiBase)}<br>
    <strong>Etat:</strong> ${state.backendOnline ? "connecte" : "mode demo local"}<br>
    <strong>Stockage:</strong> localStorage frontend + API FastAPI si disponible
  `;

  if (!state.recruiters.length) {
    els.recruitersList.innerHTML = emptyHtml();
    return;
  }

  els.recruitersList.innerHTML = state.recruiters.map((recruiter) => `
    <article class="item">
      <h3>${escapeHtml(recruiter.name)}</h3>
      <p>${escapeHtml(recruiter.email)} · ${escapeHtml(recruiter.status)}</p>
    </article>
  `).join("");
}

function renderOptions(select, jobs) {
  select.innerHTML = jobs.length
    ? jobs.map((job) => `<option value="${escapeHtml(job.id)}">${escapeHtml(job.title)}</option>`).join("")
    : `<option value="">Aucune offre</option>`;
}

function selectedJob() {
  return state.jobs.find((job) => job.id === els.recommendationJob.value || job.id === els.applicationJob.value);
}

function localMatch(cvText, job) {
  const jobSkills = job.skills || splitCsv(job.skills || "");
  const cvSkills = extractSkills(cvText);
  const matched = jobSkills.filter((skill) => containsSkill(cvText, skill));
  const missing = jobSkills.filter((skill) => !containsSkill(cvText, skill));
  const skillsScore = jobSkills.length ? (matched.length / jobSkills.length) * 100 : 45;
  const textScore = overlapScore(cvText, `${job.description} ${job.requirements}`);
  const overall = Math.min(98, Math.max(18, skillsScore * 0.7 + textScore * 0.3));

  return {
    overall_score: overall,
    skills_score: skillsScore,
    experience_score: Math.min(95, 45 + textScore),
    education_score: 65,
    tools_score: skillsScore,
    matched_skills: matched.length ? matched : cvSkills.slice(0, 3),
    missing_skills: missing,
    recommendations: [
      overall >= 70 ? "Profil recommande pour entretien." : "Profil a examiner avec attention.",
      missing.length ? `Former ou verifier: ${missing.slice(0, 4).join(", ")}.` : "Competences principales couvertes."
    ]
  };
}

function localQuestions(job) {
  const skills = (job.skills || []).slice(0, 4);
  return [
    {
      id: 1,
      question: `Expliquez une experience concrete liee au poste ${job.title}.`,
      keywords: skills,
      difficulty: "medium"
    },
    {
      id: 2,
      question: `Comment utiliseriez-vous ${skills[0] || "vos competences"} pour resoudre un probleme urgent ?`,
      keywords: skills,
      difficulty: "medium"
    },
    {
      id: 3,
      question: "Donnez un exemple ou vous avez collabore avec une equipe non technique.",
      keywords: ["communication", "collaboration", "resultat"],
      difficulty: "easy"
    }
  ];
}

function normalizeJobForApi(job) {
  return {
    title: job.title,
    description: job.description,
    requirements: job.requirements,
    skills: job.skills || [],
    experience_level: job.experience_level || "mid_level",
    salary_min: numberOrNull(job.salary_min),
    salary_max: numberOrNull(job.salary_max),
    location: job.location || job.work_location || ""
  };
}

function normalizeList(payload) {
  if (Array.isArray(payload)) return payload;
  if (Array.isArray(payload?.data)) return payload.data;
  if (Array.isArray(payload?.jobs)) return payload.jobs;
  if (Array.isArray(payload?.results)) return payload.results;
  return [];
}

function normalizeObject(payload) {
  return payload?.data || payload?.result || payload;
}

function normalizeMatch(match) {
  return {
    overall_score: Number(match.overall_score ?? match.score ?? 0),
    skills_score: Number(match.skills_score ?? match.score ?? 0),
    experience_score: Number(match.experience_score ?? 0),
    education_score: Number(match.education_score ?? 0),
    tools_score: Number(match.tools_score ?? 0),
    matched_skills: match.matched_skills || [],
    missing_skills: match.missing_skills || [],
    recommendations: match.recommendations || [match.recommendation, match.analysis].filter(Boolean)
  };
}

function mergeById(current, incoming) {
  const map = new Map(current.map((item) => [item.id, item]));
  incoming.forEach((item) => {
    const id = item.id || item._id || `item_${Date.now()}_${Math.random()}`;
    map.set(id, { ...item, id });
  });
  return Array.from(map.values());
}

function extractSkills(text) {
  const known = ["React", "JavaScript", "Python", "FastAPI", "MongoDB", "SQL", "Docker", "AWS", "API REST", "Analytics", "Power BI", "Node.js"];
  return known.filter((skill) => containsSkill(text, skill));
}

function containsSkill(text, skill) {
  return String(text || "").toLowerCase().includes(String(skill || "").toLowerCase());
}

function overlapScore(a, b) {
  const wordsA = new Set(String(a).toLowerCase().split(/[^a-z0-9+#.]+/).filter((word) => word.length > 2));
  const wordsB = String(b).toLowerCase().split(/[^a-z0-9+#.]+/).filter((word) => word.length > 2);
  if (!wordsB.length) return 0;
  const hits = wordsB.filter((word) => wordsA.has(word)).length;
  return Math.min(100, (hits / Math.max(8, wordsB.length)) * 100);
}

function splitCsv(value) {
  return String(value || "").split(",").map((item) => item.trim()).filter(Boolean);
}

function numberOrNull(value) {
  const parsed = Number(value);
  return Number.isFinite(parsed) && parsed > 0 ? parsed : null;
}

function showResult(element, html, isError = false) {
  element.innerHTML = `<div class="${isError ? "danger" : ""}">${html}</div>`;
}

function renderMatchSummary(match, title) {
  return `
    <strong>${escapeHtml(title)}</strong><br>
    Score global: <span class="score">${Math.round(match.overall_score)}%</span><br>
    Competences trouvees: ${(match.matched_skills || []).map(escapeHtml).join(", ") || "Aucune"}<br>
    A ameliorer: ${(match.missing_skills || []).map(escapeHtml).join(", ") || "Rien de majeur"}<br>
    ${(match.recommendations || []).map(escapeHtml).join("<br>")}
  `;
}

function formatObject(value) {
  if (typeof value === "string") return escapeHtml(value);
  return `<pre>${escapeHtml(JSON.stringify(value, null, 2))}</pre>`;
}

function addLog(message) {
  const time = new Date().toLocaleTimeString("fr-FR", { hour: "2-digit", minute: "2-digit" });
  state.logs.push(`[${time}] ${message}`);
  renderAi();
}

function persist() {
  localStorage.setItem("jobs", JSON.stringify(state.jobs));
  localStorage.setItem("applications", JSON.stringify(state.applications));
  localStorage.setItem("recruiters", JSON.stringify(state.recruiters));
  localStorage.setItem("cvAnalyses", JSON.stringify(state.cvAnalyses));
}

function emptyHtml() {
  return document.getElementById("emptyTemplate").innerHTML;
}

function trimText(value, max) {
  const text = String(value || "");
  return text.length > max ? `${text.slice(0, max - 3)}...` : text;
}

function cleanError(error) {
  return String(error?.message || error).slice(0, 180);
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}
