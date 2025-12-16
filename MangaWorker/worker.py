import os
import asyncio
import aiohttp
import boto3
from tqdm.asyncio import tqdm
from io import BytesIO

# Configuración básica (Idealmente usar venv variables)
# B2_BUCKET_NAME = os.getenv("B2_BUCKET_NAME")
# B2_ENDPOINT = os.getenv("B2_ENDPOINT")
# B2_KEY_ID = os.getenv("B2_KEY_ID")
# B2_APP_KEY = os.getenv("B2_APP_KEY")

async def download_image(session, url, current_index, total, save_dir):
    """Descarga una sola imagen de forma asíncrona y la guarda en disco"""
    try:
        filename = f"{current_index:03d}.webp"
        filepath = os.path.join(save_dir, filename)
        
        async with session.get(url) as response:
            if response.status == 200:
                data = await response.read()
                
                # Guardar en disco localmente (Simulación de "Tmp" antes de subir)
                with open(filepath, "wb") as f:
                    f.write(data)
                
                print(f"✅ Guardada {filename} ({current_index}/{total})")
                return filepath
            else:
                print(f"❌ Error descargando {url}: Status {response.status}")
                return None
    except Exception as e:
        print(f"❌ Exception en {url}: {e}")
        return None
    except Exception as e:
        print(f"❌ Exception en {url}: {e}")
        return None

async def process_chapter(chapter_url):
    """
    Lógica principal:
    1. Obtener HTML del capítulo
    2. Extraer URLs de imágenes (Aquí pondrás tu lógica de scraping liviana)
    3. Descargar en paralelo
    """
    print(f"🚀 Iniciando proceso para: {chapter_url}")
    
    # 1. Obtener HTML del capítulo
    print(f"🌍 Descargando HTML: {chapter_url}")
    
    # Extraer dominio para el Referer
    from urllib.parse import urlparse
    domain = urlparse(chapter_url).netloc
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": f"https://{domain}/"
    }
    
    async with aiohttp.ClientSession(headers=headers) as session:
        async with session.get(chapter_url) as response:
            if response.status != 200:
                print(f"❌ Error al acceder al capítulo: {response.status}")
                return
            html = await response.text()
            print(f"📍 URL Final tras redirección: {response.url}")
            
            # TMO/ZonaTMO Specific: Switch to Cascade if stuck on Paginated
            final_url = str(response.url)
            if "/paginated" in final_url:
                print("🔄 Detectado modo 'Paginated'. Cambiando a 'Cascade' para ver todas las imágenes...")
                cascade_url = final_url.replace("/paginated", "/cascade")
                
                # Update headers for the new request
                headers["Referer"] = f"https://{domain}/"
                
                async with session.get(cascade_url) as cascade_response:
                    if cascade_response.status == 200:
                        html = await cascade_response.text()
                        print(f"✅ Éxito cambianda a Cascade: {cascade_url}")
                    else:
                        print(f"⚠️ Falló el cambio a Cascade ({cascade_response.status}). Usando HTML original.")

    from bs4 import BeautifulSoup
    import re
    
    soup = BeautifulSoup(html, 'html.parser')
    
    # Olympus suele tener las imágenes en tags <img> dentro de un contenedor específico
    # Buscamos patrones comunes. NOTA: Esto puede variar si el sitio cambia.
    # Estrategia: Buscar todas las imágenes que parezcan del capítulo
    images = soup.find_all('img')
    image_urls = []
    
    for img in images:
        src = img.get('src')
        if src and ('uploads' in src or 'storage' in src) and not 'logo' in src:
            image_urls.append(src)
            
    # Si no encontramos nada, puede ser que estén en un script JSON (NextJS/React)
    if not image_urls:
         print("⚠️ No se encontraron imágenes en el HTML estático. Intentando búsqueda por Regex...")
         # Intento de regex para buscar URLs de imágenes comunes
         urls = re.findall(r'(https?://[^"\s]+\.(?:jpg|jpeg|png|webp))', html)
         image_urls = [u for u in urls if 'uploads' in u and 'logo' not in u]

    # Eliminar duplicados manteniendo orden
    image_urls = list(dict.fromkeys(image_urls))
    
    print(f"🔍 Encontradas {len(image_urls)} imágenes.")
    
    total_images = len(image_urls)
    if total_images == 0:
        print("❌ No se pudieron extraer imágenes. Puede que el sitio requiera JS (Selenium/Chromium).")
        return

    # Crear carpeta de descargas base
    base_download_dir = "downloads"
    os.makedirs(base_download_dir, exist_ok=True)
    
    # Buscar siguiente carpeta disponible 001-999
    download_dir = ""
    for i in range(1, 1000):
        folder_name = f"{i:03d}"
        path = os.path.join(base_download_dir, folder_name)
        if not os.path.exists(path):
            download_dir = path
            break
            
    if not download_dir:
        print("❌ Error: Se alcanzó el límite de 999 carpetas en downloads/")
        return

    os.makedirs(download_dir, exist_ok=True)
    print(f"📂 Guardando imágenes en: {os.path.abspath(download_dir)}")

    # 3. Descarga Paralela
    async with aiohttp.ClientSession(headers=headers) as session:
        tasks = []
        for i, url in enumerate(image_urls):
            task = download_image(session, url, i+1, total_images, download_dir)
            tasks.append(task)
        
        await asyncio.gather(*tasks)
        print(f"✨ ¡Descarga completa! Revisa la carpeta '{download_dir}'")
        
        # 4. AUDITORÍA MANUAL
        print("\n" + "="*50)
        print("👀  MODO AUDITORÍA  👀")
        print("="*50)
        print("1. Abre la carpeta 'downloads' y BORRA las imágenes que no quieras (publicidad, etc).")
        print("2. Verifica que el orden sea correcto.")
        
        # Abrir carpeta automáticamente en Windows
        if os.name == 'nt':
            try:
                os.startfile(os.path.abspath(download_dir))
            except:
                pass

        confirm = input("\n👉 ¿Listo para subir a Backblaze? (Escribe 'S' y Enter): ")
        if confirm.lower() != 's':
            print("❌ Proceso cancelado. No se subió nada.")
            return

        print("\n🚀 Iniciando subida a Backblaze (Simulada por ahora)...")
        # Aquí llamaríamos a la función upload_directory_to_b2(download_dir)
        print("✨ ¡Subida completada! (Mentira, es un print)")

if __name__ == "__main__":
    url_capitulo = "https://zonatmo.com/index.php/view_uploads/1682235"
    try:
        if os.name == 'nt':
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        asyncio.run(process_chapter(url_capitulo))
    except ModuleNotFoundError as e:
        print(f"\n❌ ERROR CRÍTICO: {e}")
        print("ℹ️  Estás ejecutando esto con el Python equivocado.")
        print("👉 EJECUTA: ..\\venv\\Scripts\\python.exe worker.py")

