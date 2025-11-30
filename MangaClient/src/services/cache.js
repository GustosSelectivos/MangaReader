// Simple cache with localStorage + in-memory fallback
// get(key): returns value or null
// set(key, value, ttlMs): stores with expiry
// keyFrom(ep, params): stable key for endpoint + params

const mem = new Map()

function now() { return Date.now() }

function get(key) {
  try {
    const raw = localStorage.getItem(key)
    if (raw) {
      const obj = JSON.parse(raw)
      if (!obj.expires || obj.expires > now()) return obj.value
      // expired
      localStorage.removeItem(key)
    }
  } catch {}
  if (mem.has(key)) {
    const { value, expires } = mem.get(key)
    if (!expires || expires > now()) return value
    mem.delete(key)
  }
  return null
}

function set(key, value, ttlMs) {
  const expires = ttlMs ? (now() + ttlMs) : null
  mem.set(key, { value, expires })
  try {
    const payload = JSON.stringify({ value, expires })
    localStorage.setItem(key, payload)
  } catch {}
}

function keyFrom(ep, params = {}) {
  const ordered = Object.keys(params).sort().reduce((acc,k)=>{ acc[k]=params[k]; return acc }, {})
  return `api:${ep}?${JSON.stringify(ordered)}`
}

export default { get, set, keyFrom }
