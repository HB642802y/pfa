// Recruiter page renderers
// ============================================================

function renderRecruiter() {
  renderRecruiterJobs();
  const bestScore = state.applications.length
    ? Math.max(...state.applications.map((app) => Number(app.match?.overall_score || 0)))
    : 0;
  if (els.recruiterJobMetric) els.recruiterJobMetric.textContent = String(state.jobs.length);
  if (els.recruiterAppMetric) els.recruiterAppMetric.textContent = String(state.applications.length);
  if (els.recruiterBestScore) els.recruiterBestScore.textContent = `${Math.round(bestScore)}%`;
  els.recruiterApplicationCount.textContent = String(state.applications.length);
  if (!state.applications.length) {
    els.recruiterApplications.innerHTML = emptyHtml();
    return;
  }

  els.recruiterApplications.innerHTML = `
    <table>
      <thead>
        <tr>
          <th>Candidat / nom</th>
          <th>Offre</th>
          <th>Score CV</th>
          <th>Score entretien</th>
          <th>Competences detectees</th>
          <th>Statut</th>
          <th>Details</th>
        </tr>
      </thead>
      <tbody>
        ${state.applications.map((app) => `
          <tr class="application-row">
            <td><strong>${escapeHtml(app.candidateName)}</strong><div class="muted">${escapeHtml(app.candidateEmail || "")}</div></td>
            <td>${escapeHtml(app.jobTitle)}</td>
            <td>${scoreBadge(app.match?.overall_score, "CV")}</td>
            <td>${formatInterviewScore(app)}</td>
            <td>${(app.match?.matched_skills || []).map(escapeHtml).join(", ") || "Aucune"}</td>
            <td>${statusBadge(app.status)}<div class="badge-stack">${interviewBadge(app)}</div></td>
            <td><button type="button" class="secondary" data-action="toggle-score-details" data-application-id="${escapeHtml(app.id)}">Details score</button></td>
          </tr>
          <tr class="score-detail-row hidden" data-score-details="${escapeHtml(app.id)}">
            <td colspan="7">${renderScoreDetails(app)}</td>
          </tr>
        `).join("")}
      </tbody>
    </table>
  `;
}

function renderRecruiterJobs() {
  if (!state.jobs.length) {
    els.recruiterJobsList.innerHTML = emptyHtml();
    return;
  }

  els.recruiterJobsList.innerHTML = state.jobs.map((job) => `
    <article class="item">
      <div class="item-head">
        <div>
          <h3>${escapeHtml(job.title)}</h3>
          <p>${escapeHtml(job.location || job.work_location || "Lieu non precise")} · ${escapeHtml(job.experience_level || "niveau non precise")}</p>
        </div>
        <div class="item-actions">
          <button type="button" class="secondary" data-action="edit" data-job-id="${escapeHtml(job.id)}">Modifier</button>
          <button type="button" class="danger-btn" data-action="delete" data-job-id="${escapeHtml(job.id)}">Supprimer</button>
        </div>
      </div>
      <p>${escapeHtml(trimText(job.description, 170))}</p>
      <div class="tag-row">${(job.skills || []).map((skill) => `<span class="tag">${escapeHtml(skill)}</span>`).join("")}</div>
    </article>
  `).join("");
}

function formatInterviewScore(application) {
  if (!application.interviewScore) {
    return `<span class="muted">Entretien pas encore passe</span>`;
  }

  return `
    ${scoreBadge(application.interviewScore, "IA")}
    <div class="muted">${escapeHtml(trimText(application.interviewFeedback || "", 90))}</div>
  `;
}

function renderRecruiterInterviewDetails(application) {
  const details = application.interviewDetails;
  if (!details?.answers?.length) {
    return `<p><strong>Detail entretien par nom:</strong> aucun entretien complete pour ${escapeHtml(application.candidateName)}.</p>`;
  }

  return `
    <div class="interview-detail-block">
      <p><strong>Detail entretien de ${escapeHtml(application.candidateName)}:</strong> ${escapeHtml(details.recruiterSummary || "")}</p>
      <p><strong>Forces:</strong> ${(details.strengths || []).map(escapeHtml).join(" ") || "Non precise"}</p>
      <p><strong>Risques:</strong> ${(details.risks || []).map(escapeHtml).join(" ") || "Non precise"}</p>
      <div class="answer-list">
        ${details.answers.map((item, index) => `
          <div class="answer-detail">
            <strong>Q${index + 1} - ${Math.round(Number(item.score || 0))}%</strong>
            <p>${escapeHtml(item.question?.question || item.question?.text || "")}</p>
            <p><span>Reponse:</span> ${escapeHtml(trimText(item.answer || "", 260))}</p>
            <p><span>Feedback:</span> ${escapeHtml(item.feedback || "")}</p>
          </div>
        `).join("")}
      </div>
    </div>
  `;
}

function renderScoreDetails(application) {
  const match = application.match || {};
  const scoreItems = [
    ["Score global CV", match.overall_score],
    ["Competences", match.skills_score],
    ["Experience", match.experience_score],
    ["Education", match.education_score],
    ["Outils", match.tools_score],
    ["Entretien", application.interviewScore]
  ];

  return `
    <div class="score-details">
      <div>
        <h4>Detail score CV/RAG</h4>
        <div class="score-grid">
          ${scoreItems.map(([label, value]) => `
            <div class="score-cell">
              <span>${escapeHtml(label)}</span>
              <strong>${value == null ? "-" : `${Math.round(Number(value) || 0)}%`}</strong>
              <div class="score-bar"><span style="width: ${Math.max(0, Math.min(100, Number(value || 0)))}%"></span></div>
            </div>
          `).join("")}
        </div>
      </div>
      <div>
        <h4>Analyse</h4>
        <p><strong>Competences trouvees:</strong> ${(match.matched_skills || []).map(escapeHtml).join(", ") || "Aucune"}</p>
        <p><strong>Competences manquantes:</strong> ${(match.missing_skills || []).map(escapeHtml).join(", ") || "Aucune"}</p>
        <p><strong>Recommandations:</strong> ${(match.recommendations || []).map(escapeHtml).join(" ") || "Aucune recommandation."}</p>
        <p><strong>Feedback entretien:</strong> ${escapeHtml(application.interviewFeedback || "Entretien pas encore passe.")}</p>
        ${renderRecruiterInterviewDetails(application)}
      </div>
    </div>
  `;
}

