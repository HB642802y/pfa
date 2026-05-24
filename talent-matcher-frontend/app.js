// App bootstrap
// ============================================================

document.addEventListener("DOMContentLoaded", initApp);

function initApp() {
  bindElements();
  bindEvents();
  els.apiBase.value = state.apiBase;
  try {
    renderAll();
  } catch (error) {
    console.error("Erreur de rendu initial:", error);
    resetCorruptedLocalState();
    renderAll();
  }
  checkHealth();
}

// ============================================================
// DOM bindings and navigation
// ============================================================

function bindElements() {
  [
    "apiBase", "saveApi", "apiStatus", "pageTitle", "seedDemo", "refreshData",
    "landingJobs", "landingApplications", "landingBackend", "landingScore",
    "jobsList", "jobCount", "candidateJobDetails", "applicationForm", "applicationJob", "cvFile",
    "cvText", "coverLetter", "candidateResult", "applicationsList",
    "candidateTotalApps", "candidateBestScore", "candidateInterviewMetric",
    "applicationCount", "candidateGate", "candidateContent", "candidateRegisterForm",
    "candidateRegisterName", "candidateRegisterEmail", "candidateRegisterPassword",
    "candidateRegisterResult", "candidateLoginForm", "candidateLoginEmail",
    "candidateLoginPassword", "candidateLoginResult", "candidateSessionLabel",
    "showCandidateLogin", "showCandidateRegister", "interviewGateMessage",
    "interviewBack", "interviewCandidateName", "interviewJobTitle",
    "interviewCvScore", "interviewStatusPill", "interviewProgress",
    "generateQuestions", "questionsList",
    "analyzeAnswer", "answerAnalysis", "jobForm", "jobTitle", "experienceLevel",
    "jobLocation", "salaryMin", "jobSkills", "jobDescription", "jobRequirements",
    "jobFormTitle", "jobSubmit", "cancelJobEdit", "recommendationJob",
    "recommendTalents", "talentRecommendations", "recruiterJobsList",
    "recruiterJobMetric", "recruiterAppMetric", "recruiterBestScore",
    "recruiterApplications", "recruiterApplicationCount", "adminJobs",
    "adminApplications", "adminBackend", "recruiterForm", "recruiterName", "recruiterEmail",
    "recruiterPassword", "recruitersList", "systemMonitor", "authStatus",
    "logoutBtn", "adminGate", "adminContent", "adminLoginForm", "adminLoginEmail",
    "adminLoginPassword", "adminLoginResult", "recruiterGate", "recruiterContent",
    "recruiterLoginForm", "recruiterLoginEmail", "recruiterLoginPassword",
    "recruiterLoginResult", "recruiterLogout", "recruiterSessionLabel"
  ].forEach((id) => {
    els[id] = document.getElementById(id);
  });
}

function resetCorruptedLocalState() {
  state.jobs = Array.isArray(state.jobs) ? state.jobs : [];
  state.applications = Array.isArray(state.applications) ? state.applications : [];
  state.candidates = Array.isArray(state.candidates) ? state.candidates : [];
  state.recruiters = Array.isArray(state.recruiters) ? state.recruiters : [];
  state.cvAnalyses = Array.isArray(state.cvAnalyses) ? state.cvAnalyses : [];
  state.applications = state.applications.map((application) => ({
    ...application,
    match: application.match || normalizeMatch({})
  }));
  persist();
}

function bindEvents() {
  document.querySelectorAll(".nav-btn").forEach((button) => {
    button.addEventListener("click", () => switchView(button.dataset.view));
  });
  document.querySelectorAll("[data-go-to]").forEach((button) => {
    button.addEventListener("click", () => switchView(button.dataset.goTo));
  });

  els.saveApi.addEventListener("click", () => {
    state.apiBase = els.apiBase.value.replace(/\/$/, "");
    localStorage.setItem("apiBase", state.apiBase);
    addLog(`API definie sur ${state.apiBase}`);
    checkHealth();
  });

  els.refreshData.addEventListener("click", syncJobs);
  els.seedDemo.addEventListener("click", seedDemoData);
  els.candidateRegisterForm.addEventListener("submit", registerCandidate);
  els.candidateLoginForm.addEventListener("submit", loginCandidate);
  els.showCandidateLogin.addEventListener("click", () => setCandidateAuthMode("login"));
  els.showCandidateRegister.addEventListener("click", () => setCandidateAuthMode("register"));
  els.candidateGate.addEventListener("click", handleCandidateAuthClick);
  els.jobForm.addEventListener("submit", createJob);
  els.applicationForm.addEventListener("submit", submitApplication);
  els.jobsList.addEventListener("click", handleCandidateJobClick);
  els.applicationJob.addEventListener("change", () => {
    state.selectedCandidateJobId = els.applicationJob.value;
    localStorage.setItem("selectedCandidateJobId", state.selectedCandidateJobId);
    renderJobs();
  });
  els.generateQuestions.addEventListener("click", generateQuestions);
  els.analyzeAnswer.addEventListener("click", analyzeAnswer);
  els.interviewBack.addEventListener("click", () => switchView("candidate"));
  els.recommendTalents.addEventListener("click", recommendTalents);
  els.recruiterForm.addEventListener("submit", addRecruiter);
  els.adminLoginForm.addEventListener("submit", loginAdmin);
  els.recruiterLoginForm.addEventListener("submit", loginRecruiter);
  els.logoutBtn.addEventListener("click", logout);
  els.recruiterLogout.addEventListener("click", logout);
  els.cancelJobEdit.addEventListener("click", cancelJobEdit);
  els.recruiterJobsList.addEventListener("click", handleRecruiterJobAction);
  els.applicationsList.addEventListener("click", handleCandidateApplicationAction);
}

function handleCandidateAuthClick(event) {
  if (event.target.closest("#showCandidateLogin")) {
    setCandidateAuthMode("login");
  }
  if (event.target.closest("#showCandidateRegister")) {
    setCandidateAuthMode("register");
  }
}

function switchView(view) {
  document.querySelectorAll(".nav-btn").forEach((button) => {
    button.classList.toggle("active", button.dataset.view === view);
  });
  document.querySelectorAll(".view").forEach((section) => {
    section.classList.toggle("active", section.id === `${view}View`);
  });
  const titles = {
    landing: "AI Recrutement",
    candidate: "Espace candidat",
    interview: "Entretien AI",
    recruiter: "Espace recruteur",
    admin: "Administration"
  };
  els.pageTitle.textContent = titles[view] || "Plateforme AI Recrutement";
  renderAccess();
  renderInterviewPage();
}

// ============================================================

