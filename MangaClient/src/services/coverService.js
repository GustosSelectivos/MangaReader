// Centralizado: helpers de portadas con cache en memoria
// Provee funciones para obtener portada por ID y portada principal por manga
// y deduplica solicitudes concurrentes.

import api from './api'
import { toCdnUrl } from '@/utils/cdn'

const idPromises = new Map()
const idResults = new Map()
const mainPromises = new Map()
const mainResults = new Map()

async function fetchCoverByIdRaw(id) {
  const cid = Number(id)
  if (!cid || Number.isNaN(cid)) return null
  try {
    const r = await api.get(`manga/manga-covers/${cid}/`)
    const obj = r?.data || {}
    if (typeof obj.url_absoluta === 'string') return toCdnUrl(obj.url_absoluta, { w: 400 })
    if (typeof obj.url_imagen === 'string') return toCdnUrl(obj.url_imagen, { w: 400 })
  } catch (e) { }
  return null
}

async function fetchMainCoverForMangaRaw(mangaId) {
  const mid = String(mangaId)
  if (!mid) return null
  // Buscar por manga específico primero
  try {
    const p1 = { manga: mid, vigente: true }
    const r1 = await api.get('manga/manga-covers/', { params: p1 })
    const list1 = Array.isArray(r1.data) ? r1.data : (r1.data?.results || [])
    const main = list1.find(c => c.tipo_cover === 'main') || list1[0]
    if (main?.url_absoluta) return toCdnUrl(main.url_absoluta, { w: 400 })
    if (main?.url_imagen) return toCdnUrl(main.url_imagen, { w: 400 })
  } catch (e) { }
  // Previously had a fallback fetching 1000 items here. Removed for performance.
  // The Backend serialization now provides 'cover_url', so extensive fallback search is unnecessary.

  return null
}

export function getCoverByIdCached(id) {
  const cid = Number(id)
  if (!cid || Number.isNaN(cid)) return Promise.resolve(null)
  if (idResults.has(cid)) return Promise.resolve(idResults.get(cid))
  if (idPromises.has(cid)) return idPromises.get(cid)
  const p = fetchCoverByIdRaw(cid).then(url => { idResults.set(cid, url || null); idPromises.delete(cid); return url || null })
  idPromises.set(cid, p)
  return p
}

export function getMainCoverCached(mangaId) {
  const mid = String(mangaId)
  if (!mid) return Promise.resolve(null)
  if (mainResults.has(mid)) return Promise.resolve(mainResults.get(mid))
  if (mainPromises.has(mid)) return mainPromises.get(mid)
  const p = fetchMainCoverForMangaRaw(mid).then(url => { mainResults.set(mid, url || null); mainPromises.delete(mid); return url || null })
  mainPromises.set(mid, p)
  return p
}

// Batch: intentar resolver portadas principales de varios mangas en una sola consulta
export async function getMainCoversBatch(mangaIds) {
  const ids = (Array.isArray(mangaIds) ? mangaIds : []).map(x => String(x)).filter(Boolean)
  if (!ids.length) return new Map()
  // Si ya tenemos algunas en cache, marcarlas previamente
  const result = new Map()
  const missing = []
  for (const mid of ids) {
    if (mainResults.has(mid)) result.set(mid, mainResults.get(mid))
    else missing.push(mid)
  }
  if (!missing.length) return result
  try {
    // No hay endpoint multi-id; obtenemos un listado grande y filtramos
    const rAll = await api.get('manga/manga-covers/', { params: { vigente: true, page_size: 1000 } })
    const listAll = Array.isArray(rAll.data) ? rAll.data : (rAll.data?.results || [])
    for (const mid of missing) {
      const forManga = listAll.filter(c => String(c.manga) === String(mid))
      const main = forManga.find(c => c.tipo_cover === 'main') || forManga[0]
      const url = main?.url_absoluta || main?.url_imagen || null
      mainResults.set(mid, toCdnUrl(url, { w: 400 }))
      result.set(mid, toCdnUrl(url, { w: 400 }))
    }
  } catch (e) { /* ignore */ }
  return result
}

// Paralelo: resolver portadas consultando el endpoint por manga en paralelo
// Hace una petición por cada id: api.get('manga/manga-covers/', { params: { manga, vigente:true } })
// Útil si el listado global está paginado o restringido.
export async function getMainCoversParallel(mangaIds) {
  const ids = (Array.isArray(mangaIds) ? mangaIds : []).map(x => String(x)).filter(Boolean)
  if (!ids.length) return new Map()
  const tasks = ids.map(async (mid) => {
    try {
      const r = await api.get('manga/manga-covers/', { params: { manga: mid, vigente: true } })
      const list = Array.isArray(r.data) ? r.data : (r.data?.results || [])
      const main = list.find(c => c.tipo_cover === 'main') || list[0]
      const url = main?.url_absoluta || main?.url_imagen || null
      if (url !== undefined) mainResults.set(mid, toCdnUrl(url, { w: 400 }))
      return [mid, toCdnUrl(url, { w: 400 })]
    } catch (e) {
      return [mid, null]
    }
  })
  const entries = await Promise.all(tasks)
  const map = new Map(entries)
  return map
}

// Utilidad: decide una portada remota
export async function resolveRemoteCover({ id, cover, cover_id, main_cover_id }) {
  let remote = cover
  if (!remote || typeof remote !== 'string' || !remote.startsWith('http')) {
    const byId = await getCoverByIdCached(cover_id || main_cover_id || cover)
    if (byId) remote = byId
    else {
      const viaManga = await getMainCoverCached(id)
      if (viaManga) remote = viaManga
    }
  }
  return (typeof remote === 'string' && remote.startsWith('http')) ? toCdnUrl(remote, { w: 400 }) : null
}
