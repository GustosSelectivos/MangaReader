<template>
  <div class="page-viewer">
    <img v-if="image" :src="image" :style="imgStyle" alt="page" loading="lazy" />
    <div v-else class="empty">No page</div>
  </div>
</template>

<script>
export default {
  name: 'PageViewer',
  props: {
    image: { type: String, default: null },
    fitMode: { type: String, default: 'contain' },
    noMaxHeight: { type: Boolean, default: false }
  },
  computed: {
    imgStyle() {
      const style = { 'max-width': '100%', objectFit: this.fitMode }
      if (this.fitMode === 'cover') style.width = '100%'
      if (this.noMaxHeight) {
        style['max-height'] = 'none'
        style.width = '100%'
      } else {
        style['max-height'] = '80vh'
      }
      return style
    }
  }
}
</script>

<style scoped>
.page-viewer { display:flex; align-items:center; justify-content:center; padding:8px }
.page-viewer img { display:block }
.empty { color:#999 }
</style>
