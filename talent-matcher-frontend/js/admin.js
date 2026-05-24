// Talent recommendations and admin data
// ============================================================

async function recommendTalents() {
  if (!canUseRecruiterArea()) {
    showResult(els.talentRecommendations, "Connectez-vous avec un compte recruteur cree par l'admin.", true);
    return;
  }

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
      <div class="item-head">
        <div>
          <h3>${escapeHtml(candidate.name)}</h3>
          <p>Compatibilite avec ${escapeHtml(job.title)}</p>
        </div>
        ${scoreBadge(match.overall_score, "Match")}
      </div>
      <div class="tag-row">${match.matched_skills.map((skill) => `<span class="tag">${escapeHtml(skill)}</span>`).join("")}</div>
    </article>
  `).join("");
  addLog(`Recommandation talents calculee par RAG pour ${job.title}`);
}

function addRecruiter(event) {
  event.preventDefault();
  if (!isAdminSession()) {
    showResult(els.adminLoginResult, "Connexion admin obligatoire pour creer un recruteur.", true);
    return;
  }

  const name = els.recruiterName.value.trim();
  const email = els.recruiterEmail.value.trim().toLowerCase();
  const password = els.recruiterPassword.value;
  if (!name || !email || password.length < 6) {
    return;
  }
  const existingRecruiter = state.recruiters.find((item) => item.email.toLowerCase() === email);
  if (existingRecruiter) {
    Object.assign(existingRecruiter, { name, password, role: "recruiter", status: "actif" });
    addLog(`Compte recruteur mis a jour: ${email}`);
  } else {
    state.recruiters.unshift({ id: `rec_${Date.now()}`, name, email, password, role: "recruiter", status: "actif" });
    addLog(`Compte recruteur cree: ${email}`);
  }
  persist();
  event.target.reset();
  renderAdmin();
}

function seedDemoData() {
  state.jobs = mergeById(state.jobs, demoJobs);
  if (!state.applications.length) {
    state.applications = [{
      id: "app_demo_1",
      candidateId: state.session?.role === "candidate" ? state.session.id : "candidate_demo_1",
      candidateName: "Sara El Mansouri",
      candidateEmail: state.session?.role === "candidate" ? state.session.email : "sara.demo@email.com",
      jobId: "job_demo_1",
      jobTitle: "Developpeur Full Stack React / FastAPI",
      cvText: demoCandidates[0].cvText,
      coverLetter: "Je souhaite rejoindre votre equipe pour construire des interfaces utiles et des APIs solides.",
      match: localMatch(demoCandidates[0].cvText, demoJobs[0]),
      status: "validated_ai",
      aiValidationMessage: "Votre candidature demo est validee par le RAG. Vous pouvez passer l'entretien AI.",
      interviewUnlocked: true,
      interviewStatus: "ready",
      createdAt: new Date().toISOString()
    }];
  }
  persist();
  renderAll();
  addLog("Donnees demo chargees");
}

// ============================================================
