// Interview page renderers
// ============================================================

function renderInterviewGateMessage() {
  if (!els.interviewGateMessage) return;

  if (!isCandidateSession()) {
    els.interviewGateMessage.innerHTML = "Connectez-vous comme candidat pour passer un entretien AI.";
    return;
  }

  const application = selectedInterviewApplication();
  if (!application) {
    els.interviewGateMessage.innerHTML = "Postulez a une offre. Apres validation RAG, l'entretien sera disponible ici.";
    return;
  }

  els.interviewGateMessage.innerHTML = `
    <strong>Validation RAG recue</strong><br>
    ${escapeHtml(application.aiValidationMessage || "Votre candidature est validee pour la simulation d'entretien.")}<br>
    Entretien selectionne: ${escapeHtml(application.jobTitle)}
  `;
}

function renderInterviewPage() {
  if (!els.interviewJobTitle) return;

  const application = selectedInterviewApplication();
  const canInterview = isCandidateSession() && application;
  els.interviewCandidateName.textContent = canInterview ? application.candidateName : "-";
  els.interviewJobTitle.textContent = canInterview ? application.jobTitle : "Entretien candidat";
  els.interviewCvScore.textContent = canInterview ? `${Math.round(application.match?.overall_score || 0)}%` : "-";
  els.interviewStatusPill.textContent = canInterview ? interviewStatusLabel(application.interviewStatus) : "Bloque";
  els.interviewStatusPill.className = canInterview ? `pill pill-${application.interviewStatus || "ready"}` : "pill pill-locked";

  if (!canInterview) {
    els.interviewProgress.textContent = "0/0";
    els.questionsList.innerHTML = "";
    els.answerAnalysis.innerHTML = "";
    renderInterviewGateMessage();
    return;
  }

  state.questions = getInterviewQuestions(application);
  renderInterviewGateMessage();
  renderQuestions();
  if (application.interviewScore) {
    showResult(els.answerAnalysis, renderInterviewFeedback(application));
  }
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

function saveInterviewFeedback(application, feedback) {
  application.interviewStatus = "completed";
  application.interviewScore = Number(feedback.score ?? feedback.overall_score ?? 0);
  application.interviewFeedback = feedback.feedback || feedback.recommendation || feedback.analysis || "Feedback genere.";
  application.interviewDetails = {
    answers: feedback.answers || [],
    strengths: feedback.strengths || [],
    risks: feedback.risks || [],
    recommendation: feedback.recommendation || "",
    recruiterSummary: feedback.recruiterSummary || "",
    completedAt: new Date().toISOString()
  };
  application.updatedAt = new Date().toISOString();
  persist();
}

function renderInterviewFeedback(application) {
  return `
    <div class="result-title">Feedback entretien IA</div>
    ${scoreBadge(application.interviewScore, "Entretien")}
    <br>
    ${escapeHtml(application.interviewFeedback || "")}<br>
    <span class="muted">Le score et le detail sont maintenant visibles par le recruteur avec votre nom.</span>
  `;
}

function interviewStatusLabel(status) {
  const labels = {
    ready: "Pret",
    in_progress: "En cours",
    completed: "Termine"
  };
  return labels[status] || "Pret";
}

function getInterviewQuestions(application) {
  if (!application) return [];
  return application.interviewQuestions || [];
}

function countAnsweredQuestions() {
  return Array.from(document.querySelectorAll("[data-answer-index]"))
    .filter((textarea) => textarea.value.trim()).length;
}

function buildInterviewStrengths(analyses) {
  const keywords = analyses.flatMap((item) => item.matched_keywords || []);
  const unique = Array.from(new Set(keywords)).slice(0, 6);
  if (unique.length) {
    return [`Competences confirmees pendant l'entretien: ${unique.join(", ")}.`];
  }
  return ["Le candidat a donne des reponses exploitables pour la decision recruteur."];
}

function buildRecruiterInterviewSummary(application, analyses, score) {
  const best = analyses.slice().sort((a, b) => Number(b.score || 0) - Number(a.score || 0))[0];
  const weakest = analyses.slice().sort((a, b) => Number(a.score || 0) - Number(b.score || 0))[0];
  return `${application.candidateName} a obtenu ${Math.round(score)}% a l'entretien AI pour ${application.jobTitle}. Meilleure reponse: ${Math.round(best?.score || 0)}%. Point a verifier: ${trimText(weakest?.feedback || "Aucun point critique.", 120)}`;
}

function renderQuestions() {
  const application = selectedInterviewApplication();
  const questions = getInterviewQuestions(application);
  if (!state.questions.length) {
    els.questionsList.innerHTML = emptyHtml();
    els.interviewProgress.textContent = "0/0";
    return;
  }

  els.interviewProgress.textContent = `${application?.interviewStatus === "completed" ? questions.length : countAnsweredQuestions()}/${questions.length}`;
  els.questionsList.innerHTML = questions.map((question, index) => `
    <article class="item interview-question">
      <div class="question-meta">
        <strong>Question ${index + 1}</strong>
        <span>${escapeHtml(question.category || question.type || "AI")}</span>
      </div>
      <p>${escapeHtml(question.question || question.text || String(question))}</p>
      <textarea data-answer-index="${index}" rows="4" ${application?.interviewStatus === "completed" ? "disabled" : ""} placeholder="Votre reponse detaillee">${escapeHtml(application?.interviewDetails?.answers?.[index]?.answer || application?.interviewAnswers?.[index] || "")}</textarea>
      ${application?.interviewDetails?.answers?.[index] ? `<div class="answer-note">${scoreBadge(application.interviewDetails.answers[index].score, "Reponse")} ${escapeHtml(application.interviewDetails.answers[index].feedback || "")}</div>` : ""}
    </article>
  `).join("");
}

