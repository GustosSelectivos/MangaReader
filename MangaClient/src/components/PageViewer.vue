<template>
  <div class="page-viewer" ref="containerRef">
    <div 
      class="zoom-container"
      :class="{ 'zoomed': scale > 1 }"
      @touchstart="onTouchStart"
      @touchmove="onTouchMove"
      @touchend="onTouchEnd"
      @dblclick="onDoubleTap"
    >
      <img 
        v-if="image" 
        ref="imgRef"
        :src="image" 
        :style="[imgStyle, zoomStyle]" 
        alt="page" 
        loading="lazy" 
        @load="$emit('load', $event)" 
      />
      <div v-else class="empty">
          <span class="spinner-border spinner-border-sm text-secondary" role="status" aria-hidden="true"></span>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'

export default {
  name: 'PageViewer',
  props: {
    image: { type: String, default: null },
    fitMode: { type: String, default: 'contain' },
    noMaxHeight: { type: Boolean, default: false }
  },
  setup(props) {
    const scale = ref(1)
    const translateX = ref(0)
    const translateY = ref(0)
    
    // Zoom state
    const startDistance = ref(0)
    const startScale = ref(1)
    
    // Pan state
    const isDragging = ref(false)
    const lastX = ref(0)
    const lastY = ref(0)
    
    const containerRef = ref(null)
    const imgRef = ref(null)

    const imgStyle = computed(() => {
      const style = { 'max-width': '100%', objectFit: props.fitMode }
      if (props.fitMode === 'cover') style.width = '100%'
      if (props.noMaxHeight) {
        style['max-height'] = 'none'
        style.width = '100%'
      } else {
        style['max-height'] = '80vh'
      }
      return style
    })

    const zoomStyle = computed(() => {
      return {
        transform: `translate(${translateX.value}px, ${translateY.value}px) scale(${scale.value})`,
        transition: isDragging.value ? 'none' : 'transform 0.1s ease-out'
      }
    })

    function getDistance(touches) {
      if (touches.length < 2) return 0
      const dx = touches[0].clientX - touches[1].clientX
      const dy = touches[0].clientY - touches[1].clientY
      return Math.sqrt(dx * dx + dy * dy)
    }

    function onTouchStart(e) {
      if (e.touches.length === 2) {
        // Start Pinch
        isDragging.value = true
        startDistance.value = getDistance(e.touches)
        startScale.value = scale.value
      } else if (e.touches.length === 1 && scale.value > 1) {
        // Start Pan
        isDragging.value = true
        lastX.value = e.touches[0].clientX
        lastY.value = e.touches[0].clientY
      }
    }

    function onTouchMove(e) {
      if (e.touches.length === 2) {
        // Pinching
        e.preventDefault() // Prevent page zoom/scroll
        const dist = getDistance(e.touches)
        if (startDistance.value > 0) {
          const newScale = startScale.value * (dist / startDistance.value)
          scale.value = Math.min(Math.max(1, newScale), 4) // Clamp 1x - 4x
        }
      } else if (e.touches.length === 1 && scale.value > 1 && isDragging.value) {
        // Panning
        e.preventDefault()
        const deltaX = e.touches[0].clientX - lastX.value
        const deltaY = e.touches[0].clientY - lastY.value
        translateX.value += deltaX
        translateY.value += deltaY
        lastX.value = e.touches[0].clientX
        lastY.value = e.touches[0].clientY
      }
    }

    function onTouchEnd(e) {
      if (e.touches.length < 2) {
        // End interaction
        isDragging.value = false
        if (scale.value < 1.1) {
            resetZoom()
        }
      }
    }
    
    function resetZoom() {
      scale.value = 1
      translateX.value = 0
      translateY.value = 0
    }

    function onDoubleTap(e) {
      if (scale.value > 1.2) {
        resetZoom()
      } else {
        scale.value = 2.5
        // Optional: center on tap could be added here, simplified for now
      }
    }

    return {
      scale,
      imgStyle,
      zoomStyle,
      onTouchStart,
      onTouchMove,
      onTouchEnd,
      onDoubleTap,
      containerRef,
      imgRef
    }
  }
}
</script>

<style scoped>
.page-viewer { 
    display:flex; 
    align-items:center; 
    justify-content:center; 
    padding:8px;
    overflow: hidden; /* Contain zoomed image */
    position: relative;
    touch-action: pan-y; /* Allow vertical scroll normally */
}

.zoom-container {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 100%;
    transform-origin: center center;
}

/* When zoomed, disable browser handling to allow our pan logic */
.zoom-container.zoomed {
    touch-action: none; 
    cursor: grab;
}

.page-viewer img { 
    display:block; 
    will-change: transform;
}
.empty { color:#999 }
</style>
