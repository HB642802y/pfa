// Admin page renderers
// ============================================================

function renderAdmin() {
  els.adminJobs.textContent = String(state.jobs.length);
  els.adminApplications.textContent = String(state.applications.length);
  els.adminBackend.textContent = state.backendOnline ? "ON" : "OFF";
  els.systemMonitor.innerHTML = `
    <div class="system-row"><span>API</span><strong>${escapeHtml(state.apiBase)}</strong></div>
    <div class="system-row"><span>Etat</span>${state.backendOnline ? `<span class="badge badge-success">Backend connecte</span>` : `<span class="badge badge-warning">Mode demo local</span>`}</div>
    <div class="system-row"><span>Stockage</span><strong>localStorage + FastAPI si disponible</strong></div>
  `;

  if (!state.recruiters.length) {
    els.recruitersList.innerHTML = emptyHtml();
    return;
  }

  els.recruitersList.innerHTML = state.recruiters.map((recruiter) => `
    <article class="item">
      <div class="item-head">
        <div>
          <h3>${escapeHtml(recruiter.name)}</h3>
          <p>${escapeHtml(recruiter.email)}</p>
        </div>
      </div>
      <div class="item-actions">
        <button data-edit-recruiter="${recruiter.id}" class="secondary">Modifier</button>
        <button data-delete-recruiter="${recruiter.id}" class="danger">Supprimer</button>
      </div>
    </article>
  `).join("");
}

// ============================================================
