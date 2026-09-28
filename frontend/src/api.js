import { auth } from "./firebase";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

async function authedFetch(path, options = {}) {
  const user = auth.currentUser;
  if (!user) throw new Error("Not signed in");
  const idToken = await user.getIdToken();

  const res = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${idToken}`,
      ...(options.headers || {}),
    },
  });

  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || `Request failed: ${res.status}`);
  }
  return res.json();
}

export function registerProfile(role, displayName) {
  return authedFetch("/api/register", {
    method: "POST",
    body: JSON.stringify({ role, display_name: displayName }),
  });
}

export function fetchMe() {
  return authedFetch("/api/me");
}

export function fetchDashboard() {
  return authedFetch("/api/dashboard");
}

export function createPaperDraft(paper) {
  return authedFetch("/api/papers", {
    method: "POST",
    body: JSON.stringify(paper),
  });
}

export function listPapers() {
  return authedFetch("/api/papers");
}

export function searchOtherPapers(query) {
  return authedFetch(`/api/papers/search?q=${encodeURIComponent(query)}&limit=20`)
}

export function fetchPaper(paperId) {
  return authedFetch(`/api/papers/${paperId}`);
}

export function generateQuestions(paperId) {
  return authedFetch(`/api/papers/${paperId}/generate-questions`, { method: "POST" });
}

export function updateQuestion(paperId, questionId, data) {
  return authedFetch(`/api/papers/${paperId}/questions/${questionId}`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}

export function publishPaper(paperId) {
  return authedFetch(`/api/papers/${paperId}/publish`, { method: "POST" });
}