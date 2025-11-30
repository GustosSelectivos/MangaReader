<script setup>
import { ref, onMounted } from 'vue'
import api from '@/services/api'

const mangas = ref([])
const loading = ref(false)
const error = ref('')

async function fetchMangas() {
  loading.value = true
  error.value = ''
  try {
    const r = await api.get('manga/mangas/', { params: { page_size: 200 } })
    mangas.value = Array.isArray(r.data) ? r.data : (r.data?.results || [])
  } catch (e) {
    try {
      const r2 = await api.get('mangas/', { params: { page_size: 200 } })
      mangas.value = Array.isArray(r2.data) ? r2.data : (r2.data?.results || [])
    } catch (e2) {
      error.value = e2.message || e.message || 'Error cargando mangas'
    }
  } finally {
    loading.value = false
  }
}

async function toggleErotico(m) {
  const desired = !m.erotico && !m.erotic ? true : !m.erotico
  try {
    // Pick endpoint; adjust if different naming
    await api.patch(`manga/mangas/${m.id}/`, { erotico: desired })
    m.erotico = desired
    m.erotic = desired
  } catch (e) {
    // Fallback to alternate path
    try {
      await api.patch(`mangas/${m.id}/`, { erotico: desired })
      m.erotico = desired
      m.erotic = desired
    } catch (e2) {
      error.value = e2.message || e.message || 'Error actualizando erotico'
    }
  }
}

onMounted(fetchMangas)
</script>

<template>
  <div class="mangas-admin container py-4">
    <h2 class="mb-3">Administrar Mangas</h2>
    <p class="text-muted">Lista y edición rápida del flag erótico.</p>
    <div v-if="error" class="alert alert-danger py-2">{{ error }}</div>
    <div v-if="loading">Cargando...</div>
    <table v-if="!loading" class="table table-sm table-striped align-middle">
      <thead>
        <tr>
          <th>ID</th>
          <th>Título</th>
          <th>Erótico</th>
          <th>Acciones</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="m in mangas" :key="m.id">
          <td>{{ m.id }}</td>
          <td class="text-truncate" style="max-width:240px" :title="m.titulo || m.title">{{ m.titulo || m.title }}</td>
          <td>
            <span :class="['badge', (m.erotico || m.erotic) ? 'bg-danger' : 'bg-secondary']">{{ (m.erotico || m.erotic) ? 'Sí' : 'No' }}</span>
          </td>
          <td>
            <button class="btn btn-outline-primary btn-sm" @click="toggleErotico(m)">
              {{ (m.erotico || m.erotic) ? 'Marcar No Erótico' : 'Marcar Erótico' }}
            </button>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<style scoped>
.text-truncate { white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
/* Dark mode readability for muted text and labels */
.mangas-admin { color: var(--ztmo-text); }
.mangas-admin .text-muted { color: var(--ztmo-text); opacity: 0.75; }
.mangas-admin .form-label { color: var(--ztmo-text); }
</style>
