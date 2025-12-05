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
  <div class="login-view container">
    <h2 class="mb-3 text-center">Iniciar sesión</h2>
    <p class="text-muted text-center">Ingresa tus credenciales para desbloquear las pantallas de desarrollo.</p>
    <form @submit.prevent="submit" class="v-stack gap-3 form-box">
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
      <div class="actions">
        <button class="btn btn-primary w-100" :disabled="auth.loading">{{ auth.loading ? 'Verificando...' : 'Entrar' }}</button>
        <RouterLink to="/" class="btn btn-link w-100 text-center">Cancelar</RouterLink>
      </div>
    </form>
  </div>
</template>

<style scoped>
.v-stack { display:flex; flex-direction:column; }
.gap-3 { gap:1rem; }
.login-view { max-width:800px; min-height: 80vh; display:flex; flex-direction:column; align-items:center; justify-content:center; }
.form-box { width:100%; max-width:420px; }
.actions { display:flex; flex-direction:column; gap:8px; }
</style>

