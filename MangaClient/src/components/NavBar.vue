<script setup>
import { ref, onMounted, watch, computed } from 'vue';
import { RouterLink, useRouter, useRoute } from 'vue-router';
import { useAuthStore } from '@/stores/auth';

const router = useRouter();
const query = ref('');
const emit = defineEmits(['search']);
const isDark = ref(true);
const route = useRoute()

const isReaderRoute = computed(() => {
  const n = route.name
  return n === 'reader' || n === 'chapter'
})

// Reader-specific controls moved into ReaderToolbar

// Mobile menu state
const isMenuOpen = ref(false)
function toggleMenu() { isMenuOpen.value = !isMenuOpen.value }
watch(() => route.fullPath, () => { isMenuOpen.value = false })

const auth = useAuthStore()

function applyTheme() {
  const root = document.documentElement;
  root.classList.remove(isDark.value ? 'theme-light' : 'theme-dark');
  root.classList.add(isDark.value ? 'theme-dark' : 'theme-light');
  localStorage.setItem('theme', isDark.value ? 'dark' : 'light');
}
watch(isDark, () => applyTheme());

onMounted(() => {
  const saved = localStorage.getItem('theme');
  if (saved === 'light') isDark.value = false;
  // Ensure initial class present if none
  applyTheme();
});

function submitSearch(e) {
  e.preventDefault();
  const q = query.value.trim();
  emit('search', q);
  // Navegar a la biblioteca, pasando el query como parámetro 'title'.
  router.push({ name: 'library', query: q ? { title: q } : {} });
}
</script>

<template>
  <header class="main-header">
    <nav class="navbar site-header">
      <div class="container-fluid inner">
        <RouterLink to="/" class="navbar-brand title" title="Inicio">
          TU<b>MANGA</b><i>ONLINE</i>
        </RouterLink>

        <!-- Desktop controls -->
        <template v-if="!isReaderRoute">
        <!--
          <RouterLink to="/library" class="btn btn-secondary biblioteca-btn desktop-only" title="Biblioteca">
            Biblioteca
          </RouterLink>
        -->
          <form class="search desktop-only" @submit="submitSearch">
            <input
              v-model="query"
              class="form-control"
              type="search"
              placeholder="Buscar..."
              aria-label="Buscar"
              @keyup.enter="submitSearch"
            >
          </form>
        </template>
        <template v-else><!-- reader route: no extra navbar controls --></template>

        <div class="actions desktop-only">
          <div class="theme-toggle">
            <label class="switch" :title="isDark ? 'Cambiar a modo claro' : 'Cambiar a modo oscuro'">
              <input type="checkbox" v-model="isDark">
              <span class="slider"></span>
            </label>
          </div>
          <template v-if="!auth.isAuthenticated">
            <RouterLink to="/login" class="btn btn-primary login-btn">Login</RouterLink>
          </template>
          <template v-else>
            <div class="dev-links">
              <RouterLink class="btn btn-outline-success" to="/admin">Panel Admin</RouterLink>
              <button class="btn btn-danger" @click="auth.logout()">Salir</button>
            </div>
          </template>
        </div>

        <!-- Mobile hamburger (hidden on reader route) -->
        <button v-if="!isReaderRoute" class="mobile-toggle" :aria-expanded="isMenuOpen ? 'true' : 'false'" aria-label="Menú" @click="toggleMenu">
          <svg xmlns="http://www.w3.org/2000/svg" width="22" height="22" viewBox="0 0 16 16" fill="currentColor" aria-hidden="true"><path d="M2 3h12v2H2zM2 7h12v2H2zM2 11h12v2H2z"/></svg>
        </button>
      </div>

      <!-- Mobile dropdown menu -->
      <div v-if="isMenuOpen && !isReaderRoute" class="mobile-menu">
        <!-- <RouterLink to="/library" class="btn btn-secondary w-100" @click="toggleMenu">Biblioteca</RouterLink> -->
        <form class="mobile-search" @submit="(e) => { submitSearch(e); toggleMenu() }">
          <input
            v-model="query"
            class="form-control"
            type="search"
            placeholder="Buscar..."
            aria-label="Buscar"
            @keyup.enter="(e) => { submitSearch(e); toggleMenu() }"
          >
        </form>
        <div class="mobile-theme d-flex align-items-center justify-content-between">
          <span>Tema</span>
          <label class="switch" :title="isDark ? 'Cambiar a modo claro' : 'Cambiar a modo oscuro'">
            <input type="checkbox" v-model="isDark">
            <span class="slider"></span>
          </label>
        </div>
        <template v-if="!auth.isAuthenticated">
          <RouterLink to="/login" class="btn btn-primary w-100" @click="toggleMenu">Login</RouterLink>
        </template>
        <template v-else>
          <div class="v-stack gap-2 mt-2">
            <RouterLink to="/admin" class="btn btn-outline-success w-100" @click="toggleMenu">Panel Admin</RouterLink>

            <button class="btn btn-danger w-100" @click="auth.logout(); toggleMenu()">Salir</button>
          </div>
        </template>
      </div>
    </nav>
  </header>
</template>

<style scoped>
.main-header { width:100%; }
.navbar { padding:.5rem 1rem; }
.inner { display:flex; align-items:center; gap:.75rem; flex-wrap:nowrap; }
.title { font-size:1.25rem; display:flex; align-items:center; gap:.25rem; flex:0 0 auto; }
.title:hover { background-color:transparent; }
.biblioteca-btn, .login-btn { display:flex; align-items:center; justify-content:center; height:38px; line-height:38px; padding:0 .9rem; }
.biblioteca-btn { white-space:nowrap; }
/* Fijamos ancho base del botón login para poder limitar el buscador */
.login-btn { white-space:nowrap; width:120px; text-align:center; }
/* Buscador: nunca más del doble (240px). Permite encogerse si espacio limitado */
.search { flex:0 1 240px; max-width:240px; width:100%; }
.search .form-control { width:100%; height:38px; padding:.375rem .75rem; }
.actions { display:flex; align-items:center; gap:.75rem; }
.theme-toggle { display:flex; align-items:center; }
.switch { position:relative; display:inline-block; width:52px; height:26px; }
.switch input { opacity:0; width:0; height:0; }
.slider { position:absolute; cursor:pointer; top:0; left:0; right:0; bottom:0; background:#495867; transition:.25s; border-radius:26px; }
.slider:before { position:absolute; content:""; height:20px; width:20px; left:3px; top:3px; background:white; border-radius:50%; transition:.25s; }
input:checked + .slider { background:#2957ba; }
input:checked + .slider:before { transform:translateX(26px); }
/* Mobile behavior */
.mobile-toggle { display:none; background:transparent; border:none; margin-left:auto; padding:.25rem; color:var(--ztmo-text); }
.desktop-only { display:flex; }
.mobile-menu { display:none; }
@media (max-width: 640px) {
  .desktop-only { display:none !important; }
  .mobile-toggle { display:inline-flex; align-items:center; justify-content:center; }
  .mobile-menu {
    display:block;
    padding:.5rem 1rem;
    border-top:1px solid var(--ztmo-border);
    background:var(--ztmo-card);
    color:var(--ztmo-text);
    /* Full-bleed across the viewport */
    width:100vw;
    margin-left:calc(50% - 50vw);
    margin-right:calc(50% - 50vw);
  }
  .mobile-menu .mobile-search { margin:.5rem 0; }
  .mobile-menu .mobile-search .form-control { height:38px; }
  .mobile-menu .mobile-theme { padding:.25rem 0 .5rem; border-bottom:1px solid var(--ztmo-border); margin-bottom:.5rem; }
}
@media (max-width: 400px) {
  .mobile-menu .mobile-search .form-control { height:34px; }
}
.dev-links { display:flex; align-items:center; gap:.5rem; }
</style>
