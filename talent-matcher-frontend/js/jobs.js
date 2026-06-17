// Recruiter job management
// ============================================================

async function createJob(event) {
  event.preventDefault();
  if (!canUseRecruiterArea()) {
    showResult(els.talentRecommendations, "Connectez-vous avec un compte recruteur cree par l'admin.", true);
    return;
  }

  const editingJob = state.jobs.find((item) => item.id === state.editingJobId);
  const job = {
    id: editingJob?.id || `job_${Date.now()}`,
    title: els.jobTitle.value.trim(),
    description: els.jobDescription.value.trim(),
    requirements: els.jobRequirements.value.trim(),
    skills: splitCsv(els.jobSkills.value),
    experience_level: els.experienceLevel.value,
    salary_min: numberOrNull(els.salaryMin.value),
    salary_max: null,
    location: els.jobLocation.value.trim() || "Non precise",
    status: "pending"
  };

  if (editingJob) {
    Object.assign(editingJob, job, { updatedAt: new Date().toISOString() });
    state.applications.forEach((app) => {
      if (app.jobId === editingJob.id) {
        app.jobTitle = job.title;
      }
    });
    addLog(`Offre modifiee: ${job.title}`);
    persist();
    event.target.reset();
    cancelJobEdit(false);
    renderAll();
    return;
  }

  let savedJob = job;
  if (state.backendOnline) {
    try {
      const headers = {
        "Content-Type": "application/json"
      };
      if (state.authToken) {
        headers["Authorization"] = `Bearer ${state.authToken}`;
      }
      const response = await fetch(`${state.apiBase}/recruiter/job/create`, {
        method: "POST",
        headers: headers,
        body: JSON.stringify(job)
      });
      const payload = await response.json();
      if (response.ok) {
        savedJob = normalizeObject(payload) || job;
        addLog(`Offre creee cote backend: ${savedJob.title}`);
      } else {
        addLog(`Creation backend echouee: ${payload.detail || 'Erreur'}`);
      }
    } catch (error) {
      addLog(`Creation backend echouee, sauvegarde locale: ${cleanError(error)}`);
    }
  }

  state.jobs = mergeById(state.jobs, [savedJob]);
  persist();
  event.target.reset();
  renderAll();
}

function handleRecruiterJobAction(event) {
  const scoreButton = event.target.closest("button[data-action='toggle-score-details'][data-application-id]");
  if (scoreButton && canUseRecruiterArea()) {
    toggleScoreDetails(scoreButton.dataset.applicationId);
    return;
  }

  const button = event.target.closest("button[data-action][data-job-id]");
  if (!button || !canUseRecruiterArea()) return;

  const jobId = button.dataset.jobId;
  if (button.dataset.action === "edit") {
    startJobEdit(jobId);
    return;
  }

  if (button.dataset.action === "delete") {
    deleteJob(jobId);
  }
}

function toggleScoreDetails(applicationId) {
  const row = document.querySelector(`[data-score-details="${CSS.escape(applicationId)}"]`);
  if (!row) return;
  row.classList.toggle("hidden");
}

function startJobEdit(jobId) {
  const job = state.jobs.find((item) => item.id === jobId);
  if (!job) return;

  state.editingJobId = job.id;
  els.jobTitle.value = job.title || "";
  els.experienceLevel.value = job.experience_level || "mid_level";
  els.jobLocation.value = job.location || job.work_location || "";
  els.salaryMin.value = job.salary_min || "";
  els.jobSkills.value = Array.isArray(job.skills) ? job.skills.join(", ") : String(job.skills || "");
  els.jobDescription.value = job.description || "";
  els.jobRequirements.value = job.requirements || "";
  els.jobFormTitle.textContent = "Modifier une offre";
  els.jobSubmit.textContent = "Enregistrer modification";
  els.cancelJobEdit.classList.remove("hidden");
  els.jobTitle.focus();
}

function cancelJobEdit(shouldReset = true) {
  state.editingJobId = null;
  els.jobFormTitle.textContent = "Creer une offre";
  els.jobSubmit.textContent = "Publier offre";
  els.cancelJobEdit.classList.add("hidden");
  if (shouldReset) {
    els.jobForm.reset();
  }
}

function deleteJob(jobId) {
  const job = state.jobs.find((item) => item.id === jobId);
  if (!job) return;

  const confirmed = window.confirm(`Supprimer l'offre "${job.title}" ?`);
  if (!confirmed) return;

  state.jobs = state.jobs.filter((item) => item.id !== jobId);
  if (state.editingJobId === jobId) {
    cancelJobEdit();
  }
  persist();
  addLog(`Offre supprimee: ${job.title}`);
  renderAll();
}

// ============================================================

