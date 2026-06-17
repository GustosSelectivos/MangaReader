<template>
  <div class="library-view">
    <div class="layout">

      <!-- Top: Search + Filters in two columns -->
      <div class="top-filters">
        <div class="filters-col">
          <form @submit.prevent="applySearch" class="search-bar">
            <input
              v-model.trim="search"
              @keydown.enter.prevent="applySearch"
              type="text"
              placeholder="Buscar..."
              class="search-input"
            />
            <button type="submit" class="btn primary search-btn">Buscar</button>
          </form>
          <div class="order-row">
            <label class="order-label">Ordenar por:</label>
            <select v-model="orderItem" class="order-select">
              <option value="likes_count">Me gusta</option>
              <option value="alphabetically">Alfabético</option>
              <option value="score">Puntuación</option>
              <option value="creation">Creación</option>
              <option value="release_date">Estreno</option>
              <option value="num_chapters">Capítulos</option>
            </select>
            <select v-model="orderDir" class="order-select small">
              <option value="asc">ASC</option>
              <option value="desc">DESC</option>
            </select>
          </div>

          <section class="filter-group" :class="{ open: openSection==='basic' }">
            <header @click="toggleSection('basic')"><span>Filtros Básicos</span><i></i></header>
            <div class="content">
              <div class="field">
                <label>Tipo</label>
                <select v-model="type">
                  <option value="">Ver todo</option>
                  <option value="manga">Manga</option>
                  <option value="manhwa">Manhwa</option>
                  <option value="manhua">Manhua</option>
                  <option value="novel">Novela</option>
                  <option value="one_shot">One shot</option>
                  <option value="doujinshi">Doujinshi</option>
                  <option value="comic">Comic</option>
                </select>
              </div>
              <div class="field">
                <label>Demografía</label>
                <select v-model="demography">
                  <option value="">Ver todo</option>
                  <option value="Seinen">Seinen</option>
                  <option value="Shoujo">Shoujo</option>
                  <option value="Shounen">Shounen</option>
                  <option value="Josei">Josei</option>
                  <option value="Kodomo">Kodomo</option>
                </select>
              </div>
              <div v-if="showStatus" class="field">
                <label>Estado</label>
                <select v-model="status">
                  <option value="">Ver todo</option>
                  <option value="Publicándose">Publicándose</option>
                  <option value="Finalizado">Finalizado</option>
                  <option value="Cancelado">Cancelado</option>
                  <option value="Pausado">Pausado</option>
                </select>
              </div>
            </div>
          </section>
        </div>

        <div class="filters-col">
          <section class="filter-group" :class="{ open: openSection==='genres' }">
            <header @click="toggleSection('genres')"><span>Géneros (máx {{ genreLimit }})</span><i></i></header>
            <div class="content genres">
              <div v-for="g in genres" :key="g.id" class="checkbox">
                <label>
                  <input type="checkbox" :value="g.id" v-model="includeGenres" @change="enforceGenreLimit" /> {{ g.name }}
                </label>
              </div>
            </div>
          </section>

          <section class="filter-group" :class="{ open: openSection==='exclude' }">
            <header @click="toggleSection('exclude')"><span>Excluir Géneros</span><i></i></header>
            <div class="content genres">
              <div v-for="g in genres" :key="'ex-'+g.id" class="checkbox">
                <label>
                  <input type="checkbox" :value="g.id" v-model="excludeGenres" /> {{ g.name }}
                </label>
              </div>
            </div>
          </section>

          <div style="margin-top:12px;">
            <button class="btn apply" @click="reload">Aplicar filtros</button>
          </div>
        </div>
      </div>

      <!-- Results -->
      <section class="results">
        <div v-if="loading && !mangas.length" class="loading-container">
          <img src="/assets/load.gif" alt="Cargando..." class="loading-icon" />
          <p class="text-muted">Cargando biblioteca...</p>
        </div>

        <div v-else-if="error && !mangas.length" class="empty-container">
          <div class="text-center py-5">
            <h4 class="mb-2">Ocurrió un error</h4>
            <p class="text-muted">No pudimos cargar los mangas. Intenta nuevamente.</p>
          </div>
        </div>

        <div v-else-if="!mangas.length && !loading" class="empty-container">
          <div class="text-center py-5">
            <h3 class="mb-2">Sin resultados</h3>
            <p class="text-muted">No encontramos nada con esos filtros.</p>
          </div>
        </div>

        <div v-else-if="!ready" class="empty-container">
          <div class="text-center py-5">
            <p class="text-muted">Usa los filtros o el buscador para encontrar mangas.</p>
          </div>
        </div>

        <div v-else class="cards-grid">
          <MangaCard
            v-for="(m, i) in mangas"
            :key="m.id"
            :item="m"
            :index="i"
            :showEroticLabel="isAuthenticated"
          />
        </div>

        <div class="pagination-row" v-if="mangas.length">
          <button v-if="!loadAll && showLoadMore" class="btn" @click="loadMore">Cargar más</button>
          <button v-if="!loadAll" class="btn" @click="activateLoadAll">Cargar todas</button>
          <div v-if="loadAll" class="page-info">Cargadas todas ({{ mangas.length }})</div>
          <div class="page-info" v-if="mangas.length">Página {{ page }} • Mostrando {{ mangas.length }}</div>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/features/Auth/stores/authStore'
import MangaCard from '@/features/Catalog/components/MangaCard.vue'
import { listMangas } from '@/services/mangaService'

// ── Auth ─────────────────────────────────────────────────────────────────────
const auth = useAuthStore()
const isAuthenticated = computed(() => auth.isAuthenticated)

// ── Router ────────────────────────────────────────────────────────────────────
const route = useRoute()
const router = useRouter()

// ── State ─────────────────────────────────────────────────────────────────────
const mangas   = ref([])
const loading  = ref(false)
const error    = ref(null)

// ── Search & ordering ─────────────────────────────────────────────────────────
const search   = ref(route.query.title ? String(route.query.title) : '')
const orderItem = ref('likes_count')
const orderDir  = ref('desc')

// ── Basic filters ─────────────────────────────────────────────────────────────
const type       = ref('')
const demography = ref('')
const status     = ref('')
const amateur    = ref('')
const erotic     = ref('')

// ── Genres ────────────────────────────────────────────────────────────────────
const genreLimit    = 5
const includeGenres = ref([])
const excludeGenres = ref([])
const genres = ref([
  { id: 1,  name: 'Acción' },       { id: 2,  name: 'Aventura' },
  { id: 3,  name: 'Comedia' },      { id: 4,  name: 'Drama' },
  { id: 5,  name: 'Slice of Life' },{ id: 6,  name: 'Ecchi' },
  { id: 7,  name: 'Fantasia' },     { id: 8,  name: 'Magia' },
  { id: 9,  name: 'Sobrenatural' }, { id: 10, name: 'Horror' },
  { id: 11, name: 'Misterio' },     { id: 12, name: 'Psicológico' },
  { id: 13, name: 'Romance' },      { id: 14, name: 'Sci-Fi' },
  { id: 15, name: 'Thriller' },     { id: 16, name: 'Deporte' },
  { id: 17, name: 'Girls Love' },   { id: 18, name: 'Boys Love' },
  { id: 19, name: 'Harem' },        { id: 20, name: 'Mecha' }
])

function enforceGenreLimit() {
  if (includeGenres.value.length > genreLimit) includeGenres.value.pop()
}

// ── UI: collapsible filter sections ──────────────────────────────────────────
const openSection = ref('')
const toggleSection = key => { openSection.value = openSection.value === key ? '' : key }
const showStatus = computed(() => type.value && type.value !== 'one_shot')

// ── Pagination ────────────────────────────────────────────────────────────────
const page           = ref(1)
const pageSize       = ref(20)
const lastFetchCount = ref(0)
const loadAll        = ref(false)
const showLoadMore   = computed(() => lastFetchCount.value === pageSize.value)

// ── API params ────────────────────────────────────────────────────────────────
const params = computed(() => ({
  title:           search.value || undefined,
  order_item:      orderItem.value,
  order_dir:       orderDir.value,
  type:            type.value || undefined,
  demography:      demography.value || undefined,
  status:          status.value || undefined,
  amateur:         amateur.value || undefined,
  erotic:          !isAuthenticated.value ? 'false' : (erotic.value || undefined),
  genders:         includeGenres.value.length ? includeGenres.value.join(',') : undefined,
  exclude_genders: excludeGenres.value.length ? excludeGenres.value.join(',') : undefined,
  page:            page.value,
  page_size:       pageSize.value
}))

// ── Normalize: usa lo que el serializer ya devuelve, sin requests extra ───────
function normalizeItem(raw) {
  const id    = raw.id || raw.slug || raw.uuid || Math.random().toString(36).slice(2)
  const title = raw.title || raw.titulo || raw.name || raw.manga_title || `Item ${id}`

  // La API ya devuelve cover_url. Si no viene, mostramos string vacío —
  // MangaCard mostrará el fallback del navegador.
  const cover = raw.cover_url || raw.cover || raw.url_absoluta || ''

  // Demografía: preferir el campo _display que ya viene resuelto del serializer
  let dem = raw.demografia_display || raw.demography || raw.demografia || ''
  if (Array.isArray(dem)) dem = dem.join(' ')
  if (dem && typeof dem === 'object') dem = dem.descripcion || dem.name || ''
  dem = String(dem || '')

  return {
    id,
    title,
    slug:      raw.slug,
    cover,
    displayCover: cover,
    type:      raw.type || raw.book_type || raw.tipo_serie || 'manga',
    demography: dem,
    dem_color:  raw.dem_color || '',
    erotic:    raw.erotico ?? raw.erotic ?? false,
    tags:      raw.tags || []
  }
}

// ── Fetch ─────────────────────────────────────────────────────────────────────
async function fetchData() {
  if (loadAll.value) return fetchAllPages()
  loading.value = true
  error.value   = null
  try {
    const data = await listMangas(params.value)
    const items = Array.isArray(data) ? data.map(normalizeItem) : []
    lastFetchCount.value = items.length
    mangas.value = page.value > 1 ? mangas.value.concat(items) : items
  } catch (e) {
    console.error('Library fetch error', e)
    error.value = e
    if (!mangas.value.length) mangas.value = []
  } finally {
    loading.value = false
  }
}

async function fetchAllPages() {
  loading.value = true
  error.value   = null
  try {
    mangas.value = []
    const accumulated = []
    let currentPage   = 1
    const maxPages    = 200
    while (currentPage <= maxPages) {
      const chunk = await listMangas({ ...params.value, page: currentPage })
      if (!Array.isArray(chunk) || !chunk.length) break
      accumulated.push(...chunk.map(normalizeItem))
      if (chunk.length < pageSize.value) break
      currentPage++
    }
    mangas.value         = accumulated
    lastFetchCount.value = accumulated.length
    page.value           = currentPage
  } catch (e) {
    console.error('Library fetch all error', e)
    error.value = e
  } finally {
    loading.value = false
  }
}

function activateLoadAll() {
  loadAll.value = true
  page.value    = 1
  fetchAllPages()
}

function loadMore() {
  if (loading.value) return
  page.value++
  fetchData()
}

// ── Actions ───────────────────────────────────────────────────────────────────
function reload() {
  ready.value = true
  page.value  = 1
  fetchData()
}

function applySearch() {
  ready.value = true
  page.value  = 1
  router.push({ query: { ...route.query, title: search.value || undefined } })
  fetchData()
}

// ── Watchers ──────────────────────────────────────────────────────────────────
// `ready` evita que el watcher de params dispare una búsqueda automática
// al entrar a la página. El usuario debe pulsar Buscar o Aplicar filtros.
const ready = ref(false)

watch(() => route.query.title, val => {
  const newVal = val || ''
  if (newVal !== search.value) {
    search.value = val || ''
    ready.value  = true
    fetchData()
  }
})

let debounceTimer = null
watch(params, () => {
  if (!ready.value) return   // ignorar cambios antes del primer fetch explícito
  clearTimeout(debounceTimer)
  debounceTimer = setTimeout(() => {
    if (page.value !== 1) page.value = 1
    fetchData()
  }, 300)
}, { deep: true })

watch(isAuthenticated, val => {
  if (!val && ready.value) {
    erotic.value = ''
    page.value   = 1
    fetchData()
  }
})

// ── Init ──────────────────────────────────────────────────────────────────────
// Solo búsqueda automática si viene un ?title= desde la navbar
onMounted(() => {
  if (route.query.title) {
    search.value = String(route.query.title)
    ready.value  = true
    fetchData()
  }
})
</script>

<style scoped>
/* ── Layout ────────────────────────────────────────────────────────────────── */
.library-view { width:100%; }
.layout {
  display: flex;
  flex-direction: column;
  gap: 20px;
  width: 100%;
  max-width: 1600px;
  margin: 0 auto;
  padding: 12px 20px;
  box-sizing: border-box;
}

/* Top filters: two-column on desktop */
.top-filters {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 18px;
}
@media (max-width: 720px) {
  .top-filters { grid-template-columns: 1fr; }
  .layout { padding: 8px 12px; }
}

.filters-col { display:flex; flex-direction:column; gap:12px; min-width:0; }

/* ── Search bar ─────────────────────────────────────────────────────────────── */
.search-bar { display:flex; gap:8px; }
.search-input {
  flex: 1;
  min-width: 0;           /* evita desbordamiento en flex */
  padding: 8px 10px;
  background: var(--surface-1,#1e1e1e);
  border: 1px solid var(--border-color,#333);
  color: var(--text-primary,#eaeaea);
  border-radius: 4px;
  font-size: 14px;
}
.search-input:focus { outline:2px solid var(--accent,#3d6bff); }

/* ── Buttons ─────────────────────────────────────────────────────────────────── */
.btn {
  cursor: pointer; border: none;
  padding: 8px 14px;
  font-size: 14px;
  border-radius: 4px;
  transition: .15s;
  white-space: nowrap;
  background: var(--surface-2,#2a2a2a);
  color: var(--text-primary,#eaeaea);
}
.btn.primary { background:var(--accent,#3d6bff); color:#fff; height:38px; padding:0 14px; }
.btn.apply   { background:var(--accent,#3d6bff); color:#fff; width:100%; }
.btn.primary:hover, .btn.apply:hover { filter:brightness(1.15); }
.btn:hover { filter:brightness(1.1); }

/* ── Order row ───────────────────────────────────────────────────────────────── */
.order-row {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}
.order-label { font-size:13px; opacity:.85; white-space:nowrap; }
.order-select {
  padding: 6px 8px;
  height: 38px;
  background: var(--surface-1,#1e1e1e);
  border: 1px solid var(--border-color,#333);
  color: var(--text-primary,#eaeaea);
  border-radius: 4px;
  flex: 1;
  min-width: 100px;
}
.order-select.small { flex: 0 0 80px; min-width:80px; }
@media (max-width: 400px) {
  .order-select { font-size:13px; }
}

/* ── Filter accordion ─────────────────────────────────────────────────────────── */
.filter-group {
  border: 1px solid var(--border-color,#333);
  border-radius: 6px;
  background: var(--surface-1,#181818);
  overflow: hidden;
}
.filter-group header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 12px;
  cursor: pointer;
  font-weight: 600;
  font-size: 14px;
  background: var(--surface-2,#222);
  user-select: none;
}
.filter-group header i { width:16px; height:16px; position:relative; flex-shrink:0; }
.filter-group header i:before {
  content:''; position:absolute; top:4px; left:4px;
  width:8px; height:8px;
  border:2px solid var(--text-primary,#eaeaea);
  border-top:none; border-left:none;
  transform:rotate(45deg); transition:.25s;
}
.filter-group.open header i:before { transform:rotate(225deg); top:6px; }
.filter-group .content { display:none; padding:10px 12px 14px; overflow:auto; }
.filter-group.open .content { display:block; }
.filter-group .field { display:flex; flex-direction:column; gap:4px; margin-bottom:10px; }
.filter-group .field label { font-size:12px; opacity:.8; }
.filter-group select {
  padding:6px 8px; height:36px;
  background:var(--surface-2,#222);
  border:1px solid var(--border-color,#333);
  color:var(--text-primary,#eaeaea);
  border-radius:4px;
  width:100%;
}
.genres { display:grid; grid-template-columns:repeat(auto-fill,minmax(110px,1fr)); gap:6px; }
.checkbox { font-size:11px; display:flex; align-items:center; }
.checkbox input { margin-right:4px; flex-shrink:0; }

/* ── Results ────────────────────────────────────────────────────────────────── */
.results { min-height: 300px; }
.loading-container {
  display: flex; flex-direction:column;
  align-items:center; justify-content:center;
  padding: 40px 0;
}
.loading-icon { width:48px; height:48px; margin-bottom:12px; }
.empty-container { padding:40px 0; text-align:center; opacity:.8; }
.library-view .text-muted { color:var(--ztmo-text); opacity:.75; }

/* ── Card grid ───────────────────────────────────────────────────────────────── */
.cards-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
  gap: 14px;
}
@media (min-width:1600px) { .cards-grid { grid-template-columns:repeat(auto-fill,minmax(220px,1fr)); } }
@media (max-width:900px)  { .cards-grid { grid-template-columns:repeat(auto-fill,minmax(140px,1fr)); gap:10px; } }
@media (max-width:420px)  { .cards-grid { grid-template-columns:repeat(2,1fr); gap:6px; } }

/* ── Pagination ──────────────────────────────────────────────────────────────── */
.pagination-row {
  display: flex;
  align-items: center;
  justify-content: flex-start;
  gap: 10px;
  margin-top: 14px;
  flex-wrap: wrap;
}
.page-info { opacity:.85; font-size:13px; }

/* ── Scrollbar ───────────────────────────────────────────────────────────────── */
.filter-group .content::-webkit-scrollbar { width:6px; }
.filter-group .content::-webkit-scrollbar-track { background:transparent; }
.filter-group .content::-webkit-scrollbar-thumb { background:#444; border-radius:4px; }

/* ── Light theme ─────────────────────────────────────────────────────────────── */
.theme-light .search-input,
.theme-light .order-select,
.theme-light .filter-group select { background:#ffffff; border-color:#d0d0d0; color:#111; }
.theme-light .filter-group { background:#ffffff; border-color:#d5d5d5; }
.theme-light .filter-group header { background:#f3f3f3; color:#111; }
.theme-light .order-label { color:#222; }
.theme-light .checkbox { color:#222; }
.theme-light .btn.primary, .theme-light .btn.apply { background:#2563eb; }
</style>
