<script setup>
import { ref, onMounted } from 'vue'
import api from '@/services/api'

// We will fetch 5 items
const items = ref([])
const currentIndex = ref(0)
const loading = ref(true)

// Fetch data from backend
async function fetchRandom() {
  try {
    const res = await api.get('manga/mangas/random/')
    let raw = res.data
    // Normalize if array is wrapped
    if (raw && !Array.isArray(raw) && raw.results) raw = raw.results
    
    // Process items (minimal processing for display)
    items.value = (raw || []).map(item => ({
       id: item.id,
       title: item.title || item.titulo,
       description: item.sinopsis || item.description || '',
       // Prefer absolute url or cover_url
       image: item.cover_url || item.url_absoluta || item.cover || '/assets/no-cover.jpg',
       // Fallback for demo if no cover
    }))
  } catch (e) {
    console.error("Error loading banner", e)
  } finally {
    loading.value = false
  }
}

function next() {
  currentIndex.value = (currentIndex.value + 1) % items.value.length
}

function prev() {
  currentIndex.value = (currentIndex.value - 1 + items.value.length) % items.value.length
}

function goTo(index) {
  currentIndex.value = index
}

onMounted(() => {
  fetchRandom()
  // Auto slide?
  setInterval(() => {
    if (items.value.length > 1) next()
  }, 8000)
})
</script>

<template>
  <div v-if="loading" class="skeleton-banner"></div>
  
  <div v-else-if="items.length" class="banner-wrapper">
    <div class="banner-inner">
        <!-- Current Item -->
        <div class="slides-container">
            <template v-for="(item, index) in items" :key="item.id">
                <div v-show="index === currentIndex" class="slide-item">
                    <img 
                        :src="item.image" 
                        :alt="item.title" 
                        class="slide-img"
                        :fetchpriority="index === 0 ? 'high' : 'auto'"
                        :loading="index === 0 ? 'eager' : 'lazy'"
                    >
                     <div class="gradient-overlay-h"></div>
                     <div class="gradient-overlay-v"></div>
                </div>
            </template>
        </div>

        <!-- Controls (Moved outside to be relative to full width) -->
        <button @click="prev" class="nav-btn prev-btn" aria-label="Anterior">
            <svg stroke="currentColor" fill="currentColor" stroke-width="0" viewBox="0 0 512 512" width="24" height="24" xmlns="http://www.w3.org/2000/svg"><path fill="none" stroke-linecap="round" stroke-linejoin="round" stroke-width="48" d="M328 112L184 256l144 144"></path></svg>
        </button>
        <button @click="next" class="nav-btn next-btn" aria-label="Siguiente">
            <svg stroke="currentColor" fill="currentColor" stroke-width="0" viewBox="0 0 512 512" width="24" height="24" xmlns="http://www.w3.org/2000/svg"><path fill="none" stroke-linecap="round" stroke-linejoin="round" stroke-width="48" d="M184 112l144 144-144 144"></path></svg>
        </button>
        
        <!-- Indicators -->
        <div class="indicators">
            <button 
                v-for="(item, index) in items" 
                :key="`ind-${item.id}`"
                @click="goTo(index)"
                class="indicator-dot"
                :class="{ active: currentIndex === index }"
                :aria-label="`Ir a diapositiva ${index + 1}`"
            ></button>
        </div>
    </div>
    
    <!-- Text Overlay -->
    <div class="text-content">
        <template v-for="(item, index) in items" :key="`txt-${item.id}`">
             <div v-show="index === currentIndex" class="text-slide animate-fade-in">
                <h2 class="banner-title">{{ item.title }}</h2>
                <div class="banner-desc">
                    {{ item.description }}
                </div>
                <a :href="`/library/manga/${item.id}`" class="btn-action">Ir a la Serie</a>
             </div>
        </template>
    </div>
  </div>
</template>

<style scoped>
/* CSS Implementation replicating the provided Tailwind classes */
.banner-wrapper {
    position: relative;
    background-color: #000;
    width: 100%;
    height: 40vh; /* Default mobile height */
    overflow: hidden;
    margin-bottom: 20px;
    border-radius: 6px;
}

@media (min-width: 1200px) { /* xl breakpoint */
    .banner-wrapper {
        height: 65vh;
        /* margin-top removed to prevent overlap issues */
    }
}

.banner-inner {
    width: 100%;
    height: 100%;
}

.slides-container {
    position: relative;
    width: 100%;
    height: 100%;
}

@media (min-width: 1200px) {
    /* xl:w-3/4 xl:left-1/4 logic from reference */
    .slides-container {
        width: 75%;
        left: 25%;
    }
}

.slide-item {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
}

.slide-img {
    width: 100%;
    height: 100%;
    object-fit: cover;
    transition: opacity 1000ms;
}

/* Gradients */
.gradient-overlay-h {
    position: absolute;
    bottom: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: linear-gradient(to right, black 0%, black 10%, transparent 100%);
}
@media (min-width: 1024px) {
     .gradient-overlay-h {
        background: linear-gradient(to right, black 0%, black 10%, transparent 100%);
     }
}

.gradient-overlay-v {
    position: absolute;
    bottom: 0;
    left: 0;
    width: 100%;
    height: 30vh;
    background: linear-gradient(to top, black, transparent);
}

/* Navigation Buttons */
.nav-btn {
    position: absolute;
    top: 50%;
    transform: translateY(-50%);
    z-index: 20;
    height: 100%;
    padding: 1.5rem; /* Increased for touch target */
    background: transparent;
    border: none;
    color: white; /* Default white */
    cursor: pointer;
    transition: all 0.3s;
}
.nav-btn:hover {
    background-color: rgba(0,0,0,0.5);
    color: white;
}
.prev-btn { left: 0; }
@media (min-width: 1200px) { .prev-btn { left: 0; } }

.next-btn { 
    right: 0; 
    color: black; /* Ref had text-black for next btn? */
    backdrop-filter: blur(4px);
}
.next-btn:hover { color: white; }

/* Indicators */
.indicators {
    position: absolute;
    bottom: 20px; /* bottom-20 approx 80px, reduced for simplicity */
    left: 50%;
    transform: translateX(-50%);
    z-index: 20;
    display: flex;
    gap: 0.5rem;
}
.indicator-dot {
    width: 12px;
    height: 12px;
    border-radius: 50%;
    border: none;
    background-color: rgba(255,255,255,0.5);
    transition: all 0.3s;
    cursor: pointer;
    padding: 6px; /* Touch area padding */
    box-sizing: content-box; /* Ensure padding adds to size for hit area, but keep visual dot small */
    background-clip: content-box; /* Background only inside content box */
}
.indicator-dot:hover { background-color: rgba(255,255,255,0.75); }
.indicator-dot.active {
    background-color: white;
    transform: scale(1.25);
}

/* Text Content */
.text-content {
    position: absolute;
    bottom: 0;
    left: 0;
    z-index: 10;
    display: flex;
    flex-direction: column;
    justify-content: flex-end;
    padding: 1.25rem; /* px-5 */
    padding-bottom: 5rem;
    width: 100%;
    max-width: 36rem; /* max-w-xl */
    pointer-events: none;
}
@media (min-width: 1024px) {
    .text-content { padding-left: 4rem; /* lg:pl-16 */ }
}

.text-slide {
    pointer-events: auto;
    animation: fadeIn 1s ease-in-out;
}

.banner-title {
    color: #f8fafc; /* slate-50 */
    font-size: 2.25rem; /* text-4xl */
    font-weight: 700;
    margin-bottom: 1rem;
    line-height: 1;
    text-shadow: 0 4px 6px rgba(0,0,0,0.5);
}
@media (min-width: 1024px) {
    .banner-title { font-size: 4.5rem; /* lg:text-7xl */ }
}

.banner-desc {
    color: #cbd5e1; /* slate-300 */
    font-size: 1rem;
    line-height: 1.5;
    margin-bottom: 1rem;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
    text-shadow: 0 2px 4px rgba(0,0,0,0.5);
}

.btn-action {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    padding: 0 1.5rem; /* px-4... adjusted */
    height: 2.5rem; /* h-10 */
    background-color: white; /* bg-default (guessing white/light) */
    color: black;
    border-radius: 0.5rem; /* rounded-medium */
    font-weight: 500;
    text-decoration: none;
    transition: all 0.3s;
    width: 50%;
    cursor: pointer;
    border: none;
}
.btn-action:hover {
    opacity: 0.9;
    transform: scale(0.97);
}

.skeleton-banner {
    height: 40vh;
    background: #111;
}

@keyframes fadeIn {
    from { opacity: 0; }
    to { opacity: 1; }
}
</style>
