<script setup>
import { ref } from 'vue'
import { useRouter, useRoute, RouterLink } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const route = useRoute()
const auth = useAuthStore()

const username = ref('')
const password = ref('')
const showPw = ref(false)

async function submit() {
  const ok = await auth.login(username.value.trim(), password.value)
  if (ok) {
    const redirect = route.query.redirect || '/'
    router.replace(String(redirect))
  }
}
</script>

<template>
  <div class="login-view container py-4">
    <h2 class="mb-3">Iniciar sesión</h2>
    <p class="text-muted">Ingresa tus credenciales para desbloquear las pantallas de desarrollo.</p>
    <form @submit.prevent="submit" class="v-stack gap-3" style="max-width:420px">
      <div>
        <label class="form-label">Usuario</label>
        <input v-model="username" type="text" class="form-control" required autocomplete="username" />
      </div>
      <div>
        <label class="form-label">Contraseña</label>
        <div class="input-group">
          <input :type="showPw ? 'text' : 'password'" v-model="password" class="form-control" required autocomplete="current-password" />
          <button class="btn btn-outline-secondary" type="button" @click="showPw = !showPw">{{ showPw ? 'Ocultar' : 'Mostrar' }}</button>
        </div>
      </div>
      <div v-if="auth.error" class="alert alert-danger py-2">{{ auth.error }}</div>
      <div>
        <button class="btn btn-primary" :disabled="auth.loading">{{ auth.loading ? 'Verificando...' : 'Entrar' }}</button>
        <RouterLink to="/" class="btn btn-link">Cancelar</RouterLink>
      </div>
    </form>
  </div>
</template>

<style scoped>
.v-stack { display:flex; flex-direction:column; }
.gap-3 { gap:1rem; }
.login-view { max-width:800px; }
</style>

