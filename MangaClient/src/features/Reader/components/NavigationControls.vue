<template>
  <div class="nav-controls">
    <button v-if="!hideButtons" class="btn btn-primary" @click="$emit('prev')" :disabled="page<=1">Anterior página</button>
    <span>Page</span>
    <input
      type="number"
      class="form-control form-control-sm input-page text-center"
      v-model.number="localPage"
      @keydown.enter="go"
      :min="1"
      :max="total"
    />
    <span>/ {{ total }}</span>
    <button v-if="!hideButtons" class="btn btn-primary" @click="$emit('next')" :disabled="page>=total">Siguiente página</button>
  </div>
</template>

<script>
export default {
  name: 'NavigationControls',
  props: {
    page: { type: Number, required: true },
    total: { type: Number, required: true },
    hideButtons: { type: Boolean, default: false }
  },
  data() { return { localPage: this.page } },
  watch: { page(v) { this.localPage = v } },
  methods: {
    go() { this.$emit('go', Number(this.localPage)) }
  }
}
</script>

<style scoped>
 .nav-controls { display:flex; gap:8px; align-items:center }
 .input-page { width: 72px; max-width: 100px; padding: 2px 6px }
 /* remove number input spinners for a cleaner look */
 .nav-controls input[type=number]::-webkit-outer-spin-button,
 .nav-controls input[type=number]::-webkit-inner-spin-button { -webkit-appearance: none; margin: 0 }
 .nav-controls input[type=number] { appearance: textfield; -moz-appearance: textfield }
</style>
