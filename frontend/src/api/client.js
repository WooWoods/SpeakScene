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

  if (response.status === 204) {
    return null
  }

  return response.json()
}

export async function synthesizeSpeech(text) {
  const response = await fetch(`${API_BASE_URL}/tts/speech`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ text }),
  })

  if (!response.ok) {
    const detail = await response.text()
    throw new Error(detail || `Request failed with ${response.status}`)
  }

  return response.blob()
}

export function startScenario({ level, category, scenarioName }) {
  return request("/scenarios/start", {
    method: "POST",
    body: JSON.stringify({ level, category, scenario_name: scenarioName || undefined }),
  })
}

export function addTurn({ sessionId, textEn, inputMode }) {
  return request(`/sessions/${sessionId}/turns`, {
    method: "POST",
    body: JSON.stringify({ text_en: textEn, input_mode: inputMode }),
  })
}

export function completeSession({ sessionId }) {
  return request(`/sessions/${sessionId}/complete`, {
    method: "POST",
  })
}

export function getHistory() {
  return request("/history")
}

export function getFavorites() {
  return request("/favorites")
}

export function createFavorite(payload) {
  return request("/favorites", {
    method: "POST",
    body: JSON.stringify(payload),
  })
}

export function deleteFavorite({ favoriteId }) {
  return request(`/favorites/${favoriteId}`, {
    method: "DELETE",
  })
}
