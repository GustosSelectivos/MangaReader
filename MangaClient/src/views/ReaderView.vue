<template>
  <div class="reader-page">
    <header class="element-header manga">
      <div class="container header-inner">
        <div class="row align-items-start">
          <div class="col-12 col-md-3 text-center">
            <h4 class="book-type">MANGA</h4>
            <div class="element-image my-2">
              <img class="book-thumbnail" :src="cover" alt="cover" loading="lazy" decoding="async" fetchpriority="high" />
            </div>
            <h1 class="element-title">{{ mangaTitle }} <small v-if="year">( {{ year }} )</small></h1>
            <h2 class="element-subtitle">{{ mangaTitle }}</h2>
            <p class="element-description">{{ description }}</p>
            <!-- external link removed per request -->
            <div class="badges">
              <span class="badge badge-primary" v-for="g in genres" :key="g">{{ g }}</span>
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
            const resp = await api.get('/mock/chapters_universal.json')
            const data = resp?.data
            if (data) {
              chs = data
              mockLoaded = Array.isArray(chs) && chs.length > 0
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
          if (!cover.value || typeof cover.value !== 'string' || cover.value.trim() === '' || !cover.value.startsWith('http')) {
            const byId = await fetchCoverById(apiClient, mData.cover_id || mData.main_cover_id || mData.cover)
            cover.value = byId || (await fetchCoverForManga(apiClient, mangaIdVal.value)) || cover.value
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
            cover.value = (await fetchCoverForManga(client, mangaIdVal.value)) || cover.value
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
      externalLink, uploadLink, genres: []
    }
  }
}
</script>

<style scoped>
.reader-page { padding: 0; color: var(--text-primary); }
.element-header { background: var(--surface-1, #f8f9fa); padding: 12px 0; border-bottom: 1px solid var(--border-color); }
.header-inner .book-type { display:inline-block; padding:6px 10px; background:var(--accent,#2957ba); color:var(--surface-1,#fff); border-radius:3px }
.element-image { margin-top:10px }
.book-thumbnail { width:160px; height:auto; border-radius:4px; box-shadow:0 2px 8px rgba(0,0,0,0.08); border:1px solid rgba(0,0,0,0.04); }
.element-title { font-size:1.6rem; margin-bottom:6px; color:var(--color-heading); }
.element-description { margin-top:8px; color:var(--text-primary,#444); }
.badges .badge { margin-right:6px }
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
  .book-thumbnail { width:120px }
}
</style>
