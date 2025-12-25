<script setup>
import { ref, onMounted, watch, computed } from 'vue'
import { useAuthStore } from '@/stores/auth'
import api from '@/services/api'
import cache from '@/services/cache'
import { getMainCoverCached, getMainCoversBatch, getMainCoversParallel } from '@/services/coverService'
import HomeBanner from '@/components/HomeBanner.vue'
import MostViewedCarousel from '@/components/MostViewedCarousel.vue'

const populars = ref([])
const trending = ref([])
const displayedTrending = ref([])
const latest = ref([])
const mostViewed = ref([])
const loading = ref(true)
const error = ref(null)
const popularTab = ref('all')
const pendingTab = ref('pending')
const trendingTab = ref('all')
const trendingFilter = ref('all') // control used now via tabs
// Cache for fast tab switching (client-side filtered lists)
const trendingCache = ref({ all: [], shonen: [], seinen: [], erotico: [] })
// Avoid flicker while switching tabs and guard late API responses
const switching = ref(false)
let trendingFilterReqId = 0
const demografiaIds = ref({ shonen: null, seinen: null, erotico: null })
// Mapa de demografías para resolver descripción/color sin esperas
const demografiasMap = new Map()
let demografiasLoaded = false

// --- Auth state (Pinia) para control de acceso ---
const auth = useAuthStore()
const isAuthenticated = computed(() => auth.isAuthenticated)
const isSuperuser = ref(false)

// Reaccionar a cambios de autenticación (logout/login)
// Al desloguearse, ocultar sección erótico y limpiar su caché
watch(isAuthenticated, (val) => {
  if (!val) {
    trendingCache.value.erotico = []
    if (popularTab.value === 'erotico') setPopularTab('all')
    trendingFilter.value = 'all'
    displayedTrending.value = getFilteredByTab('all')
  }
})


function setPopularTab(v) {
  popularTab.value = v
  trendingFilter.value = (v === 'all') ? 'all' : v
  
  // If cache is empty for this tab, try to fetch it now (if not already invoked)
  if ((!trendingCache.value[v] || !trendingCache.value[v].length) && v !== 'all') {
    fetchSpecificTab(v)
  }

  // Instant switch if cache exists, otherwise Vue will react when fetchSpecificTab updates cache
  if (trendingCache.value[v] && trendingCache.value[v].length) {
    // If it's a proxy from existing data, use it
     displayedTrending.value = trendingCache.value[v]
  } else {
    // Show spinner or empty while loading? Or keep current?
    // For now we keep current strictly to avoid flicker, or empty array
    // handled by reactivity on trendingCache
    displayedTrending.value = [] 
  }
}
function setPendingTab(v) { pendingTab.value = v }
function setTrendingTab(v) { trendingTab.value = v }
function setTrendingFilter(e) { trendingFilter.value = e.target ? e.target.value : e }

// Try a list of API endpoints (relative). No mocks or local fallbacks.
const apiCandidates = [
  'manga/mangas/',
]

function normalizeData(raw) {
  if (Array.isArray(raw)) return raw;
  if (raw && typeof raw === 'object') {
    for (const key of ['results', 'mangas', 'data', 'items']) {
      if (Array.isArray(raw[key])) return raw[key];
    }
    // Object-of-objects fallback
    const collected = Object.values(raw).filter(v => v && typeof v === 'object' && (('title' in v) || ('name' in v)));
    if (collected.length) {
      return collected.map(v => ({ ...v, title: v.title || v.name }));
    }
  }
  return [];
}

async function processItems(items) {
  if (!items || !items.length) return []
  
  // Ensure demographies are loaded for resolution
  await preloadDemografias()

  // Process items in parallel (lightweight)
  return items.map(it => {
    const copy = { ...it }
    
    // Normalize basic fields
    copy.title = copy.title || copy.titulo || ''
    
    // Cover logic: Backend now sends 'cover_url' via optimized serializer
    // We Map this to 'cover' and 'displayCover' for the template
    let c = copy.cover_url || copy.cover || copy.url_absoluta || ''
    if (c && typeof c === 'string' && !c.startsWith('http')) {
        // If relative, assume keys not needed if backend is doing its job, 
        // but just in case keeping it simple.
    }
    copy.cover = c
    copy.displayCover = c // No more local probing
    
    // Erotic flag
    if (copy.erotico === true || copy.erotico === false) {
      copy.erotic = copy.erotico
    }
    
    // Demography resolution
    let dem = copy.demografia_display || copy.demography || copy.demografia || ''
    // If numeric ID, resolve from local map
    if (typeof dem === 'number' || (typeof dem === 'string' && /^\d+$/.test(dem))) {
       const resolved = demografiasMap.get(Number(dem))
       if (resolved) {
         dem = resolved.descripcion
         copy.dem_color = copy.dem_color || resolved.color
       }
    } else if (typeof dem === 'object') {
       dem = dem.descripcion || dem.name || ''
    }
    copy.demography = String(dem || '')
    
    // Fallback color
    if (!copy.dem_color && demografiasMap.size) {
        // Try to match by name if ID failed
        for (const [, val] of demografiasMap) {
            if (val.descripcion === dem) {
                copy.dem_color = val.color
                break
            }
        }
    }

    return copy
  })
}

async function tryApis() {
  for (const ep of apiCandidates) {
    try {
      const key = cache.keyFrom(ep)
      const cached = cache.get(key)
      if (cached) return cached
      const res = await api.get(ep)
      if (res && res.data) return res.data
    } catch (e) {
      // ignore and try next
    }
  }
  return null
}


 
 async function loadData() {
  try {
    // Parallel fetching for initial tabs
    // We only fetch small chunks (limit=10/12) instead of 100+ items
    const [rPopular, rTrending, rLatest, rMostViewed] = await Promise.all([
       api.get('manga/mangas/', { params: { limit: 12, ordering: '-vistas' } }), // Popular (All)
       api.get('manga/mangas/', { params: { limit: 8, ordering: '-creado_en' } }), // Trending (mock logic, using new)
       api.get('manga/mangas/', { params: { limit: 8, ordering: '-actualizado_en' } }), // Latest
       api.get('manga/mangas/', { params: { limit: 30, ordering: '-vistas' } })  // Most Viewed Sidebar (fetched more to allow filtering)
    ])

    // Process data to map covers, demography, etc.
    // Process data to map covers, demography, etc.
    populars.value = await processItems(normalizeData(rPopular?.data))
    trending.value = await processItems(normalizeData(rTrending?.data))
    latest.value = await processItems(normalizeData(rLatest?.data))
    mostViewed.value = await processItems(normalizeData(rMostViewed?.data))

    // Initialize displayed lists
    displayedTrending.value = trending.value
    
    // Cache "All" tab
    trendingCache.value.all = populars.value

    // Pre-fetch other tabs in background to make switching instant, but lazily
    fetchSpecificTab('shonen')
    fetchSpecificTab('seinen')
    if (isAuthenticated.value) fetchSpecificTab('erotico')

  } catch (e) {
    console.error("Error loading home data", e)
    error.value = "Error cargando contenido."
  } finally {
    loading.value = false
  }
}

async function fetchSpecificTab(type) {
  if (trendingCache.value[type] && trendingCache.value[type].length) return
  try {
    let params = { limit: 12, ordering: '-vistas' }
    if (type === 'erotico') params.erotico = 'true'
    else if (type === 'shonen') params.demografia = 'Shonen' // Adjust if backend expects ID
    else if (type === 'seinen') params.demografia = 'Seinen'

    // If backend requires ID for demography, we rely on ensureDemografiaIds
    if ((type === 'shonen' || type === 'seinen') && demografiaIds.value[type]) {
        delete params.demografia
        params.demografia = demografiaIds.value[type]
    }

    const res = await api.get('manga/mangas/', { params })
    const data = await processItems(normalizeData(res?.data))
    trendingCache.value[type] = data
  } catch (e) {}
}

async function fetchDemografiaIds() {
  try {
    const p = { page_size: 100 }
    const k = cache.keyFrom('mantenedor/demografias/', p)
    const c = cache.get(k)
    const r = c ? { data: c } : await api.get('mantenedor/demografias/', { params: p })
    const list = Array.isArray(r.data) ? r.data : (r.data?.results || [])
    cache.set(k, list, 24 * 60 * 60 * 1000)
    for (const d of list) {
      const desc = (d.descripcion || d.name || d.title || '').toLowerCase()
      if (desc.includes('shonen') || desc.includes('shounen')) demografiaIds.value.shonen = d.id
      else if (desc.includes('seinen')) demografiaIds.value.seinen = d.id
      else if (desc.includes('erot') || desc.includes('ecchi')) demografiaIds.value.erotico = d.id
    }
  } catch (e) { /* ignore */ }
}

async function ensureDemografiaIds() {
  // Asegurar que tengamos IDs antes de hacer requests filtrados
  if (!demografiaIds.value.shonen || !demografiaIds.value.seinen) {
    await fetchDemografiaIds()
  }
}

// Precargar lista completa de demografías para evitar múltiples llamadas por ítem
async function preloadDemografias() {
  if (demografiasLoaded) return
  try {
    const p = { page_size: 1000 }
    const k = cache.keyFrom('mantenedor/demografias/', p)
    const c = cache.get(k)
    const r = c ? { data: c } : await api.get('mantenedor/demografias/', { params: p })
    const list = Array.isArray(r.data) ? r.data : (r.data?.results || [])
    cache.set(k, list, 24 * 60 * 60 * 1000)
    for (const d of list) {
      const desc = d.descripcion || d.name || d.title || ''
      const color = d.color || d.dem_color || ''
      demografiasMap.set(Number(d.id), { descripcion: desc, color })
    }
    demografiasLoaded = true
  } catch (e) { /* ignore */ }
}

async function resolveDemografiaDescripcion(idOrName) {
  if (!idOrName && idOrName !== 0) return { descripcion: '', color: '' }
  // Intento por ID numérico en mapa precargado
  const mid = Number(idOrName)
  if (Number.isFinite(mid) && demografiasMap.has(mid)) return demografiasMap.get(mid)
  // Intento por clave directa
  const direct = demografiasMap.get(idOrName)
  if (direct) return { descripcion: direct.descripcion || direct.name || direct.title || '', color: direct.color || direct.dem_color || '' }
  // Intento por nombre/descripción (case-insensitive) en mapa
  if (typeof idOrName === 'string' && demografiasMap.size) {
    const needle = idOrName.trim().toLowerCase()
    for (const [, val] of demografiasMap) {
      const name = (val.descripcion || val.name || val.title || '').trim().toLowerCase()
      if (name && name === needle) {
        return { descripcion: val.descripcion || val.name || val.title || '', color: val.color || val.dem_color || '' }
      }
    }
  }
  // Fallback: petición directa por ID; si es texto, se intentará listado
  try {
    const r = await api.get(`mantenedor/demografias/${idOrName}/`)
    const d = r?.data || {}
    return { descripcion: d.descripcion || d.name || d.title || '', color: d.color || d.dem_color || '' }
  } catch (e) {}
  try {
    const rl = await api.get('mantenedor/demografias/', { params: { page_size: 1000 } })
    const list = Array.isArray(rl.data) ? rl.data : (rl.data?.results || [])
    const found = list.find(x => String(x.id) === String(idOrName) || String((x.descripcion || x.name || x.title || '')).toLowerCase() === String(idOrName).toLowerCase()) || {}
    return { descripcion: found.descripcion || found.name || found.title || '', color: found.color || found.dem_color || '' }
  } catch (e) {}
  return { descripcion: '', color: '' }
}

// El filtro de trending se resuelve en cliente usando el cache cargado
function loadTrendingFiltered() {
  const key = trendingFilter.value
  const baseAll = trendingCache.value.all.length ? trendingCache.value.all : trending.value
  if (key === 'erotico') {
    displayedTrending.value = trendingCache.value.erotico.length
      ? trendingCache.value.erotico
      : baseAll.filter(i => isErotic(i))
    return
  }
  if (key === 'shonen') {
    displayedTrending.value = trendingCache.value.shonen.length
      ? trendingCache.value.shonen
      : baseAll.filter(i => String(i.demography || '').toLowerCase().includes('shon'))
    return
  }
  if (key === 'seinen') {
    displayedTrending.value = trendingCache.value.seinen.length
      ? trendingCache.value.seinen
      : baseAll.filter(i => String(i.demography || '').toLowerCase().includes('sein'))
    return
  }
  displayedTrending.value = baseAll
}

const filteredMostViewed = computed(() => {
  if (isAuthenticated.value) return mostViewed.value
  return mostViewed.value.filter(i => !isErotic(i))
})

onMounted(async () => {
  await fetchDemografiaIds()
  await preloadDemografias()
  await loadData()
  // Forzar estado consistente tras carga inicial
  setPopularTab('all')
  // Resolver filtro actual en cliente
  loadTrendingFiltered()
  if (!displayedTrending.value || !displayedTrending.value.length) {
    const baseAll = trendingCache.value.all.length ? trendingCache.value.all : trending.value
    displayedTrending.value = baseAll
  }
})

// Watch the select filter
watch(trendingFilter, () => { loadTrendingFiltered() })

// Client-side filter helper for instant tab switches
function getFilteredByTab(tab) {
  const key = tab || 'all'
  if (key === 'erotico') {
    if (trendingCache.value.erotico.length) return trendingCache.value.erotico
    const baseAll = trendingCache.value.all.length ? trendingCache.value.all : trending.value
    return baseAll.filter(i => (i.erotico === true) || isErotic(i))
  }
  const base = trendingCache.value.all.length ? trendingCache.value.all : trending.value
  if (key === 'shonen') return base.filter(i => String(i.demography || '').toLowerCase().includes('shon'))
  if (key === 'seinen') return base.filter(i => String(i.demography || '').toLowerCase().includes('sein'))
  return base
}

// (moved into onMounted above with demografia fetch)

// Helper to map a type/demography to a color class
function typeClass(item) {
  // Normalize possible shapes: string, array, object
  let raw = item && (item.demography || item.type || item.book_type || '')
  if (Array.isArray(raw)) raw = raw.join(' ')
  if (raw && typeof raw === 'object') raw = raw.name || raw.title || JSON.stringify(raw)
  raw = String(raw || '').toLowerCase()
  if (raw.includes('manhwa')) return 'type-manhwa'
  if (raw.includes('manhua')) return 'type-manhua'
  if (raw.includes('novel') || raw.includes('novela')) return 'type-novela'
  if (raw.includes('shoujo')) return 'type-shoujo'
  if (raw.includes('josei')) return 'type-josei'
  if (raw.includes('seinen')) return 'type-seinen'
  if (raw.includes('shounen') || raw.includes('shonen')) return 'type-shounen'
  if (raw.includes('manga')) return 'type-manga'
  return 'type-default'
}

// Return a readable demography/type string for the template
function displayType(item) {
  let val = item && (item.demography || item.dem_descripcion || item.demografia_descripcion || item.demografia || item.type || '')
  // If val is a JSON string, parse it
  if (typeof val === 'string') {
    const s = val.trim()
    if (s.startsWith('{') || s.startsWith('[')) {
      try { val = JSON.parse(s) } catch (e) { /* keep original string */ }
    }
  }
  if (Array.isArray(val)) val = val.join(' ')
  if (val && typeof val === 'object') val = val.descripcion || val.description || val.name || val.title || val.label || JSON.stringify(val)
  return String(val || 'MANGA')
}

// Return origin label: Manga / Manhua / Manhwa / Novela
function originLabel(item) {
  let t = item && (item.mng_tipo_manga || item.mng_tipo_serie || item.tipo_serie || item.manga_tipo_serie || item.type || item.book_type || item.raw?.type || item.origin || '')
  if (!t && item) {
    // try tags or demography heuristics
    const tags = item.tags || item.tags_list || []
    if (Array.isArray(tags) && tags.length) {
      const joined = tags.map(x => (x.nombre || x.name || x)).join(' ').toLowerCase()
      if (joined.includes('manhwa')) t = 'manhwa'
      if (joined.includes('manhua')) t = 'manhua'
    }
  }
  if (typeof t === 'string') t = t.toLowerCase()
  // Normalize common synonyms
  const norm = String(t || '')
  if (norm.includes('comic')) return 'Comic'
  if (/one[\s_\-]?shot/.test(norm)) return 'One-shot'
  if (t && t.includes('manhwa')) return 'Manhwa'
  if (t && t.includes('manhua')) return 'Manhua'
  if (t && t.includes('novel')) return 'Novela'
  return 'Manga'
}

function isErotic(item) {
  if (!item) return false
  if (item.erotic === true) return true
  if (item.tags && Array.isArray(item.tags)) {
    const joined = item.tags.map(t => (t.nombre || t.name || t)).join(' ').toLowerCase()
    if (joined.includes('ecchi') || joined.includes('erotic') || joined.includes('erótico') || joined.includes('erotico')) return true
  }
  const dem = (String(item.demography || item.demografia || item.type || '')).toLowerCase()
  if (dem.includes('erotic') || dem.includes('erótico') || dem.includes('erotico') || dem.includes('ecchi')) return true
  return false
}

</script>

<template>
  <div class="home-view pb-5">
    <div v-if="loading" class="loading-container">
      <img src="/assets/load.gif" alt="Cargando..." class="loading-icon" />
      <p>Cargando contenido...</p>
    </div>
    <div v-else-if="!populars.length && !displayedTrending.length && !latest.length && !mostViewed.length" class="empty-container">
      <div class="text-center py-5">
        <h3 class="mb-2">No hay contenido disponible</h3>
        <p class="text-muted">Intenta recargar o verificar la conexión con el servidor.</p>
      </div>
    </div>

    <div class="home-layout" v-else>
      
      <!-- Integration of Banner -->
       <div class="col-12 mb-4" style="grid-column: 1 / -1;">
         <HomeBanner />
       </div>

      <div class="home-main">

          <!-- Populares / Tabs -->
          <div class="row">
            <div class="col">
                <nav class="nav nav-pills nav-justified mb-3" id="pills-tab" role="tablist" aria-label="Tabs populares">
                 <a href="#"
                   role="tab"
                   :aria-selected="popularTab === 'all' ? 'true' : 'false'"
                   aria-controls="pills-populars"
                   @click.prevent="setPopularTab('all')"
                   :class="['nav-item nav-link', { active: popularTab === 'all' }]">All</a>
                 <a href="#"
                   role="tab"
                   :aria-selected="popularTab === 'shonen' ? 'true' : 'false'"
                   aria-controls="pills-populars-shonen"
                   @click.prevent="setPopularTab('shonen')"
                   :class="['nav-item nav-link', { active: popularTab === 'shonen' }]">Shonen</a>
                 <a href="#"
                   role="tab"
                   :aria-selected="popularTab === 'seinen' ? 'true' : 'false'"
                   aria-controls="pills-populars-seinen"
                   @click.prevent="setPopularTab('seinen')"
                   :class="['nav-item nav-link', { active: popularTab === 'seinen' }]">Seinen</a>
                 <a v-if="isAuthenticated" href="#"
                   role="tab"
                   :aria-selected="popularTab === 'erotico' ? 'true' : 'false'"
                   aria-controls="pills-populars-erotico"
                   @click.prevent="setPopularTab('erotico')"
                   :class="['nav-item nav-link', { active: popularTab === 'erotico' }]">Erótico</a>
                </nav>

              <div class="tab-content" id="pills-tabContent" :key="popularTab">
                <div v-show="popularTab === 'all'" class="tab-pane" id="pills-populars" role="tabpanel" aria-labelledby="pills-tab">
                  <div class="cards-grid">
                    <div v-for="(item, index) in populars.filter(i => i.erotic !== true)" :key="item.id" class="card-item">
                      <a :href="`/library/manga/${item.id}`" class="card-link">
                          <div class="thumbnail book">
                          <img :src="item.displayCover || item.cover" :alt="item.title" 
                               :loading="index < 6 ? 'eager' : 'lazy'" 
                               :fetchpriority="index < 4 ? 'high' : 'auto'"
                               decoding="async" />
                          <div class="thumbnail-title top-strip"><h3 class="h6 m-0 text-truncate" :title="item.title">{{ item.title }}</h3></div>
                          <span class="book-type badge badge-manga">MANGA</span>
                          <div class="type-bubble">{{ originLabel(item) }}</div>
                          <div class="thumbnail-type-bar" :class="typeClass(item)" :style="{ '--type-bar-color': item.dem_color || undefined }">{{ displayType(item) }}</div>
                        </div>
                      </a>
                    </div>
                  </div>

                  <!-- Recommendation block moved up below popular cards -->
                  <div class="recommendation-block mt-4" v-if="populars.length">
                    <h3 class="mb-3 h5">Hoy recomendamos...</h3>
                    <div class="recommendation-inner">
                      <div class="rec-cover">
                        <a target="_blank" href="#"><img class="img-fluid" :src="populars[0] ? (populars[0].displayCover || populars[0].cover) : ''" :alt="populars[0]?.title || 'cover'" loading="eager" fetchpriority="high" /></a>
                      </div>
                      <div class="rec-info">
                        <h4 class="text-truncate mb-2">{{ populars[0] ? populars[0].title : '' }}</h4>
                        <p class="m-0 small">Resumen corto de la recomendación.</p>
                      </div>
                    </div>
                  </div>

                    <div class="row text-center mt-2">
                    <div class="col-12 col-sm-4 offset-sm-4">
                      <a class="btn btn-primary w-100" href="/populars">Ver todo</a>
                    </div>
                  </div>
                </div>

                <!-- Simple placeholders for other tabs (can be replaced by filtered lists) -->
                <div v-show="popularTab === 'shonen'" class="tab-pane" id="pills-populars-shonen" role="tabpanel" aria-labelledby="pills-tab">
                  <div class="cards-grid">
                    <!-- Usar displayedTrending para evitar que cargas tardías reemplacen el filtro -->
                    <div v-for="item in displayedTrending.filter(i => i.erotic !== true)" :key="`sh-${item.id}`" class="card-item">
                      <a :href="`/library/manga/${item.id}`" class="card-link">
                        <div class="thumbnail book">
                          <img :src="item.displayCover || item.cover" :alt="item.title" loading="lazy" decoding="async" />
                          <div class="thumbnail-title top-strip"><h3 class="h6 m-0 text-truncate" :title="item.title">{{ item.title }}</h3></div>
                          <div class="type-bubble">{{ originLabel(item) }}</div>
                          <div class="thumbnail-type-bar" :class="typeClass(item)" :style="{ '--type-bar-color': item.dem_color || undefined }">{{ displayType(item) }}</div>
                        </div>
                      </a>
                    </div>
                  </div>
                </div>
                <div v-show="popularTab === 'seinen'" class="tab-pane" id="pills-populars-seinen" role="tabpanel" aria-labelledby="pills-tab">
                  <div class="cards-grid">
                    <!-- Usar displayedTrending para evitar que cargas tardías reemplacen el filtro -->
                    <div v-for="item in displayedTrending.filter(i => i.erotic !== true)" :key="`se-${item.id}`" class="card-item">
                      <a :href="`/library/manga/${item.id}`" class="card-link">
                        <div class="thumbnail book">
                          <img :src="item.displayCover || item.cover" :alt="item.title" loading="lazy" decoding="async" />
                          <div class="thumbnail-title top-strip"><h3 class="h6 m-0 text-truncate" :title="item.title">{{ item.title }}</h3></div>
                          <div class="type-bubble">{{ originLabel(item) }}</div>
                          <div class="thumbnail-type-bar" :class="typeClass(item)" :style="{ '--type-bar-color': item.dem_color || undefined }">{{ displayType(item) }}</div>
                        </div>
                      </a>
                    </div>
                  </div>
                </div>
                <div v-if="isAuthenticated" v-show="popularTab === 'erotico'" class="tab-pane" id="pills-populars-erotico" role="tabpanel" aria-labelledby="pills-tab">
                  <div class="cards-grid">
                    <!-- Usar displayedTrending para evitar que cargas tardías reemplacen el filtro -->
                    <div v-for="item in displayedTrending.filter(i => i.erotic === true)" :key="`er-${item.id}`" class="card-item">
                      <a :href="`/library/manga/${item.id}`" class="card-link">
                        <div class="thumbnail book">
                          <img :src="item.displayCover || item.cover" :alt="item.title" loading="lazy" decoding="async" />
                          <div class="thumbnail-title top-strip"><h3 class="h6 m-0 text-truncate" :title="item.title">{{ item.title }}</h3></div>
                          <div class="type-bubble">{{ originLabel(item) }}<span class="age-18">+18</span></div>
                          <div class="thumbnail-type-bar" :class="typeClass(item)" :style="{ '--type-bar-color': item.dem_color || undefined }">{{ displayType(item) }}</div>
                        </div>
                      </a>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Trending section (shows test data from the same source) -->
          <div class="row mt-3">
            <div class="col">
              <h2 class="mt-3">Series Disponibles</h2>


              <div class="cards-grid cards-grid--trending">
                <div v-for="(item, index) in (popularTab === 'erotico' 
                    ? displayedTrending.filter(i => isErotic(i)) 
                    : (isAuthenticated ? displayedTrending : displayedTrending.filter(i => !isErotic(i))))" 
                  :key="`tr-${item.id}`" class="card-item">
                  <a :href="`/library/manga/${item.id}`" class="card-link">
                    <div class="thumbnail book">
                      <img :src="item.displayCover || item.cover" :alt="item.title" 
                           :loading="index < 6 ? 'eager' : 'lazy'" 
                           :fetchpriority="index < 4 ? 'high' : 'auto'"
                           decoding="async" />
                      <div class="thumbnail-title top-strip"><h3 class="h6 m-0 text-truncate" :title="item.title">{{ item.title }}</h3></div>
                      <div class="type-bubble">{{ originLabel(item) }}<span v-if="isAuthenticated && isErotic(item)" class="age-18">+18</span></div>
                      <div class="thumbnail-type-bar" :class="typeClass(item)" :style="{ '--type-bar-color': item.dem_color || undefined }">{{ displayType(item) }}</div>
                    </div>
                  </a>
                </div>
              </div>
            </div>
          </div>
          
           <!-- Carousel Integration Moved to Bottom -->
           <div class="row mt-5 mb-4" v-if="filteredMostViewed && filteredMostViewed.length">
             <div class="col-12">
               <h3 class="mb-3">Más vistos</h3>
               <MostViewedCarousel :items="filteredMostViewed.slice(0, 10)" />
             </div>
           </div>
      </div>
      </div>
  </div>
</template>

<style scoped>
.home-view { padding-left: 16px; padding-right: 16px; max-width:1600px; margin:0 auto; }
.home-layout { display: block; }
/* Modified layout to be single column as per request to remove sidebar section */
.home-main { min-width:0; }
.home-sidebar { min-width:0; position:sticky; top:90px; align-self:start; }

.home-view .thumbnail.book {
  aspect-ratio: 2 / 3;
  min-height: 220px;
  position: relative;
  border-radius: 6px;
  overflow: hidden;
  color: #fff;
  display: block;
}
.home-view .thumbnail.book img {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
  transition: transform 0.4s ease;
}
.thumbnail .thumbnail-title.top-strip { position:absolute; top:0; left:0; right:0; background:rgba(0,0,0,0.8); padding:4px 6px; }
.thumbnail .thumbnail-title.top-strip h3 { margin:0; font-size:14px; color:#fff; width:100%; line-height:1.15; }
.home-view .nav { flex-wrap: wrap; gap: 8px; }
.home-view .thumbnail.book { width: 100%; }
/* Adaptive cards grid */
.cards-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 14px; }
@media (min-width: 1600px) { .cards-grid { grid-template-columns: repeat(auto-fill, minmax(240px, 1fr)); } }
.card-item { list-style:none; }
.card-link { text-decoration:none; display:block; outline: none; border: none; }
.card-link:hover, .card-link:focus { outline: none; border: none; }
.book-type { position: absolute; right:8px; top:8px; background: rgba(0,0,0,0.85); padding:3px 6px; border-radius:4px; font-size:11px }
.thumbnail-type-bar { position:absolute; left:0; right:0; bottom:0; padding:4px 6px 5px; font-size:12px; font-weight:600; letter-spacing:.3px; background:linear-gradient(90deg, var(--type-bar-color, rgba(0,0,0,0.85)) 0%, rgba(0,0,0,0.6) 100%); color:#fff; }
.type-manga { --type-bar-color:#1e88e5; }
.type-manhwa { --type-bar-color:#43a047; }
.type-manhua { --type-bar-color:#c62828; }
.type-novela { --type-bar-color:#6a1b9a; }
.type-shounen { --type-bar-color:#1976d2; }
.type-seinen { --type-bar-color:#546e7a; }
.type-josei { --type-bar-color:#8e24aa; }
.type-shoujo { --type-bar-color:#ff4081; }
.type-default { --type-bar-color:#455a64; }
.pending-items .pending-item { text-align:center }
.ranked-item { display:flex; align-items:center; padding:6px 0 }
.ranked-item .position { width:36px; font-weight:700 }
.ranked-item .description { flex:1; white-space:nowrap; overflow:hidden; text-overflow:ellipsis }

@media (min-width: 1200px) {
  .home-view { padding-left: 32px; padding-right: 32px; }
  .home-view .col-12.col-lg-8.col-xl-9 { padding-left: 0; }
  
  /* Advanced Hover Effects for PC */
  /* Advanced Hover Effects for PC removed as per request */
  /* .cards-grid:hover .card-item { ... } removed */
  
  .cards-grid .card-item:hover {
      transform: scale(1.1) translateY(-5px);
      z-index: 100;
      box-shadow: 0 10px 20px rgba(0,0,0,0.5);
  }
  /* Reset transition for non-hovered state to avoid laggy feeling on mouseout */
  .cards-grid .card-item {
      transition: all 0.4s ease;
  }
}

@media (max-width: 576px) {
  .home-view .thumbnail.book { min-height: 180px; }
  .home-view .nav { justify-content: center; }
  /* Force at least 3 columns: allow very small card width */
  .cards-grid { gap:8px; grid-template-columns: repeat(3, minmax(0, 1fr)); }
  /* On mobile, trending grid shows 2 columns */
  .cards-grid.cards-grid--trending { grid-template-columns: repeat(2, 1fr); }
  .cards-grid .thumbnail.book { aspect-ratio: 9 / 14; min-height: 170px; }
  .cards-grid .thumbnail-title.top-strip h3 { font-size:12px; }
  .book-type { font-size:9px; padding:2px 4px; }
  .thumbnail-type-bar { font-size:10px; padding:3px 5px 4px; }
}

/* Extra small phones */
@media (max-width: 420px) {
  .home-view { padding-left: 10px; padding-right: 10px; }
  /* Maintain 3 columns on very narrow screens */
  .cards-grid { grid-template-columns: repeat(3, 1fr); gap:6px; }
  /* Trending grid stays at 2 columns on extra-small */
  .cards-grid.cards-grid--trending { grid-template-columns: repeat(2, 1fr); }
  .cards-grid .thumbnail.book { min-height: 160px; }
  .home-view .nav .nav-link { padding:6px 10px; font-size:13px; }
  .recommendation-inner .rec-cover img { width:90px; }
}

/* Ultra-wide screens: prevent over-dense columns */
@media (min-width: 1900px) {
  .home-view { max-width:1700px; }
  .cards-grid { grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); }
  .home-layout { grid-template-columns: 5.5fr 1.2fr; }
}

/* Recommendation block styles */
.recommendation-block { background:#0f1b26; border-radius:6px; padding:12px; }
.recommendation-inner { display:flex; gap:12px; align-items:stretch; }
.recommendation-inner .rec-cover img { border-radius:4px; width:110px; aspect-ratio:2/3; object-fit:cover; }
.recommendation-inner .rec-info { flex:1; min-width:0; }
.recommendation-inner h4 { font-size:16px; }
.type-bubble { position:absolute; left:8px; top:36px; background:rgba(0,0,0,0.6); color:#fff; padding:3px 8px; border-radius:12px; font-size:11px; font-weight:600; display:inline-flex; align-items:center; gap:6px }
.type-bubble .age-18 { color:#ff4d4f; background:transparent; padding-left:6px; font-weight:800 }

.loading-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 60vh;
  padding: 60px 20px;
}

.loading-icon {
  width: 192px;
  height: 192px;
  margin-bottom: 20px;
}

.empty-container { min-height: 40vh; display:flex; align-items:center; justify-content:center; }

/* Improve dark mode readability for muted texts */
.home-view .text-muted { color: var(--ztmo-text); opacity: 0.75; }
.home-view .form-label { color: var(--ztmo-text); }
</style>

