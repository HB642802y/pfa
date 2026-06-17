// App bootstrap
// ============================================================

document.addEventListener("DOMContentLoaded", initApp);

function initApp() {
  bindElements();
  bindEvents();
  document.body.dataset.view = "landing";
  if (els.apiBase) {
    els.apiBase.value = state.apiBase;
  }
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
    "apiBase", "saveApi", "apiStatus", "pageTitle",
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
    "recruiterLoginResult", "recruiterLogout", "recruiterSessionLabel",
    "editRecruiterForm", "editRecruiterId", "editRecruiterName", "editRecruiterEmail",
    "editRecruiterPhone", "editRecruiterLocation", "cancelEditRecruiter", "editRecruiterPlaceholder",
    "candidateForm", "candidateName", "candidateEmail", "candidatePassword",
    "candidatesList", "editCandidateForm", "editCandidateId", "editCandidateName",
    "editCandidateEmail", "editCandidatePhone", "editCandidateLocation",
    "editCandidatePlaceholder", "cancelEditCandidate", "jobsToValidate",
    "adminTotalJobs", "adminActiveJobs", "adminPendingJobs", "adminTotalCandidates",
    "adminTotalRecruiters", "adminTotalApplications", "adminAvgScore", "adminTotalInterviews"
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

  if (els.saveApi && els.apiBase) {
    els.saveApi.addEventListener("click", () => {
      state.apiBase = els.apiBase.value.replace(/\/$/, "");
      localStorage.setItem("apiBase", state.apiBase);
      addLog(`API definie sur ${state.apiBase}`);
      checkHealth();
    });
  }

  if (els.candidateRegisterForm) els.candidateRegisterForm.addEventListener("submit", registerCandidate);
  if (els.candidateLoginForm) els.candidateLoginForm.addEventListener("submit", loginCandidate);
  if (els.showCandidateLogin) els.showCandidateLogin.addEventListener("click", () => setCandidateAuthMode("login"));
  if (els.showCandidateRegister) els.showCandidateRegister.addEventListener("click", () => setCandidateAuthMode("register"));
  if (els.candidateGate) els.candidateGate.addEventListener("click", handleCandidateAuthClick);
  if (els.jobForm) els.jobForm.addEventListener("submit", createJob);
  if (els.applicationForm) els.applicationForm.addEventListener("submit", submitApplication);
  if (els.jobsList) els.jobsList.addEventListener("click", handleCandidateJobClick);
  if (els.applicationJob) els.applicationJob.addEventListener("change", () => {
    state.selectedCandidateJobId = els.applicationJob.value;
    localStorage.setItem("selectedCandidateJobId", state.selectedCandidateJobId);
    renderJobs();
  });
  if (els.generateQuestions) els.generateQuestions.addEventListener("click", generateQuestions);
  if (els.analyzeAnswer) els.analyzeAnswer.addEventListener("click", analyzeAnswer);
  if (els.interviewBack) els.interviewBack.addEventListener("click", () => switchView("candidate"));
  if (els.recommendTalents) els.recommendTalents.addEventListener("click", recommendTalents);
  if (els.recruiterForm) els.recruiterForm.addEventListener("submit", addRecruiter);
  if (els.adminLoginForm) els.adminLoginForm.addEventListener("submit", loginAdmin);
  if (els.recruiterLoginForm) els.recruiterLoginForm.addEventListener("submit", loginRecruiter);
  if (els.logoutBtn) els.logoutBtn.addEventListener("click", logout);
  if (els.recruiterLogout) els.recruiterLogout.addEventListener("click", logout);
  if (els.cancelJobEdit) els.cancelJobEdit.addEventListener("click", cancelJobEdit);
  if (els.recruiterJobsList) els.recruiterJobsList.addEventListener("click", handleRecruiterJobAction);
  if (els.recruiterApplications) els.recruiterApplications.addEventListener("click", handleRecruiterJobAction);
  if (els.applicationsList) els.applicationsList.addEventListener("click", handleCandidateApplicationAction);
  if (els.editRecruiterForm) els.editRecruiterForm.addEventListener("submit", updateRecruiter);
  if (els.cancelEditRecruiter) els.cancelEditRecruiter.addEventListener("click", cancelEditRecruiter);
  if (els.recruitersList) els.recruitersList.addEventListener("click", handleRecruiterListClick);
  if (els.candidateForm) els.candidateForm.addEventListener("submit", addCandidate);
  if (els.editCandidateForm) els.editCandidateForm.addEventListener("submit", updateCandidate);
  if (els.cancelEditCandidate) els.cancelEditCandidate.addEventListener("click", cancelEditCandidate);
  if (els.candidatesList) els.candidatesList.addEventListener("click", handleCandidateListClick);
  if (els.jobsToValidate) els.jobsToValidate.addEventListener("click", handleJobsToValidateClick);
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
  document.body.dataset.view = view;
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

// Recruiter Edit Functions
function handleRecruiterListClick(e) {
  const editBtn = e.target.closest("[data-edit-recruiter]");
  const deleteBtn = e.target.closest("[data-delete-recruiter]");
  
  if (editBtn) {
    const recruiterId = editBtn.dataset.editRecruiter;
    const recruiter = state.recruiters.find(r => r.id === recruiterId);
    if (recruiter) {
      showEditRecruiterForm(recruiter);
    }
  }
  
  if (deleteBtn) {
    const recruiterId = deleteBtn.dataset.deleteRecruiter;
    const recruiter = state.recruiters.find(r => r.id === recruiterId);
    if (recruiter) {
      deleteRecruiter(recruiterId, recruiter.email);
    }
  }
}

function showEditRecruiterForm(recruiter) {
  els.editRecruiterId.value = recruiter.id;
  els.editRecruiterName.value = recruiter.name || "";
  els.editRecruiterEmail.value = recruiter.email || "";
  els.editRecruiterPhone.value = recruiter.phone || "";
  els.editRecruiterLocation.value = recruiter.location || "";
  
  els.editRecruiterPlaceholder.style.display = "none";
  els.editRecruiterForm.style.display = "grid";
}

function cancelEditRecruiter() {
  els.editRecruiterForm.style.display = "none";
  els.editRecruiterPlaceholder.style.display = "block";
  els.editRecruiterForm.reset();
}

async function updateRecruiter(e) {
  e.preventDefault();
  
  if (!state.currentUser || state.currentUser.role !== "admin") {
    alert("Accès réservé aux administrateurs");
    return;
  }
  
  const recruiterId = els.editRecruiterId.value;
  const updateData = {
    first_name: els.editRecruiterName.value.split(" ")[0] || els.editRecruiterName.value,
    last_name: els.editRecruiterName.value.split(" ").slice(1).join(" ") || "",
    email: els.editRecruiterEmail.value,
    phone: els.editRecruiterPhone.value || null,
    location: els.editRecruiterLocation.value || null
  };
  
  try {
    const response = await fetch(`${state.apiBase}/admin/update-recruiter/${recruiterId}`, {
      method: "PUT",
      headers: {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${state.authToken}`
      },
      body: JSON.stringify(updateData)
    });
    
    const data = await response.json();
    
    if (response.ok) {
      // Update local state
      const recruiterIndex = state.recruiters.findIndex(r => r.id === recruiterId);
      if (recruiterIndex !== -1) {
        state.recruiters[recruiterIndex] = {
          ...state.recruiters[recruiterIndex],
          name: els.editRecruiterName.value,
          email: els.editRecruiterEmail.value,
          phone: els.editRecruiterPhone.value,
          location: els.editRecruiterLocation.value
        };
        localStorage.setItem("recruiters", JSON.stringify(state.recruiters));
      }
      
      cancelEditRecruiter();
      renderRecruiters();
      addLog(`Recruteur mis à jour: ${updateData.email}`);
      alert("Recruteur mis à jour avec succès!");
    } else {
      alert(`Erreur: ${data.detail}`);
    }
  } catch (error) {
    console.error("Error updating recruiter:", error);
    alert("Erreur de connexion au serveur");
  }
}

async function deleteRecruiter(recruiterId, email) {
  console.log("Tentative de suppression du recruteur:", recruiterId, email);
  console.log("Recruteurs avant suppression:", state.recruiters);
  console.log("Utilisateur connecté:", state.currentUser);
  console.log("Token:", state.authToken);
  
  if (!confirm(`Êtes-vous sûr de vouloir supprimer le recruteur ${email}?`)) {
    return;
  }
  
  // Remove from local state
  const beforeCount = state.recruiters.length;
  state.recruiters = state.recruiters.filter(r => r.id !== recruiterId);
  const afterCount = state.recruiters.length;
  
  console.log("Recruteurs après suppression:", state.recruiters);
  console.log(`Avant: ${beforeCount}, Après: ${afterCount}`);
  
  localStorage.setItem("recruiters", JSON.stringify(state.recruiters));
  
  renderRecruiters();
  addLog(`Recruteur supprimé: ${email}`);
  alert(`Recruteur supprimé! (${beforeCount - afterCount} recruteur(s) supprimé(s))`);
  
  // Try backend in background
  try {
    const headers = {
      "Content-Type": "application/json"
    };
    
    if (state.authToken) {
      headers["Authorization"] = `Bearer ${state.authToken}`;
    }
    
    const response = await fetch(`${state.apiBase}/admin/delete-recruiter/${recruiterId}`, {
      method: "DELETE",
      headers: headers
    });
    
    console.log("Backend response status:", response.status);
  } catch (error) {
    console.error("Error deleting recruiter from backend:", error);
  }
}

// ============================================================

