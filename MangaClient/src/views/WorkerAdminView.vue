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
              <div class="status-indicator online"></div>
              <div>
                <h3 class="m-0">En Línea</h3>
                <small class="text-muted">v1.2.0 • Uptime: 4d 12h</small>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Queue Card -->
      <div class="col-12 col-md-4">
        <div class="card h-100 border-0 shadow-sm">
          <div class="card-body">
            <h5 class="card-title text-muted mb-3">Cola de Descargas</h5>
            <div class="d-flex align-items-center justify-content-between">
              <div>
                <h3 class="m-0">0</h3>
                <small class="text-muted">Tareas pendientes</small>
              </div>
              <div class="icon-bg bg-light rounded-circle p-3">
                <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" fill="var(--bs-primary)" viewBox="0 0 16 16">
                  <path d="M8.235 1.559a.5.5 0 0 0-.47 0l-7.5 4a.5.5 0 0 0 0 .882L3.188 8 .264 9.559a.5.5 0 0 0 0 .882l7.5 4a.5.5 0 0 0 .47 0l7.5-4a.5.5 0 0 0 0-.882L12.813 8l2.922-1.559a.5.5 0 0 0 0-.882l-7.5-4zm3.515 7.008L14.438 10 8 13.433 1.562 10 4.25 8.567l3.515 1.874a.5.5 0 0 0 .47 0l3.515-1.874zM8 9.433 1.562 6 8 2.567 14.438 6 8 9.433z"/>
                </svg>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Storage Card -->
      <div class="col-12 col-md-4">
        <div class="card h-100 border-0 shadow-sm">
          <div class="card-body">
            <h5 class="card-title text-muted mb-3">Staging (B2)</h5>
            <div class="d-flex align-items-center justify-content-between">
              <div>
                <h3 class="m-0">12</h3>
                <small class="text-muted">Capítulos por aprobar</small>
              </div>
              <div class="icon-bg bg-light rounded-circle p-3">
                <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" fill="var(--bs-success)" viewBox="0 0 16 16">
                   <path fill-rule="evenodd" d="M7.646 5.146a.5.5 0 0 1 .708 0l2 2a.5.5 0 0 1-.708.708L8.5 6.707V10.5a.5.5 0 0 1-1 0V6.707L6.354 7.854a.5.5 0 1 1-.708-.708l2-2z"/>
                   <path d="M4.406 3.342A5.53 5.53 0 0 1 8 2c2.69 0 4.923 2 5.166 4.579C14.758 6.804 16 8.137 16 9.773 16 11.569 14.502 13 12.687 13H3.781C1.708 13 0 11.366 0 9.318c0-1.763 1.266-3.223 2.942-3.593.143-.863.698-1.723 1.464-2.383zm.653.757c-.757.653-1.153 1.44-1.153 2.056v.448l-.445.049C2.064 6.805 1 7.952 1 9.318 1 10.785 2.23 12 3.781 12h8.906C13.98 12 15 10.988 15 9.773c0-1.216-1.02-2.228-2.313-2.228h-.5v-.5C12.188 4.825 10.328 3 8 3a4.53 4.53 0 0 0-2.941 1.1z"/>
                </svg>
              </div>
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
// Placeholder logic
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
