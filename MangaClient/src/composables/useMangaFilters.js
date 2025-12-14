
// Logic to determine if a manga is erotic based on tags or demography
export const isErotic = (item) => {
    if (!item) return false
    if (item.erotic === true || item.erotico === true) return true

    if (item.tags && Array.isArray(item.tags)) {
        const joined = item.tags.map(t => (t.nombre || t.name || t)).join(' ').toLowerCase()
        if (joined.includes('ecchi') || joined.includes('erotic') || joined.includes('erótico') || joined.includes('erotico')) return true
    }

    const dem = (String(item.demography || item.demografia || item.type || '')).toLowerCase()
    if (dem.includes('erotic') || dem.includes('erótico') || dem.includes('erotico') || dem.includes('ecchi')) return true

    return false
}

export const useMangaFilters = () => {

    const filters = {
        all: (items) => items,

        shonen: (items) => items.filter(i => {
            const dem = String(i.demography || i.demografia || '').toLowerCase()
            return dem.includes('shon') || dem.includes('shounen')
        }),

        seinen: (items) => items.filter(i => {
            const dem = String(i.demography || i.demografia || '').toLowerCase()
            return dem.includes('sein')
        }),

        erotico: (items) => items.filter(i => isErotic(i))
    }

    const applyFilter = (items, filterName) => {
        const fn = filters[filterName] || filters.all
        return fn(items)
    }

    return {
        applyFilter,
        isErotic
    }
}
