// AI interview flow
// ============================================================

async function generateQuestions() {
  const application = selectedInterviewApplication();
  if (!application) {
    showResult(els.answerAnalysis, "Postulez d'abord a une offre pour recevoir la validation RAG et passer l'entretien.", true);
    return;
  }

  const job = state.jobs.find((item) => item.id === application.jobId) || selectedJob() || state.jobs[0] || demoJobs[0];
  let questions = [];

  if (state.backendOnline) {
    try {
      const payload = await apiFetch("/interview/generate-questions", {
        method: "POST",
        body: JSON.stringify(normalizeJobForApi(job))
      });
      questions = Array.isArray(payload) ? payload : normalizeList(payload);
      addLog(`Questions entretien generees par RAG pour ${job.title}`);
    } catch (error) {
      addLog(`Generation questions RAG echouee: ${cleanError(error)}`);
    }
  }

  if (!questions.length) {
    questions = localQuestions(job);
  }

  state.questions = questions.slice(0, 5);
  application.interviewQuestions = state.questions;
  application.interviewAnswers = application.interviewAnswers || {};
  application.interviewStatus = "in_progress";
  state.currentInterviewApplicationId = application.id;
  localStorage.setItem("currentInterviewApplicationId", application.id);
  persist();
  renderAll();
}

async function analyzeAnswer() {
  const application = selectedInterviewApplication();
  if (!application) {
    showResult(els.answerAnalysis, "Aucun entretien actif. Lancez l'entretien depuis une candidature validee.", true);
    return;
  }

  const questions = getInterviewQuestions(application);
  const answers = Array.from(document.querySelectorAll("[data-answer-index]")).map((textarea) => ({
    index: Number(textarea.dataset.answerIndex),
    answer: textarea.value.trim()
  }));
  const missingAnswer = answers.find((item) => !item.answer);
  if (!questions.length || missingAnswer) {
    showResult(els.answerAnalysis, "Generez les questions puis repondez a chaque question avant d'envoyer le score.", true);
    return;
  }

  const analyses = [];
  for (const item of answers) {
    const question = questions[item.index];
    const analysis = await analyzeInterviewAnswer(question, item.answer);
    analyses.push({ question, answer: item.answer, ...analysis });
  }

  const score = analyses.reduce((sum, item) => sum + Number(item.score || 0), 0) / analyses.length;
  const weakAnswers = analyses.filter((item) => Number(item.score || 0) < 65).length;
  saveInterviewFeedback(application, {
    score,
    feedback: score >= 75
      ? "Entretien convaincant: les reponses sont structurees et proches des attentes du poste."
      : "Entretien a approfondir: ajoutez plus d'exemples concrets, resultats chiffres et liens avec les competences demandees.",
    recommendation: score >= 75 ? "recommande_entretien_recruteur" : "a_revoir",
    answers: analyses,
    strengths: buildInterviewStrengths(analyses),
    risks: weakAnswers ? [`${weakAnswers} reponse(s) doivent etre approfondies.`] : ["Aucun risque majeur detecte dans les reponses."],
    recruiterSummary: buildRecruiterInterviewSummary(application, analyses, score)
  });
  showResult(els.answerAnalysis, renderInterviewFeedback(application));
  addLog(`Score entretien envoye au recruteur pour ${application.candidateName}: ${Math.round(score)}%`);
  renderAll();
}

async function analyzeInterviewAnswer(question, answer) {
  if (state.backendOnline) {
    try {
      const analysis = await apiFetch("/interview/analyze-answer", {
        method: "POST",
        body: JSON.stringify({ question, answer, response_time: 90 })
      });
      const normalized = normalizeObject(analysis);
      return {
        score: Number(normalized.score ?? normalized.overall_score ?? 0),
        feedback: normalized.feedback || normalized.recommendation || "Analyse generee.",
        matched_keywords: normalized.matched_keywords || []
      };
    } catch (error) {
      addLog(`Analyse reponse RAG echouee, calcul local: ${cleanError(error)}`);
    }
  }

  const keywords = question.keywords || [];
  const keywordScore = keywords.length ? overlapScore(answer, keywords.join(" ")) * 0.6 : 20;
  const lengthScore = Math.min(30, answer.length / 12);
  const structureScore = /projet|resultat|impact|solution|equipe|client/i.test(answer) ? 10 : 4;
  const score = Math.min(96, Math.round(keywordScore + lengthScore + structureScore));
  return {
    score,
    feedback: score >= 70 ? "Reponse claire et alignee." : "Reponse a renforcer avec un exemple et un resultat mesurable.",
    matched_keywords: keywords.filter((keyword) => containsSkill(answer, keyword))
  };
}

// ============================================================

