<template>
  <div class="manga-reader" ref="rootRef">
    <ReaderToolbar
        :title="title"
        :chapter="currentChapter"
        @prev="goPrevChapter"
        @next="goNextChapter"
      >
        <template #actions>
          <span class="badge bg-warning text-dark me-2" v-if="true">Dir: {{ direction }} | RTL: {{ isRTL }}</span>
          <div class="view-mode-toggle btn-group btn-group-sm" role="group">
            <button :class="['btn','btn-sm','d-flex','align-items-center', viewMode === 'paginated' ? 'btn-primary' : 'btn-outline-secondary']" @click="setView('paginated')">
              <svg class="icon" xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 16 16" fill="currentColor" aria-hidden="true"><path d="M2 3h9v7H2zM5 6h9v7H5z"/></svg>
              <span class="btn-label">Paginado</span>
            </button>
            <button :class="['btn','btn-sm','d-flex','align-items-center', viewMode === 'cascade' ? 'btn-primary' : 'btn-outline-secondary']" @click="setView('cascade')">
              <svg class="icon" xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 16 16" fill="currentColor" aria-hidden="true"><path d="M2 3h12v2H2zM2 7h12v2H2zM2 11h12v2H2z"/></svg>
              <span class="btn-label">Cascada</span>
            </button>
            <button :class="['btn','btn-sm','d-flex','align-items-center','d-none','d-sm-inline-flex', viewMode === 'libreta' ? 'btn-primary' : 'btn-outline-secondary']" @click="setView('libreta')">
              <svg class="icon" xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 16 16" fill="currentColor" aria-hidden="true"><path d="M2 3h6v10H2zM8 3h6v10H8z"/></svg>
              <span class="btn-label">Libreta</span>
            </button>
          </div>
          <div class="ms-2 d-inline-block">
            <button class="btn btn-outline-secondary btn-sm d-flex align-items-center" :title="viewerGap === 'compact' ? 'Espaciado normal' : 'Quitar espacios entre imágenes'" @click="toggleViewerGap">
              <span v-if="viewerGap === 'compact'">🔲</span>
              <span v-else>⬛</span>
            </button>
          </div>
        </template>
      </ReaderToolbar>

      <div class="reader-content">
        <div v-if="viewMode === 'paginated'" class="single-page-view" ref="singlePageRef">
          <div class="click-zone" @pointerdown.prevent="onSinglePointer" role="button" tabindex="0">
            <PageViewer :image="pages[currentPage - 1]" :fitMode="fitMode" :noMaxHeight="true" />
          </div>

          <!-- Controles combinados: capítulo y página en paginado -->
          <div class="page-controls-wrapper d-flex justify-content-between align-items-center" :class="{ 'flex-row-reverse': isRTL }">
            <div class="d-flex gap-2 align-items-center" :class="{ 'flex-row-reverse': isRTL }">
              <button class="btn btn-outline-secondary btn-sm d-flex align-items-center" :class="{ 'flex-row-reverse': isRTL }" @click="goPrevChapter">
                <svg class="icon" :class="{ 'rtl-flip': isRTL }" xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 16 16" fill="currentColor" aria-hidden="true"><path d="M9.5 14L3.5 8l6-6v12zM14 14L8 8l6-6v12z"/></svg>
                <span class="btn-label">Anterior capítulo</span>
              </button>
              <button class="btn btn-primary btn-sm d-flex align-items-center" :class="{ 'flex-row-reverse': isRTL }" @click="prevPage">
                <svg class="icon" :class="{ 'rtl-flip': isRTL }" xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 16 16" fill="currentColor" aria-hidden="true"><path d="M11 14L5 8l6-6v12z"/></svg>
                <span class="btn-label">Anterior página</span>
              </button>
            </div>
            <NavigationControls
              :page="currentPage"
              :total="pages.length"
              :hideButtons="true"
              @go="goToPage"
            />
            <div class="d-flex gap-2 align-items-center" :class="{ 'flex-row-reverse': isRTL }">
              <button class="btn btn-primary btn-sm d-flex align-items-center" :class="{ 'flex-row-reverse': isRTL }" @click="nextPage">
                <span class="btn-label">Siguiente página</span>
                <svg class="icon" :class="{ 'rtl-flip': isRTL }" xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 16 16" fill="currentColor" aria-hidden="true"><path d="M5 2l6 6-6 6V2z"/></svg>
              </button>
              <button class="btn btn-outline-secondary btn-sm d-flex align-items-center" :class="{ 'flex-row-reverse': isRTL }" @click="goNextChapter">
                <span class="btn-label">Siguiente capítulo</span>
                <svg class="icon" :class="{ 'rtl-flip': isRTL }" xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 16 16" fill="currentColor" aria-hidden="true"><path d="M6.5 2l6 6-6 6V2zM2 2l6 6-6 6V2z"/></svg>
              </button>
            </div>
          </div>
        </div>

        <div v-else-if="viewMode === 'cascade'" class="cascade-view">
          <div v-for="(p, i) in pages" :key="i" class="cascade-page" :ref="el => setCascadePageRef(el, i)">
            <!-- Windowed loading: Only pass URL if index is within the allowed limit -->
            <PageViewer 
              :image="i < cascadeLimit ? p : null" 
              :fitMode="'contain'" 
              :noMaxHeight="true" 
              @load="onPageLoaded(i)"
            />
          </div>
          <div class="cascade-controls-bar d-flex justify-content-between align-items-center mt-3" :class="{ 'flex-row-reverse': isRTL }">
            <div>
              <button class="btn btn-outline-secondary btn-sm d-flex align-items-center" :class="{ 'flex-row-reverse': isRTL }" @click="goPrevChapter">
                <svg class="icon" :class="{ 'rtl-flip': isRTL }" xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 16 16" fill="currentColor" aria-hidden="true"><path d="M9.5 14L3.5 8l6-6v12zM14 14L8 8l6-6v12z"/></svg>
                <span class="btn-label">Anterior capítulo</span>
              </button>
            </div>
            <div>
              <button class="btn btn-outline-secondary btn-sm d-flex align-items-center" :class="{ 'flex-row-reverse': isRTL }" @click="goNextChapter">
                <span class="btn-label">Siguiente capítulo</span>
                <svg class="icon" :class="{ 'rtl-flip': isRTL }" xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 16 16" fill="currentColor" aria-hidden="true"><path d="M6.5 2l6 6-6 6V2zM2 2l6 6-6 6V2z"/></svg>
              </button>
            </div>
          </div>
        </div>

        <!-- Libreta mode: show current pair only, reuse page-controls-wrapper -->
        <div v-else class="libreta-view">
          <div class="libreta-pair card p-2 mb-3">
            <div class="page-viewer libreta-pair-inner" :class="libretaContainerClass" v-if="currentPair.length" @pointerdown.prevent="onLibretaPointer">
                <PageViewer v-for="(item, i) in currentPair" :key="(item.url || '') + i" :image="item.url || item" :fitMode="'contain'" :noMaxHeight="true" :class="[getLibretaClass(item)]" />
            </div>
          </div>
          <div class="page-controls-wrapper d-flex justify-content-between align-items-center" :class="{ 'flex-row-reverse': isRTL }">
            <div class="d-flex gap-2 align-items-center" :class="{ 'flex-row-reverse': isRTL }">
              <button class="btn btn-outline-secondary btn-sm d-flex align-items-center" :class="{ 'flex-row-reverse': isRTL }" @click="goPrevChapter">
                <svg class="icon" :class="{ 'rtl-flip': isRTL }" xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 16 16" fill="currentColor" aria-hidden="true"><path d="M9.5 14L3.5 8l6-6v12zM14 14L8 8l6-6v12z"/></svg>
                <span class="btn-label">Anterior capítulo</span>
              </button>
              <button class="btn btn-primary btn-sm d-flex align-items-center" :class="{ 'flex-row-reverse': isRTL }" @click="prevPair" :disabled="pairIndex === 0">
                <svg class="icon" :class="{ 'rtl-flip': isRTL }" xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 16 16" fill="currentColor" aria-hidden="true"><path d="M11 14L5 8l6-6v12z"/></svg>
                <span class="btn-label">Anterior página</span>
              </button>
            </div>
            <NavigationControls
              :page="pairIndex + 1"
              :total="pairedPages.length"
              :hideButtons="true"
              @go="goToPair"
            />
            <div class="d-flex gap-2 align-items-center" :class="{ 'flex-row-reverse': isRTL }">
              <button class="btn btn-primary btn-sm d-flex align-items-center" :class="{ 'flex-row-reverse': isRTL }" @click="nextPair" :disabled="pairIndex >= pairedPages.length - 1">
                <span class="btn-label">Siguiente página</span>
                <svg class="icon" :class="{ 'rtl-flip': isRTL }" xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 16 16" fill="currentColor" aria-hidden="true"><path d="M5 2l6 6-6 6V2z"/></svg>
              </button>
              <button class="btn btn-outline-secondary btn-sm d-flex align-items-center" :class="{ 'flex-row-reverse': isRTL }" @click="goNextChapter">
                <span class="btn-label">Siguiente capítulo</span>
                <svg class="icon" :class="{ 'rtl-flip': isRTL }" xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 16 16" fill="currentColor" aria-hidden="true"><path d="M6.5 2l6 6-6 6V2zM2 2l6 6-6 6V2z"/></svg>
              </button>
            </div>
          </div>
        </div>

        

        <!-- ThumbnailStrip removed: thumbnails hidden by default to avoid long strip -->
      </div>
        <!-- chapter-end-actions removed per request -->
  </div>
</template>

<script>
import { ref, computed, watch, onMounted, onBeforeUnmount, nextTick } from 'vue'
import PageViewer from './PageViewer.vue'
import NavigationControls from './NavigationControls.vue'
// ThumbnailStrip intentionally removed to avoid long thumbnail strip in reader
import ReaderToolbar from './ReaderToolbar.vue'

export default {
  name: 'MangaReader',
  components: { PageViewer, NavigationControls, ReaderToolbar },
  props: {
    pages: { type: Array, required: true },
    initialPage: { type: Number, default: 1 },
    title: { type: String, default: '' },
    chapter: { type: Object, default: null },
    direction: { type: String, default: 'rtl' } // 'rtl' (manga) or 'ltr' (comic)
  },
  setup(props, { emit }) {
    const currentPage = ref(props.initialPage)
    const fitMode = ref('contain')
    const viewMode = ref('paginated')
    const pairIndex = ref(0)
    const rootRef = ref(null)
    const swipeStartX = ref(null)
    const SWIPE_THRESHOLD = 40
    const orientationMap = ref({}) // url -> 'landscape'|'portrait'
    const currentChapter = computed(() => props.chapter)
    const singlePageRef = ref(null)
    const viewerGap = ref('spacious')
    const cascadePageEls = ref([])
    const preloadedSet = new Set()

    const isRTL = computed(() => props.direction === 'rtl')

    // Cascade Window Logic
    const CASCADE_PRELOAD_SIZE = 5
    const cascadeLimit = ref(CASCADE_PRELOAD_SIZE)

    function onPageLoaded(index) {
      // "Sequential with parallel buffer": 
      // Ensure that for every loaded page 'i', we unlock up to 'i + 1 + buffer'
      // effectively maintaining a sliding window ahead of the completed pages.
      cascadeLimit.value = Math.max(cascadeLimit.value, index + 1 + CASCADE_PRELOAD_SIZE)
    }

    watch(() => props.initialPage, (v) => { currentPage.value = v })
    watch(currentPage, () => preloadUpcoming())
    watch(() => props.pages, () => { 
      cascadeLimit.value = CASCADE_PRELOAD_SIZE // Reset window
      preloadUpcoming(); 
      ensureOrientations() 
    }, { deep: true })

    onMounted(() => {
      // ... existing onMounted code ...
      try {
        const saved = localStorage.getItem('viewer-mode')
        if (saved === 'cascade' || saved === 'paginated' || saved === 'libreta') viewMode.value = saved
      } catch (e) {}
      // Listen for external changes to viewer-mode (from NavBar)
      function onViewerMode(e) {
        const v = (e && e.detail) || null
        if (v === 'cascade' || v === 'paginated' || v === 'libreta') viewMode.value = v
        if (viewMode.value === 'libreta') { pairIndex.value = 0; ensureOrientations() }
      }
      window.addEventListener('viewer-mode', onViewerMode)
      // Keep a reference so we can remove it later
      window.__onViewerMode = onViewerMode
      // Initialize viewer gap from localStorage and apply class
      try {
        const savedGap = localStorage.getItem('viewer-gap')
        if (savedGap === 'compact' || savedGap === 'spacious') viewerGap.value = savedGap
      } catch (e) {}
      applyViewerGapClass()
      // Precalcular orientaciones al montar
      ensureOrientations()

      // Keyboard navigation (left/right)
      function onKeyDown(e) {
        if (e.key === 'ArrowLeft') {
          if (viewMode.value === 'libreta') prevPair()
          else prevPage()
        } else if (e.key === 'ArrowRight') {
          if (viewMode.value === 'libreta') nextPair()
          else nextPage()
        }
      }
      window.addEventListener('keydown', onKeyDown)
      window.__manga_onKeyDown = onKeyDown

      // Swipe handling on rootRef
      nextTick(() => {
        try {
          const root = rootRef.value
          if (!root) return
          const onPointerDownGlobal = (ev) => {
            try { swipeStartX.value = ev.clientX !== undefined ? ev.clientX : (ev.touches && ev.touches[0] && ev.touches[0].clientX) } catch (e) { swipeStartX.value = null }
          }
          const onPointerUpGlobal = (ev) => {
            try {
              const endX = ev.clientX !== undefined ? ev.clientX : (ev.changedTouches && ev.changedTouches[0] && ev.changedTouches[0].clientX)
              if (swipeStartX.value == null || endX == null) { swipeStartX.value = null; return }
              const delta = endX - swipeStartX.value
              swipeStartX.value = null
              if (Math.abs(delta) < SWIPE_THRESHOLD) return
              if (delta > 0) {
                // swipe right -> go previous
                if (viewMode.value === 'libreta') prevPair()
                else prevPage()
              } else {
                // swipe left -> go next
                if (viewMode.value === 'libreta') nextPair()
                else nextPage()
              }
            } catch (e) { swipeStartX.value = null }
          }
          root.__onPointerDown = onPointerDownGlobal
          root.__onPointerUp = onPointerUpGlobal
          root.addEventListener('pointerdown', onPointerDownGlobal)
          root.addEventListener('pointerup', onPointerUpGlobal)
          // touch fallback
          root.addEventListener('touchstart', onPointerDownGlobal)
          root.addEventListener('touchend', onPointerUpGlobal)
        } catch (e) {}
      })
    })

    onBeforeUnmount(() => {
      // ... existing onBeforeUnmount code ...
      const fn = window.__onViewerMode
      if (fn) window.removeEventListener('viewer-mode', fn)
      try {
        const k = window.__manga_onKeyDown
        if (k) window.removeEventListener('keydown', k)
      } catch (e) {}
      try {
        const root = rootRef.value
        if (root) {
          if (root.__onPointerDown) root.removeEventListener('pointerdown', root.__onPointerDown)
          if (root.__onPointerUp) root.removeEventListener('pointerup', root.__onPointerUp)
          try { root.removeEventListener('touchstart', root.__onPointerDown) } catch (e) {}
          try { root.removeEventListener('touchend', root.__onPointerUp) } catch (e) {}
        }
      } catch (e) {}
    })

    function setView(mode) {
      viewMode.value = (mode === 'cascade' || mode === 'libreta') ? mode : 'paginated'
      try { localStorage.setItem('viewer-mode', viewMode.value) } catch (e) {}
      // Al cambiar a paginado intenta precargar próximas páginas
      if (viewMode.value === 'paginated') preloadUpcoming()
      if (viewMode.value === 'libreta') { pairIndex.value = 0; ensureOrientations() }
    }

    async function scrollToSinglePageTop() {
      try {
        const el = singlePageRef.value
        if (!el) return
        const header = document.querySelector('.main-header')
        const offset = (header && header.offsetHeight) ? header.offsetHeight : 0
        const rect = el.getBoundingClientRect()
        const top = window.scrollY + rect.top - offset - 8
        window.scrollTo({ top, behavior: 'smooth' })
      } catch (e) {}
    }

    function shouldScroll() { return viewMode.value === 'paginated' }

    async function prevPage() {
      if (currentPage.value > 1) {
        currentPage.value--
        if (shouldScroll()) await nextTick().then(scrollToSinglePageTop)
      }
    }
    async function nextPage() {
      if (currentPage.value < props.pages.length) {
        currentPage.value++
        if (shouldScroll()) await nextTick().then(scrollToSinglePageTop)
      }
    }
    async function goToPage(page) {
      if (page >= 1 && page <= props.pages.length) {
        currentPage.value = page
        if (shouldScroll()) await nextTick().then(scrollToSinglePageTop)
      }
    }
    function goPrevChapter() { emit('prev-chapter') }
    function goNextChapter() { emit('next-chapter') }

    function setCascadePageRef(el, idx) {
      if (!el) return
      cascadePageEls.value[idx] = el
    }
    function getCurrentCascadeIndex() {
      const els = cascadePageEls.value || []
      if (!els.length) return 0
      let bestIdx = 0
      let bestDist = Number.POSITIVE_INFINITY
      const target = 100 // pixels from top as reference
      for (let i = 0; i < els.length; i++) {
        const rect = els[i].getBoundingClientRect()
        const dist = Math.abs(rect.top - target)
        if (dist < bestDist) { bestDist = dist; bestIdx = i }
      }
      return bestIdx
    }
    function scrollToCascadeIndex(idx) {
      const els = cascadePageEls.value || []
      if (idx < 0 || idx >= els.length) return
      try { els[idx].scrollIntoView({ behavior: 'smooth', block: 'start' }) } catch (e) {}
    }
    function prevPageCascade() {
      const i = getCurrentCascadeIndex()
      if (i > 0) scrollToCascadeIndex(i - 1)
    }
    function nextPageCascade() {
      const i = getCurrentCascadeIndex()
      const els = cascadePageEls.value || []
      if (i < els.length - 1) scrollToCascadeIndex(i + 1)
    }

    // Handle pointer/click on single paginated view: left -> prev, right -> next
    function onSinglePointer(e) {
      try {
        const el = singlePageRef.value
        if (!el) return
        const rect = el.getBoundingClientRect()
        const clientX = (e.clientX !== undefined) ? e.clientX : (e.touches && e.touches[0] && e.touches[0].clientX)
        if (clientX === undefined) return
        const rel = (clientX - rect.left) / rect.width
        if (rel < 0.5) prevPage()
        else nextPage()
      } catch (err) {}
    }

    // Handle pointer/click on libreta pair container: left -> prevPair, right -> nextPair
    function onLibretaPointer(e) {
      try {
        // use the currentTarget to ensure we're measuring the container
        const container = e.currentTarget || e.target
        const rect = container.getBoundingClientRect()
        const clientX = (e.clientX !== undefined) ? e.clientX : (e.touches && e.touches[0] && e.touches[0].clientX)
        if (clientX === undefined) return
        const rel = (clientX - rect.left) / rect.width
        if (rel < 0.5) prevPair()
        else nextPair()
      } catch (err) {}
    }

    function applyViewerGapClass() {
      try {
        if (viewerGap.value === 'compact') document.documentElement.classList.add('viewer-gap-compact')
        else document.documentElement.classList.remove('viewer-gap-compact')
      } catch (e) {}
    }
    function toggleViewerGap() {
      viewerGap.value = viewerGap.value === 'compact' ? 'spacious' : 'compact'
      try { localStorage.setItem('viewer-gap', viewerGap.value) } catch (e) {}
      applyViewerGapClass()
      try { window.dispatchEvent(new CustomEvent('viewer-gap', { detail: viewerGap.value })) } catch (e) {}
    }

    function preloadUpcoming() {
      if (viewMode.value !== 'paginated') return
      const baseIndex = currentPage.value - 1
      for (let offset = 1; offset <= 2; offset++) {
        const target = props.pages[baseIndex + offset]
        if (!target || preloadedSet.has(target)) continue
        try {
          const img = new Image()
          img.src = target
          preloadedSet.add(target)
        } catch (e) {}
      }
    }

    function preloadLibreta() {
      if (viewMode.value !== 'libreta') return
      const pairs = pairedPages.value || []
      const idx = pairIndex.value
      const toPreload = []
      const addUrls = (pair) => {
        if (!Array.isArray(pair)) return
        pair.forEach(item => {
          const url = item?.url || item
          if (typeof url === 'string' && !preloadedSet.has(url)) toPreload.push(url)
        })
      }
      // preload next two pairs
      addUrls(pairs[idx + 1])
      addUrls(pairs[idx + 2])
      // keep previous pair preloaded for smooth back navigation
      addUrls(pairs[idx - 1])
      toPreload.forEach(url => {
        try { const img = new Image(); img.src = url; preloadedSet.add(url) } catch (e) {}
      })
    }

    onMounted(() => { preloadUpcoming(); preloadLibreta() })

    function ensureOrientations() {
      const arr = props.pages || []
      arr.forEach(url => {
        if (orientationMap.value[url]) return
        try {
          const img = new Image()
          img.onload = () => {
            orientationMap.value[url] = (img.naturalWidth > img.naturalHeight) ? 'landscape' : 'portrait'
          }
          img.src = url
        } catch (e) {}
      })
    }

    function pageNum(url) {
      if (typeof url !== 'string') return null
      const m = url.match(/\/([0-9]{3})\.webp(?:$|\?)/)
      return m ? Number(m[1]) : null
    }

    const pairedPages = computed(() => {
      const arr = props.pages || []
      const out = []
      let i = 0
      // rightIsOdd: when true -> odd goes to right, even to left (default for RTL/Manga)
      // when false -> even goes to right, odd to left (flipped for LTR/Comic)
      let rightIsOdd = (props.direction !== 'ltr')
      while (i < arr.length) {
        const aUrl = arr[i]
        const aOri = orientationMap.value[aUrl]
        const aNum = pageNum(aUrl)
        if (aOri === 'landscape') {
          // Single, set ordering rule for next pair based on parity of this landscape page
          // Decide alignment side for single based on current rule and parity
          let side = 'right'
          if (typeof aNum === 'number') {
            if (rightIsOdd) {
              side = (aNum % 2 === 1) ? 'right' : 'left'
            } else {
              side = (aNum % 2 === 0) ? 'right' : 'left'
            }
          }
          out.push([{ url: aUrl, pageNum: aNum, side }])
          if (typeof aNum === 'number') {
            rightIsOdd = (aNum % 2 === 0) ? true : false
          }
          i += 1
          continue
        }
        const bUrl = arr[i + 1]
        const bOri = bUrl ? orientationMap.value[bUrl] : null
        const bNum = bUrl ? pageNum(bUrl) : null
        if (bUrl && bOri !== 'landscape') {
          let left = { url: aUrl, pageNum: aNum }
          let right = bUrl ? { url: bUrl, pageNum: bNum } : null
          if (aNum != null && bNum != null) {
            // Decide placement based on current rule (rightIsOdd)
            const oddCandidate = (aNum % 2 === 1) ? left : right
            const evenCandidate = (aNum % 2 === 0) ? left : right
            if (rightIsOdd) {
              // odd to right, even to left
              left = { ...(evenCandidate || {}), side: 'left' }
              right = { ...(oddCandidate || {}), side: 'right' }
            } else {
              // even to right, odd to left (flipped)
              left = { ...(oddCandidate || {}), side: 'left' }
              right = { ...(evenCandidate || {}), side: 'right' }
            }
          }
          out.push([left, right].filter(Boolean))
          i += 2
        } else {
          // Only one page (or next is landscape). Single portrait.
          // Decide side similarly for single portrait based on current rule
          let side = 'right'
          if (typeof aNum === 'number') {
            if (rightIsOdd) {
              side = (aNum % 2 === 1) ? 'right' : 'left'
            } else {
              side = (aNum % 2 === 0) ? 'right' : 'left'
            }
          }
          out.push([{ url: aUrl, pageNum: aNum, side }])
          i += 1
        }
      }
      return out
    })
    const currentPair = computed(() => pairedPages.value[pairIndex.value] || [])
    function prevPair() { if (pairIndex.value > 0) pairIndex.value-- }
    function nextPair() { if (pairIndex.value < pairedPages.value.length - 1) pairIndex.value++ }
    function goToPair(n) {
      const idx = Number(n) - 1
      if (idx >= 0 && idx < pairedPages.value.length) pairIndex.value = idx
    }

    function extractPageNumberFromUrl(url) {
      if (typeof url !== 'string') return null
      const m = url.match(/\/([0-9]{3})\.webp(?:$|\?)/)
      return m ? Number(m[1]) : null
    }
    function getLibretaClass(item) {
      // Prefer explicit side if provided by pairing logic
      const side = item && item.side
      if (side === 'left') return 'libreta-left'
      if (side === 'right') return 'libreta-right'
      // Fallback: derive from parity (default rule)
      const num = item && typeof item.pageNum === 'number' ? item.pageNum : extractPageNumberFromUrl(item && item.url ? item.url : item)
      if (!num) return 'libreta-right'
      return num % 2 === 0 ? 'libreta-left' : 'libreta-right'
    }

    const libretaContainerClass = computed(() => {
      const pair = currentPair.value
      if (!pair || pair.length === 0) return ''
      if (pair.length === 1) {
        const item = pair[0]
        const cls = getLibretaClass(item)
        // single-left/right decides alignment
        return {
          single: true,
          'single-left': cls === 'libreta-left',
          'single-right': cls === 'libreta-right'
        }
      }
      return {}
    })

    // React to pair changes and pages changes to preload libreta neighbors
    watch(pairIndex, () => preloadLibreta())
    watch(pairedPages, () => preloadLibreta())

    return { currentPage, fitMode, prevPage, nextPage, goToPage, currentChapter, goPrevChapter, goNextChapter, viewMode, setView, singlePageRef, viewerGap, toggleViewerGap, setCascadePageRef, prevPageCascade, nextPageCascade, pairedPages, currentPair, pairIndex, prevPair, nextPair, goToPair, getLibretaClass, libretaContainerClass, onSinglePointer, onLibretaPointer, isRTL, cascadeLimit, onPageLoaded }
  }
}
</script>

<style scoped>
.manga-reader { display:flex; flex-direction:column; gap:12px }
.reader-content { display:flex; gap:16px; align-items:flex-start; justify-content:center }
.cascade-view { display:flex; flex-direction:column; gap:18px }
.cascade-page .page-viewer { background: transparent; display:flex; justify-content:center; align-items:center }
.single-page-view { width:100% }

.page-controls-wrapper { display:flex; justify-content:space-between; margin-top:8px; flex-wrap: nowrap; gap:8px }

.cascade-controls-bar { padding: 8px 0 }
 
/* Mobile responsiveness */
@media (max-width: 576px) {
  .reader-content { flex-direction: column }
  .page-controls-wrapper { overflow-x: auto; -webkit-overflow-scrolling: touch }
  .cascade-controls-bar { flex-direction: column; gap: 8px }
  .btn-label { display: none }
}
.icon { vertical-align: text-bottom; margin: 0 2px }

/* Libreta styles */
.libreta-view { display:flex; flex-direction:column; gap:12px }
.libreta-controls { padding: 4px 0 }
.libreta-pair-inner { display:flex; justify-content:center; align-items:center; gap:12px; flex-wrap: nowrap }
.libreta-pair-inner .page-viewer { flex:1; display:flex; justify-content:center; align-items:center }
.libreta-pair-inner img { width:100%; height:auto; object-fit:contain }
/* Clickable zones for quick left/right navigation */
.click-zone { cursor: pointer; display: block }
.click-zone:active { opacity: 0.98 }
/* Align even pages (left) and odd pages (right) within the pair */
.libreta-left { order: 0 }
.libreta-right { order: 1 }
/* Center single image nicely */
.libreta-pair-inner.single { justify-content: center }
.libreta-pair-inner.single .page-viewer { max-width: 900px }
.libreta-pair-inner.single-left { justify-content: flex-start }
.libreta-pair-inner.single-right { justify-content: flex-end }


.rtl-flip { transform: scaleX(-1); }
</style>
