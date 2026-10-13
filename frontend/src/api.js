const API = import.meta.env.VITE_API_URL || ''

export async function api(path) {
  const response = await fetch(`${API}${path}`)
  if (!response.ok) {
    const body = await response.json().catch(() => ({}))
    throw new Error(body.detail || `Request failed (${response.status})`)
  }
  return response.json()
}

export const money = (value) => new Intl.NumberFormat('en-IN', {
  style: 'currency', currency: 'INR', maximumFractionDigits: 0,
}).format(Number(value || 0))

export const compact = (value) => new Intl.NumberFormat('en-IN', {
  notation: 'compact', maximumFractionDigits: 1,
}).format(Number(value || 0))
