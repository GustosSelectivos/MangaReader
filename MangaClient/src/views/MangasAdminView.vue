<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import api from '@/services/api'
import { listEstados, listDemografias, listAutores, listTags } from '@/services/mantenedorService'
import { listMangasBasic, createManga, listAltTitulos, listCovers, listAutoresRel, listTagsRel, createAltTitulo, createCover, createAutorRel, createTagRel } from '@/services/mangaAdminService'

// Vista: lista, búsqueda o formulario (por defecto: lista)
const currentView = ref('list') // 'list' | 'search' | 'form'

// Step 1: Search
const searchType = ref('nombre')
const searchQuery = ref('')
const searchResults = ref([])
const searching = ref(false)
const searchError = ref('')

// Step 2: Selected manga & form data
const selectedSerie = ref(null)
const editingManga = ref(null)

// Form fields
const mangaForm = ref({
  codigo: '',
  titulo: '',
  sinopsis: '',
  estado_id: null,
  demografia_id: null,
  tipo_serie: 'manga',
  autor_id: null,
  fecha_lanzamiento: '',
  erotico: false,
  vigente: true
})

// Related data
const titulosAlternativos = ref([])
const covers = ref([])
const coversToDelete = ref([])
const autoresExtra = ref([])
const tagsSeleccionados = ref([])
const coverFile = ref(null)

// Catalogs
const estados = ref([])
const demografias = ref([])
const autores = ref([])
const allTags = ref([])
const catalogsLoaded = ref(false)

// Preview
const previewUrl = ref('')

// List view
const mangas = ref([])
const mangasFiltered = ref([])
const searchListQuery = ref('')
const loading = ref(false)
const error = ref('')

// Saving
const saving = ref(false)
const saveError = ref('')
const saveSuccess = ref('')

// --- Codename generator (JS version of provided Python) ---
function slugBase(title) {
  if (!title || !String(title).trim()) return ''
  const nfd = String(title).normalize('NFD').replace(/[\u0300-\u036f]/g, '')
  let out = ''
  let prevUS = false
  for (const ch of nfd.toLowerCase()) {
    if (/[a-z0-9]/.test(ch)) { out += ch; prevUS = false }
    else if (!prevUS) { out += '_'; prevUS = true }
  }
  return out.replace(/^_+|_+$/g, '')
}

async function sha1Hex(str) {
  const enc = new TextEncoder().encode(String(str))
  const buf = await crypto.subtle.digest('SHA-1', enc)
  const bytes = new Uint8Array(buf)
  return Array.from(bytes).map(b => b.toString(16).padStart(2, '0')).join('')
}

async function codenameFromTitleAsync(title) {
  const base = slugBase(title)
  const parts = base ? base.split('_').filter(Boolean) : []
  const initials = (parts.length ? (parts[0][0] || '') + (parts[1]?.[0] || '') : '').toLowerCase() || 'x'
  const h = (await sha1Hex(title || '')).slice(0, 6)
  return `${initials}-${h}`
}

const lastAutoCode = ref('')
let autoGenSeq = 0

async function maybeAutoGenerateCode(title) {
  // Only auto-generate when creating (not editing)
  if (editingManga.value) return
  const mySeq = ++autoGenSeq
  const gen = await codenameFromTitleAsync(title || '')
  if (mySeq !== autoGenSeq) return // stale
  const current = mangaForm.value.codigo || ''
  // Set if empty or if it still matches the previous auto value
  if (!current || current === lastAutoCode.value) {
    mangaForm.value.codigo = gen
    lastAutoCode.value = gen
  } else {
    // user has typed a custom code; don't override
    lastAutoCode.value = gen
  }
}

// Tipo serie options
const tipoSerieOptions = [
  { value: 'manga', label: 'Manga' },
  { value: 'manhwa', label: 'Manhwa' },
  { value: 'manhua', label: 'Manhua' },
  { value: 'one shot', label: 'One Shot' },
  { value: 'novel', label: 'Novel' },
  { value: 'doujinshi', label: 'Doujinshi' },
  { value: 'comic', label: 'Comic' }
]

const coverTipoOptions = [
  { value: 'main', label: 'Principal' },
  { value: 'thumbnail', label: 'Miniatura' },
  { value: 'banner', label: 'Banner' },
  { value: 'extra', label: 'Extra' }
]

const rolOptions = [
  { value: 'author', label: 'Autor' },
  { value: 'illustrator', label: 'Ilustrador' },
  { value: 'writer', label: 'Escritor' },
  { value: 'editor', label: 'Editor' }
]

// Load catalogs
async function loadCatalogs() {
  try {
    const [estadosRes, demosRes, autoresRes, tagsRes] = await Promise.all([
      listEstados({ page_size: 1000 }),
      listDemografias({ page_size: 1000 }),
      listAutores({ page_size: 1000 }),
      listTags({ page_size: 1000 })
    ])
    estados.value = estadosRes || []
    demografias.value = demosRes || []
    autores.value = autoresRes || []
    allTags.value = tagsRes || []
    catalogsLoaded.value = true
    // Tras cargar catálogos, asegurar que los selects queden en el valor del manga
    ensureSelectDefaults()
  } catch (e) {
    console.error('Error cargando catálogos:', e)
  }
}

async function fetchMangas() {
  loading.value = true
  error.value = ''
  try {
    const list = await listMangasBasic({ page_size: 200 })
    mangas.value = list
    // Top 20 más visitados por defecto (ordenar por "vistas")
    const sorted = [...list].sort((a, b) => Number(b.vistas || 0) - Number(a.vistas || 0))
    if ((searchListQuery.value || '').trim()) {
      // Mantener filtro activo si existe
      searchInList()
    } else {
      mangasFiltered.value = sorted.slice(0, 20)
    }
  } catch (e) {
    try {
      const r2 = await api.get('mangas/', { params: { page_size: 200 } })
      const list2 = Array.isArray(r2.data) ? r2.data : (r2.data?.results || [])
      mangas.value = list2
      const sorted2 = [...list2].sort((a, b) => Number(b.vistas || 0) - Number(a.vistas || 0))
      if ((searchListQuery.value || '').trim()) {
        searchInList()
      } else {
        mangasFiltered.value = sorted2.slice(0, 20)
      }
    } catch (e2) {
      error.value = e2.message || e.message || 'Error cargando mangas'
    }
  } finally {
    loading.value = false
  }
}

function searchInList() {
  const q = (searchListQuery.value || '').toLowerCase().trim()
  if (!q) {
    const sorted = [...mangas.value].sort((a, b) => Number(b.vistas || 0) - Number(a.vistas || 0))
    mangasFiltered.value = sorted.slice(0, 20)
    return
  }
  const filtered = mangas.value.filter(m => {
    const t = (m.titulo || m.title || '').toLowerCase()
    const c = (m.codigo || '').toLowerCase()
    return t.includes(q) || c.includes(q)
  })
  mangasFiltered.value = filtered.slice(0, 20)
}

async function toggleErotico(m) {
  const desired = !m.erotico && !m.erotic ? true : !m.erotico
  try {
    await api.patch(`manga/mangas/${m.id}/`, { erotico: desired })
    m.erotico = desired
    m.erotic = desired
  } catch (e) {
    try {
      await api.patch(`mangas/${m.id}/`, { erotico: desired })
      m.erotico = desired
      m.erotic = desired
    } catch (e2) {
      error.value = e2.message || e.message || 'Error actualizando erotico'
    }
  }
}

// Show search view
function showSearchView() {
  currentView.value = 'search'
  searchResults.value = []
  searchQuery.value = ''
  searchError.value = ''
}

// Search mangas
async function searchMangas() {
  if (!searchQuery.value.trim()) {
    searchError.value = 'Debe ingresar un término de búsqueda'
    return
  }
  
  searching.value = true
  searchError.value = ''
  searchResults.value = []
  
  try {
    const params = {}
    if (searchType.value === 'nombre') {
      params.search = searchQuery.value.trim()
    } else if (searchType.value === 'codigo') {
      params.codigo = searchQuery.value.trim()
    }
    
    const response = await api.get('manga/mangas/', { params })
    searchResults.value = response.data.results || response.data || []
    
    if (searchResults.value.length === 0) {
      searchError.value = 'No se encontraron series con ese criterio'
    }
  } catch (e) {
    searchError.value = e.response?.data?.detail || 'Error al buscar series'
  } finally {
    searching.value = false
  }
}
// Cargar datos relacionados del manga seleccionado
async function loadRelatedForManga(mangaId) {
  try {
    const alts = await listAltTitulos({ manga: mangaId, page_size: 1000 })
    titulosAlternativos.value = alts.map(x => ({ id: x.id, titulo_alternativo: x.titulo_alternativo || x.titulo || x.title || '', codigo_lenguaje: x.codigo_lenguaje || 'es', vigente: x.vigente !== false }))
  } catch { titulosAlternativos.value = [] }
  try {
    const cvs = await listCovers({ manga: mangaId, page_size: 1000 })
    covers.value = cvs.map(x => ({ id: x.id, url_imagen: x.url_imagen || x.url || '', tipo_cover: x.tipo_cover || 'main', vigente: x.vigente !== false }))
    updatePreview()
  } catch { covers.value = [] }
  try {
    const auts = await listAutoresRel({ manga: mangaId, page_size: 1000 })
    autoresExtra.value = auts.map(x => ({ id: x.id, autor_id: x.autor?.id || x.autor || null, rol: x.rol || 'author', vigente: x.vigente !== false }))
  } catch { autoresExtra.value = [] }
  try {
    const tgs = await listTagsRel({ manga: mangaId, page_size: 1000 })
    existingTagIds.value = tgs.map(x => Number(x.tag?.id || x.tag)).filter(Boolean)
    tagsSeleccionados.value = [...existingTagIds.value]
  } catch {
    existingTagIds.value = []
    tagsSeleccionados.value = []
  }
}

// Seleccionar serie desde resultados y preparar formulario
async function selectSerie(serie) {
  if (!catalogsLoaded.value) await loadCatalogs()
  selectedSerie.value = serie
  editingManga.value = serie
  currentView.value = 'form'
  mangaForm.value = {
    codigo: serie.codigo || '',
    titulo: serie.titulo || '',
    sinopsis: serie.sinopsis || '',
    estado_id: Number(serie.estado?.id ?? serie.estado ?? serie.estado_id ?? '') || null,
    demografia_id: Number(serie.demografia?.id ?? serie.demografia ?? serie.demografia_id ?? '') || null,
    tipo_serie: String(serie.tipo_serie || 'manga'),
    autor_id: Number(serie.autor?.id ?? serie.autor ?? serie.autor_id ?? '') || null,
    fecha_lanzamiento: serie.fecha_lanzamiento || '',
    erotico: serie.erotico || false,
    vigente: serie.vigente !== false
  }
  ensureSelectDefaults()
  await loadRelatedForManga(serie.id)
}

// Start fresh (create new manga)
function startFresh() {
  selectedSerie.value = null
  editingManga.value = null
  currentView.value = 'form'
  searchResults.value = []
  searchQuery.value = ''
  
  mangaForm.value = {
    codigo: '',
    titulo: '',
    sinopsis: '',
    estado_id: null,
    demografia_id: null,
    tipo_serie: 'manga',
    autor_id: null,
    fecha_lanzamiento: '',
    erotico: false,
    vigente: true
  }
  
  
  titulosAlternativos.value = []
  covers.value = []
  coversToDelete.value = []
  autoresExtra.value = []
  tagsSeleccionados.value = []
  previewUrl.value = ''
  lastAutoCode.value = ''
  coverFile.value = null
  // Reset file input if exists
  const fileInput = document.getElementById('coverFileUpload')
  if (fileInput) fileInput.value = ''
}

// Forzar que los selects queden con el valor actual del formulario
function ensureSelectDefaults() {
  try {
    if (mangaForm.value.estado_id) mangaForm.value.estado_id = Number(mangaForm.value.estado_id)
    if (mangaForm.value.demografia_id) mangaForm.value.demografia_id = Number(mangaForm.value.demografia_id)
    if (mangaForm.value.autor_id) mangaForm.value.autor_id = Number(mangaForm.value.autor_id)
  } catch (e) {}
}

// Back to list
function backToList() {
  currentView.value = 'list'
  saveSuccess.value = ''
  saveError.value = ''
  fetchMangas()
}

// Add titulo alternativo
function addTituloAlt() {
  titulosAlternativos.value.push({
    titulo_alternativo: '',
    codigo_lenguaje: 'es',
    vigente: true
  })
}

function removeTituloAlt(index) {
  titulosAlternativos.value.splice(index, 1)
}

// Add cover
function addCover() {
  covers.value.push({
    url_imagen: '',
    tipo_cover: 'main',
    vigente: true
  })
}

function removeCover(index) {
  const item = covers.value[index]
  if (item.id) {
    coversToDelete.value.push(item)
  }
  covers.value.splice(index, 1)
}

function updatePreview() {
  const mainCover = covers.value.find(c => c.tipo_cover === 'main')
  previewUrl.value = mainCover?.url_imagen || ''
}

// Add autor extra
function addAutorExtra() {
  autoresExtra.value.push({
    autor_id: null,
    rol: 'author',
    vigente: true
  })
}

function removeAutorExtra(index) {
  autoresExtra.value.splice(index, 1)
}

// Para comparar tags existentes al editar
const existingTagIds = ref([])

function handleFileChange(event) {
  const file = event.target.files[0]
  if (file) {
    coverFile.value = file
    // Preview local
    previewUrl.value = URL.createObjectURL(file)
  } else {
    coverFile.value = null
  }
}

// Save manga
async function saveManga() {
  if (!mangaForm.value.titulo.trim()) {
    saveError.value = 'El título es obligatorio'
    return
  }
  if (!mangaForm.value.estado_id) {
    saveError.value = 'Debe seleccionar un estado'
    return
  }
  if (!mangaForm.value.demografia_id) {
    saveError.value = 'Debe seleccionar una demografía'
    return
  }
  if (!mangaForm.value.autor_id) {
    saveError.value = 'Debe seleccionar un autor principal'
    return
  }
  
  saving.value = true
  saveError.value = ''
  saveSuccess.value = ''
  
  try {
    // Build payload matching API field names (no *_id)
    const baseSinopsis = (mangaForm.value.sinopsis || '').trim()
    const payload = {
      codigo: mangaForm.value.codigo || '',
      titulo: mangaForm.value.titulo || '',
      sinopsis: editingManga.value ? baseSinopsis : (baseSinopsis || 'Sin sinopsis.'),
      estado: Number(mangaForm.value.estado_id),
      demografia: Number(mangaForm.value.demografia_id),
      tipo_serie: mangaForm.value.tipo_serie,
      autor: Number(mangaForm.value.autor_id),
      fecha_lanzamiento: mangaForm.value.fecha_lanzamiento || null,
      erotico: !!mangaForm.value.erotico,
      vigente: mangaForm.value.vigente !== false
    }

    let mangaId
    if (editingManga.value) {
      // Edit: check if we have a file to upload
      if (coverFile.value) {
        const formData = new FormData()
        Object.keys(payload).forEach(key => {
          if (payload[key] !== null && payload[key] !== undefined) {
             formData.append(key, payload[key])
          }
        })
        formData.append('cover_image', coverFile.value)
        
        const response = await api.patch(`manga/mangas/${editingManga.value.id}/`, formData, {
          headers: { 'Content-Type': 'multipart/form-data' }
        })
        mangaId = response.data.id
      } else {
        const response = await api.patch(`manga/mangas/${editingManga.value.id}/`, payload)
        mangaId = response.data.id
      }
    } else {
      // Creation: check if we have a file to upload
      if (coverFile.value) {
        const formData = new FormData()
        Object.keys(payload).forEach(key => {
          if (payload[key] !== null && payload[key] !== undefined) {
             formData.append(key, payload[key])
          }
        })
        formData.append('cover_image', coverFile.value)
        
        const response = await api.post('manga/mangas/', formData, {
          headers: { 'Content-Type': 'multipart/form-data' }
        })
        mangaId = response.data.id
      } else {
        const response = await api.post('manga/mangas/', payload)
        mangaId = response.data.id
      }
    }
    
    // Títulos alternativos: PATCH si existe id, POST si no
    for (const titulo of titulosAlternativos.value) {
      if (titulo.titulo_alternativo && titulo.titulo_alternativo.trim()) {
        if (titulo.id) {
          await api.patch(`manga/manga-alt-titulos/${titulo.id}/`, {
            manga: mangaId,
            titulo_alternativo: titulo.titulo_alternativo,
            codigo_lenguaje: titulo.codigo_lenguaje,
            vigente: titulo.vigente
          })
        } else {
          await api.post('manga/manga-alt-titulos/', {
            manga: mangaId,
            titulo_alternativo: titulo.titulo_alternativo,
            codigo_lenguaje: titulo.codigo_lenguaje,
            vigente: titulo.vigente
          })
        }
      }
    }
    
    // Covers: PATCH si id, POST si no
    // Clone covers list to avoid modifying the UI bound array
    const coversToSync = [...covers.value]
    
    // CRITICAL: If we uploaded a new Main Cover file (coverFile), the backend (MangaSerializer)
    // automatically sets all previous 'main' covers to vigente=False.
    // If we include those same 'main' covers in this update loop with vigente=True (from UI),
    // we will undo the backend's work and create duplicates.
    // So, if coverFile exists, we SKIP syncing any 'main' cover from the list.
    if (coverFile.value) {
      for (let i = coversToSync.length - 1; i >= 0; i--) {
         if (coversToSync[i].tipo_cover === 'main') {
           coversToSync.splice(i, 1)
         }
      }
    }

    for (const cover of coversToSync) {
      if (cover.url_imagen && cover.url_imagen.trim()) {
        if (cover.id) {
          await api.patch(`manga/manga-covers/${cover.id}/`, {
            manga: mangaId,
            url_imagen: cover.url_imagen,
            tipo_cover: cover.tipo_cover,
            vigente: cover.vigente
          })
        } else {
          await api.post('manga/manga-covers/', {
            manga: mangaId,
            url_imagen: cover.url_imagen,
            tipo_cover: cover.tipo_cover,
            vigente: cover.vigente
          })
        }
      }
    }


    // Process deleted covers
    for (const dCover of coversToDelete.value) {
      if (dCover.id) {
        // Option A: Hard Delete
        // await api.delete(`manga/manga-covers/${dCover.id}/`)
        // Option B: Soft Delete (Vigente = false) - Safer
        await api.patch(`manga/manga-covers/${dCover.id}/`, { vigente: false })
      }
    }
    
    // Autores adicionales: PATCH si id, POST si no
    for (const autor of autoresExtra.value) {
      if (autor.autor_id) {
        if (autor.id) {
          await api.patch(`manga/manga-autores/${autor.id}/`, {
            manga: mangaId,
            autor: autor.autor_id,
            rol: autor.rol,
            vigente: autor.vigente
          })
        } else {
          await api.post('manga/manga-autores/', {
            manga: mangaId,
            autor: autor.autor_id,
            rol: autor.rol,
            vigente: autor.vigente
          })
        }
      }
    }
    
    // Tags: crear solo los que no existían
    const toCreate = tagsSeleccionados.value
      .map(x => Number(x))
      .filter(x => !existingTagIds.value.includes(x))

    for (const tagId of toCreate) {
      await api.post('manga/manga-tags/', { manga: mangaId, tag: tagId, vigente: true })
    }
    
    saveSuccess.value = editingManga.value 
      ? 'Manga actualizado exitosamente' 
      : 'Manga creado exitosamente'
    
    setTimeout(() => {
      backToList()
    }, 2000)
    
  } catch (e) {
    saveError.value = e.response?.data?.detail || e.response?.data?.error || 'Error al guardar el manga'
    console.error('Error guardando manga:', e.response?.data || e)
  } finally {
    saving.value = false
  }
}

const canSearch = computed(() => searchQuery.value.trim().length > 0)

onMounted(() => {
  fetchMangas()
  loadCatalogs()
})

// Auto-generate 'codigo' from 'titulo' while creating
watch(() => mangaForm.value.titulo, (t) => {
  if (!editingManga.value) {
    maybeAutoGenerateCode(t)
  }
})
</script>

<template>
  <div class="mangas-admin container py-4">
    <!-- LIST VIEW -->
    <div v-if="currentView === 'list'">
      <div class="d-flex justify-content-between align-items-center mb-3">
        <h2 class="mb-0">Administrar Mangas</h2>
        <div class="btn-group">
          <button @click="startFresh" class="btn btn-outline-success">
            <i class="bi bi-plus-circle"></i> Crear
          </button>
        </div>
      </div>
      
      <p class="text-muted">Lista y edición rápida del flag erótico.</p>
      <div v-if="error" class="alert alert-danger py-2">{{ error }}</div>
      <div v-if="loading" class="text-center py-4">
        <img src="/assets/load.gif" alt="Cargando..." style="width: 48px; height: 48px;" />
        <p>Cargando mangas...</p>
      </div>
      <!-- Buscador manual y top 20 más visitados -->
      <div v-if="!loading" class="mb-3">
        <div class="input-group">
          <input v-model="searchListQuery" type="text" class="form-control" placeholder="Buscar por nombre o código..." @keyup.enter="searchInList" />
          <button class="btn btn-primary" @click="searchInList">Buscar</button>
        </div>
        <small class="text-muted">Si no buscas, se muestran las 20 series más visitadas.</small>
      </div>

      <div v-if="!loading" class="row g-3">
        <div v-for="m in mangasFiltered" :key="m.id" class="col-12 col-md-6 col-lg-4">
          <div class="card h-100">
            <div class="card-body d-flex flex-column">
              <h6 class="text-truncate mb-2" :title="m.titulo || m.title">{{ m.titulo || m.title }}</h6>
              <div class="mb-2">
                <span :class="['badge', (m.erotico || m.erotic) ? 'bg-danger' : 'bg-secondary']">{{ (m.erotico || m.erotic) ? 'Erótico' : 'No Erótico' }}</span>
                <span class="badge bg-dark ms-2">Vistas: {{ m.vistas || 0 }}</span>
              </div>
              <div class="mt-auto d-flex gap-2">
                <button class="btn btn-sm btn-outline-primary flex-grow-1" @click="toggleErotico(m)">
                  {{ (m.erotico || m.erotic) ? 'Marcar No Erótico' : 'Marcar Erótico' }}
                </button>
                <button class="btn btn-sm btn-outline-secondary" @click="selectSerie(m)">Editar</button>
              </div>
            </div>
          </div>
        </div>
        <div v-if="!mangasFiltered.length" class="text-center py-4 text-muted">No hay mangas para mostrar.</div>
      </div>
    </div>

    <!-- SEARCH VIEW -->
    <div v-if="currentView === 'search'">
      <div class="mb-3">
        <button @click="backToList" class="btn btn-outline-secondary btn-sm">
          ← Volver a lista
        </button>
      </div>
      
      <div class="card mb-4">
      </div>
    </div>

    <!-- FORM VIEW -->
    <div v-if="currentView === 'form'">
      <div class="mb-3 d-flex gap-2">
        <button @click="backToList" class="btn btn-outline-secondary btn-sm">
          ← Volver a lista
        </button>
      </div>
      
      <h3 class="mb-3">{{ editingManga ? 'Editar' : 'Crear' }} Manga</h3>
      
      <div v-if="saveSuccess" class="alert alert-success">{{ saveSuccess }}</div>
      <div v-if="saveError" class="alert alert-danger">{{ saveError }}</div>
      
      <!-- Main Manga Data -->
      <div class="card mb-3">
        <div class="card-header">
          <h5>Datos Principales del Manga</h5>
        </div>
        <div class="card-body">
          <div class="row g-3">
            <div class="col-md-6">
              <label class="form-label">Código</label>
              <input v-model="mangaForm.codigo" type="text" class="form-control" />
            </div>
            
            <div class="col-md-6">
              <label class="form-label">Título <span class="text-danger">*</span></label>
              <input v-model="mangaForm.titulo" type="text" class="form-control" required />
            </div>
            
            <div class="col-12">
              <label class="form-label">Sinopsis</label>
              <textarea v-model="mangaForm.sinopsis" class="form-control" rows="4"></textarea>
            </div>
            
            <div class="col-md-4">
              <label class="form-label">Estado <span class="text-danger">*</span></label>
              <select v-model="mangaForm.estado_id" class="form-select" required>
                <option :value="null">Seleccione...</option>
                <option v-for="e in estados" :key="e.id" :value="e.id">
                  {{ e.descripcion }}
                </option>
              </select>
            </div>
            
            <div class="col-md-4">
              <label class="form-label">Demografía <span class="text-danger">*</span></label>
              <select v-model="mangaForm.demografia_id" class="form-select" required>
                <option :value="null">Seleccione...</option>
                <option v-for="d in demografias" :key="d.id" :value="d.id">
                  {{ d.descripcion }}
                </option>
              </select>
            </div>
            
            <div class="col-md-4">
              <label class="form-label">Tipo de Serie <span class="text-danger">*</span></label>
              <select v-model="mangaForm.tipo_serie" class="form-select" required>
                <option v-for="t in tipoSerieOptions" :key="t.value" :value="t.value">
                  {{ t.label }}
                </option>
              </select>
            </div>
            
            <div class="col-md-4">
              <label class="form-label">Autor Principal <span class="text-danger">*</span></label>
              <select v-model="mangaForm.autor_id" class="form-select" required>
                <option :value="null">Seleccione...</option>
                <option v-for="a in autores" :key="a.id" :value="a.id">
                  {{ a.nombre }} ({{ a.tipo_autor }})
                </option>
              </select>
            </div>
            
            <div class="col-md-4">
              <label class="form-label">Fecha de Lanzamiento</label>
              <input v-model="mangaForm.fecha_lanzamiento" type="date" class="form-control" />
            </div>
            
            <div class="col-md-4 d-flex align-items-center gap-3 pt-4">
              <div class="form-check">
                <input v-model="mangaForm.erotico" type="checkbox" class="form-check-input" id="erotico" />
                <label class="form-check-label" for="erotico">Erótico</label>
              </div>
              
              <div class="form-check">
                <input v-model="mangaForm.vigente" type="checkbox" class="form-check-input" id="vigente" />
                <label class="form-check-label" for="vigente">Vigente</label>
              </div>
            </div>
          </div>
        </div>
      </div>
      
      <!-- Títulos Alternativos -->
      <div class="card mb-3">
        <div class="card-header d-flex justify-content-between align-items-center">
          <h5>Títulos Alternativos</h5>
          <button @click="addTituloAlt" class="btn btn-sm btn-outline-primary">
            + Agregar Título
          </button>
        </div>
        <div class="card-body">
          <div v-if="titulosAlternativos.length === 0" class="text-muted text-center py-3">
            No hay títulos alternativos.
          </div>
          
          <div v-for="(titulo, index) in titulosAlternativos" :key="index" class="row g-2 mb-2 align-items-center">
            <div class="col-md-6">
              <input v-model="titulo.titulo_alternativo" type="text" class="form-control" placeholder="Título alternativo" />
            </div>
            <div class="col-md-3">
              <input v-model="titulo.codigo_lenguaje" type="text" class="form-control" placeholder="Idioma (ej: es, en, ja)" />
            </div>
            <div class="col-md-2">
              <div class="form-check">
                <input v-model="titulo.vigente" type="checkbox" class="form-check-input" :id="'tit-vig-' + index" />
                <label class="form-check-label" :for="'tit-vig-' + index">Vigente</label>
              </div>
            </div>
            <div class="col-md-1">
              <button @click="removeTituloAlt(index)" class="btn btn-sm btn-outline-danger">✕</button>
            </div>
          </div>
        </div>
      </div>
      
      <!-- Covers with Preview -->
      <div class="card mb-3">
        <div class="card-header d-flex justify-content-between align-items-center">
          <h5>Imágenes de Portada</h5>
          <button @click="addCover" class="btn btn-sm btn-outline-primary">
            + Agregar Cover
          </button>
        </div>
        <div class="card-body">
          <div class="row">
            <div class="col-md-8">
              <div v-if="covers.length === 0" class="text-muted text-center py-3">
                No hay covers.
              </div>
              
              <div v-for="(cover, index) in covers" :key="index" class="row g-2 mb-2 align-items-center">
                <div class="col-md-5">
                  <input 
                    v-model="cover.url_imagen" 
                    type="text" 
                    class="form-control" 
                    placeholder="URL de la imagen"
                    @input="updatePreview"
                  />
                </div>
                <div class="col-md-3">
                  <select v-model="cover.tipo_cover" class="form-select" @change="updatePreview">
                    <option v-for="t in coverTipoOptions" :key="t.value" :value="t.value">
                      {{ t.label }}
                    </option>
                  </select>
                </div>
                <div class="col-md-2">
                  <div class="form-check">
                    <input v-model="cover.vigente" type="checkbox" class="form-check-input" :id="'cov-vig-' + index" />
                    <label class="form-check-label" :for="'cov-vig-' + index">Vigente</label>
                  </div>
                </div>
                <div class="col-md-2">
                  <button @click="removeCover(index); updatePreview()" class="btn btn-sm btn-outline-danger">✕</button>
                </div>
              </div>
            </div>
            

            
            <!-- Upload Cover File (Creation & Edit) -->
            <div class="col-12 mt-3">
              <div class="alert alert-info" v-if="!editingManga">
                <strong>Nuevo:</strong> Puedes subir la portada principal directamente aquí. Se creará automáticamente la entrada en Covers.
              </div>
              <div class="alert alert-warning" v-else>
                <strong>Editar Portada:</strong> Si subes un archivo aquí, se agregará como nueva portada principal.
              </div>
              <label class="form-label">Subir Portada Principal (Archivo)</label>
              <input type="file" id="coverFileUpload" class="form-control" accept="image/*" @change="handleFileChange" />
            </div>

            <!-- Preview -->
            <div class="col-md-4">
              <div class="cover-preview">
                <h6 class="text-center mb-2">Preview (Main Cover)</h6>
                <div v-if="previewUrl" class="preview-container">
                  <img :src="previewUrl" alt="Preview" class="img-fluid rounded" />
                </div>
                <div v-else class="preview-placeholder">
                  <p class="text-muted">Sin imagen</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
      
      <!-- Autores Extra -->
      <div class="card mb-3">
        <div class="card-header d-flex justify-content-between align-items-center">
          <h5>Autores Adicionales</h5>
          <button @click="addAutorExtra" class="btn btn-sm btn-outline-primary">
            + Agregar Autor
          </button>
        </div>
        <div class="card-body">
          <div v-if="autoresExtra.length === 0" class="text-muted text-center py-3">
            No hay autores adicionales.
          </div>
          
          <div v-for="(autor, index) in autoresExtra" :key="index" class="row g-2 mb-2 align-items-center">
            <div class="col-md-5">
              <select v-model="autor.autor_id" class="form-select">
                <option :value="null">Seleccione autor...</option>
                <option v-for="a in autores" :key="a.id" :value="a.id">
                  {{ a.nombre }} ({{ a.tipo_autor }})
                </option>
              </select>
            </div>
            <div class="col-md-3">
              <select v-model="autor.rol" class="form-select">
                <option v-for="r in rolOptions" :key="r.value" :value="r.value">
                  {{ r.label }}
                </option>
              </select>
            </div>
            <div class="col-md-2">
              <div class="form-check">
                <input v-model="autor.vigente" type="checkbox" class="form-check-input" :id="'aut-vig-' + index" />
                <label class="form-check-label" :for="'aut-vig-' + index">Vigente</label>
              </div>
            </div>
            <div class="col-md-2">
              <button @click="removeAutorExtra(index)" class="btn btn-sm btn-outline-danger">✕</button>
            </div>
          </div>
        </div>
      </div>
      
      <!-- Tags -->
      <div class="card mb-3">
        <div class="card-header">
          <h5>Tags / Géneros</h5>
        </div>
        <div class="card-body">
          <div class="row">
            <div class="col-md-12">
              <label class="form-label">Seleccione tags (puede elegir varios):</label>
              <select v-model="tagsSeleccionados" class="form-select" multiple size="8">
                <option v-for="tag in allTags" :key="tag.id" :value="tag.id">
                  {{ tag.descripcion }}
                </option>
              </select>
              <small class="text-muted">Mantén Ctrl (Windows) o Cmd (Mac) para seleccionar múltiples opciones.</small>
            </div>
          </div>
          
          <div v-if="tagsSeleccionados.length > 0" class="mt-3">
            <strong>Tags seleccionados:</strong>
            <div class="d-flex flex-wrap gap-1 mt-2">
              <span 
                v-for="tagId in tagsSeleccionados" 
                :key="tagId" 
                class="badge bg-info"
              >
                {{ allTags.find(t => t.id === tagId)?.descripcion }}
              </span>
            </div>
          </div>
        </div>
      </div>
      
      <!-- Save Button -->
      <div class="text-center">
        <button 
          @click="saveManga" 
          class="btn btn-success btn-lg"
          :disabled="saving"
        >
          {{ saving ? 'Guardando...' : (editingManga ? 'Actualizar Manga' : 'Crear Manga') }}
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped lang="css">
.mangas-admin-view { color: var(--ztmo-text); }
.mangas-admin-view .form-label, .mangas-admin-view .text-muted, .mangas-admin-view label, .mangas-admin-view h2, .mangas-admin-view h5, .mangas-admin-view h6, .mangas-admin-view p, .mangas-admin-view span {
  color: var(--ztmo-text);
}
.mangas-admin-view .card {
  background-color: var(--ztmo-panel, var(--ztmo-bg-secondary));
  border-color: var(--ztmo-border);
}
.mangas-admin-view .card-header {
  background-color: var(--ztmo-panel, var(--ztmo-bg-secondary));
  border-bottom-color: var(--ztmo-border);
}
.mangas-admin-view .form-control, .mangas-admin-view .form-select {
  background-color: var(--ztmo-bg-secondary);
  color: var(--ztmo-text);
  border-color: var(--ztmo-border);
}
.mangas-admin-view .form-control::placeholder { color: rgba(255,255,255,0.6); }
.mangas-admin-view .btn, .mangas-admin-view .btn-outline-primary, .mangas-admin-view .btn-outline-success, .mangas-admin-view .btn-outline-danger, .mangas-admin-view .btn-primary, .mangas-admin-view .btn-success, .mangas-admin-view .btn-danger {
  color: var(--ztmo-text);
}
.text-truncate { white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
.mangas-admin { color: var(--ztmo-text); max-width: 1200px; }
.mangas-admin .text-muted { color: var(--ztmo-text); opacity: 0.75; }
.mangas-admin .form-label { color: var(--ztmo-text); font-weight: 500; }
.text-danger { color: #dc3545 !important; }

.card {
  background-color: var(--ztmo-bg-secondary);
  border-color: var(--ztmo-border);
}

.card-header {
  background-color: var(--ztmo-bg-tertiary);
  border-bottom-color: var(--ztmo-border);
}

.list-group-item {
  background-color: var(--ztmo-bg-secondary);
  border-color: var(--ztmo-border);
  color: var(--ztmo-text);
}

.list-group-item:hover {
  background-color: var(--ztmo-bg-tertiary);
}

.cover-preview {
  position: sticky;
  top: 20px;
}

.preview-container {
  border: 2px solid var(--ztmo-border);
  border-radius: 8px;
  overflow: hidden;
  min-height: 300px;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: var(--ztmo-bg-tertiary);
}

.preview-container img {
  max-height: 400px;
  object-fit: contain;
}

.preview-placeholder {
  border: 2px dashed var(--ztmo-border);
  border-radius: 8px;
  min-height: 300px;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: var(--ztmo-bg-tertiary);
}

.form-select[multiple] {
  background-color: var(--ztmo-bg-secondary);
  color: var(--ztmo-text);
  border-color: var(--ztmo-border);
}

.form-select[multiple] option {
  padding: 8px;
}

.form-select[multiple] option:checked {
  background-color: #0d6efd;
  color: white;
}
</style>
