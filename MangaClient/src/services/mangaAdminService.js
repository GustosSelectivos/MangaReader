import api from './api'

export async function listMangasBasic(params = {}) {
  try {
    const r = await api.get('manga/mangas/', { params })
    return Array.isArray(r.data) ? r.data : (r.data?.results || [])
  } catch {
    const r2 = await api.get('mangas/', { params })
    return Array.isArray(r2.data) ? r2.data : (r2.data?.results || [])
  }
}

export async function createManga(payload) {
  const r = await api.post('manga/mangas/', payload)
  return r?.data
}

export async function createAltTitulo(payload) {
  const r = await api.post('manga/manga-alt-titulos/', payload)
  return r?.data
}

export async function createCover(payload) {
  const r = await api.post('manga/manga-covers/', payload)
  return r?.data
}

export async function createAutorRel(payload) {
  const r = await api.post('manga/manga-autores/', payload)
  return r?.data
}

export async function createTagRel(payload) {
  const r = await api.post('manga/manga-tags/', payload)
  return r?.data
}

export async function listAltTitulos(params = {}) {
  const r = await api.get('manga/manga-alt-titulos/', { params })
  return Array.isArray(r.data) ? r.data : (r.data?.results || [])
}

export async function listCovers(params = {}) {
  const r = await api.get('manga/manga-covers/', { params })
  return Array.isArray(r.data) ? r.data : (r.data?.results || [])
}

export async function listAutoresRel(params = {}) {
  const r = await api.get('manga/manga-autores/', { params })
  return Array.isArray(r.data) ? r.data : (r.data?.results || [])
}

export async function listTagsRel(params = {}) {
  const r = await api.get('manga/manga-tags/', { params })
  return Array.isArray(r.data) ? r.data : (r.data?.results || [])
}
