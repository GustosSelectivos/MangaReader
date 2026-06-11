import api from './api'

export async function listDemografias(params = {}) {
  const r = await api.get('catalog/demografias', { params })
  return Array.isArray(r.data) ? r.data : (r.data?.results || [])
}

export async function getDemografia(id) {
  const r = await api.get(`catalog/demografias/${id}`)
  return r?.data || {}
}

export async function listAutores(params = {}) {
  const r = await api.get('catalog/autores', { params })
  return Array.isArray(r.data) ? r.data : (r.data?.results || [])
}

export async function listTags(params = {}) {
  const r = await api.get('catalog/tags', { params })
  return Array.isArray(r.data) ? r.data : (r.data?.results || [])
}

export async function listEstados(params = {}) {
  const r = await api.get('catalog/estados', { params })
  return Array.isArray(r.data) ? r.data : (r.data?.results || [])
}

export async function resolveDemografiaDescripcion(numId) {
  if (!numId && numId !== 0) return { descripcion: '', color: '' }
  try {
    const d = await getDemografia(numId)
    return { descripcion: d.descripcion || d.name || d.title || '', color: d.color || d.dem_color || '' }
  } catch {}
  try {
    const list = await listDemografias({ page_size: 1000 })
    const found = list.find(x => String(x.id) === String(numId)) || {}
    return { descripcion: found.descripcion || found.name || found.title || '', color: found.color || found.dem_color || '' }
  } catch {}
  return { descripcion: '', color: '' }
}

// Create endpoints (admin)
export async function createDemografia(payload) {
  const r = await api.post('catalog/demografias', payload)
  return r?.data
}

export async function createTag(payload) {
  const r = await api.post('catalog/tags', payload)
  return r?.data
}

export async function createAutor(payload) {
  const r = await api.post('catalog/autores', payload)
  return r?.data
}

export async function createEstado(payload) {
  const r = await api.post('catalog/estados', payload)
  return r?.data
}
