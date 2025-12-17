<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import api from '@/services/api'
import axios from 'axios'

// Inputs
const mangaId = ref('')
const chapterNumber = ref('')
const chapterTitle = ref('')
const volume = ref('')
const pagesCount = ref('')
const seriesCode = ref('') // código entre chapters/ y /<num-capitulo>/

// Manga list for selection
const mangas = ref([])
const loadingMangas = ref(false)
const searchQuery = ref('')
const searching = ref(false)
const searchError = ref('')

// Editing existing chapter
const chapters = ref([])
const loadingChapters = ref(false)
const selectedChapterId = ref('')
const existing = ref(null)

const uploading = ref(false)
const message = ref('')
const error = ref('')

// Modes: 'manual' | 'url'
const uploadMode = ref('manual')
const importUrl = ref('')
const useManualCode = ref(false)
const manualSeriesCode = ref('')

const normalizedChapterNumber = computed(() => pad3(chapterNumber.value))
const normalizedPagesCount = computed(() => Number(pagesCount.value) || 0)

function pad3(v) {
  const n = String(v || '').replace(/\D/g, '')
  if (!n) return ''
  return n.padStart(3, '0')
}

function buildImageUrls() {
  const count = normalizedPagesCount.value
  const chapterStr = normalizedChapterNumber.value
  const code = (seriesCode.value || '').trim()
  if (!code || !chapterStr || !count) return []
  const base = 'https://f005.backblazeb2.com/file/MangaApi/chapters'
  const arr = []
  for (let i = 1; i <= count; i++) {
    const page = String(i).padStart(3, '0')
    arr.push(`${base}/${code}/${chapterStr}/${page}.webp`)
  }
  return arr
}

const chapterPayload = computed(() => {
  const defaultTitle = chapterNumber.value ? `Capitulo ${normalizedChapterNumber.value}` : ''
  const title = (chapterTitle.value || '').trim() || defaultTitle
  const chNumRaw = Number(String(chapterNumber.value || '').replace(/[^\d.]/g, ''))
  const volNumRaw = Number(String(volume.value || '').replace(/[^\d.]/g, ''))
  return {
    manga: Number(mangaId.value) || null,
    capitulo_numero: Number.isFinite(chNumRaw) && chNumRaw > 0 ? chNumRaw.toFixed(2) : null,
    titulo: title,
    volumen_numero: Number.isFinite(volNumRaw) && volNumRaw > 0 ? volNumRaw.toFixed(2) : null,
    pages: { images: buildImageUrls() },
  }
})

async function fetchMangas() {
  loadingMangas.value = true
  try {
    const { listMangas } = await import('@/services/mangaService')
    const data = await listMangas({ page_size: 500, ordering: '-id' })
    let list = Array.isArray(data) ? data : (data?.results || [])
    // Fallback a endpoints directos si el servicio devuelve vacío
    if (!list.length) {
      try {
        const r = await api.get('manga/mangas/', { params: { page_size: 500, ordering: '-id' } })
        list = Array.isArray(r.data) ? r.data : (r.data?.results || [])
      } catch (e2) {
        try {
          const r2 = await api.get('mangas/', { params: { page_size: 500, ordering: '-id' } })
          list = Array.isArray(r2.data) ? r2.data : (r2.data?.results || [])
        } catch {}
      }
    }
    // Map minimal info and sort desc by id
    mangas.value = list
      .map(m => ({ id: m.id, titulo: m.titulo || m.title || `Manga #${m.id}`, codigo: m.codigo || m.code || '' }))
      .sort((a, b) => Number(b.id) - Number(a.id))
  } catch (e) {
    // Fallback: intenta directo a API
    try {
      const r = await api.get('manga/mangas/', { params: { page_size: 500, ordering: '-id' } })
      const list = Array.isArray(r.data) ? r.data : (r.data?.results || [])
      mangas.value = list
        .map(m => ({ id: m.id, titulo: m.titulo || m.title || `Manga #${m.id}`, codigo: m.codigo || m.code || '' }))
        .sort((a, b) => Number(b.id) - Number(a.id))
    } catch (e2) {
      try {
        const r2 = await api.get('mangas/', { params: { page_size: 500, ordering: '-id' } })
        const list2 = Array.isArray(r2.data) ? r2.data : (r2.data?.results || [])
        mangas.value = list2
          .map(m => ({ id: m.id, titulo: m.titulo || m.title || `Manga #${m.id}`, codigo: m.codigo || m.code || '' }))
          .sort((a, b) => Number(b.id) - Number(a.id))
      } catch {
        // Si todo falla, deja vacío y el usuario puede ingresar el ID/código manualmente
        mangas.value = []
      }
    }
  } finally {
    loadingMangas.value = false
  }
}

onMounted(fetchMangas)

// Autofill seriesCode from selected manga if available
watch(mangaId, (val) => {
  const m = mangas.value.find(x => String(x.id) === String(val))
  if (m && m.codigo && !seriesCode.value) {
    seriesCode.value = m.codigo
  }
  // Load chapters for selected manga
  if (val) fetchChaptersForManga(val)
})

async function fetchChaptersForManga(mangaIdVal) {
  loadingChapters.value = true
  chapters.value = []
  existing.value = null
  selectedChapterId.value = ''
  try {
    // List chapters for manga
    const { listChapters } = await import('@/services/chapterService')
    const data = await listChapters({ manga: mangaIdVal, page_size: 500, ordering: '-id' })
    chapters.value = Array.isArray(data) ? data : (data?.results || [])
  } catch (e) {
    // leave empty; user can still input ID
  } finally {
    loadingChapters.value = false
  }
}

// Búsqueda manual por título o código
async function searchMangasManual() {
  searchError.value = ''
  searching.value = true
  try {
    const q = (searchQuery.value || '').trim()
    if (!q) { searchError.value = 'Ingresa un término'; return }
    const params = {}
    // Heurística: si contiene espacios o letras, usa search (título); si es código corto sin espacios, intenta código
    if (/\s/.test(q) || /[a-zA-Z]/.test(q)) params.search = q
    else params.codigo = q
    params.page_size = 50
    let list = []
    try {
      const r = await api.get('manga/mangas/', { params })
      list = Array.isArray(r.data) ? r.data : (r.data?.results || [])
    } catch (e1) {
      try {
        const r2 = await api.get('mangas/', { params })
        list = Array.isArray(r2.data) ? r2.data : (r2.data?.results || [])
      } catch (e2) {
        throw e2
      }
    }
    mangas.value = list
      .map(m => ({ id: m.id, titulo: m.titulo || m.title || `Manga #${m.id}`, codigo: m.codigo || m.code || '' }))
      .sort((a, b) => Number(b.id) - Number(a.id))
    if (!mangas.value.length) searchError.value = 'Sin resultados'
  } catch (e) {
    searchError.value = e?.message || 'Error buscando'
  } finally {
    searching.value = false
  }
}

async function loadSelectedChapter() {
  existing.value = null
  if (!selectedChapterId.value) return
  try {
    const { getChapter } = await import('@/services/chapterService')
    const data = await getChapter(selectedChapterId.value)
    existing.value = data || null
    // Prefill form from existing chapter
    if (existing.value) {
      mangaId.value = existing.value.manga
      chapterNumber.value = String(existing.value.capitulo_numero || '').split('.')[0].padStart(3, '0')
      chapterTitle.value = existing.value.titulo || ''
      volume.value = existing.value.volumen_numero ? String(existing.value.volumen_numero).split('.')[0] : ''
      // Try deducing series code from first image
      const first = existing.value.pages?.images?.[0] || ''
      const m = first.match(/chapters\/(.*?)\/[0-9]{3}\/[0-9]{3}\.webp/)
      if (m && m[1]) seriesCode.value = m[1]
      // Pages count from stored images
      pagesCount.value = String(existing.value.pages?.images?.length || '')
    }
  } catch (e) {
    existing.value = null
  }
}

const selectedFiles = ref([])
const uploadProgress = ref(0)
const totalUploads = ref(0)

function handleFiles(event) {
  const files = Array.from(event.target.files || [])
  // Sort by name ensures 1.jpg, 2.jpg order if named correctly
  selectedFiles.value = files.sort((a, b) => a.name.localeCompare(b.name, undefined, { numeric: true }))
  pagesCount.value = files.length
}

async function uploadFileToB2(file, index) {
  const ext = 'webp' // Force webp or keep original? Plan said rename to .webp
  // To keep it simple and consistent with buildImageUrls logic:
  // We will rename the file to {001}.webp
  const filename = `${pad3(index + 1)}.${ext}`
  const code = seriesCode.value.trim()
  const chap = normalizedChapterNumber.value
  const path = `chapters/${code}/${chap}/${filename}`
  
  // 1. Get signed URL
  const { data } = await api.post('upload/sign/', { 
    file_path: path,
    content_type: 'image/webp' 
  })
  
  if (!data.url) throw new Error('No signed URL returned')

  // 2. Upload to B2
  await axios.put(data.url, file, {
    headers: { 'Content-Type': 'image/webp' }
  })
}

async function submit() {
  error.value = ''
  message.value = ''
  const payload = chapterPayload.value
  
  // Worker Mode Logic
  if (uploadMode.value === 'url') {
    if (!payload.manga || !payload.capitulo_numero || !importUrl.value) {
       error.value = 'Para importar: Seleccióna Manga, Número de Capítulo y URL.'
       return
    }
    
    if (useManualCode.value && !manualSeriesCode.value) {
        error.value = 'Has marcado "Usar código manual" pero no has ingresado ninguno.'
        return
    }
    
    uploading.value = true
    try {
       const res = await api.post('chapters/fetch/', {
          url: importUrl.value,
          manga_id: payload.manga,
          chapter_num: payload.capitulo_numero,
          series_code: useManualCode.value ? manualSeriesCode.value : null
       })
       message.value = 'Tarea iniciada correctamente en el Worker. Las imágenes aparecerán pronto.'
       importUrl.value = ''
    } catch (e) {
       error.value = e.response?.data?.error || e.message || 'Error al iniciar tarea en worker'
    } finally {
       uploading.value = false
    }
    return
  }

  // Manual Mode Validation
  if (!payload.manga || !payload.capitulo_numero || !normalizedPagesCount.value || !seriesCode.value) {
    error.value = 'Completa Manga, Código de serie, Número y Cantidad de páginas.'
    return
  }
  
  if (!selectedFiles.value.length) {
    if (!payload.pages || !Array.isArray(payload.pages.images) || !payload.pages.images.length) {
      error.value = 'No has seleccionado archivos y el generador de URLs está vacío.'
      return
    }
    // If no files selected but user wants to just create DB record (legacy mode)
  }

  uploading.value = true
  uploadProgress.value = 0
  totalUploads.value = selectedFiles.value.length

  try {
    // 1. Upload files if any
    if (selectedFiles.value.length > 0) {
      let completed = 0
      // Upload sequential
      for (let i = 0; i < selectedFiles.value.length; i++) {
        await uploadFileToB2(selectedFiles.value[i], i)
        completed++
        uploadProgress.value = Math.round((completed / totalUploads.value) * 100)
      }
    }

    // 2. Create Chapter in DB
    const { createChapter } = await import('@/services/chapterService')
    await createChapter(payload)
    
    // 3. Reset
    message.value = 'Capítulo subido y creado correctamente.'
    chapterNumber.value = ''
    chapterTitle.value = ''
    volume.value = ''
    pagesCount.value = ''
    selectedFiles.value = []
    // Reset file input
    document.getElementById('fileInput').value = ''
    
  } catch (e) {
    console.error(e)
    error.value = e.message || 'Error al subir capítulos'
  } finally {
    uploading.value = false
    uploadProgress.value = 0
  }
}

async function updateChapter() {
  // Logic remains mostly same, but maybe allow re-uploading pages? 
  // For now, keep as metadata update only unless requested.
  error.value = ''
  message.value = ''
  if (!selectedChapterId.value) {
    error.value = 'Selecciona un capítulo existente para editar.'
    return
  }
  const payload = chapterPayload.value
  uploading.value = true
  try {
    await api.patch(`chapters/chapters/${selectedChapterId.value}/`, payload)
    message.value = 'Capítulo actualizado correctamente.'
  } catch (e) {
    try {
      await api.patch(`chapters/${selectedChapterId.value}/`, payload)
      message.value = 'Capítulo actualizado correctamente.'
    } catch (e2) {
      error.value = e2.message || e.message || 'Error al actualizar capítulo'
    }
  } finally {
    uploading.value = false
  }
}
</script>

<template>
  <div class="upload-chapter-view container py-4">
    <h2 class="mb-3">Subir Capítulo</h2>
    <p class="text-muted">Genera automáticamente las URLs de imágenes y crea el capítulo.</p>
    <div v-if="error" class="alert alert-danger py-2">{{ error }}</div>
    <div v-if="error" class="alert alert-danger py-2">{{ error }}</div>
    <div v-if="message" class="alert alert-success py-2">{{ message }}</div>
    
    <!-- Mode Switcher -->
    <ul class="nav nav-pills mb-3">
      <li class="nav-item">
        <a class="nav-link" :class="{ active: uploadMode === 'manual' }" href="#" @click.prevent="uploadMode = 'manual'">Subida Manual</a>
      </li>
      <li class="nav-item">
        <a class="nav-link" :class="{ active: uploadMode === 'url' }" href="#" @click.prevent="uploadMode = 'url'">Importar desde URL</a>
      </li>
    </ul>

    <form @submit.prevent="submit" class="v-stack gap-3">
      <div class="row g-3">
        <div class="col-md-6">
          <label class="form-label">Buscar Manga</label>
          <div class="d-flex gap-2 align-items-center mb-2">
            <input v-model="searchQuery" type="text" class="form-control" placeholder="Buscar por título o código" />
            <button type="button" class="btn btn-outline-secondary" :disabled="searching" @click="searchMangasManual">{{ searching ? 'Buscando...' : 'Buscar' }}</button>
          </div>
          <div v-if="searchError" class="small text-danger mb-2">{{ searchError }}</div>
          <label class="form-label">Manga (ID)</label>
          <select v-model="mangaId" class="form-select">
            <option value="" disabled>Selecciona manga</option>
            <option v-for="m in mangas" :key="m.id" :value="m.id">{{ m.id }} - {{ m.titulo }}</option>
          </select>
          <small class="text-muted">Ordenado de mayor a menor ID.</small>
          <div class="form-text">Escribe el código de serie o parte del título y elige el resultado.</div>
        </div>
        <div class="col-md-6">
          <label class="form-label">Código de serie (ej: en-9c1c08)</label>
          <input v-model="seriesCode" type="text" class="form-control" placeholder="Código entre chapters/ y /001/" />
        </div>
        <div class="col-md-4">
          <label class="form-label">Número Capítulo (001-999)</label>
          <input v-model="chapterNumber" type="text" class="form-control" placeholder="001" />
        </div>
        <div class="col-md-4">
          <label class="form-label">Volumen</label>
          <input v-model="volume" type="number" class="form-control" placeholder="Opcional" />
        </div>
        <div class="col-md-12" v-if="uploadMode === 'manual'">
          <label class="form-label">Archivos del Capítulo (Imágenes)</label>
          <input id="fileInput" type="file" multiple accept="image/*" class="form-control" @change="handleFiles" />
          <small class="text-muted">Selecciona las imágenes en orden. Se renombrarán automáticamente a 001.webp, 002.webp, etc.</small>
        </div>
        
        <div class="col-md-12" v-if="uploadMode === 'url'">
           <label class="form-label">URL del Capítulo (Scraper)</label>
           <input v-model="importUrl" type="url" class="form-control" placeholder="https://sitio-manga.com/ver/capitulo-1" />
           
           <div class="form-check mt-3">
             <input class="form-check-input" type="checkbox" id="manualCodeCheck" v-model="useManualCode">
             <label class="form-check-label" for="manualCodeCheck">
               Usar código de serie manual / existente
             </label>
           </div>
           
           <div v-if="useManualCode" class="mt-2">
             <input v-model="manualSeriesCode" type="text" class="form-control" placeholder="Ej: naruto-shippuden (nombre de carpeta)" />
             <small class="text-muted">Si no se especifica, se generará automáticamente basado en el título.</small>
           </div>
           
           <small class="text-muted d-block mt-2">El worker descargará las imágenes, las subirá a B2 y creará el capítulo automáticamente.</small>
        </div>
        <div class="col-md-4">
          <label class="form-label">Cantidad de páginas</label>
          <input v-model="pagesCount" type="number" min="1" max="999" class="form-control" placeholder="Calculado autom." />
        </div>
        <div class="col-12">
          <label class="form-label">Título del capítulo</label>
          <input v-model="chapterTitle" type="text" class="form-control" placeholder="Por defecto: Capitulo {número}" />
        </div>
      </div>

      <div class="preview">
        <h6 class="mb-2">Previsualización de JSON</h6>
        <pre class="json-preview">{{ JSON.stringify(chapterPayload, null, 2) }}</pre>
        <div v-if="buildImageUrls().length" class="small text-muted">Primera URL: {{ buildImageUrls()[0] }}</div>
      </div>

      <div>
        <button :disabled="uploading" class="btn btn-primary me-2">
          <span v-if="uploading">{{ uploadMode === 'url' ? 'Iniciando...' : 'Subiendo...' }} {{ uploadMode === 'manual' ? uploadProgress + '%' : '' }}</span>
          <span v-else>{{ uploadMode === 'url' ? 'Iniciar Importación' : 'Subir capítulo' }}</span>
        </button>
        <div v-if="uploading" class="progress mt-2" style="height: 5px;">
          <div class="progress-bar" role="progressbar" :style="{ width: uploadProgress + '%' }"></div>
        </div>
        <button type="button" :disabled="uploading || !selectedChapterId" class="btn btn-outline-success" @click="updateChapter">
          <span v-if="uploading">Guardando...</span><span v-else>Guardar cambios en capítulo</span>
        </button>
      </div>
    </form>
    <div class="container py-3">
      <hr />
      <h5 class="mb-2">Editar capítulo existente</h5>
      <p class="text-muted">Selecciona un capítulo del manga elegido para cargar y editar sus datos.</p>
      <div class="row g-2 align-items-end">
        <div class="col-md-6">
          <label class="form-label">Capítulo</label>
          <select v-model="selectedChapterId" class="form-select" @change="loadSelectedChapter">
            <option value="" disabled>Selecciona un capítulo</option>
            <option v-for="c in chapters" :key="c.id" :value="c.id">
              #{{ c.id }} · N° {{ c.capitulo_numero }} · {{ c.titulo || 'Sin título' }}
            </option>
          </select>
          <div v-if="loadingChapters" class="small text-muted">Cargando capítulos...</div>
        </div>
        <div class="col-md-6">
          <button class="btn btn-outline-secondary" type="button" @click="loadSelectedChapter" :disabled="!selectedChapterId">Cargar capítulo</button>
        </div>
      </div>
      <div v-if="existing" class="mt-3">
        <div class="alert alert-info py-2">
          Editando capítulo #{{ existing.id }} · Manga {{ existing.manga }} · N° {{ existing.capitulo_numero }}
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.v-stack { display:flex; flex-direction:column; }
.gap-3 { gap:1rem; }
.json-preview { background: #0f1b26; color: #cfe3ff; padding: .75rem; border-radius: 6px; max-height: 220px; overflow: auto; }
/* Improve readability in dark mode */
.upload-chapter-view { color: var(--ztmo-text); }
.upload-chapter-view .text-muted { color: var(--ztmo-text); opacity: 0.75; }
.upload-chapter-view .form-label { color: var(--ztmo-text); }
.upload-chapter-view .alert-info { background: rgba(41, 87, 186, 0.15); color: var(--ztmo-text); border-color: rgba(41, 87, 186, 0.35); }
</style>
