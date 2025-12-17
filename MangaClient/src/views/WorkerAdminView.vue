<template>
  <div class="worker-admin-view">
    <div class="d-flex justify-content-between align-items-center mb-4">
      <h2 class="h4 m-0">Gestión del Worker (Scraper)</h2>
      <button class="btn btn-primary btn-sm d-flex align-items-center gap-2">
        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16">
          <path fill-rule="evenodd" d="M8 3a5 5 0 1 0 4.546 2.914.5.5 0 0 1 .908-.417A6 6 0 1 1 8 2v1z"/>
          <path d="M8 4.466V.534a.25.25 0 0 1 .41-.192l2.36 1.966c.12.1.12.284 0 .384L8.41 4.658A.25.25 0 0 1 8 4.466z"/>
        </svg>
        Refrescar Estado
      </button>
    </div>

    <div class="row g-4">
      <!-- Status Card -->
      <div class="col-12 col-md-4">
        <div class="card h-100 border-0 shadow-sm">
          <div class="card-body">
            <h5 class="card-title text-muted mb-3">Estado del Servicio</h5>
            <div class="d-flex align-items-center gap-3">
              <div class="status-indicator" :class="status === 'idle' || status === 'processing' ? 'online' : 'offline'"></div>
              <div>
                <h3 class="m-0 text-capitalize">{{ status === 'processing' ? 'Procesando' : (status === 'idle' ? 'En Espera' : 'Offline') }}</h3>
                <small class="text-muted" v-if="currentTask">Activo: {{ currentTask }}</small>
                <small class="text-muted" v-else>Esperando tareas...</small>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Stats Card -->
      <div class="col-12 col-md-4">
        <div class="card h-100 border-0 shadow-sm">
          <div class="card-body">
            <h5 class="card-title text-muted mb-3">Completados vs Fallidos</h5>
            <div class="d-flex align-items-center justify-content-between">
              <div>
                <h3 class="m-0 text-success">{{ completedCount }}</h3>
                <small class="text-muted">Éxitos</small>
              </div>
              <div style="width:1px; height:40px; background:#eee;"></div>
              <div>
                <h3 class="m-0 text-danger">{{ failedCount }}</h3>
                <small class="text-muted">Fallos</small>
              </div>
              <div class="icon-bg bg-light rounded-circle p-3">
                 <!-- Icon code preserved -->
                 <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" fill="var(--bs-primary)" viewBox="0 0 16 16">
                   <path d="M8.235 1.559a.5.5 0 0 0-.47 0l-7.5 4a.5.5 0 0 0 0 .882L3.188 8 .264 9.559a.5.5 0 0 0 0 .882l7.5 4a.5.5 0 0 0 .47 0l7.5-4a.5.5 0 0 0 0-.882L12.813 8l2.922-1.559a.5.5 0 0 0 0-.882l-7.5-4zm3.515 7.008L14.438 10 8 13.433 1.562 10 4.25 8.567l3.515 1.874a.5.5 0 0 0 .47 0l3.515-1.874zM8 9.433 1.562 6 8 2.567 14.438 6 8 9.433z"/>
                 </svg>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Info/Active Task Card -->
      <div class="col-12 col-md-4">
        <div class="card h-100 border-0 shadow-sm">
          <div class="card-body">
            <h5 class="card-title text-muted mb-3">Tarea Actual</h5>
             <div v-if="currentTask">
                <div class="spinner-border text-primary spinner-border-sm mb-2" role="status"></div>
                <div><strong>{{ currentTask }}</strong></div>
                <small class="text-muted">Descargando y Subiendo...</small>
             </div>
             <div v-else class="text-muted d-flex align-items-center h-100" style="min-height: 60px;">
                <em>Ninguna tarea en curso</em>
             </div>
          </div>
        </div>
      </div>
    </div>

    <div class="alert alert-info mt-4 d-flex align-items-center gap-2" role="alert">
      <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" fill="currentColor" viewBox="0 0 16 16">
         <path d="M8 15A7 7 0 1 1 8 1a7 7 0 0 1 0 14zm0 1A8 8 0 1 0 8 0a8 8 0 0 0 0 16z"/>
         <path d="M8.93 6.588l-2.29.287-.082.38.45.083c.294.07.352.176.288.469l-.738 3.468c-.194.897.105 1.319.808 1.319.545 0 1.178-.252 1.465-.598l.088-.416c-.2.176-.492.246-.686.246-.275 0-.375-.193-.304-.533L8.93 6.588zM9 4.5a1 1 0 1 1-2 0 1 1 0 0 1 2 0z"/>
      </svg>
      <div>
        <strong>Próximamente:</strong> Aquí podrás ver el progreso de las descargas en tiempo real, pausar/reanudar el worker y aprobar manualmente las subidas al bucket público.
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import api from '@/services/api'

const STATUS_ENDPOINT = 'chapters/worker_status/'

const status = ref('offline')
const currentTask = ref(null)
const completedCount = ref(0)
const failedCount = ref(0)
const loading = ref(false)
let pollInterval = null

async function refreshStatus() {
  loading.value = true
  try {
    const { data } = await api.get(STATUS_ENDPOINT)
    status.value = data.status || 'offline'
    currentTask.value = data.current_task || null
    completedCount.value = data.completed_tasks || 0
    failedCount.value = data.failed_tasks || 0
  } catch (e) {
    status.value = 'offline'
    currentTask.value = null
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  refreshStatus()
  pollInterval = setInterval(refreshStatus, 5000) // Poll every 5 seconds
})

onUnmounted(() => {
  if (pollInterval) clearInterval(pollInterval)
})
</script>

<style scoped>
.status-indicator {
  width: 16px;
  height: 16px;
  border-radius: 50%;
  background-color: #ccc;
}
.status-indicator.online {
  background-color: #2ecc71;
  box-shadow: 0 0 8px rgba(46, 204, 113, 0.4);
}
.icon-bg {
  width: 50px;
  height: 50px;
  display: flex;
  align-items: center;
  justify-content: center;
}
</style>
