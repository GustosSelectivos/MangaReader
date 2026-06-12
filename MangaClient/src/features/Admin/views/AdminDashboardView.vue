<script setup>
import { RouterLink } from 'vue-router'
</script>

<template>
  <div class="admin-dashboard">
    <div class="dashboard-grid">
      <RouterLink to="/admin/mangas" class="dashboard-card">
        <div class="card-icon">📚</div>
        <h3>Mangas</h3>
        <p>Administrar catálogo de mangas, crear y editar.</p>
      </RouterLink>

      <RouterLink to="/admin/upload" class="dashboard-card">
        <div class="card-icon">📤</div>
        <h3>Subir Capítulo</h3>
        <p>Cargar nuevos capítulos a los mangas existentes.</p>
      </RouterLink>

      <RouterLink to="/admin/mantenedores" class="dashboard-card">
        <div class="card-icon">👥</div>
        <h3>Mantenedores</h3>
        <p>Gestionar permisos y mantenedores del sitio.</p>
      </RouterLink>

      <RouterLink to="/admin/profiles" class="dashboard-card">
        <div class="card-icon">👤</div>
        <h3>Perfiles</h3>
        <p>Ver y administrar perfiles de usuario.</p>
      </RouterLink>

      <RouterLink to="/admin/worker" class="dashboard-card">
        <div class="card-icon">🤖</div>
        <h3>Worker</h3>
        <p>Gestionar scraper, descargas y staging.</p>
      </RouterLink>
    </div>
  </div>
</template>

<style scoped>
.dashboard-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 1.5rem;
}

.dashboard-card {
  background-color: var(--ztmo-card);
  border: 1px solid var(--ztmo-border);
  border-radius: 8px;
  padding: 1.5rem;
  text-decoration: none;
  color: var(--ztmo-text);
  transition: transform 0.2s, box-shadow 0.2s;
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
}

.dashboard-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0,0,0,0.1);
  border-color: var(--ztmo-primary);
}

.card-icon {
  font-size: 3rem;
  margin-bottom: 1rem;
}

.dashboard-card h3 {
  color: var(--ztmo-text-highlight);
  margin-bottom: 0.5rem;
}

.dashboard-card p {
  color: var(--ztmo-text-muted);
  font-size: 0.9rem;
}
</style>
