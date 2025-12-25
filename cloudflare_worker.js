export default {
    async fetch(request, env, ctx) {
        const url = new URL(request.url)

        // Solo procesar imágenes (extensiones comunes)
        if (!url.pathname.match(/\.(jpg|jpeg|png|webp)$/i)) {
            return fetch(request)
        }

        // Parámetros de redimensionamiento
        // Si no vienen, se pueden poner valores por defecto o no redimensionar
        const width = url.searchParams.get("w") ? parseInt(url.searchParams.get("w")) : undefined
        const quality = url.searchParams.get("q") ? parseInt(url.searchParams.get("q")) : 75

        // URL del origen (Backblaze B2)
        // Basado en tus logs, tus imágenes salen de f005.backblazeb2.com
        // La ruta suele ser /file/MangaApi/...
        const originUrl = new URL(url.toString())
        originUrl.hostname = "f005.backblazeb2.com"
        originUrl.protocol = "https:"

        // Cloudflare Image Resizing options
        // Solo se aplican si estamos en un plan que lo soporte (Pro/Biz/Ent) o si se paga Images
        const imageOptions = {
            quality,
            format: "webp" // Forzar WebP
        }
        if (width) imageOptions.width = width

        // Petición al origen
        const response = await fetch(originUrl.toString(), {
            cf: {
                image: imageOptions,
                cacheTtl: 2592000 // Cachear 30 días en el Edge
            }
        })

        // Si el origen da error (404, etc), devolverlo tal cual
        if (!response.ok) return response

        // Devolver la imagen procesada con cabeceras de caché correctas para el navegador
        const newHeaders = new Headers(response.headers)
        newHeaders.set("Content-Type", "image/webp")
        newHeaders.set("Cache-Control", "public, max-age=31536000, immutable")
        // Eliminar cabeceras de origen que puedan molestar
        newHeaders.delete("content-length")

        return new Response(response.body, {
            status: response.status,
            headers: newHeaders
        })
    }
}
