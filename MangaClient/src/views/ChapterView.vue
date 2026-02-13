<template>
  <div class="chapter-view">
    <h2 class="m-0 text-truncate mb-2">{{ chapter?.title }}</h2>

    

    <MangaReader
      :key="chapter?.id || chapterId"
      :pages="pages"
      :initialPage="1"
      :title="mangaTitle"
      :chapter="chapter"
      :direction="readingDirection"
      @prev-chapter="goPrevChapter"
      @next-chapter="goNextChapter"
    />

    <!-- No floating buttons; end-of-chapter controls live inside MangaReader footer -->
  </div>
</template>

<script setup>
import MangaReader from '../components/MangaReader.vue'
import { ref, onMounted, watch, computed } from 'vue'
import { useRouter } from 'vue-router'
import { getChapter, listChapters } from '@/services/chapterService'
import { getManga, incrementMangaView } from '@/services/mangaService'
import { useMangaUI } from '@/composables/useMangaUI'

const props = defineProps({
  chapterId: { type: [String, Number], required: true }
})

const router = useRouter()
const { originLabel } = useMangaUI()
const pages = ref([])
const chapter = ref(null)
const mangaTitle = ref('')
const loading = ref(false)
const chaptersList = ref([])
const prevChapterId = ref(null)
const nextChapterId = ref(null)
const mangaOrigin = ref('')

const readingDirection = computed(() => {
  return (mangaOrigin.value === 'Comic') ? 'ltr' : 'rtl'
})

function deriveNeighbors() {
  if (!chapter.value || !chaptersList.value.length) return
  const idx = chaptersList.value.findIndex(c => String(c.id) === String(chapter.value.id))
  prevChapterId.value = idx > 0 ? chaptersList.value[idx - 1].id : null
  nextChapterId.value = idx >= 0 && idx < chaptersList.value.length - 1 ? chaptersList.value[idx + 1].id : null
}

// increment handled by mangaService

async function fetchChapterDetail(id) { return await getChapter(id) }

async function fetchChapterList(params) { return await listChapters(params) }

async function load() {
  loading.value = true
  try {
    if (import.meta?.env?.DEV) {
      const apiClient = (await import('@/services/api')).default
      // No mocks in this snippet logic, keeping original structure
      const list = [] 
      // DEV MOCK LOGIC OMITTED FOR BRIEFNESS AS ORIGINAL HAD EMPTY ARRAY RETURN
      // ...
    } else {
      const data = await fetchChapterDetail(props.chapterId)
      if (data) {
        chapter.value = data
        const imgs = Array.isArray(data.pages) ? data.pages : (data.pages && Array.isArray(data.pages.images) ? data.pages.images : null)
        pages.value = imgs && imgs.length ? imgs : ['/assets/demo/page1.jpg']
        mangaTitle.value = data.manga_titulo || data.manga_title || data.title || ''
        
        // Fetch manga info to determine type/origin for reading direction
        const mid = data.manga || data.manga_id
        if (mid) {
          try {
            const m = await getManga(mid)
            if (m) mangaOrigin.value = originLabel(m)
          } catch (e) {}
          await incrementMangaView(mid)
          chaptersList.value = await fetchChapterList({ manga: mid, page_size: 1000 })
        } else {
            chaptersList.value = []
        }
        deriveNeighbors()
      } else {
        // Fallback or "else" branch
        const list = await fetchChapterList({ page_size: 1000 })
        const found = list.find(c => String(c.id) === String(props.chapterId)) || list[0]
        if (found) {
          chapter.value = found
          const imgs2 = Array.isArray(found.pages) ? found.pages : (found.pages && Array.isArray(found.pages.images) ? found.pages.images : null)
          pages.value = imgs2 && imgs2.length ? imgs2 : ['/assets/demo/page1.jpg']
          mangaTitle.value = found.manga_titulo || found.manga_title || found.title || ''
          
          const mid = found.manga || found.manga_id
          if (mid) {
             try {
                const m = await getManga(mid)
                if (m) mangaOrigin.value = originLabel(m)
             } catch (e) {}
             await incrementMangaView(mid)
             chaptersList.value = await fetchChapterList({ manga: mid, page_size: 1000 })
          }
          deriveNeighbors()
        }
      }
    }
// --- Prefetch Logic ---
        // Load next chapter data silently after a short delay
        if (chaptersList.value.length) {
           setTimeout(() => {
             const idx = chaptersList.value.findIndex(c => String(c.id) === String(props.chapterId))
             if (idx >= 0 && idx < chaptersList.value.length - 1) {
               const nextCh = chaptersList.value[idx + 1]
               console.log(`Prefetching next chapter: ${nextCh.id}`)
               // Prefetch JSON
               getChapter(nextCh.id).then(data => {
                  if (data) {
                    // Optional: Prefetch first 3 images if we really want speed
                    const imgs = Array.isArray(data.pages) ? data.pages : (data.pages && Array.isArray(data.pages.images) ? data.pages.images : [])
                    if (imgs && imgs.length) {
                      const preloadCount = Math.min(imgs.length, 3)
                      for (let i=0; i<preloadCount; i++) {
                         const link = document.createElement('link')
                         link.rel = 'prefetch'
                         link.href = imgs[i]
                         document.head.appendChild(link)
                      }
                    }
                  }
               }).catch(()=>{})
             }
           }, 3000) // Wait 3s so current page renders first
        }
    } catch (err) {
    console.error('Failed to load chapter', err)
  } finally {
    loading.value = false
  }
}

onMounted(load)

// Reload when chapterId changes (navigation via prev/next buttons)
watch(() => props.chapterId, () => {
  // Reset state then load
  chapter.value = null
  pages.value = []
  prevChapterId.value = null
  nextChapterId.value = null
  mangaOrigin.value = ''
  load()
})

function goPrevChapter() {
  if (!prevChapterId.value) return
  router.push({ name: 'chapter', params: { chapterId: prevChapterId.value } })
}
function goNextChapter() {
  if (!nextChapterId.value) return
  router.push({ name: 'chapter', params: { chapterId: nextChapterId.value } })
}

 
</script>

<style scoped>
.chapter-view { padding:12px }
.chapter-header { margin-bottom: 10px; }
.chapter-actions .btn svg { vertical-align: text-bottom; margin: 0 2px; }
.chapter-bottom-actions {
  position: sticky;
  bottom: 10px;
  margin-top: 16px;
  padding: 8px 0;
  background: transparent;
}

.loading-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 400px;
  padding: 40px 0;
}

.loading-icon {
  width: 64px;
  height: 64px;
  margin-bottom: 16px;
}
 
</style>
