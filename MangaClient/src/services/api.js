/**
 * Axios API service (Adaptado para FastAPI)
 */

import axios from 'axios'

const DEFAULT_BASE = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000/api/'

const api = axios.create({
  baseURL: DEFAULT_BASE,
  headers: {
    'Content-Type': 'application/json',
    Accept: 'application/json'
  }
})

api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('auth_token')
    // FastAPI generalmente usa Bearer para OAuth2
    if (token) config.headers.Authorization = `Bearer ${token}`
    return config
  },
  (error) => Promise.reject(error)
)

api.interceptors.response.use(
  (response) => response,
  (error) => {
    const status = error?.response?.status
    const config = error?.config || {}

    // Manejo global para errores 422 de Pydantic/FastAPI
    if (status === 422) {
      console.warn('[FastAPI Validation Error]:', error.response.data?.detail)
    }

    // Reintentar una vez sin Authorization si 401 en GET (Mantenido de la V1)
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
