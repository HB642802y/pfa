// Shared page helpers
// ============================================================

function statusLabel(status) {
  const labels = {
    reviewing: "En analyse",
    validated_ai: "Validee par RAG",
    rejected: "Refusee",
    accepted: "Acceptee"
  };
  return labels[status] || status || "En analyse";
}

function statusTone(status) {
  const tones = {
    accepted: "success",
    validated_ai: "success",
    interview_scheduled: "info",
    reviewing: "warning",
    pending: "warning",
    rejected: "danger"
  };
  return tones[status] || "neutral";
}

function statusBadge(status) {
  return `<span class="badge badge-${statusTone(status)}">${escapeHtml(statusLabel(status))}</span>`;
}

function interviewBadge(application) {
  if (application?.interviewStatus === "completed") {
    return `<span class="badge badge-success">Entretien termine</span>`;
  }
  if (application?.interviewUnlocked) {
    return `<span class="badge badge-info">Entretien debloque</span>`;
  }
  return `<span class="badge badge-warning">Entretien verrouille</span>`;
}

function scoreTone(value) {
  const score = Number(value || 0);
  if (score >= 75) return "high";
  if (score >= 60) return "mid";
  return "low";
}

function scoreBadge(value, label = "Score") {
  const score = Math.round(Number(value || 0));
  return `<span class="score-badge score-${scoreTone(score)}"><span>${escapeHtml(label)}</span><strong>${score}%</strong></span>`;
}

