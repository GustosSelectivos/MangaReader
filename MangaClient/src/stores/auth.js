import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import api from '@/services/api'

export const useAuthStore = defineStore('auth', () => {
  const token = ref(localStorage.getItem('auth_token') || '')
  const user = ref(JSON.parse(localStorage.getItem('auth_user') || 'null'))
  const permissions = ref(JSON.parse(localStorage.getItem('auth_permissions') || '[]'))
  const loading = ref(false)
  const error = ref(null)

  const isAuthenticated = computed(() => !!token.value)

  async function login(username, password) {
    loading.value = true
    error.value = null
    try {
      // Prefer DRF/JWT token endpoint
      // 1) Simple TokenAuth: api/token-auth/ {username, password} -> {token}
      // 2) JWT: api/token/ {username, password} -> {access, refresh}
      let data = null
      try {
        const rJwt = await api.post('token/', { username, password })
        data = rJwt?.data || null
      } catch (eJwt) {
        try {
          const rAlt = await api.post('api/token/', { username, password })
          data = rAlt?.data || null
        } catch (eAlt) {
          const rTok = await api.post('token-auth/', { username, password })
          data = rTok?.data || null
        }
      }
      if (!data) throw new Error('No se pudo autenticar con la API')
      token.value = data.access || data.token || data.key || ''
      if (!token.value) throw new Error('Token inválido')
      user.value = { username, ...('user' in data ? data.user : {}) }
      persist()
      // Set default auth header for subsequent API calls
      try { api.defaults.headers.common['Authorization'] = `Bearer ${token.value}` } catch (e) {}
      // Fetch global permissions for the current user (if available)
      try {
        const rPerm = await api.get('auth/permissions/')
        permissions.value = rPerm?.data?.permissions || []
        localStorage.setItem('auth_permissions', JSON.stringify(permissions.value))
      } catch (e) {
        permissions.value = []
        try { localStorage.removeItem('auth_permissions') } catch (e2) {}
      }
      return true
    } catch (e) {
      error.value = e.message || 'Error de autenticación'
      return false
    } finally {
      loading.value = false
    }
  }

  function logout() {
    token.value = ''
    user.value = null
    permissions.value = []
    localStorage.removeItem('auth_token')
    localStorage.removeItem('auth_user')
    localStorage.removeItem('auth_permissions')
    try { delete api.defaults.headers.common['Authorization'] } catch (e) {}
  }

  function persist() {
    if (token.value) localStorage.setItem('auth_token', token.value)
    if (user.value) localStorage.setItem('auth_user', JSON.stringify(user.value))
    if (permissions.value) localStorage.setItem('auth_permissions', JSON.stringify(permissions.value))
  }

  return { token, user, permissions, loading, error, isAuthenticated, login, logout }
})
