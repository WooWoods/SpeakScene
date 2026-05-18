const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000/api"

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(options.headers ?? {}),
    },
    ...options,
  })

  if (!response.ok) {
    const detail = await response.text()
    throw new Error(detail || `Request failed with ${response.status}`)
  }

  return response.json()
}

export function generateTask({ level, category, scenarioName }) {
  return request("/tasks/generate", {
    method: "POST",
    body: JSON.stringify({ level, category, scenario_name: scenarioName || undefined }),
  })
}

export function submitAnswer({ taskId, userInput }) {
  return request("/attempts/submit", {
    method: "POST",
    body: JSON.stringify({ task_id: taskId, user_input: userInput }),
  })
}

export function getHints({ taskId }) {
  return request("/hints", {
    method: "POST",
    body: JSON.stringify({ task_id: taskId }),
  })
}

export function getHistory() {
  return request("/history")
}

export function getDueReviews() {
  return request("/review/due")
}

export function markMastered({ attemptId }) {
  return request(`/review/${attemptId}/mastered`, {
    method: "POST",
  })
}
