/**
 * Utilidades compartidas para formatear datos de Mangas.
 * Centraliza la lógica de etiquetas de origen, demografía, etc.
 */

// Mapeo básico de colores y tipos
export function typeClass(item) {
  let raw = item && (item.demography || item.type || item.book_type || '');
  if (Array.isArray(raw)) raw = raw.join(' ');
  if (raw && typeof raw === 'object') raw = raw.name || raw.title || JSON.stringify(raw);
  raw = String(raw || '').toLowerCase();
  
  if (raw.includes('manhwa')) return 'type-manhwa';
  if (raw.includes('manhua')) return 'type-manhua';
  if (raw.includes('novel') || raw.includes('novela')) return 'type-novela';
  if (raw.includes('shoujo')) return 'type-shoujo';
  if (raw.includes('josei')) return 'type-josei';
  if (raw.includes('seinen')) return 'type-seinen';
  if (raw.includes('shounen') || raw.includes('shonen')) return 'type-shounen';
  if (raw.includes('manga')) return 'type-manga';
  
  return 'type-default';
}

export function displayType(item) {
  let val = item && (item.demography || item.dem_descripcion || item.demografia_descripcion || item.demografia || item.type || '');
  if (typeof val === 'string') {
    const s = val.trim();
    if (s.startsWith('{') || s.startsWith('[')) {
      try { val = JSON.parse(s); } catch { /* keep original string */ }
    }
  }
  if (Array.isArray(val)) val = val.join(' ');
  if (val && typeof val === 'object') val = val.descripcion || val.description || val.name || val.title || val.label || JSON.stringify(val);
  
  return String(val || 'MANGA');
}

export function originLabel(item) {
  let t = item && (item.mng_tipo_manga || item.mng_tipo_serie || item.tipo_serie || item.manga_tipo_serie || item.type || item.book_type || item.raw?.type || item.origin || '');
  if (!t && item) {
    const tags = item.tags || item.tags_list || [];
    if (Array.isArray(tags) && tags.length) {
      const joined = tags.map(x => (x.nombre || x.name || x)).join(' ').toLowerCase();
      if (joined.includes('manhwa')) t = 'manhwa';
      if (joined.includes('manhua')) t = 'manhua';
    }
  }
  if (typeof t === 'string') t = t.toLowerCase();
  
  const norm = String(t || '');
  if (norm.includes('comic')) return 'Comic';
  if (/one[\s_-]?shot/.test(norm)) return 'One-shot';
  if (t && t.includes('manhwa')) return 'Manhwa';
  if (t && t.includes('manhua')) return 'Manhua';
  if (t && t.includes('novel')) return 'Novela';
  
  return 'Manga';
}

export function isErotic(item) {
  if (!item) return false;
  if (item.erotic === true) return true;
  if (item.erotico === true) return true;
  
  if (item.tags && Array.isArray(item.tags)) {
    const joined = item.tags.map(t => (t.nombre || t.name || t)).join(' ').toLowerCase();
    if (joined.includes('ecchi') || joined.includes('erotic') || joined.includes('erótico') || joined.includes('erotico')) return true;
  }
  
  const dem = (String(item.demography || item.demografia || item.type || '')).toLowerCase();
  if (dem.includes('erotic') || dem.includes('erótico') || dem.includes('erotico') || dem.includes('ecchi')) return true;
  
  return false;
}
