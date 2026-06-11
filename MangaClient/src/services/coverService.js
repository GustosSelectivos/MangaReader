// Centralizado: helpers de portadas con cache en memoria
// Adaptado para FastAPI: Los endpoints /manga-covers desaparecieron.
// La portada se extrae directamente de la entidad Manga.

import { toCdnUrl } from '@/utils/cdn'
import { getManga } from './mangaService'

const mainPromises = new Map()
const mainResults = new Map()

async function fetchMainCoverForMangaRaw(mangaId) {
  const mid = String(mangaId)
  if (!mid) return null
  try {
    const manga = await getManga(mid)
    if (manga && manga.cover_url) {
      return toCdnUrl(manga.cover_url, { w: 400 })
    }
  } catch (e) { }
  return null
}

export function getCoverByIdCached(id) {
  // Deprecado en FastAPI: Ya no existen IDs de covers independientes.
  // Intentamos tratar el ID como si fuera el ID del manga para mantener retrocompatibilidad parcial.
  return getMainCoverCached(id)
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

// Batch: intentar resolver portadas principales de varios mangas en paralelo
export async function getMainCoversBatch(mangaIds) {
  return getMainCoversParallel(mangaIds)
}

// Paralelo: resolver portadas consultando getManga por manga en paralelo
export async function getMainCoversParallel(mangaIds) {
  const ids = (Array.isArray(mangaIds) ? mangaIds : []).map(x => String(x)).filter(Boolean)
  if (!ids.length) return new Map()
  const tasks = ids.map(async (mid) => {
    try {
      const manga = await getManga(mid)
      const url = manga?.cover_url || null
      if (url !== null) mainResults.set(mid, toCdnUrl(url, { w: 400 }))
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
    // cover_id y main_cover_id ya no aplican en FastAPI, usamos el ID del manga
    const viaManga = await getMainCoverCached(id)
    if (viaManga) remote = viaManga
  }
  return (typeof remote === 'string' && remote.startsWith('http')) ? toCdnUrl(remote, { w: 400 }) : null
}
