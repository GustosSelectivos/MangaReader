<template>
  <div class="reader-page">
    <header class="element-header manga">
      <div class="container header-inner">
        <div class="row align-items-start">
          <div class="col-12 col-md-4 text-center">
            <h4 class="book-type">MANGA</h4>
            <div class="element-image my-2">
              <img class="book-thumbnail" :src="cover" alt="Portada del manga" loading="lazy" decoding="async" fetchpriority="high" />
            </div>
          </div>
          <div class="col-12 col-md-8">
            <h1 class="element-title display-5">{{ mangaTitle }} <small v-if="year" class="text-muted">( {{ year }} )</small></h1>
            <p class="element-description lead">{{ description }}</p>
            <!-- Genero/Demografía bajo la descripción -->
            <div v-if="mainDemography" class="demography-badge mt-2 mb-3">
              <span class="badge badge-demography">{{ mainDemography }}</span>
            </div>
            <div class="badges mb-3" v-if="genres && genres.length">
              <span class="badge badge-primary me-2 mb-2" v-for="g in genres" :key="g">{{ g }}</span>
            </div>
            <div class="status-row mb-3" v-if="statusDisplay">
              <span class="status-dot" :class="{ on: statusDisplay.on }"></span>
              <strong class="ms-2">{{ statusDisplay.label }}</strong>
            </div>
            <div class="alt-titles mb-3" v-if="altTitles && altTitles.length">
              <h6 class="mb-2">Títulos alternativos</h6>
              <div class="chips">
                <span class="chip" v-for="t in altTitles" :key="t">{{ t }}</span>
              </div>
            </div>
            <div class="synonyms mb-2" v-if="synonyms && synonyms.length">
              <h6 class="mb-2">Sinónimos</h6>
              <div class="chips">
                <span class="chip" v-for="s in synonyms" :key="s">{{ s }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </header>

    <main class="container-fluid element-body mt-3">
      <div class="container p-0 p-sm-2">
        <div class="row">
          <div class="col-12 col-lg-8 mx-auto">
            <div class="reader-area">
              <div class="reader-toolbar mb-2 d-flex justify-content-between align-items-center">
                <div>
                  <button class="btn btn-danger" @click="toggleOrder">Invertir orden</button>
                </div>
                <div>
                  <button class="btn btn-secondary" @click="showAllChapters = !showAllChapters">
                    {{ showAllChapters ? 'Ocultar' : 'Ver todo' }}
                  </button>
                </div>
              </div>

              <div v-if="loading" class="loading-container my-4">
                <img src="/assets/load.gif" alt="Cargando capítulos..." class="loading-icon" />
                <p>Cargando capítulos...</p>
              </div>

              <section class="chapters-list card mb-3" v-else>
                <h4 class="p-3 m-0">Capítulos</h4>
                <ul class="list-group list-group-flush">
                  <li v-for="(ch, idx) in visibleChapters" :key="ch.id" class="list-group-item">
                    <div class="d-flex justify-content-between align-items-center">
                      <div @click="selectChapter(idx)" class="chapter-title text-truncate" style="cursor:pointer">
                        {{ ch.title || ('Capítulo ' + ch.number) }}
                      </div>
                      <div class="d-flex align-items-center gap-3">
                        <small class="text-muted">{{ ch.date }}</small>
                        <button class="btn btn-sm btn-primary" @click="openChapter(idx)" aria-label="Leer capítulo">
                          <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 16 16" fill="currentColor" aria-hidden="true">
                            <path d="M6 4.5v7l6-3.5-6-3.5z" />
                          </svg>
                        </button>
                      </div>
                    </div>
                  </li>
                </ul>
              </section>
              <!-- Always-visible upload button under chapters -->
              <div class="mb-3">
                <a :href="uploadLink" class="btn btn-primary w-100 d-flex align-items-center justify-content-center gap-2" aria-label="Subir capítulo">
                  <svg class="icon" xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 16 16" fill="currentColor" aria-hidden="true">
                    <path d="M8 2l4 4H9v4H7V6H4l4-4z"/>
                    <path d="M3 12h10v2H3z"/>
                  </svg>
                  <span>Subir capítulo</span>
                </a>
              </div>
              
              <!-- reader-frame removed: chapter reading UI moved to ChapterView -->
            </div>
          </div>

          
        </div>

        <!-- Comments removed per request -->
      </div>
    </main>
  </div>
</template>

<script>
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { listChapters } from '@/services/chapterService'
import { getManga, listMangaCovers } from '@/services/mangaService'
import api from '@/services/api'
import { getCoverByIdCached, getMainCoverCached } from '@/services/coverService'

export default {
  name: 'ReaderView',
  props: { mangaId: { type: [String, Number], required: false } },
  setup(props) {
    const route = useRoute()
    const mangaIdVal = computed(() => props.mangaId ?? route.params.mangaId)

    const pages = ref([])
    const initialPage = ref(1)
    const mangaTitle = ref('Demo Manga')
    const cover = ref('')
    const description = ref('')
    const rating = ref('0.00')
    const year = ref('')
    const genres = ref([])
    const mainDemography = ref('')
    const statusDisplay = ref(null)
    const altTitles = ref([])
    const synonyms = ref([])

    const chapters = ref([])
    const selectedIndex = ref(0)
    const selectedChapter = computed(() => chapters.value[selectedIndex.value] || null)
    const loading = ref(true)
    const error = ref(null)
    const showAllChapters = ref(false)
    const orderAsc = ref(false)

    const pageSizeDemo = ['/assets/demo/page1.jpg', '/assets/demo/page2.jpg']

    // Cover helpers available for both DEV and PROD
    async function fetchCoverById(apiClient, possibleId) {
      const cid = Number(possibleId)
      if (!cid || Number.isNaN(cid)) return null
      try {
        const r = await apiClient.get(`manga/manga-covers/${cid}/`)
        const obj = r?.data || {}
        return typeof obj.url_imagen === 'string' ? obj.url_imagen : null
      } catch (e) { return null }
    }
    async function fetchCoverForManga(apiClient, mid) {
      if (!mid && mid !== 0) return null
      try {
        const r1 = await apiClient.get('manga/manga-covers/', { params: { manga: mid, vigente: true } })
        const list1 = Array.isArray(r1.data) ? r1.data : (r1.data?.results || [])
        const candidates = list1.filter(c => String(c.manga) === String(mid) && typeof c.url_imagen === 'string')
        if (candidates.length) {
          const pick = candidates[Math.floor(Math.random() * candidates.length)]
          return pick.url_imagen
        }
      } catch (e) {}
      try {
        const rAll = await apiClient.get('manga/manga-covers/', { params: { page_size: 1000, vigente: true } })
        const listAll = Array.isArray(rAll.data) ? rAll.data : (rAll.data?.results || [])
        const forManga = listAll.filter(c => String(c.manga) === String(mid) && typeof c.url_imagen === 'string')
        if (forManga.length) {
          const pick2 = forManga[Math.floor(Math.random() * forManga.length)]
          return pick2.url_imagen
        }
      } catch (e) {}
      return null
    }

    // Caches locales para deduplicar requests de covers (por ID y por manga)
    const _readerCoverIdPromises = new Map()
    const _readerCoverIdResults = new Map()
    const _readerMainCoverPromises = new Map()
    const _readerMainCoverResults = new Map()

    function getCoverByIdCachedClient(apiClient, id) {
      const cid = Number(id)
      if (!cid || Number.isNaN(cid)) return Promise.resolve(null)
      // Usar servicio centralizado: igual cachea en su propio mapa
      return getCoverByIdCached(cid)
    }
    function getMainCoverCachedClient(apiClient, mangaId) {
      const mid = String(mangaId)
      if (!mid) return Promise.resolve(null)
      return getMainCoverCached(mid)
    }

    async function load() {
      loading.value = true
      error.value = null
      try {
        let chs = []
        let apiClient = null
        const isDev = typeof import.meta !== 'undefined' && import.meta.env && import.meta.env.DEV

        // Attempt mock in dev
        let mockLoaded = false
        if (isDev) {
          try {
            const resp = await fetch('/mock/chapters_universal.json')
            if (resp.ok) {
              const data = await resp.json()
              if (data) {
                chs = data
                mockLoaded = Array.isArray(chs) && chs.length > 0
              }
            }
          } catch (e) { /* ignore */ }
        }

        // If mock not loaded (or not dev), use API
        if (!mockLoaded) {
          apiClient = api
          // Cargar manga y capítulos en paralelo
          const [m, chList] = await Promise.all([
            getManga(mangaIdVal.value),
            listChapters({ manga: mangaIdVal.value, page_size: 1000 })
          ])
          const mData = m || {}
          mangaTitle.value = mData.titulo || mData.title || mangaTitle.value
          cover.value = mData.cover || mData.cover_image || mData.url_imagen || cover.value
          description.value = mData.sinopsis || mData.description || description.value
          rating.value = String(mData.puntaje || mData.rating || rating.value)
          year.value = String(mData.anio || mData.year || year.value)
          // Map genres/demography
          const g = mData.generos || mData.genres || mData.tags || []
          genres.value = Array.isArray(g) ? g.map(x => (x.nombre || x.name || x.title || x)).filter(Boolean) : []
          const dem = mData.demografia_display || mData.demografia || mData.demography || ''
          mainDemography.value = typeof dem === 'object' ? (dem.descripcion || dem.name || dem.title) : String(dem || '')
          // Status mapping
          const estado = mData.estado_display || mData.estado || mData.status || ''
          const estadoStr = typeof estado === 'object' ? (estado.descripcion || estado.name || estado.title) : String(estado || '')
          if (estadoStr) statusDisplay.value = { label: estadoStr, on: /public|ongoing|publicándose|en emisión/i.test(estadoStr) }
          // Alternative titles / synonyms
          const alt = mData.titulos_alternativos || mData.alternative_titles || []
          altTitles.value = Array.isArray(alt) ? alt.map(x => (x.nombre || x.name || x.title || x)).filter(Boolean) : []
          const syn = mData.sinonimos || mData.synonyms || []
          synonyms.value = Array.isArray(syn) ? syn.map(x => (x.nombre || x.name || x.title || x)).filter(Boolean) : []
          if (!cover.value || typeof cover.value !== 'string' || cover.value.trim() === '' || !cover.value.startsWith('http')) {
            const byId = await getCoverByIdCachedClient(apiClient, mData.cover_id || mData.main_cover_id || mData.cover)
            cover.value = byId || (await getMainCoverCachedClient(apiClient, mangaIdVal.value)) || cover.value
          }
          chs = Array.isArray(chList) ? chList : []
        } else if (mangaIdVal.value && Array.isArray(chs)) {
          chs = chs.filter(c => String(c.manga) === String(mangaIdVal.value))
        }

        // Normalize chapter objects
        chapters.value = chs.map(c => ({
          id: c.id || c.pk || Math.random(),
            title: c.titulo || c.title || `Capítulo ${c.capitulo_numero || c.number || ''}`,
            number: c.capitulo_numero || c.number || '',
            pages: Array.isArray(c.pages) ? c.pages : (c.pages && Array.isArray(c.pages.images) ? c.pages.images : null),
            date: c.date || c.created_at || c.actualizado_en || c.creado_en || '',
            raw: c
        }))

        if (chapters.value.length > 0) {
          selectedIndex.value = 0
          setPagesFromSelected()
          // If header data missing, derive from first chapter
          if (!mangaTitle.value) mangaTitle.value = chapters.value[0].raw?.manga_titulo || chapters.value[0].raw?.manga_title || mangaTitle.value
          if (!cover.value) {
            const client = apiClient || (await import('@/services/api')).default
            cover.value = (await getMainCoverCachedClient(client, mangaIdVal.value)) || cover.value
          }
        } else {
          pages.value = pageSizeDemo
        }
      } catch (err) {
        console.error('Failed to load chapters', err)
        error.value = err
        pages.value = pageSizeDemo
      } finally {
        loading.value = false
      }
    }

    function setPagesFromSelected() {
      const ch = selectedChapter.value
      if (ch && Array.isArray(ch.pages) && ch.pages.length) {
        pages.value = ch.pages
      } else if (ch && Array.isArray(ch.raw?.pages) && ch.raw.pages.length) {
        const imgs = Array.isArray(ch.raw.pages) ? ch.raw.pages : (ch.raw.pages && Array.isArray(ch.raw.pages.images) ? ch.raw.pages.images : [])
        pages.value = imgs.length ? imgs : pageSizeDemo
      } else {
        pages.value = pageSizeDemo
      }
      initialPage.value = 1
    }

    function selectChapter(idx) {
      selectedIndex.value = idx
      setPagesFromSelected()
    }

    function openChapter(idx) {
      selectChapter(idx)
      const ch = chapters.value[idx]
      try {
        router.push({ name: 'chapter', params: { chapterId: ch.id } })
      } catch (e) {
        // fallback: scroll to reader-frame if route push fails
        const el = document.querySelector('.reader-frame')
        if (el) el.scrollIntoView({ behavior: 'smooth' })
      }
    }

    function prevChapter() {
      if (selectedIndex.value > 0) {
        selectedIndex.value--
        setPagesFromSelected()
      }
    }

    function nextChapter() {
      if (selectedIndex.value < chapters.value.length - 1) {
        selectedIndex.value++
        setPagesFromSelected()
      }
    }

    const visibleChapters = computed(() => {
      const list = orderAsc.value ? [...chapters.value].reverse() : chapters.value
      if (showAllChapters.value) return list
      return list.slice(0, 20)
    })

    function toggleOrder() { orderAsc.value = !orderAsc.value }

    // shareUrl removed (share UI was removed)

    const externalLink = computed(() => '#')
    const uploadLink = computed(() => '#')

    const router = useRouter()

    onMounted(load)

    return {
      pages, initialPage, mangaTitle, cover, description, rating, year,
      chapters, selectedChapter, selectedIndex, loading, error,
      selectChapter, openChapter, prevChapter, nextChapter, visibleChapters,
      showAllChapters, orderAsc, toggleOrder,
      externalLink, uploadLink, genres, mainDemography, statusDisplay, altTitles, synonyms
    }
  }
}
</script>

<style scoped>
.reader-page { padding: 0; color: var(--text-primary); }
.element-header { background: var(--surface-1, #f8f9fa); padding: 20px 0; border-bottom: 1px solid var(--border-color); }
.header-inner .book-type { display:inline-block; padding:6px 10px; background:var(--accent,#2957ba); color:var(--surface-1,#fff); border-radius:3px }
.element-image { margin-top:10px }
.book-thumbnail { width:200px; height:auto; border-radius:4px; box-shadow:0 2px 8px rgba(0,0,0,0.08); border:1px solid rgba(0,0,0,0.04); }
.genre-ribbon .ribbon { display:inline-block; margin-top:8px; padding:6px 12px; background:#e53935; color:#fff; border-radius:4px; font-weight:600 }
.demography-badge .badge-demography { display:inline-block; padding:6px 12px; background:#e53935; color:#fff; border-radius:4px; font-weight:600 }
.element-title { font-size:2.2rem; margin-bottom:10px; color:var(--color-heading); }
.element-description { margin-top:10px; color:var(--text-primary,#444); font-size: 0.95rem; line-height: 1.5; }
.badges .badge { margin-right:6px; background:#2957ba; }
.status-row { display:flex; align-items:center; }
.status-row .status-dot { width:10px; height:10px; border-radius:50%; background:#999; display:inline-block }
.status-row .status-dot.on { background:#2ecc71 }
.chips { display:flex; flex-wrap:wrap; gap:8px }
.chip { background:#1f2a44; color:#fff; padding:6px 10px; border-radius:16px; font-size:.9rem }
.chapters-list .list-group-item { cursor: default }
.sticky-top { position: sticky; top:12px }

/* Ensure buttons follow theme where possible */
.header-actions .btn { background:var(--accent); color:var(--surface-1); }

/* Make the element-body use the theme surface so it doesn't stay dark in light mode */
.element-body { background: var(--surface-1, var(--color-background)); color: var(--text-primary); }
/* icon alignment for upload button */
.icon { vertical-align: text-bottom; }

.loading-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px 20px;
}

.loading-icon {
  width: 48px;
  height: 48px;
  margin-bottom: 12px;
}

/* Center the reader image container and its image */
:deep(.page-viewer) {
  display: flex;
  justify-content: center;
  align-items: center;
  width: 100%;
}

:deep(.page-viewer img) {
  max-width: 100%;
  height: auto;
  object-fit: contain;
}

/* Libreta: dos páginas lado a lado */


@media (max-width: 767px) {
  .book-thumbnail { width:140px }
  .element-title { font-size:1.6rem }
  .element-description { font-size: 0.9rem; }
}
</style>
