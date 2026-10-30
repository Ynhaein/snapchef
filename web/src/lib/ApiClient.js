const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8000'

export async function analyzeFood(file, signal) {
  const formData = new FormData()
  formData.append('file', file)

  const response = await fetch(`${API_BASE_URL}/api/predict`, {
    method: 'POST',
    body: formData,
    signal,
  })
  const payload = await response.json().catch(() => ({}))

  if (!response.ok) {
    throw new Error(payload.detail ?? 'SnapChef could not analyze this photo.')
  }

  return payload
}

export async function detectFood(blob, signal) {
  const formData = new FormData()
  formData.append('file', blob, 'frame.jpg')
  const response = await fetch(`${API_BASE_URL}/api/detect`, {
    method: 'POST',
    body: formData,
    signal,
  })
  const payload = await response.json().catch(() => ({}))
  if (!response.ok) {
    throw new Error(payload.detail ?? 'SnapChef could not analyze this frame.')
  }
  return payload
}
export async function recommendRecipes(ingredients, signal) {
  const response = await fetch(`${API_BASE_URL}/api/recommend`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ ingredients }),
    signal,
  })
  const payload = await response.json().catch(() => ({}))

  if (!response.ok) {
    throw new Error(payload.detail ?? 'SnapChef could not find recipes for these ingredients.')
  }

  return payload
}
