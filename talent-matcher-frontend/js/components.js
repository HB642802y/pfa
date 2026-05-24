// UI components and shared DOM helpers
// ============================================================

function renderOptions(select, jobs) {
  select.innerHTML = jobs.length
    ? jobs.map((job) => `<option value="${escapeHtml(job.id)}">${escapeHtml(job.title)}</option>`).join("")
    : `<option value="">Aucune offre</option>`;
}

function showResult(element, html, isError = false) {
  element.innerHTML = `<div class="${isError ? "danger" : ""}">${html}</div>`;
}

function emptyHtml() {
  return document.getElementById("emptyTemplate").innerHTML;
}
