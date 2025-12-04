<script setup>
import { ref, onMounted, watch } from 'vue'
import api from '@/services/api'
import cache from '@/services/cache'

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

// --- Auth state for access control ---
const isAuthenticated = ref(false)
const isSuperuser = ref(false)

async function fetchAuthState() {
  // Sin endpoint /me: deducir por presencia de token (SimpleJWT)
  try {
    const storage = (typeof window !== 'undefined') ? window.localStorage : null
    const access = storage ? (storage.getItem('access') || storage.getItem('token') || storage.getItem('jwt')) : null
    // Revisar también cookies de sesión (autenticación por SessionAuth)
    let hasSession = false
    if (typeof document !== 'undefined') {
      const ck = document.cookie || ''
      hasSession = /(^|;\s)sessionid=/.test(ck) || /(^|;\s)access=/.test(ck) || /(^|;\s)jwt=/.test(ck)
    }
    isAuthenticated.value = Boolean(access || hasSession)
    // Sin endpoint de usuario, no podemos saber superuser; dejar false por defecto
    isSuperuser.value = false
  } catch (e) {
    isAuthenticated.value = false
    isSuperuser.value = false
  }
}


function setPopularTab(v) {
  popularTab.value = v
  // Direct mapping: tab key equals trendingFilter (except 'all')
  trendingFilter.value = (v === 'all') ? 'all' : v
  // Use cached client-side filtered results for instant switching (render list decoupled)
  switching.value = true
  const cached = trendingCache.value[v]
  if (Array.isArray(cached) && cached.length) {
    displayedTrending.value = cached
  } else {
    // Fallback to client-side filter over allPrepared data; keep it snappy
    displayedTrending.value = getFilteredByTab(v)
    // Populate cache for subsequent switches
    trendingCache.value[v] = displayedTrending.value
  }
  // Release switching flag next microtask to avoid overlay
  Promise.resolve().then(() => { switching.value = false })
}
function setPendingTab(v) { pendingTab.value = v }
function setTrendingTab(v) { trendingTab.value = v }
function setTrendingFilter(e) { trendingFilter.value = e.target ? e.target.value : e }

// Try a list of API endpoints (relative). If none succeed, fallback to local mock JSON.
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

async function tryApis() {
  for (const ep of apiCandidates) {
    try {
      const key = cache.keyFrom(ep)
      const cached = cache.get(key)
      if (cached) return cached
      const res = await api.get(ep, { timeout: 3000 })
      if (res && res.data) return res.data
    } catch (e) {
      // ignore and try next
    }
  }
  return null
}

async function resolveLocalCover(item) {
  // Prefer remote cover; if missing, try to resolve via API before falling back to local assets
  let remote = item.cover
  if (!remote || typeof remote !== 'string' || !remote.startsWith('http')) {
    // Try by possible id fields first
    try { console.debug('[Home] Resolviendo cover remoto para manga', item.id) } catch (e) {}
    const byId = await getCoverByIdCached(item.cover_id || item.main_cover_id || item.cover)
    if (byId) remote = byId
    else {
      const viaManga = await getMainCoverCached(item.id)
      if (viaManga) remote = viaManga
    }
  }
  if (typeof remote === 'string' && remote.startsWith('http')) {
    return remote
  }
  const webp = `/assets/covers/cover_${item.id}.webp`
  const svg = `/assets/covers/cover_${item.id}.svg`
  return await new Promise((resolve) => {
    const test = (src, okCb, failCb) => {
      const img = new Image()
      img.onload = () => okCb(src)
      img.onerror = () => failCb()
      img.src = src
    }
    test(webp, (s) => resolve(s), () => {
      test(svg, (s) => resolve(s), () => resolve(remote || svg))
    })
  })
}

// Helpers centralizados de portada
import { getCoverByIdCached, getMainCoverCached } from '@/services/coverService'

async function loadData() {
  try {
    // Fetch both erotic=false and erotic=true, but display only non-erotic initially
    let data = []
    let nonErotic = null
    let eroticOnly = null
    try {
      const rFalse = await api.get('manga/mangas/', { params: { erotico: false, page_size: 100 }, timeout: 3000 })
      nonErotic = normalizeData(rFalse?.data?.results || rFalse?.data)
    } catch (e) {
      try {
        const rFalse2 = await api.get('mangas/', { params: { erotico: false, page_size: 100 }, timeout: 3000 })
        nonErotic = normalizeData(rFalse2?.data?.results || rFalse2?.data)
      } catch (e2) {}
    }
    try {
      const rTrue = await api.get('manga/mangas/', { params: { erotico: true, page_size: 100 }, timeout: 3000 })
      eroticOnly = normalizeData(rTrue?.data?.results || rTrue?.data)
    } catch (e) {
      try {
        const rTrue2 = await api.get('mangas/', { params: { erotico: true, page_size: 100 }, timeout: 3000 })
        eroticOnly = normalizeData(rTrue2?.data?.results || rTrue2?.data)
      } catch (e2) {}
    }
    if (Array.isArray(nonErotic) || Array.isArray(eroticOnly)) {
      data = normalizeData([...(nonErotic || []), ...(eroticOnly || [])])
    } else {
      let fallbackData = await tryApis()
      data = normalizeData(fallbackData)
    }
    if (!data || !data.length) {
      // Prefer the universal mangas mock, fallback to universal chapters if present
      let mockRaw = null
      try {
        const r = await api.get('/mock/mangas_universal.json')
        mockRaw = r?.data || null
      } catch (e) {}
      if (!mockRaw) {
        try {
          const r2 = await api.get('/mock/chapters_universal.json')
          mockRaw = r2?.data || null
        } catch (e2) {}
      }
      if (!mockRaw) throw new Error('No mock data available')
      // If mockRaw is chapters list, map to simple manga-like objects
      const mapped = (Array.isArray(mockRaw) && mockRaw.length && mockRaw[0].pages) ? mockRaw.map(c => ({ id: c.id, title: c.manga_title || c.title || c.number, cover: c.cover })) : mockRaw
      data = normalizeData(mapped)
    }


    async function resolveDemography(numId) {
      if (!numId && numId !== 0) return { descripcion: '', color: '' }
      // Try detail endpoint first
      try {
        const k = cache.keyFrom(`mantenedor/demografias/${numId}/`)
        const c = cache.get(k)
        const r = c ? { data: c } : await api.get(`mantenedor/demografias/${numId}/`)
        const d = r?.data || {}
        return { descripcion: d.descripcion || d.name || d.title || '', color: d.color || d.dem_color || '' }
        cache.set(k, d, 24 * 60 * 60 * 1000)
      } catch (e) {}
      // Fallback: list and find
      try {
        const p = { page_size: 1000 }
        const k2 = cache.keyFrom('mantenedor/demografias/', p)
        const c2 = cache.get(k2)
        const rl = c2 ? { data: c2 } : await api.get('mantenedor/demografias/', { params: p })
        const list = Array.isArray(rl.data) ? rl.data : (rl.data?.results || [])
        const found = list.find(x => String(x.id) === String(numId)) || {}
        return { descripcion: found.descripcion || found.name || found.title || '', color: found.color || found.dem_color || '' }
        cache.set(k2, list, 24 * 60 * 60 * 1000)
      } catch (e) {}
      return { descripcion: '', color: '' }
    }

    const prepared = await Promise.all(data.map(async (it) => {
      const copy = { ...it }
      // Normalize title from backend key 'titulo'
      copy.title = copy.title || copy.titulo || ''
      // Prefer backend-provided cover_url when available
      copy.cover = copy.cover || copy.cover_url || copy.cover_image || copy.url_absoluta || copy.url_imagen || copy.portada || ''
      // Evitar usar assets locales como /assets/covers/cover_#.svg para forzar remoto
      if (typeof copy.cover === 'string' && (copy.cover.endsWith('.svg') || copy.cover.startsWith('/assets/covers/'))) {
        copy.cover = ''
      }
      // If no remote cover present, try fetching by cover id or via covers API
      if (!copy.cover || typeof copy.cover !== 'string' || !copy.cover.startsWith('http')) {
        // Resolve per item, in paralelo pero deduplicado vía caches
        const byId = await getCoverByIdCached(copy.cover_id || copy.main_cover_id || copy.cover)
        if (byId) copy.cover = byId
        else {
          const c = await getMainCoverCached(copy.id)
          if (c) copy.cover = c
        }
      }
      // Prefer remote cover for display when available
      copy.displayCover = await resolveLocalCover(copy)
      // If still a local asset (e.g., SVG), force remote main cover
      if (typeof copy.displayCover === 'string' && copy.displayCover.startsWith('/assets/covers/')) {
        const forced = await getMainCoverCached(copy.id)
        if (forced) copy.displayCover = forced
      }
      if (!copy.score) copy.score = copy.rating || copy.puntaje || 'N/A'
      // Map backend erotico -> frontend erotic
      if (copy.erotico === true || copy.erotico === false) {
        copy.erotic = copy.erotico
      }
      // Normalize demography to a readable string (prefer server-resolved display)
      let dem = copy.demografia_display || copy.demography || copy.demografia || copy.type || ''
      if (Array.isArray(dem)) dem = dem.join(' ')
      if (dem && typeof dem === 'object') dem = dem.descripcion || dem.description || dem.name || dem.title || dem.label || JSON.stringify(dem)
      // If it's a numeric ID, resolve via mantenedor endpoints
      if (typeof dem === 'number') {
        const resolved = await resolveDemography(dem)
        dem = resolved.descripcion || ''
        copy.dem_color = copy.dem_color || resolved.color || ''
      }
      copy.demography = String(dem || '')
      // Carry color if available from object payload
      copy.dem_color = copy.dem_color || copy.demografia_color || (copy.demografia && (copy.demografia.color || copy.demografia.dem_color)) || ''
      return copy
    }))

    // Exclude erotic content from initial lists
    const nonEroticPrepared = prepared.filter(i => i.erotic !== true)
    populars.value = nonEroticPrepared.slice(0, 12)
    trending.value = nonEroticPrepared.slice(0, 8)
    displayedTrending.value = trending.value
    // Warm caches for fast tab switching
    trendingCache.value.all = nonEroticPrepared
    trendingCache.value.shonen = nonEroticPrepared.filter(i => String(i.demography || '').toLowerCase().includes('shon'))
    trendingCache.value.seinen = nonEroticPrepared.filter(i => String(i.demography || '').toLowerCase().includes('sein'))
    // Erotic list cached separately (resolved with isErotic to be consistent)
    trendingCache.value.erotico = prepared.filter(i => isErotic(i) === true)
    latest.value = nonEroticPrepared.slice(4, 12)

    // Try to load most viewed from API (ordering by vistas desc)
    try {
      let r
      try {
        r = await api.get('manga/mangas/', { params: { ordering: '-vistas', limit: 10, page_size: 10, erotico: false }, timeout: 3000 })
      } catch (e) {
        r = await api.get('mangas/', { params: { ordering: '-vistas', limit: 10, page_size: 10, erotico: false }, timeout: 3000 })
      }
      const raw = r?.data?.results || r?.data || []
      const norm = normalizeData(raw)
      const prepped = await Promise.all(norm.slice(0, 10).map(async (it) => {
        const copy = { ...it }
        copy.displayCover = await resolveLocalCover(copy)
        // Normalize title key differences
        copy.title = copy.title || copy.titulo || ''
        // Map erotico -> erotic if provided in this list
        if (copy.erotico === true || copy.erotico === false) {
          copy.erotic = copy.erotico
        }
        return copy
      }))
      // Exclude erotic in sidebar 'Más vistos'
      mostViewed.value = prepped.filter(i => i.erotic !== true)
    } catch (e) {
      // Fallback: approximate mostViewed by using prepared list (no views available)
      mostViewed.value = prepared.filter(i => i.erotic !== true).slice(0, 10)
    }
  } catch (e) {
    error.value = e.message
    // fallback demo items if everything fails
    const fallback = [
      { id: 90655, title: 'Reencarné como el padre de una joven malvada', cover: 'https://picsum.photos/seed/90655/400/600', score: '8.2', demography: 'Shounen' },
      { id: 76332, title: 'Dungeon ni Hisomu Yandere', cover: 'https://picsum.photos/seed/76332/400/600', score: '7.9', demography: 'Seinen' },
      { id: 90721, title: 'Pensé que sería popular...', cover: 'https://picsum.photos/seed/90721/400/600', score: '7.4', demography: 'Shounen' },
      { id: 85293, title: 'Tsuihou Sareta Tanyashi', cover: 'https://picsum.photos/seed/85293/400/600', score: '6.6', demography: 'Shounen' },
      { id: 88074, title: 'Shinjiteita Nakamatachi', cover: 'https://picsum.photos/seed/88074/400/600', score: '8.9', demography: 'Seinen' },
      { id: 89191, title: 'Godlevel Assassin', cover: 'https://picsum.photos/seed/89191/400/600', score: '9.0', demography: 'Shounen' }
    ]

    const prepared = await Promise.all(fallback.map(async (it) => {
      const copy = { ...it }
      copy.displayCover = await resolveLocalCover(copy)
      return copy
    }))

    populars.value = prepared
    trending.value = prepared.slice(0, 6)
    latest.value = prepared.slice(0, 6)
    mostViewed.value = prepared.slice(0, 10)
  } finally {
    loading.value = false
  }
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

async function loadTrendingFiltered() {
  const reqId = ++trendingFilterReqId
  const baseParams = { page_size: 100 }
  let params = { ...baseParams }
  // Asegura tener demografías antes de aplicar filtro por tab
  await ensureDemografiaIds()
  // Filtro por demografía (ID). Shonen usa 7 en tu backend.
  if (trendingFilter.value === 'shonen') params.demografia = demografiaIds.value.shonen ?? 7
  else if (trendingFilter.value === 'seinen') params.demografia = demografiaIds.value.seinen ?? 9
  else if (trendingFilter.value === 'erotico' && demografiaIds.value.erotico) params.demografia = demografiaIds.value.erotico
  // Backend-driven erotic filter when tab is 'erotico'
  if (trendingFilter.value === 'erotico') {
    params.erotico = true
  } else {
    // For other tabs (including 'all'), explicitly request non-erotic content
    params.erotico = false
  }
  // Si no contamos con demografia numérica (producción sin mantenedor), evita hacer request sin filtro
  if ((trendingFilter.value === 'shonen' && !demografiaIds.value.shonen) || (trendingFilter.value === 'seinen' && !demografiaIds.value.seinen)) {
    // Mantener listado cliente usando cache/local sin pedir al backend sin filtro
    const key = trendingFilter.value
    if (trendingCache.value[key]?.length) {
      displayedTrending.value = trendingCache.value[key]
    }
    return
  }
  try {
    const r = await api.get('manga/mangas/', { params })
    const raw = Array.isArray(r.data) ? r.data : (r.data?.results || [])
    // Prefetch batch covers for items missing http cover
    const needBatch = raw.filter(it => {
      const c = it.cover || it.cover_image || it.url_absoluta || it.url_imagen || ''
      return !c || typeof c !== 'string' || !c.startsWith('http')
    })
    const idsForBatch = needBatch.map(it => it.id).filter(Boolean)
    let batchMap = new Map()
    if (idsForBatch.length) {
      try {
        const { getMainCoversBatch } = await import('@/services/coverService')
        batchMap = await getMainCoversBatch(idsForBatch)
      } catch (e) { batchMap = new Map() }
    }
      const mapped = await Promise.all(raw.map(async it => {
      const copy = { ...it }
      copy.title = copy.titulo || copy.title || ''
      copy.cover = copy.cover || copy.cover_image || copy.url_absoluta || copy.url_imagen || ''
      if (typeof copy.cover === 'string' && (copy.cover.endsWith('.svg') || copy.cover.startsWith('/assets/covers/'))) {
        copy.cover = ''
      }
      // Resolve remote cover if needed (numeric id or missing http prefix)
          if (!copy.cover || typeof copy.cover !== 'string' || !copy.cover.startsWith('http')) {
            const pre = batchMap.get(String(copy.id))
            if (pre) copy.cover = pre
            else {
              const byId = await getCoverByIdCached(copy.cover_id || copy.main_cover_id || copy.cover)
              if (byId) copy.cover = byId
              else {
                const c = await getMainCoverCached(copy.id)
                if (c) copy.cover = c
              }
            }
          }
      copy.displayCover = await resolveLocalCover(copy)
      if (typeof copy.displayCover === 'string' && copy.displayCover.startsWith('/assets/covers/')) {
        const forced = await getMainCoverCached(copy.id)
        if (forced) copy.displayCover = forced
      }
      // Preferir valor del serializer si viene resuelto
      let dem = copy.demografia_display || copy.demografia || copy.demography || copy.type || ''
      if (typeof dem === 'number') {
        // Resolver vía mapa precargado para evitar esperas; si falta, pedir puntualmente
        const local = demografiasMap.get(Number(dem))
        if (local) {
          dem = local.descripcion || ''
          copy.dem_color = copy.dem_color || local.color || ''
        } else {
          const resolved = await resolveDemografiaDescripcion(dem)
          dem = resolved.descripcion || ''
          copy.dem_color = copy.dem_color || resolved.color || ''
        }
      }
      // Map backend erotico -> frontend erotic so Erótico tab and badges work
      if (copy.erotico === true || copy.erotico === false) {
        copy.erotic = copy.erotico
      }
      copy.demography = String(dem || '')
      return copy
    }))
    // No sobrescribimos "trending" global para no impactar otras pestañas; solo cacheamos el filtro actual.
    // Update cache for the current filter to speed subsequent tab switches
    const key = trendingFilter.value
    // Guard against late responses overriding a newer selection
    if (reqId === trendingFilterReqId && key && trendingCache.value[key]) {
      trendingCache.value[key] = mapped
      if (popularTab.value === key) {
        displayedTrending.value = mapped
      }
    }
  } catch (e) {
    // keep existing trending on error
  }
}

onMounted(async () => {
  await fetchDemografiaIds()
  await preloadDemografias()
  await loadData()
  // Forzar estado consistente tras carga inicial
  setPopularTab('all')
  if (!displayedTrending.value || !displayedTrending.value.length) {
    const baseAll = trendingCache.value.all.length ? trendingCache.value.all : trending.value
    displayedTrending.value = baseAll
  }
  fetchAuthState()
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
    
    <div class="home-layout" v-else>
      <div class="home-main">

          <!-- Populares / Tabs -->
          <div class="row">
            <div class="col">
              <nav class="nav nav-pills nav-justified mb-3" id="pills-tab" role="tablist">
                <a href="#" @click.prevent="setPopularTab('all')" :class="['nav-item nav-link', { active: popularTab === 'all' }]">All</a>
                <a href="#" @click.prevent="setPopularTab('shonen')" :class="['nav-item nav-link', { active: popularTab === 'shonen' }]">Shonen</a>
                <a href="#" @click.prevent="setPopularTab('seinen')" :class="['nav-item nav-link', { active: popularTab === 'seinen' }]">Seinen</a>
                <a v-if="isAuthenticated" href="#" @click.prevent="setPopularTab('erotico')" :class="['nav-item nav-link', { active: popularTab === 'erotico' }]">Erótico</a>
              </nav>

              <div class="tab-content" id="pills-tabContent" :key="popularTab">
                <div v-show="popularTab === 'all'" class="tab-pane" id="pills-populars">
                  <div class="cards-grid">
                    <div v-for="item in populars.filter(i => i.erotic !== true)" :key="item.id" class="card-item">
                      <a :href="`/library/manga/${item.id}`" class="card-link">
                          <div class="thumbnail book" :style="{ backgroundImage: `url(${item.displayCover || item.cover})` }">
                          <div class="thumbnail-title top-strip"><h4 class="text-truncate" :title="item.title">{{ item.title }}</h4></div>
                          <span class="book-type badge badge-manga">MANGA</span>
                          <div class="type-bubble">{{ originLabel(item) }}</div>
                          <div class="thumbnail-type-bar" :class="typeClass(item)" :style="{ '--type-bar-color': item.dem_color || undefined }">{{ displayType(item) }}</div>
                        </div>
                      </a>
                    </div>
                  </div>

                  <!-- Recommendation block moved up below popular cards -->
                  <div class="recommendation-block mt-4" v-if="populars.length">
                    <h5 class="mb-3">Hoy recomendamos...</h5>
                    <div class="recommendation-inner">
                      <div class="rec-cover">
                        <a target="_blank" href="#"><img class="img-fluid" :src="populars[0] ? (populars[0].displayCover || populars[0].cover) : ''" :alt="populars[0]?.title || 'cover'"/></a>
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
                <div v-show="popularTab === 'shonen'" class="tab-pane" id="pills-populars-shonen">
                  <div class="cards-grid">
                    <!-- Usar displayedTrending para evitar que cargas tardías reemplacen el filtro -->
                    <div v-for="item in displayedTrending.filter(i => i.erotic !== true)" :key="`sh-${item.id}`" class="card-item">
                      <a :href="`/library/manga/${item.id}`" class="card-link">
                        <div class="thumbnail book" :style="{ backgroundImage: `url(${item.displayCover || item.cover})` }">
                          <div class="thumbnail-title top-strip"><h4 class="text-truncate" :title="item.title">{{ item.title }}</h4></div>
                          <div class="type-bubble">{{ originLabel(item) }}</div>
                          <div class="thumbnail-type-bar" :class="typeClass(item)" :style="{ '--type-bar-color': item.dem_color || undefined }">{{ displayType(item) }}</div>
                        </div>
                      </a>
                    </div>
                  </div>
                </div>
                <div v-show="popularTab === 'seinen'" class="tab-pane" id="pills-populars-seinen">
                  <div class="cards-grid">
                    <!-- Usar displayedTrending para evitar que cargas tardías reemplacen el filtro -->
                    <div v-for="item in displayedTrending.filter(i => i.erotic !== true)" :key="`se-${item.id}`" class="card-item">
                      <a :href="`/library/manga/${item.id}`" class="card-link">
                        <div class="thumbnail book" :style="{ backgroundImage: `url(${item.displayCover || item.cover})` }">
                          <div class="thumbnail-title top-strip"><h4 class="text-truncate" :title="item.title">{{ item.title }}</h4></div>
                          <div class="type-bubble">{{ originLabel(item) }}</div>
                          <div class="thumbnail-type-bar" :class="typeClass(item)" :style="{ '--type-bar-color': item.dem_color || undefined }">{{ displayType(item) }}</div>
                        </div>
                      </a>
                    </div>
                  </div>
                </div>
                <div v-if="isAuthenticated" v-show="popularTab === 'erotico'" class="tab-pane" id="pills-populars-erotico">
                  <div class="cards-grid">
                    <!-- Usar displayedTrending para evitar que cargas tardías reemplacen el filtro -->
                    <div v-for="item in displayedTrending.filter(i => i.erotic === true)" :key="`er-${item.id}`" class="card-item">
                      <a :href="`/library/manga/${item.id}`" class="card-link">
                        <div class="thumbnail book" :style="{ backgroundImage: `url(${item.displayCover || item.cover})` }">
                          <div class="thumbnail-title top-strip"><h4 class="text-truncate" :title="item.title">{{ item.title }}</h4></div>
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
                <div v-for="item in (popularTab === 'erotico' 
                    ? displayedTrending.filter(i => isErotic(i)) 
                    : (isAuthenticated ? displayedTrending : displayedTrending.filter(i => !isErotic(i))))" 
                  :key="`tr-${item.id}`" class="card-item">
                  <a :href="`/library/manga/${item.id}`" class="card-link">
                    <div class="thumbnail book" :style="{ backgroundImage: `url(${item.displayCover || item.cover})` }">
                      <div class="thumbnail-title top-strip"><h4 class="text-truncate" :title="item.title">{{ item.title }}</h4></div>
                      <div class="type-bubble">{{ originLabel(item) }}<span v-if="isAuthenticated && isErotic(item)" class="age-18">+18</span></div>
                      <div class="thumbnail-type-bar" :class="typeClass(item)" :style="{ '--type-bar-color': item.dem_color || undefined }">{{ displayType(item) }}</div>
                    </div>
                  </a>
                </div>
              </div>
            </div>
          </div>

          

          

          <!-- Trending section removed: series are shown in the Populares section -->


      </div>

      <!-- Sidebar -->
      <aside class="home-sidebar">
          <div v-if="isAuthenticated && isSuperuser" class="text-center mb-3">
            <a href="/dev/upload" class="btn btn-primary btn-lg w-100"><i class="fas fa-upload"></i> Subir capítulo</a>
          </div>

          <div class="mt-2 text-center rank-wrapper">
            <div class="card rank p-3">
              <h5>Más vistos</h5>
              <div class="ranked-list">
                <div class="ranked-item" v-for="(t, idx) in mostViewed.slice(0,10)" :key="`rank-${t.id}`">
                  <div class="position">{{ idx + 1 }}.</div>
                  <div class="description">{{ t.title }}</div>
                </div>
              </div>
            </div>
          </div>
        </aside>
      </div>

  </div>
</template>

<style scoped>
.home-view { padding-left: 16px; padding-right: 16px; max-width:1600px; margin:0 auto; }
.home-layout { display: grid; grid-template-columns: 1fr; gap: 24px; }
@media (min-width: 992px) { .home-layout { grid-template-columns: 3.5fr 1fr; } }
@media (min-width: 1400px) { .home-layout { grid-template-columns: 5fr 1.2fr; } }
.home-main { min-width:0; }
.home-sidebar { min-width:0; position:sticky; top:90px; align-self:start; }

.home-view .thumbnail.book {
  background-size: cover;
  background-position: center;
  aspect-ratio: 2 / 3;
  min-height: 220px;
  position: relative;
  border-radius: 6px;
  overflow: hidden;
  color: #fff;
  display: block;
}
.thumbnail .thumbnail-title.top-strip { position:absolute; top:0; left:0; right:0; background:rgba(0,0,0,0.65); padding:4px 6px; }
.thumbnail .thumbnail-title.top-strip h4 { margin:0; font-size:14px; color:#fff; width:100%; line-height:1.15; }
.home-view .nav { flex-wrap: wrap; gap: 8px; }
.home-view .thumbnail.book { width: 100%; }
/* Adaptive cards grid */
.cards-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 14px; }
@media (min-width: 1600px) { .cards-grid { grid-template-columns: repeat(auto-fill, minmax(240px, 1fr)); } }
.card-item { list-style:none; }
.card-link { text-decoration:none; display:block; }
.book-type { position: absolute; right:8px; top:8px; background: rgba(0,0,0,0.65); padding:3px 6px; border-radius:4px; font-size:11px }
.thumbnail-type-bar { position:absolute; left:0; right:0; bottom:0; padding:4px 6px 5px; font-size:12px; font-weight:600; letter-spacing:.3px; background:linear-gradient(90deg, var(--type-bar-color, rgba(0,0,0,0.65)) 0%, rgba(0,0,0,0.4) 100%); color:#fff; }
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
}

@media (max-width: 576px) {
  .home-view .thumbnail.book { min-height: 180px; }
  .home-view .nav { justify-content: center; }
  /* Force at least 3 columns: allow very small card width */
  .cards-grid { gap:8px; grid-template-columns: repeat(3, minmax(0, 1fr)); }
  /* On mobile, trending grid shows 2 columns */
  .cards-grid.cards-grid--trending { grid-template-columns: repeat(2, 1fr); }
  .cards-grid .thumbnail.book { aspect-ratio: 9 / 14; min-height: 170px; }
  .cards-grid .thumbnail-title.top-strip h4 { font-size:12px; }
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

/* Improve dark mode readability for muted texts */
.home-view .text-muted { color: var(--ztmo-text); opacity: 0.75; }
.home-view .form-label { color: var(--ztmo-text); }
</style>

