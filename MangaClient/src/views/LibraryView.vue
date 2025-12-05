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
                  <option value="manhua">Manhua</option>
                  <option value="manhwa">Manhwa</option>
                  <option value="novel">Novela</option>
                  <option value="one_shot">One shot</option>
                  <option value="doujinshi">Doujinshi</option>
                  <option value="oel">Oel</option>
                </select>
              </div>
              <div class="field">
                <label>Demografía</label>
                <select v-model="demography">
                  <option value="">Ver todo</option>
                  <option value="seinen">Seinen</option>
                  <option value="shoujo">Shoujo</option>
                  <option value="shounen">Shounen</option>
                  <option value="josei">Josei</option>
                  <option value="kodomo">Kodomo</option>
                </select>
              </div>
              <div v-if="showStatus" class="field">
                <label>Estado</label>
                <select v-model="status">
                  <option value="">Ver todo</option>
                  <option value="publishing">Publicándose</option>
                  <option value="ended">Finalizado</option>
                  <option value="cancelled">Cancelado</option>
                  <option value="on_hold">Pausado</option>
                </select>
              </div>
              <div v-if="showStatus" class="field">
                <label>Traducciones</label>
                <select v-model="translationStatus">
                  <option value="">Ver todo</option>
                  <option value="active">Activo</option>
                  <option value="finished">Finalizado</option>
                  <option value="abandoned">Abandonado</option>
                </select>
              </div>
            </div>
          </section>
        </div>

        <div class="filters-col">
          <section class="filter-group" :class="{ open: openSection==='genres' }">
            <header @click="toggleSection('genres')"><span>Géneros (máx {{genreLimit}})</span><i></i></header>
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

      <!-- Results below top filters -->
      <section class="results">
        <div v-if="loading && !mangas.length" class="loading">Cargando...</div>
        <div v-else-if="error && !mangas.length" class="error">Error cargando datos</div>
        <div v-else class="cards-grid">
          <div v-for="m in mangas" :key="m.id" class="card-item">
            <router-link :to="`/library/manga/${m.id}`" class="card-link">
              <div class="thumbnail book">
                <img
                  class="thumbnail-img"
                  :src="safeCover(m.cover)"
                  :alt="m.title"
                  loading="lazy"
                  decoding="async"
                  :fetchpriority="indexFetchPriority(m)"
                  :srcset="buildSrcset(m.cover)"
                  :sizes="thumbnailSizes"
                />
                <div class="thumbnail-title top-strip"><h4 class="text-truncate" :title="m.title">{{ m.title }}</h4></div>
                <div class="type-bubble">{{ originLabel(m) }}<span v-if="isErotic(m)" class="age-18">+18</span></div>
                <div class="thumbnail-type-bar" :class="typeClass(m)" :style="{ '--type-bar-color': m.dem_color || undefined }">{{ displayType(m) }}</div>
              </div>
            </router-link>
          </div>
          <div v-if="!mangas.length && !loading" class="empty">Sin resultados</div>
        </div>

        <div class="pagination-row">
          <button v-if="!loadAll && showLoadMore" class="btn" @click="loadMore">Cargar más</button>
          <button v-if="!loadAll" class="btn" @click="activateLoadAll">Cargar todas</button>
          <div v-if="loadAll" class="page-info">Cargadas todas ({{ mangas.length }})</div>
          <div class="page-info" v-if="mangas.length">Página {{ page }} • Mostrando {{ mangas.length }}</div>
        </div>
      </section>
    </div>
  </div>
</template>

<script>
import { ref, computed, watch, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useRoute, useRouter } from 'vue-router'
import cache from '@/services/cache'
import { listMangas } from '@/services/mangaService'
import { getCoverByIdCached, getMainCoverCached } from '@/services/coverService'
import { resolveDemografiaDescripcion } from '@/services/mantenedorService'

export default {
  name: 'LibraryView',
  setup() {
    const route = useRoute()
    const router = useRouter()

    // Mapa de demografías precargadas para resolución inmediata
    const demografiasMap = new Map()
    let demografiasLoaded = false

    // Core reactive state
    const mangas = ref([])
    const loading = ref(false)
    const error = ref(null)

    // Search & ordering
    const search = ref(route.query.title ? String(route.query.title) : '')
    const orderItem = ref('likes_count')
    const orderDir = ref('desc')

    // Basic filters
    const type = ref('')
    const demography = ref('')
    const status = ref('')
    const translationStatus = ref('')
    const webcomic = ref('')
    const yonkoma = ref('')
    const amateur = ref('')
    const erotic = ref('')

    // Estado de autenticación desde el store
    const auth = useAuthStore()
    const isAuthenticated = computed(() => auth.isAuthenticated)

    // Genres
    const genreLimit = 5
    const includeGenres = ref([])
    const excludeGenres = ref([])
    const genres = ref([
      { id: 1, name: 'Acción' }, { id: 2, name: 'Aventura' }, { id: 3, name: 'Comedia' },
      { id: 4, name: 'Drama' }, { id: 5, name: 'Slice of Life' }, { id: 6, name: 'Ecchi' },
      { id: 7, name: 'Fantasia' }, { id: 8, name: 'Magia' }, { id: 9, name: 'Sobrenatural' },
      { id: 10, name: 'Horror' }, { id: 11, name: 'Misterio' }, { id: 12, name: 'Psicológico' },
      { id: 13, name: 'Romance' }, { id: 14, name: 'Sci-Fi' }, { id: 15, name: 'Thriller' },
      { id: 16, name: 'Deporte' }, { id: 17, name: 'Girls Love' }, { id: 18, name: 'Boys Love' },
      { id: 19, name: 'Harem' }, { id: 20, name: 'Mecha' }
    ])

    // UI
    // Start with all sections collapsed
    const openSection = ref('')
    const toggleSection = key => {
      openSection.value = openSection.value === key ? '' : key
    }

    const showStatus = computed(() => type.value && type.value !== 'one_shot')

    function enforceGenreLimit() {
      if (includeGenres.value.length > genreLimit) {
        includeGenres.value.pop()
        // Could surface a toast; keeping silent minimal rollback.
      }
    }

    // Pagination
    const page = ref(1)
    const pageSize = ref(20)
    const lastFetchCount = ref(0)
    const loadAll = ref(false)

    // Build params for API (include pagination)
    const params = computed(() => {
      return {
        title: search.value || undefined,
        order_item: orderItem.value,
        order_dir: orderDir.value,
        type: type.value || undefined,
        demography: demography.value || undefined,
        status: status.value || undefined,
        translation_status: translationStatus.value || undefined,
        webcomic: webcomic.value || undefined,
        yonkoma: yonkoma.value || undefined,
        amateur: amateur.value || undefined,
        erotic: erotic.value || undefined,
        genders: includeGenres.value.length ? includeGenres.value.join(',') : undefined,
        exclude_genders: excludeGenres.value.length ? excludeGenres.value.join(',') : undefined,
        page: page.value,
        page_size: pageSize.value
      }
    })

    async function fetchData() {
      if (loadAll.value) return fetchAllPages()
      loading.value = true
      error.value = null
      try {
        const api = await import('@/services/api')
        let res
        const data = await listMangas(params.value)
        lastFetchCount.value = Array.isArray(data) ? data.length : 0
        const items = Array.isArray(data) ? await Promise.all(data.map(d => normalizeItemAsync(d))) : []
        mangas.value = page.value > 1 ? mangas.value.concat(items) : items
      } catch (e) {
        console.error('Library fetch error', e)
        error.value = e
        if (!mangas.value.length) mangas.value = demoSeed()
        if (!mangas.value.length) mangas.value = []
      } finally {
        loading.value = false
      }
    }

    async function fetchAllPages() {
      loading.value = true
      error.value = null
      try {
        mangas.value = []
        let currentPage = 1
        const maxPages = 200
        const accumulated = []
        while (currentPage <= maxPages) {
          const pParams = { ...params.value, page: currentPage }
          const chunk = await listMangas(pParams)
            const norm = await Promise.all(chunk.map(c => normalizeItemAsync(c)))
            accumulated.push(...norm)
          if (chunk.length < pageSize.value || !chunk.length) break
          currentPage++
        }
        mangas.value = accumulated.length ? accumulated : demoSeed()
        mangas.value = accumulated
        lastFetchCount.value = accumulated.length
        page.value = currentPage
      } catch (e) {
        console.error('Library fetch all error', e)
        error.value = e
        if (!mangas.value.length) mangas.value = demoSeed()
        if (!mangas.value.length) mangas.value = []
      } finally {
        loading.value = false
      }
    }

    function activateLoadAll() {
      loadAll.value = true
      page.value = 1
      fetchAllPages()
    }

    // Caches locales para deduplicar requests de portadas
    const _libCoverIdPromises = new Map()
    const _libCoverIdResults = new Map()
    const _libMainCoverPromises = new Map()
    const _libMainCoverResults = new Map()

    async function fetchCoverByIdRaw(cid) {
      try { return await fetchCoverById(cid) } catch (e) { return null }
    }
    function getCoverByIdCached(id) {
      const cid = Number(id)
      if (!cid || Number.isNaN(cid)) return Promise.resolve(null)
      if (_libCoverIdResults.has(cid)) return Promise.resolve(_libCoverIdResults.get(cid))
      if (_libCoverIdPromises.has(cid)) return _libCoverIdPromises.get(cid)
      const p = fetchCoverByIdRaw(cid).then(url => { _libCoverIdResults.set(cid, url || null); _libCoverIdPromises.delete(cid); return url || null })
      _libCoverIdPromises.set(cid, p)
      return p
    }
    async function fetchMainCoverRaw(id) {
      try { return await getMainCoverForManga(id) } catch (e) { return null }
    }
    function getMainCoverCached(mangaId) {
      const mid = String(mangaId)
      if (!mid) return Promise.resolve(null)
      if (_libMainCoverResults.has(mid)) return Promise.resolve(_libMainCoverResults.get(mid))
      if (_libMainCoverPromises.has(mid)) return _libMainCoverPromises.get(mid)
      const p = fetchMainCoverRaw(mid).then(url => { _libMainCoverResults.set(mid, url || null); _libMainCoverPromises.delete(mid); return url || null })
      _libMainCoverPromises.set(mid, p)
      return p
    }

    async function resolveDemografiaDescripcion(idOrName) {
      if (!idOrName && idOrName !== 0) return { descripcion: '', color: '' }
      const mid = Number(idOrName)
      if (Number.isFinite(mid) && demografiasMap.has(mid)) return demografiasMap.get(mid)
      const direct = demografiasMap.get(idOrName)
      if (direct) return { descripcion: direct.descripcion || '', color: direct.color || '' }
      if (typeof idOrName === 'string' && demografiasMap.size) {
        const needle = idOrName.trim().toLowerCase()
        for (const [, val] of demografiasMap) {
          const name = (val.descripcion || '').trim().toLowerCase()
          if (name && name === needle) return { descripcion: val.descripcion || '', color: val.color || '' }
        }
      }
      // Fallback remoto: intentar obtener por ID directo, luego por listado
      try {
        const r = await svc.getDemografiaById(idOrName)
        const d = r?.data || r || {}
        const val = { descripcion: d.descripcion || d.name || d.title || '', color: d.color || d.dem_color || '' }
        if (Number.isFinite(mid)) demografiasMap.set(mid, val)
        return val
      } catch (e) {}
      try {
        const rl = await svc.listDemografias({ page_size: 1000 })
        const list = Array.isArray(rl?.data) ? rl.data : (rl?.data?.results || rl || [])
        const found = list.find(x => String(x.id) === String(idOrName) || String((x.descripcion || x.name || x.title || '')).toLowerCase() === String(idOrName).toLowerCase()) || {}
        const val = { descripcion: found.descripcion || found.name || found.title || '', color: found.color || found.dem_color || '' }
        if (Number.isFinite(mid)) demografiasMap.set(mid, val)
        return val
      } catch (e) {}
      return { descripcion: '', color: '' }
    }

    async function normalizeItemAsync(raw) {
      const id = raw.id || raw.slug || raw.uuid || Math.random().toString(36).slice(2)
      const title = raw.title || raw.titulo || raw.name || raw.manga_title || `Item ${id}`
      // Preferir portada del serializer cuando esté disponible
      let cover = raw.cover || raw.cover_url || raw.image || raw.portada || raw.cover_image || raw.url_absoluta || raw.url_imagen || ''
      // Evitar fallback local como '/assets/covers/cover_4.svg': forzar resolución remota
      if (typeof cover === 'string' && (cover.endsWith('.svg') || cover.startsWith('/assets/covers/'))) {
        cover = ''
      }
      if (!cover || typeof cover !== 'string' || !cover.startsWith('http')) {
        const byId = await getCoverByIdCached(raw.cover_id || raw.main_cover_id || cover)
        if (byId) cover = byId
        else {
          const viaManga = await getMainCoverCached(id)
          if (viaManga) cover = viaManga
        }
      }
      if (!cover) cover = resolveCover(raw)
      // Preferir demografia_display (del serializer) cuando esté disponible
      let dem = raw.demografia_display || raw.demography || raw.demografia || raw.demo || ''
      if (Array.isArray(dem)) dem = dem.join(' ')
      if (typeof dem === 'object' && dem) dem = dem.descripcion || dem.description || dem.name || dem.title || dem.label || JSON.stringify(dem)
      let dem_color = raw.dem_color || ''
      if (typeof dem === 'number') {
        // Resolver primero desde mapa precargado, luego solicitar si falta
        const mid = Number(dem)
        const local = demografiasMap.get(mid)
        if (local) {
          dem = local.descripcion || ''
          dem_color = dem_color || local.color || ''
        } else {
          const resolved = await resolveDemografiaDescripcion(dem)
          dem = resolved.descripcion || ''
          dem_color = dem_color || resolved.color || ''
        }
      }
      dem = String(dem || '')
      return {
        id,
        title,
        cover,
        type: raw.type || raw.book_type || 'manga',
        demography: dem,
        dem_color,
        erotic: (raw.erotico === true) || (raw.erotic === true) || raw.tags?.includes('erotic')
      }
    }
    function safeCover(url){
      const u = String(url || '').toLowerCase()
      const blank = 'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" width="160" height="240"/>'
      if (!u || !u.startsWith('http')) return blank
      if (u.includes('miswebtoons.uk/assets/covers')) return blank
      return url
    }

    // Build a generic srcset; if no variants exist, duplicate src as fallback
    function buildSrcset(src) {
      if (!src || typeof src !== 'string') return ''
      // If your CDN provides variants, replace with actual variant URLs
      // e.g., `${base}?w=320 320w, ${base}?w=640 640w, ...`
      return `${src} 320w, ${src} 640w, ${src} 960w, ${src} 1280w`
    }
    const thumbnailSizes = '(max-width: 576px) 33vw, (max-width: 960px) 25vw, 200px'
    function indexFetchPriority(m) {
      // prioridad alta para primeras 6 portadas visibles; resto auto
      // Nota: el v-for no da índice aquí; podrías usar key/orden si fuese necesario
      return 'auto'
    }

    function resolveCover(raw) {
      const c = raw.cover || raw.image || raw.portada || ''
      if (typeof c === 'string' && c.startsWith('http')) return c
      if (c) return `/assets/covers/${c}`
      return '/assets/demo/cover2.jpg'
    }

    function demoSeed() {
      // No demo/mocks: always return empty when no data
      return []
    }

    function reload() {
      clearTimeout(debounceTimer)
      page.value = 1
      fetchData()
    }

    function applySearch() {
      page.value = 1
      router.push({ query: { ...route.query, title: search.value || undefined } })
      fetchData()
    }

    watch(() => route.query.title, (val) => {
      if ((val || '') !== search.value) {
        search.value = val || ''
        fetchData()
      }
    })

    // Auto reload when params change (debounced)
    let debounceTimer = null
    watch(params, () => {
      clearTimeout(debounceTimer)
      debounceTimer = setTimeout(() => {
        // when filters change we want to start from page 1
        if (page.value !== 1) page.value = 1
        fetchData()
      }, 300)
    }, { deep: true })

    function loadMore() {
      if (loading.value) return
      page.value = page.value + 1
      fetchData()
    }

    const showLoadMore = computed(() => {
      return lastFetchCount.value === pageSize.value
    })

    onMounted(async () => {
      // Precargar demografías para aplicar color/descripcion inmediato
      try {
        if (!demografiasLoaded) {
          const svc = await import('@/services/mantenedorService')
          const list = await svc.listDemografias({ page_size: 1000 })
          if (Array.isArray(list)) {
            for (const d of list) {
              const desc = d.descripcion || d.name || d.title || ''
              const color = d.color || d.dem_color || ''
              demografiasMap.set(Number(d.id), { descripcion: desc, color })
            }
            demografiasLoaded = true
          }
        }
      } catch {}
      // Seed demo items inmediatamente para vista y luego cargar datos reales
      mangas.value = demoSeed()
      await fetchData()
    })

    // Reaccionar al deslogueo: desactivar filtro erótico y refrescar
    watch(isAuthenticated, (val) => {
      if (!val) {
        erotic.value = ''
        page.value = 1
        fetchData()
      }
    })

    function typeClass(m) {
      let raw = (m && (m.demography || m.type || ''))
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

    function displayType(m) {
      let val = m && (m.demography || m.demografia || m.type || 'MANGA')
      // parse JSON encoded strings
      if (typeof val === 'string') {
        const s = val.trim()
        if (s.startsWith('{') || s.startsWith('[')) {
          try { val = JSON.parse(s) } catch (e) { /* keep original */ }
        }
      }
      if (Array.isArray(val)) val = val.join(' ')
      if (val && typeof val === 'object') val = val.descripcion || val.description || val.name || val.title || JSON.stringify(val)
      return String(val || 'MANGA').toUpperCase()
    }

    function originLabel(m) {
      let t = m && (m.mng_tipo_manga || m.mng_tipo_serie || m.tipo_serie || m.manga_tipo_serie || m.type || m.book_type || '')
      if (!t && m && m.tags && Array.isArray(m.tags)) {
        const joined = m.tags.map(x => (x.nombre || x.name || x)).join(' ').toLowerCase()
        if (joined.includes('manhwa')) t = 'manhwa'
        if (joined.includes('manhua')) t = 'manhua'
      }
      if (typeof t === 'string') t = t.toLowerCase()
      if (t && t.includes('manhwa')) return 'Manhwa'
      if (t && t.includes('manhua')) return 'Manhua'
      if (t && t.includes('novel')) return 'Novela'
      return 'Manga'
    }

    function isErotic(m) {
      if (!m) return false
      if (m.erotic === true) return true
      if (m.tags && Array.isArray(m.tags)) {
        const joined = m.tags.map(t => (t.nombre || t.name || t)).join(' ').toLowerCase()
        if (joined.includes('ecchi') || joined.includes('erotic') || joined.includes('erótico') || joined.includes('erotico')) return true
      }
      const dem = String(m.demography || m.demografia || m.type || '').toLowerCase()
      if (dem.includes('erotic') || dem.includes('erótico') || dem.includes('erotico') || dem.includes('ecchi')) return true
      return false
    }

    return {
      mangas, loading, error,
      search, orderItem, orderDir,
      type, demography, status, translationStatus,
      webcomic, yonkoma, amateur, erotic,
      isAuthenticated,
      includeGenres, excludeGenres, genres, genreLimit,
      openSection, toggleSection, enforceGenreLimit,
      showStatus, reload, applySearch,
      // template helpers
      typeClass, displayType, originLabel, isErotic,
      // pagination
      page, pageSize, loadMore, showLoadMore, loadAll, activateLoadAll
    }
  }
}
</script>

<style scoped>
.library-view { width:100%; display:flex; justify-content:center; }
.layout { display:grid; grid-template-columns: 280px 1fr; gap:24px; width:100%; max-width:1600px; padding:12px 20px; }
@media (max-width: 960px){ .layout { grid-template-columns: 1fr; } .filters { order:2; } }

/* New top filters layout: two columns */
.top-filters { display:grid; grid-template-columns:repeat(2,1fr); gap:18px; margin-bottom:18px; grid-column: 1 / -1; }
@media (max-width: 960px){ .top-filters { grid-template-columns: 1fr; } }
.filters-col { display:flex; flex-direction:column; gap:12px; align-items:stretch; }
.filters-col > * { width:100%; box-sizing:border-box; }

/* Make form controls and filter-groups visually consistent */
.filters-col .search-bar .search-input,
.filters-col .order-row .order-select,
.filters-col .filter-group select {
  height:38px; line-height:38px; padding:6px 10px;
}
.filters-col .search-bar .btn.primary { height:38px; padding:0 14px; }
.filters-col .order-row { align-items:center; }
.filters-col .filter-group { width:100%; }
.filters-col .filter-group .content { max-height:320px; }
.filters-col .checkbox { font-size:13px; }
.filters-col .filter-group header { padding:10px 12px; }

@media (max-width: 960px){
  .filters-col { flex-direction:column; }
}

.filters { display:flex; flex-direction:column; gap:16px; position:relative; }
.search-bar { display:flex; gap:8px; }
.search-input { flex:1; padding:8px 10px; background:var(--surface-1,#1e1e1e); border:1px solid var(--border-color,#333); color:var(--text-primary,#eaeaea); border-radius:4px; }
.search-input:focus { outline:2px solid var(--accent,#3d6bff); }
.btn { cursor:pointer; border:none; padding:8px 14px; font-size:14px; border-radius:4px; transition:.15s; }
.btn.primary { background:var(--accent,#3d6bff); color:#fff; }
.btn.apply { background:var(--accent,#3d6bff); color:#fff; width:100%; }
.btn.primary:hover, .btn.apply:hover { filter:brightness(1.15); }

.order-row { display:flex; align-items:center; gap:8px; flex-wrap:wrap; }
.order-label { font-size:13px; opacity:.85; }
.order-select { padding:6px 8px; background:var(--surface-1,#1e1e1e); border:1px solid var(--border-color,#333); color:var(--text-primary,#eaeaea); border-radius:4px; }
.order-select.small { width:88px; }

.filter-group { border:1px solid var(--border-color,#333); border-radius:6px; background:var(--surface-1,#181818); overflow:hidden; }
.filter-group header { display:flex; justify-content:space-between; align-items:center; padding:10px 12px; cursor:pointer; font-weight:600; font-size:14px; background:var(--surface-2,#222); }
.filter-group header i { width:16px; height:16px; position:relative; }
.filter-group header i:before { content:''; position:absolute; top:4px; left:4px; width:8px; height:8px; border:2px solid var(--text-primary,#eaeaea); border-top:none; border-left:none; transform:rotate(45deg); transition:.25s; }
.filter-group.open header i:before { transform:rotate(225deg); top:6px; }
.filter-group .content { display:none; padding:10px 12px 14px; max-height:420px; overflow:auto; }
.filter-group.open .content { display:block; }
.filter-group .field { display:flex; flex-direction:column; gap:4px; margin-bottom:10px; }
.filter-group .field label { font-size:12px; opacity:.8; }
.filter-group select { padding:6px 8px; background:var(--surface-2,#222); border:1px solid var(--border-color,#333); color:var(--text-primary,#eaeaea); border-radius:4px; }
.genres { display:grid; grid-template-columns:repeat(auto-fill,minmax(110px,1fr)); gap:6px; }
.checkbox { font-size:11px; display:flex; align-items:center; }
.checkbox input { margin-right:4px; }

.results { min-height:400px; grid-column: 1 / -1; }
.loading, .error, .empty { padding:40px 0; text-align:center; font-size:15px; opacity:.8; }
.loading-container { display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 40px 0; }
.loading-icon { width: 48px; height: 48px; margin-bottom: 12px; }
/* Dark mode readability for muted helper texts */
.library-view .text-muted { color: var(--ztmo-text); opacity: 0.75; }
.library-view .form-label, .library-view label { color: var(--ztmo-text); }

.pagination-row { display:flex; align-items:center; justify-content:flex-start; gap:12px; margin-top:14px; }
.pagination-row .page-info { opacity:.85; font-size:13px; }

/* Card grid unified with HomeView */
.cards-grid { display:grid; grid-template-columns:repeat(auto-fill,minmax(200px,1fr)); gap:14px; }
@media (min-width:1600px){ .cards-grid { grid-template-columns:repeat(auto-fill,minmax(240px,1fr)); } }
@media (max-width:576px){ .cards-grid { gap:8px; grid-template-columns:repeat(3,minmax(0,1fr)); } }
.card-item { list-style:none; }
.card-link { text-decoration:none; display:block; }

.thumbnail.book { background-size:cover; background-position:center; aspect-ratio:2/3; min-height:220px; position:relative; border-radius:6px; overflow:hidden; color:#fff; display:block; }
.thumbnail-img { width:100%; height:100%; object-fit:cover; position:absolute; inset:0; }
.thumbnail-title.top-strip { position:absolute; top:0; left:0; right:0; background:rgba(0,0,0,0.65); padding:4px 6px; }
.thumbnail-title.top-strip h4 { margin:0; font-size:14px; color:#fff; width:100%; line-height:1.15; }
@media (max-width:576px){ .thumbnail-title.top-strip h4 { font-size:12px; } }
.book-type { position:absolute; right:8px; top:8px; background:rgba(0,0,0,0.65); padding:3px 6px; border-radius:4px; font-size:11px }

.thumbnail-type-bar { position:absolute; left:0; right:0; bottom:0; padding:4px 6px 5px; font-size:12px; font-weight:600; letter-spacing:.3px; background:linear-gradient(90deg, var(--type-bar-color, rgba(0,0,0,0.65)) 0%, rgba(0,0,0,0.4) 100%); color:#fff; }
.type-bubble { position:absolute; left:8px; top:36px; background:rgba(0,0,0,0.6); color:#fff; padding:3px 8px; border-radius:12px; font-size:11px; font-weight:600; display:inline-flex; align-items:center; gap:6px }
.type-bubble .age-18 { color:#ff4d4f; background:transparent; padding-left:6px; font-weight:800 }
@media (max-width:576px){ .thumbnail-type-bar { font-size:10px; padding:3px 5px 4px; } }

/* Color mapping via CSS variable just like HomeView */
.type-manga { --type-bar-color:#1e88e5; }
.type-manhwa { --type-bar-color:#43a047; }
.type-manhua { --type-bar-color:#c62828; }
.type-novela { --type-bar-color:#6a1b9a; }
.type-shounen { --type-bar-color:#1976d2; }
.type-seinen { --type-bar-color:#546e7a; }
.type-josei { --type-bar-color:#8e24aa; }
.type-shoujo { --type-bar-color:#ff4081; }
.type-default { --type-bar-color:#455a64; }

.text-truncate { white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }

/* Scrollbar minimal styling inside filter content */
.filter-group .content::-webkit-scrollbar { width:8px; }
.filter-group .content::-webkit-scrollbar-track { background:transparent; }
.filter-group .content::-webkit-scrollbar-thumb { background:#333; border-radius:4px; }

/* Light theme overrides */
.theme-light .library-view { color:#111; }
.theme-light .filters .search-input,
.theme-light .filters .order-select,
.theme-light .filter-group select { background:#ffffff; border-color:#d0d0d0; color:#111; }
.theme-light .filter-group { background:#ffffff; border-color:#d5d5d5; }
.theme-light .filter-group header { background:#f3f3f3; color:#111; }
.theme-light .order-label { color:#222; }
.theme-light .checkbox { color:#222; }
.theme-light .thumbnail.book { background:#fafafa; }
.theme-light .thumbnail-title.top-strip { background:rgba(0,0,0,.35); }
.theme-light .thumbnail-title.top-strip h4 { color:#111; }
.theme-light .thumbnail-type-bar { color:#fff; }
.theme-light .btn.primary, .theme-light .btn.apply { background:#2563eb; }
.theme-light .loading, .theme-light .error, .theme-light .empty { color:#222; }
/* type bubble shown on the cover */
.type-bubble { position:absolute; left:8px; top:36px; background:rgba(0,0,0,0.6); color:#fff; padding:3px 8px; border-radius:12px; font-size:11px; font-weight:600; display:inline-flex; align-items:center; gap:6px }
.type-bubble .age-18 { color:#ff4d4f; background:transparent; padding-left:6px; font-weight:800 }
</style>
