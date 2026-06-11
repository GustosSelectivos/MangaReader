import api from './api'

export async function listMangasBasic(params = {}) {
  try {
    const r = await api.get('mangas', { params })
    return Array.isArray(r.data) ? r.data : (r.data?.results || [])
  } catch {
    return []
  }
}

export async function createManga(payload) {
  const r = await api.post('mangas', payload)
  return r?.data
}

// UPDATE PARA FASTAPI:
// Los alt titulos, autores y tags relacionales ya no existen como endpoints independientes.
// Ahora deberían pasarse directamente en el payload de `createManga` o `updateManga`.
// Mantenemos las firmas por retrocompatibilidad, pero devolvemos objetos vacíos para evitar que el front crashee.
export async function createAltTitulo(payload) {
  console.warn("createAltTitulo deprecado: Las relaciones ahora van en el payload de Manga.")
  return payload
}

// En FastAPI, la portada se sube como Multipart form-data al editar un manga existente.
export async function createCover(payload) {
  // Asumimos que payload es { manga: ID, cover: File/Blob, ... }
  // Lo convertimos a FormData y hacemos un PATCH a /mangas/{id}
  if (!payload.manga) throw new Error("Falta el ID del manga")
  const formData = new FormData()
  if (payload.cover || payload.image || payload.file) {
    formData.append('cover_image', payload.cover || payload.image || payload.file)
  }
  const r = await api.patch(`mangas/${payload.manga}`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  })
  return r?.data
}

export async function createAutorRel(payload) {
  console.warn("createAutorRel deprecado: Las relaciones ahora van en el payload de Manga.")
  return payload
}

export async function createTagRel(payload) {
  console.warn("createTagRel deprecado: Las relaciones ahora van en el payload de Manga.")
  return payload
}

export async function listAltTitulos(params = {}) {
  return []
}

export async function listCovers(params = {}) {
  return []
}

export async function listAutoresRel(params = {}) {
  return []
}

export async function listTagsRel(params = {}) {
  return []
}
