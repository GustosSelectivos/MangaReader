import api from './api'
import cache from './cache'

export async function listMangas(params = {}) {
  const key = cache.keyFrom('mangas', params)
  const cached = cache.get(key)
  if (cached) return Array.isArray(cached) ? cached : (cached?.results || [])

  try {
    const res = await api.get('mangas', { params })
    const data = Array.isArray(res.data) ? res.data : (res.data?.results || res.data?.mangas || [])
    if (Array.isArray(data)) cache.set(key, data, 5 * 60 * 1000)
    return data
  } catch (e) {
    console.error('Error fetching mangas:', e)
    return []
  }
}

export async function getManga(id) {
  const key = cache.keyFrom('mangas/:id', { id })
  const cached = cache.get(key)
  if (cached) return cached

  try {
    const r = await api.get(`mangas/${id}`)
    if (r?.data) {
      cache.set(key, r.data, 60 * 1000)
      return r.data
    }
  } catch (e) {
    console.error(`Error fetching manga ${id}:`, e)
  }
  return null
}

export async function incrementMangaView(id) {
  if (!id) return
  try { await api.post(`mangas/${id}/increment-view`) } catch { }
}

// Deprecated en FastAPI: Las portadas ahora se incluyen directamente en el objeto Manga como `cover_url`
export async function listMangaCovers(params = {}) {
  return []
}

export async function getMangaCover(id) {
  return {}
}

export async function fetchCoverById(possibleId) {
  const cid = Number(possibleId)
  if (!cid || Number.isNaN(cid)) return null
  return null
}

// Actualizado: Extrae la cover_url directamente del manga
export async function getMainCoverForManga(id) {
  try {
    const manga = await getManga(id)
    if (manga && manga.cover_url && isValidCdn(manga.cover_url)) {
      return manga.cover_url
    }
  } catch { }
  return null
}

export function isValidCdn(url) {
  if (!url || typeof url !== 'string') return false
  const u = url.trim().toLowerCase()
  if (!u.startsWith('http://') && !u.startsWith('https://')) return false
  if (u.includes('miswebtoons.uk/assets/covers')) return false
  return true
}
