// Talent recommendations and admin data
// ============================================================

async function addCandidate(event) {
  event.preventDefault();
  if (!isAdminSession()) {
    showResult(els.adminLoginResult, "Connexion admin obligatoire pour creer un candidat.", true);
    return;
  }

  const name = els.candidateName.value.trim();
  const email = els.candidateEmail.value.trim().toLowerCase();
  const password = els.candidatePassword.value;
  if (!name || !email || password.length < 6) {
    showResult(els.adminLoginResult, "Completez tous les champs (minimum 6 caracteres pour le mot de passe).", true);
    return;
  }

  // Split name into first_name and last_name
  const nameParts = name.split(" ");
  const first_name = nameParts[0] || name;
  const last_name = nameParts.slice(1).join(" ") || "";

  try {
    const response = await fetch(`${state.apiBase}/admin/create-candidate`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${state.authToken}`
      },
      body: JSON.stringify({
        first_name,
        last_name,
        email,
        password,
        role: "candidate"
      })
    });

    const data = await response.json();

    if (response.ok) {
      // Add to local state
      state.candidates.unshift({
        id: data.user_id || data.id || `cand_${Date.now()}`,
        name,
        email,
        password,
        role: "candidate",
        status: "actif"
      });
      localStorage.setItem("candidates", JSON.stringify(state.candidates));
      event.target.reset();
      renderCandidates();
      addLog(`Compte candidat cree: ${email}`);
      alert(`Candidat cree avec succes! Email: ${email}, Mot de passe: ${password}`);
    } else {
      showResult(els.adminLoginResult, `Erreur: ${data.detail}`, true);
    }
  } catch (error) {
    console.error("Error creating candidate:", error);
    // Fallback to local storage if backend is unavailable
    const existingCandidate = state.candidates.find((item) => item.email.toLowerCase() === email);
    if (existingCandidate) {
      Object.assign(existingCandidate, { name, password, role: "candidate", status: "actif" });
      addLog(`Compte candidat mis a jour localement: ${email}`);
    } else {
      state.candidates.unshift({ id: `cand_${Date.now()}`, name, email, password, role: "candidate", status: "actif" });
      addLog(`Compte candidat cree localement: ${email}`);
    }
    localStorage.setItem("candidates", JSON.stringify(state.candidates));
    event.target.reset();
    renderCandidates();
    alert(`Candidat cree localement (backend indisponible). Email: ${email}, Mot de passe: ${password}`);
  }
}

async function updateCandidate(event) {
  event.preventDefault();

  if (!isAdminSession()) {
    alert("Accès réservé aux administrateurs");
    return;
  }

  const candidateId = els.editCandidateId.value;
  const updateData = {
    first_name: els.editCandidateName.value.split(" ")[0] || els.editCandidateName.value,
    last_name: els.editCandidateName.value.split(" ").slice(1).join(" ") || "",
    email: els.editCandidateEmail.value,
    phone: els.editCandidatePhone.value || null,
    location: els.editCandidateLocation.value || null
  };

  try {
    const response = await fetch(`${state.apiBase}/admin/update-candidate/${candidateId}`, {
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
      const candidateIndex = state.candidates.findIndex(c => c.id === candidateId);
      if (candidateIndex !== -1) {
        state.candidates[candidateIndex] = {
          ...state.candidates[candidateIndex],
          name: els.editCandidateName.value,
          email: els.editCandidateEmail.value,
          phone: els.editCandidatePhone.value,
          location: els.editCandidateLocation.value
        };
        localStorage.setItem("candidates", JSON.stringify(state.candidates));
      }

      cancelEditCandidate();
      renderCandidates();
      addLog(`Candidat mis à jour: ${updateData.email}`);
      alert("Candidat mis à jour avec succès!");
    } else {
      alert(`Erreur: ${data.detail}`);
    }
  } catch (error) {
    console.error("Error updating candidate:", error);
    alert("Erreur de connexion au serveur");
  }
}

function cancelEditCandidate() {
  state.editingCandidateId = null;
  els.editCandidateForm.style.display = "none";
  els.editCandidatePlaceholder.style.display = "block";
  els.editCandidateForm.reset();
}

function handleCandidateListClick(event) {
  const button = event.target.closest("button[data-action][data-candidate-id]");
  if (!button) return;

  const candidateId = button.dataset.candidateId;
  const candidate = state.candidates.find((item) => item.id === candidateId);

  if (!candidate) return;

  if (button.dataset.action === "edit") {
    startCandidateEdit(candidateId);
  } else if (button.dataset.action === "delete") {
    deleteCandidate(candidateId, candidate.email);
  }
}

function startCandidateEdit(candidateId) {
  const candidate = state.candidates.find((item) => item.id === candidateId);
  if (!candidate) return;

  state.editingCandidateId = candidate.id;
  els.editCandidateId.value = candidate.id;
  els.editCandidateName.value = candidate.name || "";
  els.editCandidateEmail.value = candidate.email || "";
  els.editCandidatePhone.value = candidate.phone || "";
  els.editCandidateLocation.value = candidate.location || "";
  els.editCandidateForm.style.display = "block";
  els.editCandidatePlaceholder.style.display = "none";
}

function deleteCandidate(candidateId, email) {
  if (!confirm(`Êtes-vous sûr de vouloir supprimer le candidat ${email}?`)) {
    return;
  }

  // Remove from local state
  state.candidates = state.candidates.filter(c => c.id !== candidateId);
  localStorage.setItem("candidates", JSON.stringify(state.candidates));

  renderCandidates();
  addLog(`Candidat supprimé: ${email}`);
  alert(`Candidat supprimé!`);

  // Try backend in background
  try {
    const headers = {
      "Content-Type": "application/json"
    };

    if (state.authToken) {
      headers["Authorization"] = `Bearer ${state.authToken}`;
    }

    fetch(`${state.apiBase}/admin/delete-candidate/${candidateId}`, {
      method: "DELETE",
      headers: headers
    });
  } catch (error) {
    console.error("Error deleting candidate from backend:", error);
  }
}

function renderCandidates() {
  if (!els.candidatesList) return;

  if (!state.candidates.length) {
    els.candidatesList.innerHTML = '<div class="empty">Aucun candidat pour le moment.</div>';
    return;
  }

  els.candidatesList.innerHTML = state.candidates.map((candidate) => `
    <article class="item" data-candidate-id="${candidate.id}">
      <div class="item-head">
        <div>
          <h3>${escapeHtml(candidate.name)}</h3>
          <p>${escapeHtml(candidate.email)}</p>
        </div>
        <div class="item-actions">
          <button type="button" data-action="edit" data-candidate-id="${candidate.id}" class="secondary">Modifier</button>
          <button type="button" data-action="delete" data-candidate-id="${candidate.id}">Supprimer</button>
        </div>
      </div>
    </article>
  `).join("");
}

function renderJobsToValidate() {
  if (!els.jobsToValidate) return;

  const pendingJobs = state.jobs.filter(job => job.status === "pending" || job.status === "draft");

  if (!pendingJobs.length) {
    els.jobsToValidate.innerHTML = '<div class="empty">Aucune offre en attente de validation.</div>';
    return;
  }

  els.jobsToValidate.innerHTML = pendingJobs.map((job) => `
    <article class="item" data-job-id="${job.id}">
      <div class="item-head">
        <div>
          <h3>${escapeHtml(job.title)}</h3>
          <p>${escapeHtml(job.location || "Non précisé")}</p>
          <p class="small">${escapeHtml(job.description || "")}</p>
        </div>
        <div class="item-actions">
          <button type="button" data-action="validate" data-job-id="${job.id}" class="btn btn-primary">Valider</button>
          <button type="button" data-action="reject" data-job-id="${job.id}">Rejeter</button>
        </div>
      </div>
    </article>
  `).join("");
}

function renderAdminStatistics() {
  if (!els.adminTotalJobs) return;

  const totalJobs = state.jobs.length;
  const activeJobs = state.jobs.filter(job => job.status === "active").length;
  const pendingJobs = state.jobs.filter(job => job.status === "pending" || job.status === "draft").length;
  const totalCandidates = state.candidates.length;
  const totalRecruiters = state.recruiters.length;
  const totalApplications = state.applications.length;
  const scores = state.applications.map(app => Number(app.match?.overall_score || 0)).filter(Boolean);
  const avgScore = scores.length ? Math.round(scores.reduce((sum, score) => sum + score, 0) / scores.length) : 0;
  const totalInterviews = state.applications.filter(app => app.interviewStatus === "completed").length;

  els.adminTotalJobs.textContent = String(totalJobs);
  els.adminActiveJobs.textContent = String(activeJobs);
  els.adminPendingJobs.textContent = String(pendingJobs);
  els.adminTotalCandidates.textContent = String(totalCandidates);
  els.adminTotalRecruiters.textContent = String(totalRecruiters);
  els.adminTotalApplications.textContent = String(totalApplications);
  els.adminAvgScore.textContent = `${avgScore}%`;
  els.adminTotalInterviews.textContent = String(totalInterviews);
}

function handleJobsToValidateClick(event) {
  const button = event.target.closest("button[data-action][data-job-id]");
  if (!button) return;

  const jobId = button.dataset.jobId;
  const action = button.dataset.action;

  if (action === "validate") {
    validateJob(jobId);
  } else if (action === "reject") {
    rejectJob(jobId);
  }
}

async function validateJob(jobId) {
  if (!confirm("Voulez-vous valider cette offre?")) return;

  try {
    const response = await fetch(`${state.apiBase}/admin/validate-job/${jobId}`, {
      method: "PUT",
      headers: {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${state.authToken}`
      }
    });

    if (response.ok) {
      // Update local state
      const jobIndex = state.jobs.findIndex(j => j.id === jobId);
      if (jobIndex !== -1) {
        state.jobs[jobIndex].status = "active";
        state.jobs[jobIndex].validated_at = new Date().toISOString();
        localStorage.setItem("jobs", JSON.stringify(state.jobs));
      }
      renderJobsToValidate();
      addLog(`Offre validée: ${jobId}`);
      alert("Offre validée avec succès!");
    } else {
      const data = await response.json();
      alert(`Erreur: ${data.detail}`);
    }
  } catch (error) {
    console.error("Error validating job:", error);
    // Fallback to local update
    const jobIndex = state.jobs.findIndex(j => j.id === jobId);
    if (jobIndex !== -1) {
      state.jobs[jobIndex].status = "active";
      state.jobs[jobIndex].validated_at = new Date().toISOString();
      localStorage.setItem("jobs", JSON.stringify(state.jobs));
    }
    renderJobsToValidate();
    addLog(`Offre validée localement: ${jobId}`);
    alert("Offre validée (mode local)");
  }
}

async function rejectJob(jobId) {
  if (!confirm("Voulez-vous rejeter cette offre?")) return;

  try {
    const response = await fetch(`${state.apiBase}/admin/reject-job/${jobId}`, {
      method: "PUT",
      headers: {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${state.authToken}`
      }
    });

    if (response.ok) {
      // Update local state
      const jobIndex = state.jobs.findIndex(j => j.id === jobId);
      if (jobIndex !== -1) {
        state.jobs[jobIndex].status = "rejected";
        state.jobs[jobIndex].rejected_at = new Date().toISOString();
        localStorage.setItem("jobs", JSON.stringify(state.jobs));
      }
      renderJobsToValidate();
      addLog(`Offre rejetée: ${jobId}`);
      alert("Offre rejetée avec succès!");
    } else {
      const data = await response.json();
      alert(`Erreur: ${data.detail}`);
    }
  } catch (error) {
    console.error("Error rejecting job:", error);
    // Fallback to local update
    const jobIndex = state.jobs.findIndex(j => j.id === jobId);
    if (jobIndex !== -1) {
      state.jobs[jobIndex].status = "rejected";
      state.jobs[jobIndex].rejected_at = new Date().toISOString();
      localStorage.setItem("jobs", JSON.stringify(state.jobs));
    }
    renderJobsToValidate();
    addLog(`Offre rejetée localement: ${jobId}`);
    alert("Offre rejetée (mode local)");
  }
}

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

  let recommendations;

  // Try backend Content-Based Filtering first
  if (state.backendOnline) {
    try {
      const response = await fetch(`${state.apiBase}/recommend/talents`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${state.authToken}`
        },
        body: JSON.stringify({
          job_id: job.id,
          job_description: normalizeJobForApi(job)
        })
      });

      if (response.ok) {
        const data = await response.json();
        recommendations = data.recommendations || [];
        addLog(`Recommandation talents par Content-Based Filtering pour ${job.title}`);
      } else {
        throw new Error("Backend recommendation failed");
      }
    } catch (error) {
      console.error("Error getting backend recommendations:", error);
      addLog(`Content-Based Filtering indisponible, calcul local: ${cleanError(error)}`);
      // Fallback to local matching
      recommendations = candidates
        .map((candidate) => ({ candidate, match: localMatch(candidate.cvText, job) }))
        .sort((a, b) => b.match.overall_score - a.match.overall_score);
    }
  } else {
    // Local matching
    recommendations = candidates
      .map((candidate) => ({ candidate, match: localMatch(candidate.cvText, job) }))
      .sort((a, b) => b.match.overall_score - a.match.overall_score);
  }

  els.talentRecommendations.innerHTML = recommendations.map((rec) => {
    const candidate = rec.candidate || rec;
    const match = rec.match || { overall_score: 0, matched_skills: [] };
    return `
    <article class="item">
      <div class="item-head">
        <div>
          <h3>${escapeHtml(candidate.name)}</h3>
          <p>Compatibilite avec ${escapeHtml(job.title)}</p>
        </div>
        ${scoreBadge(match.overall_score, "Match")}
      </div>
      <div class="tag-row">${(match.matched_skills || []).map((skill) => `<span class="tag">${escapeHtml(skill)}</span>`).join("")}</div>
    </article>
  `}).join("");
  addLog(`Recommandation talents calculee pour ${job.title}`);
}

async function addRecruiter(event) {
  event.preventDefault();
  if (!isAdminSession()) {
    showResult(els.adminLoginResult, "Connexion admin obligatoire pour creer un recruteur.", true);
    return;
  }

  const name = els.recruiterName.value.trim();
  const email = els.recruiterEmail.value.trim().toLowerCase();
  const password = els.recruiterPassword.value;
  if (!name || !email || password.length < 6) {
    showResult(els.adminLoginResult, "Completez tous les champs (minimum 6 caracteres pour le mot de passe).", true);
    return;
  }

  // Split name into first_name and last_name
  const nameParts = name.split(" ");
  const first_name = nameParts[0] || name;
  const last_name = nameParts.slice(1).join(" ") || "";

  try {
    const response = await fetch(`${state.apiBase}/admin/create-recruiter`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${state.authToken}`
      },
      body: JSON.stringify({
        first_name,
        last_name,
        email,
        password,
        role: "recruiter"
      })
    });

    const data = await response.json();

    if (response.ok) {
      // Add to local state
      state.recruiters.unshift({
        id: data.user_id || data.id || `rec_${Date.now()}`,
        name,
        email,
        password,
        role: "recruiter",
        status: "actif"
      });
      localStorage.setItem("recruiters", JSON.stringify(state.recruiters));
      event.target.reset();
      renderAdmin();
      addLog(`Compte recruteur cree: ${email}`);
      alert(`Recruteur cree avec succes! Email: ${email}, Mot de passe: ${password}`);
    } else {
      showResult(els.adminLoginResult, `Erreur: ${data.detail}`, true);
    }
  } catch (error) {
    console.error("Error creating recruiter:", error);
    // Fallback to local storage if backend is unavailable
    const existingRecruiter = state.recruiters.find((item) => item.email.toLowerCase() === email);
    if (existingRecruiter) {
      Object.assign(existingRecruiter, { name, password, role: "recruiter", status: "actif" });
      addLog(`Compte recruteur mis a jour localement: ${email}`);
    } else {
      state.recruiters.unshift({ id: `rec_${Date.now()}`, name, email, password, role: "recruiter", status: "actif" });
      addLog(`Compte recruteur cree localement: ${email}`);
    }
    persist();
    event.target.reset();
    renderAdmin();
    alert(`Recruteur cree localement (backend indisponible). Email: ${email}, Mot de passe: ${password}`);
  }
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
