<script setup>
import { RouterView } from 'vue-router';
import '@/assets/zonatmo.css';
import NavBar from './components/NavBar.vue';
</script>

<template>
  <div class="app-root">
    <NavBar />

    <main role="main" class="container-fluid">
      <RouterView v-slot="{ Component }">
        <Suspense>
          <template #default>
            <div v-if="Component">
              <component :is="Component" />
            </div>
            <div v-else>
              <div class="loading">Cargando...</div>
            </div>
          </template>
          <template #fallback>
            <div class="loading">Cargando...</div>
          </template>
        </Suspense>
      </RouterView>
    </main>
  </div>
</template>

<style scoped>
/* Extend root to full viewport */
#app, .app-root { display:flex; flex-direction:column; width:100%; }
.app-root > main.container-fluid { flex:1 1 auto; padding:0; display:flex; flex-direction:column; justify-content:flex-start; min-height:0; overflow-y:auto; -webkit-overflow-scrolling: touch; }
/* Center only routed view containers; let them size to max-width internally */
.app-root > main.container-fluid > .home-view { flex:0 0 auto; width:100%; max-width:1600px; margin:0 auto; }
@media (min-width: 1700px) { .app-root > main.container-fluid > .home-view { max-width:1700px; } }
html, body { height:100%; width:100%; }
@media (max-width: 576px) { #app > main.container-fluid { overflow-y:auto; -webkit-overflow-scrolling: touch; } }
</style>
