/**
 * Transform Backblaze B2 URLs to Cloudflare Worker CDN URLs
 * 
 * @param {string} url - The original URL (potentially from B2)
 * @param {object} options - Resize options { w, q }
 * @returns {string} - The optimized CDN URL
 */
export function toCdnUrl(url, options = {}) {
    if (!url || typeof url !== 'string') return url;

    // Configuration
    const CDN_HOST = 'https://img.miswebtoons.uk'; // Cloudflare Worker domain
    const B2_HOSTS = ['s3.us-east-005.backblazeb2.com', 'f005.backblazeb2.com'];

    try {
        const urlObj = new URL(url);

        // Check if it's a B2 URL
        if (B2_HOSTS.includes(urlObj.hostname)) {
            // Replace host with CDN host
            const newUrl = new URL(url.replace(urlObj.origin, CDN_HOST));

            // Add options
            if (options.w) newUrl.searchParams.set('w', options.w);
            if (options.q) newUrl.searchParams.set('q', options.q);

            return newUrl.toString();
        }
    } catch (e) {
        // invalid url, return original
    }

    return url;
}
