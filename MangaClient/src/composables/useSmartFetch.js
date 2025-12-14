import { ref } from 'vue'
import api from '@/services/api'
import cache from '@/services/cache'

/**
 * Smart fetch with caching and transformation
 * @param {string} endpoint - API endpoint
 * @param {Object} options - { transform: fn, cacheKey: string, params: object }
 */
export const useSmartFetch = (endpoint, options = {}) => {
    const { transform, cacheKey, params } = options
    const loading = ref(false)
    const error = ref(null)

    const fetch = async () => {
        loading.value = true
        error.value = null

        try {
            // 1. Check Cache
            if (cacheKey) {
                const fullKey = cache.keyFrom(cacheKey, params)
                const cached = cache.get(fullKey)
                if (cached) {
                    loading.value = false
                    return cached
                }
            }

            // 2. Fetch
            // Note: Endpoint might be relative, api service handles base URL
            const res = await api.get(endpoint, { params })
            let data = res.data

            // 3. Transform
            if (transform && typeof transform === 'function') {
                data = await transform(data)
            }

            // 4. Update Cache
            if (cacheKey && data) {
                const fullKey = cache.keyFrom(cacheKey, params)
                // Default cache time 5 minutes if not specified? cache service handles it.
                cache.set(fullKey, data, 5 * 60 * 1000)
            }

            return data

        } catch (err) {
            console.error(`Error fetching ${endpoint}`, err)
            error.value = err
            return null
        } finally {
            loading.value = false
        }
    }

    return {
        fetch,
        loading,
        error
    }
}
