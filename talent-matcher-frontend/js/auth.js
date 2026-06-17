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
  els.candidateContent.classList.add("unlocked");
  els.candidateGate.style.display = "none";
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
  els.candidateLoginResult.innerHTML = "";
  els.candidateContent.classList.add("unlocked");
  els.candidateGate.style.display = "none";
  addLog(`Connexion candidat: ${email}`);
  switchView("candidate");
  renderAll();
  // Scroll to the "Postuler" section after login (first function in candidate flow)
  setTimeout(() => {
    const applicationSection = document.querySelector('#candidateContent .band.two-col .panel.card:nth-child(2)');
    if (applicationSection) {
      applicationSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
      // Focus on the job select
      const jobSelect = document.getElementById('applicationJob');
      if (jobSelect) {
        jobSelect.focus();
      }
    }
  }, 100);
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

async function loginAdmin(event) {
  event.preventDefault();
  const email = els.adminLoginEmail.value.trim().toLowerCase();
  const password = els.adminLoginPassword.value;

  try {
    // Try to login with backend first
    const response = await fetch(`${state.apiBase}/auth/login`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        email,
        password
      })
    });

    const data = await response.json();

    if (response.ok) {
      // Backend login successful
      state.authToken = data.access_token;
      state.currentUser = data.user;
      localStorage.setItem("authToken", state.authToken);
      localStorage.setItem("currentUser", JSON.stringify(state.currentUser));

      setSession({
        id: data.user.user_id || data.user.id,
        name: `${data.user.first_name} ${data.user.last_name}`,
        email: data.user.email,
        role: data.user.role
      });
      els.adminLoginForm.reset();
      els.adminLoginResult.innerHTML = "";
      els.adminContent.classList.add("unlocked");
      els.adminGate.style.display = "none";
      addLog("Connexion admin reussie (backend)");
      switchView("admin");
      renderAll();
      // Scroll to the "Gerer recruteurs" section after login (first function in admin flow)
      setTimeout(() => {
        const recruiterSection = document.querySelector('#adminContent .panel.card');
        if (recruiterSection) {
          recruiterSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
          // Focus on the recruiter name input
          const recruiterNameInput = document.getElementById('recruiterName');
          if (recruiterNameInput) {
            recruiterNameInput.focus();
          }
        }
      }, 100);
    } else {
      // Backend login failed, try local fallback
      if (email !== defaultAdmin.email || password !== defaultAdmin.password) {
        showResult(els.adminLoginResult, `Identifiants incorrects. Backend: ${data.detail || 'Erreur'}`, true);
        return;
      }

      setSession({
        id: defaultAdmin.id,
        name: defaultAdmin.name,
        email: defaultAdmin.email,
        role: defaultAdmin.role
      });
      els.adminLoginForm.reset();
      els.adminContent.classList.add("unlocked");
      els.adminGate.style.display = "none";
      addLog("Connexion admin reussie (mode local)");
      switchView("admin");
      renderAll();
      // Scroll to the "Gerer recruteurs" section after login (first function in admin flow)
      setTimeout(() => {
        const recruiterSection = document.querySelector('#adminContent .panel.card');
        if (recruiterSection) {
          recruiterSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
          // Focus on the recruiter name input
          const recruiterNameInput = document.getElementById('recruiterName');
          if (recruiterNameInput) {
            recruiterNameInput.focus();
          }
        }
      }, 100);
    }
  } catch (error) {
    console.error("Backend login error:", error);
    // Fallback to local login
    if (email !== defaultAdmin.email || password !== defaultAdmin.password) {
      showResult(els.adminLoginResult, "Backend indisponible. Identifiants admin incorrects. Demo: admin@pfam.local / admin123", true);
      return;
    }

    setSession({
      id: defaultAdmin.id,
      name: defaultAdmin.name,
      email: defaultAdmin.email,
      role: defaultAdmin.role
    });
    els.adminLoginForm.reset();
    els.adminContent.classList.add("unlocked");
    els.adminGate.style.display = "none";
    addLog("Connexion admin reussie (mode local - backend indisponible)");
    switchView("admin");
    renderAll();
    // Scroll to the "Gerer recruteurs" section after login (first function in admin flow)
    setTimeout(() => {
      const recruiterSection = document.querySelector('#adminContent .panel.card');
      if (recruiterSection) {
        recruiterSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
        // Focus on the recruiter name input
        const recruiterNameInput = document.getElementById('recruiterName');
        if (recruiterNameInput) {
          recruiterNameInput.focus();
        }
      }
    }, 100);
  }
}

async function loginRecruiter(event) {
  event.preventDefault();
  const email = els.recruiterLoginEmail.value.trim().toLowerCase();
  const password = els.recruiterLoginPassword.value;

  try {
    // Try to login with backend first
    const response = await fetch(`${state.apiBase}/auth/login`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        email,
        password
      })
    });

    const data = await response.json();

    if (response.ok) {
      // Backend login successful
      state.authToken = data.access_token;
      state.currentUser = data.user;
      localStorage.setItem("authToken", state.authToken);
      localStorage.setItem("currentUser", JSON.stringify(state.currentUser));

      setSession({
        id: data.user.user_id || data.user.id,
        name: `${data.user.first_name} ${data.user.last_name}`,
        email: data.user.email,
        role: data.user.role
      });
      els.recruiterLoginForm.reset();
      els.recruiterContent.classList.add("unlocked");
      els.recruiterGate.style.display = "none";
      addLog(`Connexion recruteur: ${email} (backend)`);
      switchView("recruiter");
      renderAll();
      // Scroll to the "Creer une offre" section after login (first function in recruiter flow)
      setTimeout(() => {
        const jobSection = document.querySelector('#recruiterContent .band.two-col .panel.card:nth-child(1)');
        if (jobSection) {
          jobSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
          // Focus on the job title input
          const jobTitleInput = document.getElementById('jobTitle');
          if (jobTitleInput) {
            jobTitleInput.focus();
          }
        }
      }, 100);
    } else {
      // Backend login failed, try local fallback
      const recruiter = state.recruiters.find((item) => item.email.toLowerCase() === email);
      if (!recruiter || recruiter.password !== password) {
        showResult(els.recruiterLoginResult, `Compte recruteur introuvable. Backend: ${data.detail || 'Erreur'}`, true);
        return;
      }

      setSession({
        id: recruiter.id,
        name: recruiter.name,
        email: recruiter.email,
        role: "recruiter"
      });
      els.recruiterLoginForm.reset();
      els.recruiterLoginResult.innerHTML = "";
      els.recruiterContent.classList.add("unlocked");
      els.recruiterGate.style.display = "none";
      addLog(`Connexion recruteur: ${recruiter.email} (mode local)`);
      switchView("recruiter");
      renderAll();
      // Scroll to the "Creer une offre" section after login (first function in recruiter flow)
      setTimeout(() => {
        const jobSection = document.querySelector('#recruiterContent .band.two-col .panel.card:nth-child(1)');
        if (jobSection) {
          jobSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
          // Focus on the job title input
          const jobTitleInput = document.getElementById('jobTitle');
          if (jobTitleInput) {
            jobTitleInput.focus();
          }
        }
      }, 100);
    }
  } catch (error) {
    console.error("Backend login error:", error);
    // Fallback to local login
    const recruiter = state.recruiters.find((item) => item.email.toLowerCase() === email);
    if (!recruiter || recruiter.password !== password) {
      showResult(els.recruiterLoginResult, "Backend indisponible. Compte recruteur introuvable. L'admin doit d'abord creer ce compte.", true);
      return;
    }

    setSession({
      id: recruiter.id,
      name: recruiter.name,
      email: recruiter.email,
      role: "recruiter"
    });
    els.recruiterLoginForm.reset();
    els.recruiterContent.classList.add("unlocked");
    els.recruiterGate.style.display = "none";
    addLog(`Connexion recruteur: ${recruiter.email} (mode local - backend indisponible)`);
    switchView("recruiter");
    renderAll();
    // Scroll to the "Creer une offre" section after login (first function in recruiter flow)
    setTimeout(() => {
      const jobSection = document.querySelector('#recruiterContent .band.two-col .panel.card:nth-child(1)');
      if (jobSection) {
        jobSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
        // Focus on the job title input
        const jobTitleInput = document.getElementById('jobTitle');
        if (jobTitleInput) {
          jobTitleInput.focus();
        }
      }
    }, 100);
  }
}

function setSession(session) {
  state.session = session;
  localStorage.setItem("session", JSON.stringify(session));
}

function logout() {
  const previousRole = state.session?.role;
  state.session = null;
  state.authToken = null;
  state.currentUser = null;
  state.currentInterviewApplicationId = null;
  localStorage.removeItem("session");
  localStorage.removeItem("authToken");
  localStorage.removeItem("currentUser");
  localStorage.removeItem("currentInterviewApplicationId");

  // Reset locked content classes
  els.candidateContent.classList.remove("unlocked");
  els.adminContent.classList.remove("unlocked");
  els.recruiterContent.classList.remove("unlocked");

  // Reset gate displays
  els.candidateGate.style.display = "block";
  els.adminGate.style.display = "block";
  els.recruiterGate.style.display = "block";

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
  if (els.authStatus) {
    els.authStatus.textContent = label;
  }
  if (els.logoutBtn) {
    els.logoutBtn.classList.toggle("hidden", !state.session);
  }

  // Candidate access
  if (els.candidateGate && els.candidateContent) {
    if (isCandidateSession()) {
      els.candidateGate.style.display = "none";
      els.candidateContent.classList.add("unlocked");
    } else {
      els.candidateGate.style.display = "block";
      els.candidateContent.classList.remove("unlocked");
    }
  }
  if (els.candidateSessionLabel) {
    els.candidateSessionLabel.textContent = isCandidateSession()
      ? `Candidat: ${state.session?.name || state.session?.email || ""}`
      : "";
  }

  // Admin access
  if (els.adminGate && els.adminContent) {
    if (isAdminSession()) {
      els.adminGate.style.display = "none";
      els.adminContent.classList.add("unlocked");
    } else {
      els.adminGate.style.display = "block";
      els.adminContent.classList.remove("unlocked");
    }
  }

  // Recruiter access
  if (els.recruiterGate && els.recruiterContent) {
    if (canUseRecruiterArea()) {
      els.recruiterGate.style.display = "none";
      els.recruiterContent.classList.add("unlocked");
    } else {
      els.recruiterGate.style.display = "block";
      els.recruiterContent.classList.remove("unlocked");
    }
  }
  if (els.recruiterSessionLabel) {
    els.recruiterSessionLabel.textContent = canUseRecruiterArea()
      ? `${isAdminSession() ? "Mode admin" : "Compte recruteur"}: ${state.session?.email || ""}`
      : "";
  }
  if (typeof renderInterviewGateMessage === "function") {
    renderInterviewGateMessage();
  }
}

function roleLabel(role) {
  if (role === "admin") return "Admin";
  if (role === "recruiter") return "Recruteur";
  if (role === "candidate") return "Candidat";
  return "Invite";
}

// ============================================================

