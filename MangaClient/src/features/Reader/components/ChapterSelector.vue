<template>
  <div class="chapter-selector">
    <label for="chapter">Chapter</label>
    <select id="chapter" v-model.number="selected" @change="emitChange">
      <option v-for="c in chapters" :value="c.id" :key="c.id">{{ c.number }} - {{ c.title }}</option>
    </select>
  </div>
</template>

<script>
export default {
  name: 'ChapterSelector',
  props: {
    chapters: { type: Array, default: () => [] },
    value: { type: [Number, String], default: null }
  },
  data() { return { selected: this.value } },
  watch: { value(v) { this.selected = v } },
  methods: { emitChange() { this.$emit('update:value', this.selected); this.$emit('change', this.selected) } }
}
</script>

<style scoped>
.chapter-selector { display:flex; gap:8px; align-items:center }
</style>
