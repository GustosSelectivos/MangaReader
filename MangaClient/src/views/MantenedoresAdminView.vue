<script setup>
import { ref, onMounted } from 'vue'
import api from '@/services/api'

const demografias = ref([])
const tags = ref([])
const autores = ref([])
const estados = ref([])
const loading = ref(false)
const error = ref('')
const newDemografia = ref('')
const newDemografiaColor = ref('')
const newTag = ref('')
const newAutor = ref('')
const newAutorTipo = ref('')
const newAutorFoto = ref('')
const newEstado = ref('')

async function fetchLists() {
  loading.value = true
  error.value = ''
  try {
    const d = await api.get('mantenedor/demografias/', { params: { page_size: 200 } })
    demografias.value = Array.isArray(d.data) ? d.data : (d.data?.results || [])
    const t = await api.get('mantenedor/tags/', { params: { page_size: 200 } })
    tags.value = Array.isArray(t.data) ? t.data : (t.data?.results || [])
    // Fetch autores (authors)
    try {
      const a = await api.get('mantenedor/autores/', { params: { page_size: 200 } })
      autores.value = Array.isArray(a.data) ? a.data : (a.data?.results || [])
    } catch (e) {}
    // Fetch estados (statuses)
    try {
      const s = await api.get('mantenedor/estados/', { params: { page_size: 200 } })
      estados.value = Array.isArray(s.data) ? s.data : (s.data?.results || [])
    } catch (e) {}
  } catch (e) {
    error.value = e.message || 'Error cargando listas'
  } finally {
    loading.value = false
  }
}

async function addDemografia() {
  if (!newDemografia.value) return
  try {
    const payload = { descripcion: newDemografia.value }
    if (newDemografiaColor.value) payload.color = newDemografiaColor.value
    const res = await api.post('mantenedor/demografias/', payload)
    demografias.value.push(res.data)
    newDemografia.value = ''
    newDemografiaColor.value = ''
  } catch (e) { error.value = e.message || 'Error creando demografía' }
}
async function patchItem(endpoint, id, payload) {
  try {
    const r = await api.patch(`${endpoint}${id}/`, payload)
    return r?.data
  } catch (e) {
    try {
      const base = endpoint.endsWith('/') ? endpoint.slice(0, -1) : endpoint
      const r2 = await api.patch(`${base}/${id}/`, payload)
      return r2?.data
    } catch (e2) {
      throw e2
    }
  }
}

// Inline editing handlers
async function saveDemografia(d) {
  const payload = {
    descripcion: d.descripcion || d.name || d.title || '',
    color: d.color || d.dem_color || '',
  }
  try {
    const updated = await patchItem('mantenedor/demografias/', d.id, payload)
    Object.assign(d, updated)
  } catch (e) { error.value = e.message || 'Error actualizando demografía' }
}
async function saveTag(t) {
  const payload = { nombre: t.nombre || t.tag_nombre || t.name || t.title || '' }
  try {
    const updated = await patchItem('mantenedor/tags/', t.id, payload)
    Object.assign(t, updated)
  } catch (e) { error.value = e.message || 'Error actualizando tag' }
}
async function saveAutor(a) {
  const payload = {
    nombre: a.nombre || a.name || a.titulo || a.title || '',
    tipo: a.tipo || a.tipo_autor || a.type || '',
    foto_url: a.foto_url || a.photo_url || a.avatar || '',
  }
  try {
    const updated = await patchItem('mantenedor/autores/', a.id, payload)
    Object.assign(a, updated)
  } catch (e) { error.value = e.message || 'Error actualizando autor' }
}
async function saveEstado(s) {
  const payload = { descripcion: s.descripcion || s.name || s.title || '' }
  try {
    const updated = await patchItem('mantenedor/estados/', s.id, payload)
    Object.assign(s, updated)
  } catch (e) { error.value = e.message || 'Error actualizando estado' }
}
async function addTag() {
  if (!newTag.value) return
  try {
    const res = await api.post('mantenedor/tags/', { descripcion: newTag.value })
    tags.value.push(res.data)
    newTag.value = ''
  } catch (e) { error.value = e.message || 'Error creando tag' }
}
async function addAutor() {
  if (!newAutor.value || !newAutorTipo.value) return
  try {
    const res = await api.post('mantenedor/autores/', {
      nombre: newAutor.value,
      tipo_autor: newAutorTipo.value,
    })
    autores.value.push(res.data)
    newAutor.value = ''
    newAutorTipo.value = ''
  } catch (e) { error.value = e.message || 'Error creando autor' }
}
async function addEstado() {
  if (!newEstado.value) return
  try {
    const res = await api.post('mantenedor/estados/', { descripcion: newEstado.value })
    estados.value.push(res.data)
    newEstado.value = ''
  } catch (e) { error.value = e.message || 'Error creando estado' }
}

onMounted(fetchLists)
</script>

<template>
  <div class="mantenedores-admin container py-4">
    <h2 class="mb-3">Administrar Mantenedores</h2>
    <p class="text-muted">Gestiona demografías, tags, autores y estados.</p>
    <div v-if="error" class="alert alert-danger py-2">{{ error }}</div>
    <div v-if="loading">Cargando...</div>
    <div class="row" v-if="!loading">
      <div class="col-md-6 mb-4">
        <h5>Demografías</h5>
        <ul class="list-group mb-2">
          <li v-for="d in demografias" :key="d.id" class="list-group-item d-flex justify-content-between align-items-center">
            <div class="flex-grow-1 me-3">
              <template v-if="!d._editing">
                <strong>{{ d.descripcion || ('Demografía #' + d.id) }}</strong>
                <span v-if="d.color" class="ms-2 badge" :style="{ backgroundColor: d.color, color: '#000' }">{{ d.color }}</span>
              </template>
              <template v-else>
                <div class="d-flex gap-2">
                  <input v-model="d.descripcion" type="text" class="form-control form-control-sm" placeholder="Descripción" />
                  <input v-model="d.color" type="text" class="form-control form-control-sm" placeholder="Color (#RRGGBB o nombre)" />
                </div>
              </template>
            </div>
            <div class="d-flex align-items-center gap-2">
              <span class="badge bg-secondary">ID {{ d.id }}</span>
              <button v-if="!d._editing" class="btn btn-outline-primary btn-sm" @click="d._editing = true">Editar</button>
              <button v-else class="btn btn-outline-success btn-sm" @click="saveDemografia(d); d._editing = false">Guardar</button>
            </div>
          </li>
        </ul>
        <form class="row g-2 align-items-end" @submit.prevent="addDemografia">
          <div class="col-12 col-md-5">
            <input v-model="newDemografia" type="text" class="form-control form-control-sm" placeholder="Nueva demografía" />
          </div>
          <div class="col-12 col-md-5">
            <input v-model="newDemografiaColor" type="text" class="form-control form-control-sm" placeholder="Color (opcional)" />
          </div>
          <div class="col-12 col-md-2">
            <button class="btn btn-primary btn-sm w-100" :disabled="!newDemografia">Agregar</button>
          </div>
        </form>
      </div>
      <div class="col-md-6 mb-4">
        <h5>Tags</h5>
        <ul class="list-group mb-2">
          <li v-for="t in tags" :key="t.id" class="list-group-item d-flex justify-content-between align-items-center">
            <div class="flex-grow-1 me-3">
              <template v-if="!t._editing">
                <strong>{{ t.nombre || t.tag_nombre || t.descripcion || t.desc || t.slug || t.codigo || ('Tag #' + t.id) }}</strong>
              </template>
              <template v-else>
                <input v-model="t.nombre" type="text" class="form-control form-control-sm" placeholder="Nombre" />
              </template>
            </div>
            <div class="d-flex align-items-center gap-2">
              <span class="badge bg-secondary">ID {{ t.id }}</span>
              <button v-if="!t._editing" class="btn btn-outline-primary btn-sm" @click="t._editing = true">Editar</button>
              <button v-else class="btn btn-outline-success btn-sm" @click="saveTag(t); t._editing = false">Guardar</button>
            </div>
          </li>
        </ul>
        <form class="row g-2 align-items-end" @submit.prevent="addTag">
          <div class="col-12 col-md-10">
            <input v-model="newTag" type="text" class="form-control form-control-sm" placeholder="Nuevo tag" />
          </div>
          <div class="col-12 col-md-2">
            <button class="btn btn-primary btn-sm w-100" :disabled="!newTag">Agregar</button>
          </div>
        </form>
      </div>
      <div class="col-md-6 mb-4">
        <h5>Autores</h5>
        <ul class="list-group mb-2">
          <li v-for="a in autores" :key="a.id" class="list-group-item d-flex justify-content-between align-items-center">
            <div class="flex-grow-1 me-3">
              <template v-if="!a._editing">
                <div class="d-flex flex-column">
                  <div>
                    <strong>{{ a.nombre || ('Autor #' + a.id) }}</strong>
                    <span v-if="a.tipo" class="ms-2 badge bg-info text-dark">{{ a.tipo }}</span>
                  </div>
                  <div class="text-muted small">
                    <span v-if="a.foto_url">Foto: {{ a.foto_url }}</span>
                  </div>
                </div>
              </template>
              <template v-else>
                <div class="d-flex flex-column gap-2">
                  <input v-model="a.nombre" type="text" class="form-control form-control-sm" placeholder="Nombre" />
                  <div class="d-flex gap-2">
                    <input v-model="a.tipo" type="text" class="form-control form-control-sm" placeholder="Tipo de autor" />
                    <input v-model="a.foto_url" type="text" class="form-control form-control-sm" placeholder="URL de foto" />
                  </div>
                </div>
              </template>
            </div>
            <div class="d-flex align-items-center gap-2">
              <span class="badge bg-secondary">ID {{ a.id }}</span>
              <button v-if="!a._editing" class="btn btn-outline-primary btn-sm" @click="a._editing = true">Editar</button>
              <button v-else class="btn btn-outline-success btn-sm" @click="saveAutor(a); a._editing = false">Guardar</button>
            </div>
          </li>
        </ul>
        <form class="row g-2 align-items-end" @submit.prevent="addAutor">
          <div class="col-12 col-md-5">
            <input v-model="newAutor" type="text" class="form-control form-control-sm" placeholder="Nombre del autor" />
          </div>
          <div class="col-12 col-md-5">
            <input v-model="newAutorTipo" type="text" class="form-control form-control-sm" placeholder="Tipo de autor" />
          </div>
          <div class="col-12 col-md-2">
            <button class="btn btn-primary btn-sm w-100" :disabled="!newAutor || !newAutorTipo">Agregar</button>
          </div>
        </form>
      </div>
      <div class="col-md-6 mb-4">
        <h5>Estados</h5>
        <ul class="list-group mb-2">
          <li v-for="s in estados" :key="s.id" class="list-group-item d-flex justify-content-between align-items-center">
            <div class="flex-grow-1 me-3">
              <template v-if="!s._editing">
                <strong>{{ s.descripcion || ('Estado #' + s.id) }}</strong>
              </template>
              <template v-else>
                <input v-model="s.descripcion" type="text" class="form-control form-control-sm" placeholder="Descripción" />
              </template>
            </div>
            <div class="d-flex align-items-center gap-2">
              <span class="badge bg-secondary">ID {{ s.id }}</span>
              <button v-if="!s._editing" class="btn btn-outline-primary btn-sm" @click="s._editing = true">Editar</button>
              <button v-else class="btn btn-outline-success btn-sm" @click="saveEstado(s); s._editing = false">Guardar</button>
            </div>
          </li>
        </ul>
        <form class="row g-2 align-items-end" @submit.prevent="addEstado">
          <div class="col-12 col-md-10">
            <input v-model="newEstado" type="text" class="form-control form-control-sm" placeholder="Nuevo estado" />
          </div>
          <div class="col-12 col-md-2">
            <button class="btn btn-primary btn-sm w-100" :disabled="!newEstado">Agregar</button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<style scoped>
.gap-2 { gap:.5rem; }
/* Dark mode readability for muted text and labels */
.mantenedores-admin { color: var(--ztmo-text); }
.mantenedores-admin .text-muted { color: var(--ztmo-text); opacity: 0.75; }
.mantenedores-admin .form-label { color: var(--ztmo-text); }
</style>
