// Renderers
// ============================================================

function renderAll() {
  renderAccess();
  renderLanding();
  renderJobs();
  renderApplications();
  renderInterviewPage();
  renderRecruiter();
  renderAdmin();
  renderCandidates();
  renderJobsToValidate();
  renderAdminStatistics();
}

function renderLanding() {
  if (!els.landingJobs) return;
  const scores = state.applications.map((app) => Number(app.match?.overall_score || 0)).filter(Boolean);
  const averageScore = scores.length
    ? Math.round(scores.reduce((sum, score) => sum + score, 0) / scores.length)
    : 0;
  els.landingJobs.textContent = String(state.jobs.length);
  els.landingApplications.textContent = String(state.applications.length);
  els.landingBackend.textContent = state.backendOnline ? "ON" : "OFF";
  if (els.landingScore) {
    els.landingScore.textContent = `${averageScore}%`;
  }
}

