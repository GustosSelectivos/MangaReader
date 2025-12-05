<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import api from '@/services/api'

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

async function submit() {
  error.value = ''
  message.value = ''
  const payload = chapterPayload.value
  if (!payload.manga || !payload.capitulo_numero || !normalizedPagesCount.value || !seriesCode.value) {
    error.value = 'Completa Manga, Código de serie, Número y Cantidad de páginas.'
    return
  }
  if (!payload.pages || !Array.isArray(payload.pages.images) || !payload.pages.images.length) {
    error.value = 'No se pudieron generar las URLs de imágenes. Revisa el código, número y páginas.'
    return
  }
  uploading.value = true
  try {
    // Envía JSON con `images` y metadatos del capítulo
    // Ajusta endpoint real cuando exista en el backend
    const { createChapter } = await import('@/services/chapterService')
    await createChapter(payload)
    message.value = 'Capítulo creado y subido correctamente.'
    // Limpia el formulario
    chapterNumber.value = ''
    chapterTitle.value = ''
    volume.value = ''
    pagesCount.value = ''
  } catch (e) {
    error.value = e.message || 'Error al subir capítulo'
  } finally {
    uploading.value = false
  }
}

async function updateChapter() {
  error.value = ''
  message.value = ''
  if (!selectedChapterId.value) {
    error.value = 'Selecciona un capítulo existente para editar.'
    return
  }
  const payload = chapterPayload.value
  if (!payload.manga || !payload.capitulo_numero || !normalizedPagesCount.value || !seriesCode.value) {
    error.value = 'Completa Manga, Código de serie, Número y Cantidad de páginas.'
    return
  }
  if (!payload.pages || !Array.isArray(payload.pages.images) || !payload.pages.images.length) {
    error.value = 'No se pudieron generar las URLs de imágenes. Revisa el código, número y páginas.'
    return
  }
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
    <div v-if="message" class="alert alert-success py-2">{{ message }}</div>
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
        <div class="col-md-4">
          <label class="form-label">Cantidad de páginas</label>
          <input v-model="pagesCount" type="number" min="1" max="999" class="form-control" placeholder="Ej: 90" />
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
          <span v-if="uploading">Subiendo...</span><span v-else>Subir capítulo</span>
        </button>
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
