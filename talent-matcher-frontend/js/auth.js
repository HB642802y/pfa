// Authentication and session
// ============================================================

function registerCandidate(event) {
  event.preventDefault();
  const name = els.candidateRegisterName.value.trim();
  const email = els.candidateRegisterEmail.value.trim().toLowerCase();
  const password = els.candidateRegisterPassword.value;

  if (!name || !email || password.length < 6) {
    showResult(els.candidateRegisterResult, "Completez le nom, un email valide et un mot de passe de 6 caracteres minimum.", true);
    return;
  }

  if (state.candidates.some((candidate) => candidate.email.toLowerCase() === email)) {
    showResult(els.candidateRegisterResult, "Ce compte candidat existe deja. Connectez-vous avec cet email.", true);
    return;
  }

  const candidate = {
    id: `cand_${Date.now()}`,
    name,
    email,
    password,
    role: "candidate",
    createdAt: new Date().toISOString()
  };
  state.candidates.unshift(candidate);
  persist();
  setSession({ id: candidate.id, name: candidate.name, email: candidate.email, role: "candidate" });
  els.candidateRegisterForm.reset();
  showResult(els.candidateResult, `Compte candidat cree pour ${escapeHtml(candidate.name)}. Vous pouvez maintenant consulter les offres et postuler.`);
  addLog(`Compte candidat cree: ${email}`);
  renderAll();
}

function loginCandidate(event) {
  event.preventDefault();
  const email = els.candidateLoginEmail.value.trim().toLowerCase();
  const password = els.candidateLoginPassword.value;
  const candidate = state.candidates.find((item) => item.email.toLowerCase() === email);

  if (!candidate || candidate.password !== password) {
    showResult(els.candidateLoginResult, "Email ou mot de passe candidat incorrect.", true);
    return;
  }

  setSession({ id: candidate.id, name: candidate.name, email: candidate.email, role: "candidate" });
  els.candidateLoginForm.reset();
  addLog(`Connexion candidat: ${email}`);
  renderAll();
}

function setCandidateAuthMode(mode) {
  const isRegister = mode === "register";
  els.candidateLoginForm.classList.toggle("active", !isRegister);
  els.candidateRegisterForm.classList.toggle("active", isRegister);
  els.showCandidateLogin.classList.toggle("active", !isRegister);
  els.showCandidateRegister.classList.toggle("active", isRegister);
  els.candidateLoginResult.innerHTML = "";
  els.candidateRegisterResult.innerHTML = "";
}

function loginAdmin(event) {
  event.preventDefault();
  const email = els.adminLoginEmail.value.trim().toLowerCase();
  const password = els.adminLoginPassword.value;

  if (email !== defaultAdmin.email || password !== defaultAdmin.password) {
    showResult(els.adminLoginResult, "Identifiants admin incorrects. Demo: admin@pfam.local / admin123", true);
    return;
  }

  setSession({
    id: defaultAdmin.id,
    name: defaultAdmin.name,
    email: defaultAdmin.email,
    role: defaultAdmin.role
  });
  els.adminLoginForm.reset();
  addLog("Connexion admin reussie");
  renderAll();
}

function loginRecruiter(event) {
  event.preventDefault();
  const email = els.recruiterLoginEmail.value.trim().toLowerCase();
  const password = els.recruiterLoginPassword.value;
  const recruiter = state.recruiters.find((item) => item.email.toLowerCase() === email);

  if (!recruiter || recruiter.password !== password) {
    showResult(els.recruiterLoginResult, "Compte recruteur introuvable. L'admin doit d'abord creer ce compte.", true);
    return;
  }

  setSession({
    id: recruiter.id,
    name: recruiter.name,
    email: recruiter.email,
    role: "recruiter"
  });
  els.recruiterLoginForm.reset();
  addLog(`Connexion recruteur: ${recruiter.email}`);
  renderAll();
}

function setSession(session) {
  state.session = session;
  localStorage.setItem("session", JSON.stringify(session));
}

function logout() {
  const previousRole = state.session?.role;
  state.session = null;
  state.currentInterviewApplicationId = null;
  localStorage.removeItem("session");
  localStorage.removeItem("currentInterviewApplicationId");
  addLog("Session fermee");
  if (previousRole === "candidate") switchView("candidate");
  if (previousRole === "admin") switchView("admin");
  if (previousRole === "recruiter") switchView("recruiter");
  renderAll();
}

function isCandidateSession() {
  return state.session?.role === "candidate";
}

function isAdminSession() {
  return state.session?.role === "admin";
}

function isRecruiterSession() {
  return state.session?.role === "recruiter";
}

function canUseRecruiterArea() {
  return isAdminSession() || isRecruiterSession();
}

function renderAccess() {
  const label = state.session
    ? `${roleLabel(state.session.role)}: ${state.session.email}`
    : "Invite";
  els.authStatus.textContent = label;
  els.logoutBtn.classList.toggle("hidden", !state.session);

  els.candidateGate.classList.toggle("hidden", isCandidateSession());
  els.candidateContent.classList.toggle("hidden", !isCandidateSession());
  els.candidateSessionLabel.textContent = isCandidateSession()
    ? `Candidat: ${state.session.name || state.session.email}`
    : "";

  els.adminGate.classList.toggle("hidden", isAdminSession());
  els.adminContent.classList.toggle("hidden", !isAdminSession());

  els.recruiterGate.classList.toggle("hidden", canUseRecruiterArea());
  els.recruiterContent.classList.toggle("hidden", !canUseRecruiterArea());
  els.recruiterSessionLabel.textContent = canUseRecruiterArea()
    ? `${isAdminSession() ? "Mode admin" : "Compte recruteur"}: ${state.session.email}`
    : "";
  renderInterviewGateMessage();
}

function roleLabel(role) {
  if (role === "admin") return "Admin";
  if (role === "recruiter") return "Recruteur";
  if (role === "candidate") return "Candidat";
  return "Invite";
}

// ============================================================

