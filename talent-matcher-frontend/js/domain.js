// Domain helpers
// ============================================================

function selectedJob() {
  return state.jobs.find((job) => job.id === els.recommendationJob.value || job.id === els.applicationJob.value);
}

function localMatch(cvText, job) {
  const jobSkills = job.skills || splitCsv(job.skills || "");
  const cvSkills = extractSkills(cvText);
  const matched = jobSkills.filter((skill) => containsSkill(cvText, skill));
  const missing = jobSkills.filter((skill) => !containsSkill(cvText, skill));
  const skillsScore = jobSkills.length ? (matched.length / jobSkills.length) * 100 : 45;
  const textScore = overlapScore(cvText, `${job.description} ${job.requirements}`);
  const overall = Math.min(98, Math.max(18, skillsScore * 0.7 + textScore * 0.3));

  return {
    overall_score: overall,
    skills_score: skillsScore,
    experience_score: Math.min(95, 45 + textScore),
    education_score: 65,
    tools_score: skillsScore,
    matched_skills: matched.length ? matched : cvSkills.slice(0, 3),
    missing_skills: missing,
    recommendations: [
      overall >= 70 ? "Profil recommande pour entretien." : "Profil a examiner avec attention.",
      missing.length ? `Former ou verifier: ${missing.slice(0, 4).join(", ")}.` : "Competences principales couvertes."
    ]
  };
}

function localQuestions(job) {
  const skills = (job.skills || []).slice(0, 4);
  return [
    {
      id: 1,
      question: `Expliquez une experience concrete liee au poste ${job.title}.`,
      keywords: skills,
      difficulty: "medium"
    },
    {
      id: 2,
      question: `Comment utiliseriez-vous ${skills[0] || "vos competences"} pour resoudre un probleme urgent ?`,
      keywords: skills,
      difficulty: "medium"
    },
    {
      id: 3,
      question: "Donnez un exemple ou vous avez collabore avec une equipe non technique.",
      keywords: ["communication", "collaboration", "resultat"],
      difficulty: "easy"
    }
  ];
}

function normalizeJobForApi(job) {
  return {
    title: job.title,
    description: job.description,
    requirements: job.requirements,
    skills: job.skills || [],
    experience_level: job.experience_level || "mid_level",
    salary_min: numberOrNull(job.salary_min),
    salary_max: numberOrNull(job.salary_max),
    location: job.location || job.work_location || ""
  };
}

function normalizeList(payload) {
  if (Array.isArray(payload)) return payload;
  if (Array.isArray(payload?.data)) return payload.data;
  if (Array.isArray(payload?.jobs)) return payload.jobs;
  if (Array.isArray(payload?.results)) return payload.results;
  return [];
}

function normalizeObject(payload) {
  return payload?.data || payload?.result || payload;
}

function normalizeMatch(match) {
  return {
    overall_score: Number(match.overall_score ?? match.score ?? 0),
    skills_score: Number(match.skills_score ?? match.score ?? 0),
    experience_score: Number(match.experience_score ?? 0),
    education_score: Number(match.education_score ?? 0),
    tools_score: Number(match.tools_score ?? 0),
    matched_skills: match.matched_skills || [],
    missing_skills: match.missing_skills || [],
    recommendations: match.recommendations || [match.recommendation, match.analysis].filter(Boolean)
  };
}

// ============================================================

