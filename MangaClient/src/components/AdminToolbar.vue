<script setup>
import { useRoute, RouterLink } from 'vue-router'
import { computed } from 'vue'

const route = useRoute()

// Computed title based on current route name or meta
const pageTitle = computed(() => {
  switch (route.name) {
    case 'admin-dashboard': return 'Dashboard General';
    case 'mangas-admin': return 'Gestión de Mangas';
    case 'upload-chapter': return 'Subir Capítulo';
    case 'mantenedores-admin': return 'Mantenedores';
    case 'profiles-admin': return 'Perfiles de Usuario';
    default: return 'Administración';
  }
})
</script>

<template>
  <div class="admin-toolbar">
    <div class="container-fluid d-flex align-items-center justify-content-between h-100">
      <div class="toolbar-left d-flex align-items-center gap-3">
        <RouterLink to="/admin" class="btn btn-sm btn-ghost" exact-active-class="active">Dashboard</RouterLink>
        <div class="vr mx-2"></div>
        <nav class="d-flex gap-1 admin-nav">
          <RouterLink to="/admin/mangas" class="btn btn-sm btn-ghost" active-class="active">Mangas</RouterLink>
          <RouterLink to="/admin/upload" class="btn btn-sm btn-ghost" active-class="active">Subir</RouterLink>
          <RouterLink to="/admin/mantenedores" class="btn btn-sm btn-ghost" active-class="active">Mantenedores</RouterLink>
          <RouterLink to="/admin/profiles" class="btn btn-sm btn-ghost" active-class="active">Perfiles</RouterLink>
          <RouterLink to="/admin/worker" class="btn btn-sm btn-ghost" active-class="active">Worker</RouterLink>
        </nav>
      </div>
      
      <div class="toolbar-right d-flex align-items-center gap-2">
        <!-- Placeholder for future toolbar actions -->
        <span class="text-muted small">v1.0.0</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.admin-toolbar {
  height: 48px;
  background-color: var(--ztmo-card); /* Distinct from main navbar */
  border-bottom: 1px solid var(--ztmo-border);
  width: 100%;
  flex-shrink: 0;
}

.toolbar-title {
  font-weight: 600;
  font-size: 0.95rem;
  color: var(--ztmo-text-highlight);
  padding-left: 1rem;
  border-left: 3px solid var(--ztmo-primary);
  line-height: 1;
  white-space: nowrap;
}

.btn-ghost {
  color: var(--ztmo-text);
  border: 1px solid transparent;
}
.btn-ghost:hover {
  background-color: var(--ztmo-hover);
}
.btn-ghost.active {
  background-color: var(--ztmo-primary); /* Or a highlight color */
  color: #fff;
}

.text-muted {
  font-size: 0.75rem;
}
</style>
