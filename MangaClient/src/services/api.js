/**
 * Axios API service
 *
 * Usage:
 *  import api from '@/services/api'
 *  const res = await api.get('manga/mangas/')
 *  // res.data contains the response body
 *
 * Configuration:
 * - Uses `import.meta.env.VITE_API_BASE_URL` if present, otherwise defaults
 *   to `http://127.0.0.1:8000/api/`.
 * - Exposes an axios instance with a default `baseURL` and JSON headers.
 * - Example interceptors show how to add auth tokens and global error handling.
 */

import axios from 'axios'

// SECURITY WARNING: Storing tokens in localStorage is vulnerable to XSS.
// TODO: Refactor to usage of HttpOnly cookies for better security.
const DEFAULT_BASE = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000/api/'

const api = axios.create({
  baseURL: DEFAULT_BASE,
  headers: {
    'Content-Type': 'application/json',
    Accept: 'application/json'
  },
  // No global timeout to avoid premature aborts
})

// Request interceptor: add auth token if present
api.interceptors.request.use(
  (config) => {
    // Example: attach token from localStorage
    const token = localStorage.getItem('auth_token')
    if (token) config.headers.Authorization = `Bearer ${token}`
    return config
  },
  (error) => Promise.reject(error)
)

// Response interceptor: centralize error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    const status = error?.response?.status
    const config = error?.config || {}
    // Reintentar una vez sin Authorization si 401 en GET
    if (status === 401 && config && !config.__retried401 && String(config.method).toLowerCase() === 'get') {
      config.__retried401 = true
      try { delete config.headers?.Authorization } catch (e) { }
      try { localStorage.removeItem('auth_token') } catch (e) { }
      return api.request(config)
    }
    return Promise.reject(error)
  }
)

export default api
