import api from './api'
import cache from './cache'

export async function listMangas(params = {}) {
  try {
    const key = cache.keyFrom('manga/mangas/', params)
    const cached = cache.get(key)
    if (cached) return Array.isArray(cached) ? cached : (cached?.results || [])
    const res = await api.get('manga/mangas/', { params })
    const data = Array.isArray(res.data) ? res.data : (res.data?.results || res.data?.mangas || [])
    if (Array.isArray(data)) cache.set(key, data, 5 * 60 * 1000)
    return data
  } catch {
    const res = await api.get('manga/mangas/', { params })
    const data = Array.isArray(res.data) ? res.data : (res.data?.results || res.data?.mangas || [])
    return data
  }
}

export async function getManga(id) {
  const key = cache.keyFrom('manga/mangas/:id', { id })
  const cached = cache.get(key)
  if (cached) return cached
  const candidates = [`manga/mangas/${id}/`, `mangas/${id}/`, `manga/${id}/`]
  for (const ep of candidates) {
    try {
      const r = await api.get(ep)
      if (r?.data) { cache.set(key, r.data, 60 * 1000); return r.data }
    } catch { /* try next */ }
  }
  return null
}

export async function incrementMangaView(id) {
  if (!id) return
  try { await api.post(`manga/mangas/${id}/increment-view/`) } catch { }
}

export async function listMangaCovers(params = {}) {
  const res = await api.get('manga/manga-covers/', { params })
  return Array.isArray(res.data) ? res.data : (res.data?.results || [])
}

export async function getMangaCover(id) {
  const r = await api.get(`manga/manga-covers/${id}/`)
  return r?.data || {}
}

export async function fetchCoverById(possibleId) {
  const cid = Number(possibleId)
  if (!cid || Number.isNaN(cid)) return null
  try {
    const obj = await getMangaCover(cid)
    if (typeof obj.url_absoluta === 'string') return obj.url_absoluta
    if (typeof obj.url_imagen === 'string') return obj.url_imagen
  } catch { }
  return null
}

export async function getMainCoverForManga(id) {
  try {
    const list1 = await listMangaCovers({ manga: id, vigente: true })
    const main = list1.find(c => c.tipo_cover === 'main') || list1[0]
    if (main && typeof main.url_absoluta === 'string' && isValidCdn(main.url_absoluta)) return main.url_absoluta
    if (main && typeof main.url_imagen === 'string' && isValidCdn(main.url_imagen)) return main.url_imagen
  } catch { }
  try {
    const listAll = await listMangaCovers({ vigente: true, page_size: 1000 })
    const forManga = listAll.filter(c => String(c.manga) === String(id))
    const main2 = forManga.find(c => c.tipo_cover === 'main') || forManga[0]
    if (main2 && typeof main2.url_absoluta === 'string' && isValidCdn(main2.url_absoluta)) return main2.url_absoluta
    if (main2 && typeof main2.url_imagen === 'string' && isValidCdn(main2.url_imagen)) return main2.url_imagen
  } catch { }
  return null
}

// Accept only http(s) and avoid known bad domains/placeholders
export function isValidCdn(url) {
  if (!url || typeof url !== 'string') return false
  const u = url.trim().toLowerCase()
  if (!u.startsWith('http://') && !u.startsWith('https://')) return false
  // Block legacy domain causing slow misses
  if (u.includes('miswebtoons.uk/assets/covers')) return false
  // You can refine with your CDN host (e.g., backblazeb2 or your custom domain)
  return true
}
