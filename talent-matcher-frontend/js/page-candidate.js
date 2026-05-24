// Candidate page renderers
// ============================================================

function renderJobs() {
  els.jobCount.textContent = `${state.jobs.length} offres`;
  renderOptions(els.applicationJob, state.jobs);
  renderOptions(els.recommendationJob, state.jobs);

  if (!state.jobs.length) {
    els.jobsList.innerHTML = emptyHtml();
    renderCandidateJobDetails(null);
    return;
  }

  if (!state.selectedCandidateJobId || !state.jobs.some((job) => job.id === state.selectedCandidateJobId)) {
    state.selectedCandidateJobId = state.jobs[0].id;
  }
  els.applicationJob.value = state.selectedCandidateJobId;

  els.jobsList.innerHTML = state.jobs.map((job) => `
    <article class="item job-card ${job.id === state.selectedCandidateJobId ? "selected" : ""}" data-job-id="${escapeHtml(job.id)}">
      <div class="item-head">
        <div>
          <h3>${escapeHtml(job.title)}</h3>
          <p>${escapeHtml(job.location || job.work_location || "Lieu non precise")} - ${escapeHtml(job.experience_level || "niveau non precise")}</p>
        </div>
        <span class="badge badge-success">Active</span>
      </div>
      <p>${escapeHtml(trimText(job.description, 150))}</p>
      <div class="tag-row">${(job.skills || []).map((skill) => `<span class="tag">${escapeHtml(skill)}</span>`).join("")}</div>
    </article>
  `).join("");

  renderCandidateJobDetails(selectedCandidateJob());
}

function handleCandidateJobClick(event) {
  const target = event.target.closest("[data-job-id]");
  if (!target) return;

  const job = state.jobs.find((item) => item.id === target.dataset.jobId);
  if (!job) return;

  state.selectedCandidateJobId = job.id;
  localStorage.setItem("selectedCandidateJobId", job.id);
  els.applicationJob.value = job.id;
  renderJobs();
}

function selectedCandidateJob() {
  return state.jobs.find((job) => job.id === state.selectedCandidateJobId) || state.jobs[0] || null;
}

function renderCandidateJobDetails(job) {
  if (!els.candidateJobDetails) return;

  if (!job) {
    els.candidateJobDetails.classList.add("hidden");
    els.candidateJobDetails.innerHTML = "";
    return;
  }

  els.candidateJobDetails.classList.remove("hidden");
  els.candidateJobDetails.innerHTML = `
    <div class="job-details-head">
      <div>
        <p class="eyebrow">Offre selectionnee</p>
        <h3>${escapeHtml(job.title)}</h3>
      </div>
      <span class="badge badge-info">Seuil entretien ${INTERVIEW_MIN_SCORE}%</span>
    </div>
    <p>${escapeHtml(job.location || job.work_location || "Lieu non precise")} - ${escapeHtml(job.experience_level || "niveau non precise")}</p>
    <p>${escapeHtml(job.description || "Aucune description.")}</p>
    <p><strong>Exigences:</strong> ${escapeHtml(job.requirements || "Non precisees.")}</p>
    <div class="tag-row">${(job.skills || []).map((skill) => `<span class="tag">${escapeHtml(skill)}</span>`).join("")}</div>
  `;
}

function renderApplications() {
  const applications = candidateApplications();
  const bestScore = applications.length
    ? Math.max(...applications.map((app) => Number(app.match?.overall_score || 0)))
    : 0;
  const unlockedInterviews = applications.filter(canStartInterview).length;
  if (els.candidateTotalApps) els.candidateTotalApps.textContent = String(applications.length);
  if (els.candidateBestScore) els.candidateBestScore.textContent = `${Math.round(bestScore)}%`;
  if (els.candidateInterviewMetric) els.candidateInterviewMetric.textContent = String(unlockedInterviews);
  els.applicationCount.textContent = String(applications.length);
  if (!isCandidateSession()) {
    els.applicationsList.innerHTML = `<div class="empty">Connectez-vous comme candidat pour voir vos candidatures.</div>`;
    return;
  }
  if (!applications.length) {
    els.applicationsList.innerHTML = emptyHtml();
    return;
  }

  els.applicationsList.innerHTML = applications.map((app) => `
    <article class="item">
      <div class="item-head">
        <div>
          <h3>${escapeHtml(app.jobTitle)}</h3>
          <div class="meta-row">${statusBadge(app.status)} ${interviewBadge(app)} ${scoreBadge(app.match?.overall_score, "CV")}</div>
        </div>
        ${canStartInterview(app) ? `<button type="button" data-action="start-interview" data-application-id="${escapeHtml(app.id)}">${app.interviewStatus === "completed" ? "Voir entretien AI" : "Passer entretien AI"}</button>` : `<button type="button" class="secondary" disabled>Entretien verrouille</button>`}
      </div>
      <p>${escapeHtml(app.aiValidationMessage || "")}</p>
      <p>${escapeHtml(trimText(app.coverLetter || "Sans lettre de motivation", 120))}</p>
      ${app.interviewScore ? `<div class="meta-row">${scoreBadge(app.interviewScore, "Entretien")} <span class="muted">${escapeHtml(app.interviewFeedback || "")}</span></div>` : ""}
    </article>
  `).join("");
}

function handleCandidateApplicationAction(event) {
  const button = event.target.closest("button[data-action='start-interview'][data-application-id]");
  if (!button || !isCandidateSession()) return;

  const application = state.applications.find((item) => item.id === button.dataset.applicationId);
  if (!application || application.candidateId !== state.session.id || !canStartInterview(application)) return;

  state.currentInterviewApplicationId = application.id;
  localStorage.setItem("currentInterviewApplicationId", application.id);
  application.interviewStatus = application.interviewStatus || "ready";
  persist();
  switchView("interview");
  if (!getInterviewQuestions(application).length) {
    generateQuestions();
  } else {
    renderInterviewPage();
  }
}

function candidateApplications() {
  if (!isCandidateSession()) return [];
  return state.applications.filter((app) => app.candidateId === state.session.id);
}

function selectedInterviewApplication() {
  if (!isCandidateSession()) return null;
  const applications = candidateApplications().filter(canStartInterview);
  return applications.find((app) => app.id === state.currentInterviewApplicationId) || applications[0] || null;
}

function canStartInterview(application) {
  return Boolean(application?.interviewUnlocked) && Number(application.match?.overall_score || 0) >= INTERVIEW_MIN_SCORE;
}

function buildAiValidationMessage(match, job) {
  const score = Math.round(match.overall_score || 0);
  if (score >= INTERVIEW_MIN_SCORE) {
    return `Votre candidature pour ${job.title} est validee par le RAG avec un score de ${score}%. Vous pouvez passer l'entretien AI.`;
  }
  return `Votre candidature pour ${job.title} a un score de ${score}%. Le seuil minimum est ${INTERVIEW_MIN_SCORE}%, donc l'entretien AI est bloque.`;
}

function renderAiValidation(application) {
  return `
    <div class="result-title">Message de validation IA</div>
    ${scoreBadge(application.match?.overall_score, "Matching CV")}
    <br>
    ${escapeHtml(application.aiValidationMessage)}<br>
    Competences trouvees: ${(application.match?.matched_skills || []).map(escapeHtml).join(", ") || "Aucune"}<br>
    Prochaine etape: ${application.interviewUnlocked ? `ouvrez "Mes candidatures" puis cliquez sur "Passer entretien AI".` : `ameliorez votre CV pour atteindre au moins ${INTERVIEW_MIN_SCORE}% et debloquer l'entretien AI.`}
  `;
}
