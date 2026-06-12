<template>
  <div class="thumbnail-strip">
    <div v-for="(p, i) in pages" :key="i" :class="['thumb', {active: i+1===current}]" @click="$emit('select', i+1)">
      <img :src="p" alt="thumb" />
    </div>
  </div>
</template>

<script>
export default {
  name: 'ThumbnailStrip',
  props: {
    pages: { type: Array, required: true },
    current: { type: Number, default: 1 }
  }
}
</script>

<style scoped>
.thumbnail-strip { display:flex; gap:6px; overflow:auto; padding:6px }
.thumb { width:60px; height:80px; cursor:pointer; border:2px solid transparent }
.thumb img { width:100%; height:100%; object-fit:cover }
.thumb.active { border-color:#42b983 }
</style>
