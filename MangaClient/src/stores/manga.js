import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { useSmartFetch } from '@/composables/useSmartFetch'
import api from '@/services/api'
import cache from '@/services/cache'

export const useMangaStore = defineStore('manga', () => {

    // -- State --
    const populars = ref([])
    const trending = ref([])
    const latest = ref([])
    const mostViewed = ref([])

    // Tab caches to avoid refetching on every click
    const tabCache = ref({
        all: [],
        shonen: [],
        seinen: [],
        erotico: []
    })

    const demografiaIds = ref({ shonen: null, seinen: null, erotico: null })
    const demografiasMap = ref(new Map())
    const demografiasLoaded = ref(false)

    // -- Actions / Methods --

    // Normalize API response to standard structure
    const normalizeData = (raw) => {
        if (!raw) return []
        if (Array.isArray(raw)) return raw
        if (raw.results) return raw.results
        if (raw.items) return raw.items
        if (raw.data) return raw.data
        if (typeof raw === 'object') {
            return Object.values(raw).filter(v => v && typeof v === 'object' && ('title' in v || 'name' in v))
        }
        return []
    }

    // Process items (resolve covers, colors, etc)
    const processItems = async (items) => {
        if (!items || !items.length) return []
        await ensureDemografias() // ensure map is ready

        return items.map(it => {
            const copy = { ...it }
            copy.title = copy.title || copy.titulo || ''

            // Cover logic
            let c = copy.cover_url || copy.cover || copy.url_absoluta || ''
            copy.cover = c
            copy.displayCover = c

            // Demography resolution
            let dem = copy.demografia_display || copy.demography || copy.demografia || ''
            if ((typeof dem === 'number' || /^\d+$/.test(dem))) {
                const resolved = demografiasMap.value.get(Number(dem))
                if (resolved) {
                    dem = resolved.descripcion
                    copy.dem_color = copy.dem_color || resolved.color
                }
            } else if (typeof dem === 'object') {
                dem = dem.descripcion || dem.name || ''
            }
            copy.demography = String(dem || '')

            // Fallback color match
            if (!copy.dem_color) {
                for (const [, val] of demografiasMap.value) {
                    if (val.descripcion === dem) {
                        copy.dem_color = val.color
                        break
                    }
                }
            }

            // Erotic flag
            if (copy.erotico !== undefined) copy.erotic = copy.erotico

            return copy
        })
    }

    // Load initial data (Home View)
    const fetchHomeData = async () => {
        // Parallel fetch of main sections
        // Using raw api.get for batch, but could useSmartFetch individually if prefer granular loading states
        // For performance, one batch is usually better or parallel promises

        try {
            const [rPopular, rTrending, rLatest, rMostViewed] = await Promise.all([
                api.get('manga/mangas/', { params: { limit: 12, ordering: '-vistas' } }),
                api.get('manga/mangas/', { params: { limit: 8, ordering: '-creado_en' } }),
                api.get('manga/mangas/', { params: { limit: 8, ordering: '-actualizado_en' } }),
                api.get('manga/mangas/', { params: { limit: 10, ordering: '-vistas' } })
            ])

            populars.value = await processItems(normalizeData(rPopular?.data))
            trending.value = await processItems(normalizeData(rTrending?.data))
            latest.value = await processItems(normalizeData(rLatest?.data))
            mostViewed.value = await processItems(normalizeData(rMostViewed?.data))

            // Initialize 'all' tab with populars
            tabCache.value.all = populars.value

        } catch (e) {
            console.error("Store: Error loading home data", e)
            throw e
        }
    }

    // Fetch specific tab data
    const fetchTab = async (tabName) => {
        if (tabCache.value[tabName] && tabCache.value[tabName].length) {
            return tabCache.value[tabName]
        }

        // Prepare params
        let params = { limit: 12, ordering: '-vistas' }

        await ensureDemografias()

        if (tabName === 'erotico') params.erotico = 'true'
        else if (tabName === 'shonen' && demografiaIds.value.shonen) params.demografia = demografiaIds.value.shonen
        else if (tabName === 'seinen' && demografiaIds.value.seinen) params.demografia = demografiaIds.value.seinen
        // else fallback to name match if needed?

        // Smart fetch logic inline or utility?
        // Using raw for simplicity in store context, or wrap.
        try {
            const res = await api.get('manga/mangas/', { params })
            const data = await processItems(normalizeData(res?.data))
            tabCache.value[tabName] = data
            return data
        } catch (e) {
            console.error(`Store: error fetching tab ${tabName}`, e)
            return []
        }
    }

    // -- Shared Helpers --

    async function fetchDemografias() {
        if (demografiasLoaded.value) return
        try {
            const p = { page_size: 1000 }
            const k = cache.keyFrom('mantenedor/demografias/', p)
            const c = cache.get(k)
            const r = c ? { data: c } : await api.get('mantenedor/demografias/', { params: p })
            const list = normalizeData(r.data)

            if (!c) cache.set(k, list, 24 * 60 * 60 * 1000)

            // Populate Map and IDs
            for (const d of list) {
                const desc = (d.descripcion || d.name || '').toLowerCase()

                demografiasMap.value.set(Number(d.id), {
                    descripcion: d.descripcion || d.name,
                    color: d.color || d.dem_color
                })

                if (desc.includes('shonen') || desc.includes('shounen')) demografiaIds.value.shonen = d.id
                else if (desc.includes('seinen')) demografiaIds.value.seinen = d.id
                else if (desc.includes('erot') || desc.includes('ecchi')) demografiaIds.value.erotico = d.id
            }
            demografiasLoaded.value = true
        } catch (e) { console.error("Store: demografias error", e) }
    }

    async function ensureDemografias() {
        if (!demografiasLoaded.value) await fetchDemografias()
    }

    return {
        // State
        populars,
        trending,
        latest,
        mostViewed,
        tabCache,

        // Actions
        fetchHomeData,
        fetchTab,
        ensureDemografias,
    }
})
