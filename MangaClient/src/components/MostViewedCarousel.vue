<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { toCdnUrl } from '@/utils/cdn'

const props = defineProps({
  items: {
    type: Array,
    default: () => []
  }
})

const containerRef = ref(null)
const isPaused = ref(false)
let animationId = null
let scrollPos = 0
const speed = 0.5 // Pixels per frame

function animate() {
  if (!isPaused.value && containerRef.value) {
    scrollPos += speed
    if (scrollPos >= containerRef.value.scrollWidth / 2) {
      scrollPos = 0
    }
    containerRef.value.scrollLeft = scrollPos
  }
  animationId = requestAnimationFrame(animate)
}

onMounted(() => {
  // Clone items to create infinite loop effect if needed or just handle scroll reset
  // For simple infinite scroll, we might need to duplicate content in template or JS
  // A simple CSS animation might be smoother, but JS gives precise pause control.
  // Let's stick to the requestAnimationFrame for now, but ensure we have enough content to scroll.
  animationId = requestAnimationFrame(animate)
})

onUnmounted(() => {
  if (animationId) cancelAnimationFrame(animationId)
})

function pause() {
  isPaused.value = true
}

function resume() {
  isPaused.value = false
}
</script>

<template>
  <div class="carousel-wrapper" @mouseenter="pause" @mouseleave="resume">
    <div class="carousel-track" ref="containerRef">
      <!-- Duplicate items for seamless loop -->
      <div v-for="(item, index) in [...items, ...items]" :key="index + '-' + item.id" class="carousel-card">
          <a :href="`/library/manga/${item.id}`" class="card-link">
            <div class="cover-container">
              <img 
                :src="toCdnUrl(item.displayCover || item.cover, { w: 200, q: 80 })" 
                :alt="item.title"
                class="cover-image"
                :loading="index === 0 ? 'eager' : 'lazy'"
                :fetchpriority="index === 0 ? 'high' : 'auto'"
              />
               <div class="hover-overlay">
                  <div class="info-content">
                     <div class="views-badge">
                        <span class="rank-badge">#{{ (index % items.length) + 1 }}</span> <i class="fas fa-eye"></i> {{ item.vistas || 0 }}
                     </div>
                     <h4 class="title text-truncate">{{ item.title }}</h4>
                  </div>
               </div>
            </div>
          </a>
      </div>
    </div>
  </div>
</template>

<style scoped>
.carousel-wrapper {
  width: 100%;
  overflow: hidden;
  position: relative;
  padding: 10px 0;
}

.carousel-track {
  display: flex;
  gap: 16px;
  overflow-x: hidden; /* Hide scrollbar */
  white-space: nowrap;
  
  /* Smooth scrolling */
  scroll-behavior: auto;
  
  /* Hide scrollbar completely */
  scrollbar-width: none; /* Firefox */
  -ms-overflow-style: none; /* IE/Edge */
}

.carousel-track::-webkit-scrollbar {
    display: none;
}

.carousel-card {
  flex: 0 0 auto;
  width: 160px;
  height: 240px;
  border-radius: 8px;
  overflow: hidden;
  position: relative;
  transition: transform 0.3s ease;
  cursor: pointer;
}

.carousel-card:hover {
  transform: scale(1.05);
  z-index: 2;
}

.card-link {
    display: block;
    width: 100%;
    height: 100%;
}

.cover-container {
    width: 100%;
    height: 100%;
    position: relative;
    overflow: hidden;
}

.cover-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.hover-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(to top, rgba(0,0,0,0.9), rgba(0,0,0,0.4), transparent);
  opacity: 0;
  transition: opacity 0.3s ease;
  display: flex;
  flex-direction: column;
  justify-content: flex-end;
  padding: 12px;
}

/* On Desktop: Show overlay on hover */
@media (min-width: 768px) {
    .carousel-card:hover .hover-overlay {
        opacity: 1;
    }
}

/* On Mobile: Always visible, but maybe smaller or adjusted */
@media (max-width: 767px) {
    .hover-overlay {
        opacity: 1;
        background: linear-gradient(to top, rgba(0,0,0,0.85) 0%, transparent 100%);
        padding: 8px;
    }
    
    .carousel-card {
        width: 120px;
        height: 180px;
    }
}

.info-content {
    text-align: center;
    width: 100%;
}

.views-badge {
    background: #e91e63; /* Pink/Red accent */
    color: white;
    padding: 4px 10px;
    border-radius: 20px;
    font-size: 0.8rem;
    font-weight: bold;
    display: inline-flex;
    align-items: center;
    gap: 5px;
    margin-bottom: 8px;
    box-shadow: 0 4px 6px rgba(0,0,0,0.3);
}

.rank-badge {
    background: #ffffff;
    color: #e91e63;
    border-radius: 50%;
    width: 20px;
    height: 20px;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    font-size: 0.75rem;
    margin-right: 6px;
    font-weight: 800;
}

.title {
    color: white;
    font-size: 0.95rem;
    margin: 0;
    font-weight: 600;
    text-shadow: 0 2px 4px rgba(0,0,0,0.8);
    white-space: normal; /* Allow wrap if needed or truncate */
    display: -webkit-box;
    -webkit-line-clamp: 2;
    line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
}
</style>
