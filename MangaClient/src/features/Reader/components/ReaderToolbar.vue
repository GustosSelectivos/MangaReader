<template>
  <div class="reader-toolbar">
    <div class="left d-flex gap-2 align-items-center">
      <button class="btn btn-outline-secondary btn-sm" @click="$emit('prev')">
        <svg class="icon" xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 16 16" fill="currentColor" aria-hidden="true"><path d="M9.5 14L3.5 8l6-6v12zM14 14L8 8l6-6v12z"/></svg>
        <span class="btn-label">Anterior capítulo</span>
      </button>
      <button class="btn btn-outline-secondary btn-sm" @click="$emit('next')">
        <span class="btn-label">Siguiente capítulo</span>
        <svg class="icon" xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 16 16" fill="currentColor" aria-hidden="true"><path d="M6.5 2l6 6-6 6V2zM2 2l6 6-6 6V2z"/></svg>
      </button>
    </div>
    <div class="center text-truncate">{{ title }} <small v-if="chapter">- {{ chapter.number }} {{ chapter.title }}</small></div>
    <div class="right">
      <slot name="actions"></slot>
    </div>
  </div>
</template>

<script>
export default {
  name: 'ReaderToolbar',
  props: {
    title: { type: String, default: '' },
    chapter: { type: Object, default: null }
  }
}
</script>

<style scoped>
.reader-toolbar { display:flex; justify-content:space-between; align-items:center; gap:12px; padding:8px; background:#f5f5f5 }
.reader-toolbar .center { font-weight:600; min-width:0; overflow:hidden; text-overflow:ellipsis; white-space:nowrap }
.reader-toolbar .icon { vertical-align: text-bottom; margin: 0 2px }
/* Force black center text on dark theme for better contrast */
.theme-dark .reader-toolbar .center { color: #000 }
@media (max-width: 576px) {
  .reader-toolbar .btn-label { display: none }
  .reader-toolbar .center { display: none }
}
</style>
