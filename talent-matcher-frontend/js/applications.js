// Candidate applications and CV matching
// ============================================================

async function submitApplication(event) {
  event.preventDefault();
  if (!isCandidateSession()) {
    showResult(els.candidateResult, "Inscrivez-vous ou connectez-vous comme candidat avant de postuler.", true);
    return;
  }

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
      addLog(`CV analyse par le RAG: ${file.name}`);
    } catch (error) {
      addLog(`Analyse CV RAG echouee: ${cleanError(error)}`);
    }
  }

  if (!cvText) {
    cvText = "React Python FastAPI MongoDB API REST recrutement analytics";
  }

  const match = await calculateMatch(cvText, job, parsedCv);
  const interviewUnlocked = Number(match.overall_score || 0) >= INTERVIEW_MIN_SCORE;
  const application = {
    id: `app_${Date.now()}`,
    candidateId: state.session.id,
    candidateName: state.session.name || state.session.email,
    candidateEmail: state.session.email,
    jobId: job.id,
    jobTitle: job.title,
    cvText,
    coverLetter: els.coverLetter.value.trim(),
    match,
    status: "validated_ai",
    aiValidationMessage: buildAiValidationMessage(match, job),
    interviewUnlocked,
    interviewStatus: interviewUnlocked ? "ready" : "locked",
    createdAt: new Date().toISOString()
  };

  state.applications.unshift(application);
  if (interviewUnlocked) {
    state.currentInterviewApplicationId = application.id;
    localStorage.setItem("currentInterviewApplicationId", application.id);
  }
  state.cvAnalyses.push({ id: application.id, cvText, parsedCv, match });
  persist();
  event.target.reset();
  renderAll();
  showResult(els.candidateResult, renderAiValidation(application));

  // Notify recruiter about new application
  notifyRecruiterAboutApplication(application, job);
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
      addLog(`Matching RAG calcule pour ${job.title}`);
      return normalizeMatch(match);
    } catch (error) {
      addLog(`Matching RAG indisponible, calcul local: ${cleanError(error)}`);
    }
  }

  return localMatch(cvText, job);
}

async function notifyRecruiterAboutApplication(application, job) {
  try {
    const response = await fetch(`${state.apiBase}/notifications/application`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${state.authToken}`
      },
      body: JSON.stringify({
        application_id: application.id,
        candidate_name: application.candidateName,
        candidate_email: application.candidateEmail,
        job_id: job.id,
        job_title: job.title,
        match_score: application.match.overall_score,
        status: application.status
      })
    });

    if (response.ok) {
      addLog(`Notification envoyée au recruteur pour ${job.title}`);
    } else {
      addLog(`Échec de la notification au recruteur`);
    }
  } catch (error) {
    console.error("Error notifying recruiter:", error);
    addLog(`Notification locale: Nouvelle candidature pour ${job.title}`);
  }
}

// ============================================================

