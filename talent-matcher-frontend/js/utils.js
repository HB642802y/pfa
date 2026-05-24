// Generic utilities and persistence
// ============================================================

function mergeById(current, incoming) {
  const map = new Map(current.map((item) => [item.id, item]));
  incoming.forEach((item) => {
    const id = item.id || item._id || `item_${Date.now()}_${Math.random()}`;
    map.set(id, { ...item, id });
  });
  return Array.from(map.values());
}

function extractSkills(text) {
  const known = ["React", "JavaScript", "Python", "FastAPI", "MongoDB", "SQL", "Docker", "AWS", "API REST", "Analytics", "Power BI", "Node.js"];
  return known.filter((skill) => containsSkill(text, skill));
}

function containsSkill(text, skill) {
  return String(text || "").toLowerCase().includes(String(skill || "").toLowerCase());
}

function overlapScore(a, b) {
  const wordsA = new Set(String(a).toLowerCase().split(/[^a-z0-9+#.]+/).filter((word) => word.length > 2));
  const wordsB = String(b).toLowerCase().split(/[^a-z0-9+#.]+/).filter((word) => word.length > 2);
  if (!wordsB.length) return 0;
  const hits = wordsB.filter((word) => wordsA.has(word)).length;
  return Math.min(100, (hits / Math.max(8, wordsB.length)) * 100);
}

function splitCsv(value) {
  return String(value || "").split(",").map((item) => item.trim()).filter(Boolean);
}

function numberOrNull(value) {
  const parsed = Number(value);
  return Number.isFinite(parsed) && parsed > 0 ? parsed : null;
}

function addLog(message) {
  const time = new Date().toLocaleTimeString("fr-FR", { hour: "2-digit", minute: "2-digit" });
  state.logs.push(`[${time}] ${message}`);
}

function persist() {
  localStorage.setItem("jobs", JSON.stringify(state.jobs));
  localStorage.setItem("applications", JSON.stringify(state.applications));
  localStorage.setItem("candidates", JSON.stringify(state.candidates));
  localStorage.setItem("recruiters", JSON.stringify(state.recruiters));
  localStorage.setItem("cvAnalyses", JSON.stringify(state.cvAnalyses));
  if (state.selectedCandidateJobId) {
    localStorage.setItem("selectedCandidateJobId", state.selectedCandidateJobId);
  }
  if (state.currentInterviewApplicationId) {
    localStorage.setItem("currentInterviewApplicationId", state.currentInterviewApplicationId);
  }
}

function trimText(value, max) {
  const text = String(value || "");
  return text.length > max ? `${text.slice(0, max - 3)}...` : text;
}

function cleanError(error) {
  return String(error?.message || error).slice(0, 180);
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

