import api from './api'
import cache from './cache'

export async function getChapter(id) {
  const key = cache.keyFrom('chapters/chapters/:id', { id })
  const cached = cache.get(key)
  if (cached) return cached
  const candidates = [`chapters/chapters/${id}/`, `chapters/chapters/?id=${id}`]
  for (const ep of candidates) {
    try {
      const res = await api.get(ep)
      if (res?.data && (res.data.id || res.data.title || res.data.titulo)) { cache.set(key, res.data, 60 * 1000); return res.data }
    } catch {}
  }
  return null
}

export async function listChapters(params = {}) {
  const key = cache.keyFrom('chapters/chapters/', params)
  const cached = cache.get(key)
  if (cached) return Array.isArray(cached) ? cached : (cached?.results || [])
  try {
    const res = await api.get('chapters/chapters/', { params })
    const data = Array.isArray(res.data) ? res.data : (res.data?.results || [])
    if (Array.isArray(data)) cache.set(key, data, 60 * 1000)
    return data
  } catch {
    try {
      const res2 = await api.get('chapters/', { params })
      const data2 = Array.isArray(res2.data) ? res2.data : (res2.data?.results || [])
      if (Array.isArray(data2)) cache.set(key, data2, 60 * 1000)
      return data2
    } catch { return [] }
  }
}

export async function createChapter(payload) {
  try {
    const res = await api.post('chapters/chapters/', payload)
    return res?.data
  } catch (e) {
    try { const res2 = await api.post('chapters/', payload); return res2?.data } catch { throw e }
  }
}
