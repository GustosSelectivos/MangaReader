
/**
 * Composable for shared Manga UI logic.
 * Standardizes how manga types, content warnings (erotic), and labels are displayed across Home and Library views.
 */
export function useMangaUI() {

    /**
     * Determine CSS class based on manga type/demography.
     * Usage: :class="typeClass(manga)"
     */
    function typeClass(item) {
        let raw = item && (item.demography || item.type || item.book_type || '')
        if (Array.isArray(raw)) raw = raw.join(' ')
        if (raw && typeof raw === 'object') raw = raw.name || raw.title || JSON.stringify(raw)
        raw = String(raw || '').toLowerCase()

        if (raw.includes('manhwa')) return 'type-manhwa'
        if (raw.includes('manhua')) return 'type-manhua'
        if (raw.includes('novel') || raw.includes('novela')) return 'type-novela'
        if (raw.includes('shoujo')) return 'type-shoujo'
        if (raw.includes('josei')) return 'type-josei'
        if (raw.includes('seinen')) return 'type-seinen'
        if (raw.includes('shounen') || raw.includes('shonen')) return 'type-shounen'
        if (raw.includes('manga')) return 'type-manga'
        return 'type-default'
    }

    /**
     * Return a readable display label for the manga type/demography.
     */
    function displayType(item) {
        let val = item && (item.demography || item.dem_descripcion || item.demografia_descripcion || item.demografia || item.type || '')

        // Parse JSON if needed
        if (typeof val === 'string') {
            const s = val.trim()
            if (s.startsWith('{') || s.startsWith('[')) {
                try { val = JSON.parse(s) } catch (e) { /* keep original */ }
            }
        }

        if (Array.isArray(val)) val = val.join(' ')
        if (val && typeof val === 'object') val = val.descripcion || val.description || val.name || val.title || val.label || JSON.stringify(val)
        return String(val || 'MANGA').toUpperCase()
    }

    /**
     * Return the origin label (Manga, Manhwa, etc.) based on tags or properties.
     */
    function originLabel(item) {
        let t = item && (item.mng_tipo_manga || item.mng_tipo_serie || item.tipo_serie || item.manga_tipo_serie || item.type || item.book_type || item.raw?.type || item.origin || '')

        if (!t && item) {
            // Try tags heuristic
            const tags = item.tags || item.tags_list || []
            if (Array.isArray(tags) && tags.length) {
                const joined = tags.map(x => (x.nombre || x.name || x)).join(' ').toLowerCase()
                if (joined.includes('manhwa')) t = 'manhwa'
                if (joined.includes('manhua')) t = 'manhua'
                if (joined.includes('novel') || joined.includes('novela')) t = 'novela'
            }
        }

        if (typeof t === 'string') t = t.toLowerCase()
        const norm = String(t || '')

        if (norm.includes('comic')) return 'Comic'
        if (/one[\s_\-]?shot/.test(norm)) return 'One-shot'
        if (norm.includes('manhwa')) return 'Manhwa'
        if (norm.includes('manhua')) return 'Manhua'
        if (norm.includes('novel')) return 'Novela'
        return 'Manga'
    }

    /**
     * Check if the item is Erotic/Hentai/+18 based on flags, tags, or demography.
     */
    function isErotic(item) {
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

    /**
     * Return a safe cover URL (standard placeholder if missing/invalid).
     */
    function safeCover(url) {
        const u = String(url || '').toLowerCase()
        const blank = 'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" width="160" height="240"/>'
        if (!u || !u.startsWith('http')) return blank
        return url
    }

    return {
        typeClass,
        displayType,
        originLabel,
        isErotic,
        safeCover
    }
}
