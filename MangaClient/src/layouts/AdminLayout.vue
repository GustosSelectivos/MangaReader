<script setup>
import { RouterLink, RouterView } from 'vue-router'
import AdminToolbar from '@/components/AdminToolbar.vue'
</script>

<template>
  <div class="admin-layout">
    <AdminToolbar />
    <div class="admin-body">
      <main class="admin-content">
        <RouterView />
      </main>
    </div>
  </div>
</template>

<style scoped>
.admin-layout {
  display: flex;
  flex-direction: column;
  min-height: calc(100vh - 60px); /* Adjust based on main navbar height */
  background-color: var(--ztmo-bg);
}

.admin-body {
  display: flex;
  flex: 1;
}

.admin-content {
  flex: 1;
  padding: 2rem;
  overflow-y: auto;
}

@media (max-width: 768px) {
  .admin-body {
    flex-direction: column;
  }
}
</style>
