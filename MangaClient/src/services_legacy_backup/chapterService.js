import api from './api'
import cache from './cache'

export async function getChapter(id) {
  const key = cache.keyFrom('chapters/:id', { id })
  const cached = cache.get(key)
  if (cached) return cached

  // Correct endpoint is /api/chapters/{id}/ based on router config
  try {
    const res = await api.get(`chapters/${id}/`)
    if (res?.data && (res.data.id || res.data.title || res.data.titulo)) {
      cache.set(key, res.data, 60 * 1000)
      return res.data
    }
  } catch { }
  return null
}

export async function listChapters(params = {}) {
  const key = cache.keyFrom('chapters/', params)
  const cached = cache.get(key)
  if (cached) return Array.isArray(cached) ? cached : (cached?.results || [])

  try {
    const res = await api.get('chapters/', { params })
    const data = Array.isArray(res.data) ? res.data : (res.data?.results || [])
    if (Array.isArray(data)) cache.set(key, data, 60 * 1000)
    return data
  } catch {
    return []
  }
}

export async function createChapter(payload) {
  const res = await api.post('chapters/', payload)
  return res?.data
}
