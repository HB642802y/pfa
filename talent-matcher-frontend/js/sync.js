// Backend synchronization
// ============================================================

async function checkHealth() {
  try {
    const health = await apiFetch("/health");
    state.backendOnline = true;
    els.apiStatus.textContent = `Connecte: ${health.status || "ok"}`;
    els.apiStatus.className = "status ok";
    addLog("Backend disponible via /health");
  } catch (error) {
    state.backendOnline = false;
    els.apiStatus.textContent = "Backend indisponible, mode demo actif";
    els.apiStatus.className = "status bad";
    addLog("Mode demo actif: backend non disponible");
  }
  renderAdmin();
}

async function syncJobs() {
  await checkHealth();
  if (!state.backendOnline) {
    renderAll();
    return;
  }

  try {
    const payload = await apiFetch("/jobs");
    const jobs = normalizeList(payload);
    if (jobs.length) {
      state.jobs = mergeById(state.jobs, jobs);
      persist();
      addLog(`${jobs.length} offres synchronisees depuis /jobs`);
    }
  } catch (error) {
    addLog(`Synchronisation /jobs impossible: ${cleanError(error)}`);
  }
  renderAll();
}

// ============================================================

