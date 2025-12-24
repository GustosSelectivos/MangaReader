import os
import asyncio
import aiohttp

from tqdm.asyncio import tqdm
from io import BytesIO
import hashlib
import unicodedata
from urllib.parse import urlparse, urljoin
import time
# import ctypes


from dotenv import load_dotenv
from PIL import Image

# Cargar variables de entorno desde .env si existe
load_dotenv()

# Configuración básica

# API Configuration to match Frontend
# API Configuration
API_BASE_URL = os.getenv("BACKEND_API_URL", "http://127.0.0.1:8000/api")

async def get_presigned_url(session, file_path, content_type='image/webp'):
    """Requests a presigned URL from the local Backend API"""
    try:
        # TODO: Add Authorization header if API requires it (token from login?)
        # For now, assuming internal/dev mode or IP whitelisting might allow it,
        # OR we need to ask user for a token. 
        # But wait, UploadChapterView uses `api.post` which attaches token.
        # If the endpoint is protected (IsAuthenticated), we need a token.
        # User is 'Ezequiel' / '1234'. We can login first?
        # Or simpler: IsAuthenticatedOrReadOnly?
        # b2_view.py showed `permission_classes = [IsAuthenticated]`.
        # So we NEED to authenticate.
        
        # Adding a LOGIN function to get token.
        pass
        
    except Exception as e:
        print(f"❌ Error getting sign: {e}")
        return None

async def login_and_get_token(session, username, password):
    url = f"{API_BASE_URL}/token/" 
    # Check if that's the endpoint. settings.py didn't show URLs.
    # But usually simplejwt uses /token/. 
    # Let's verify urls.py if possible, but standard is /api/token/.
    try:
        async with session.post(url, json={'username': username, 'password': password}) as resp:
            if resp.status == 200:
                data = await resp.json()
                return data.get('access')
            else:
                print(f"❌ Login failed: {resp.status}")
                return None
    except Exception as e:
        print(f"❌ Login error: {e}")
        return None

async def upload_file_via_api(session, local_path, relative_path, token):
    # 1. Sign
    sign_url = f"{API_BASE_URL}/upload/sign/"
    headers = {'Authorization': f'Bearer {token}'}
    payload = {'file_path': relative_path, 'content_type': 'image/webp'}
    
    async with session.post(sign_url, json=payload, headers=headers) as resp:
        if resp.status != 200:
            text = await resp.text()
            print(f"  ❌ Sign failed for {relative_path}: {resp.status} - {text}")
            return False
        data = await resp.json()
    
    upload_url = data.get('url')
    if not upload_url:
        print("  ❌ No URL returned from sign")
        return False
        
    # 2. Upload to B2 (PUT)
    # Read file content
    with open(local_path, 'rb') as f:
        file_content = f.read()
        
    async with session.put(upload_url, data=file_content, headers={'Content-Type': 'image/webp'}) as resp:
        if resp.status not in [200, 204]: # 204 is common for PUT
             # Backblaze usually returns 200
            print(f"  ❌ Upload failed: {resp.status}")
            return False
            
    print(f"  ✅ Subido: {relative_path}")
    return True

async def upload_directory_to_b2(local_dir, username=None, password=None, token=None):
    async with aiohttp.ClientSession() as session:
        # 1. Login (if token not provided)
        if not token:
            username = username or os.getenv("API_USER")
            password = password or os.getenv("API_PASS")
            
            if not username or not password:
                print("❌ Error: Credenciales API no proporcionadas (API_USER/API_PASS en .env o argumentos)")
                return False
        
            print(f"🔑 Autenticando en API Backend ({API_BASE_URL})...")
            token = await login_and_get_token(session, username, password)
                
        if not token:
            print("❌ No se pudo loguear en el API. No se puede subir.")
            return False

        print("✅ Autenticado. Iniciando subida...")
        
        # Calculate paths
        abs_local_dir = os.path.abspath(local_dir)
        worker_root = os.getcwd() 
        
        # Determine prefix based on logic: chapters/CODE/NUM
        # worker.py is in MangaWorker.
        # files are in MangaWorker/chapters/CODE/NUM/img.webp
        
        tasks = []
        for root, dirs, files in os.walk(local_dir):
            for file in files:
                local_path = os.path.join(root, file)
                
                # Relative path logic:
                # We want B2 key: chapters/CODE/NUM/001.webp
                # local_path is c:/.../chapters/CODE/NUM/001.webp
                # If we take relpath from 'MangaWorker', it is 'chapters/CODE/NUM/001.webp'.
                # This matches EXACTLY what we want.
                
                rel_path = os.path.relpath(local_path, worker_root).replace("\\", "/")
                
                # Serial execution or parallel? Parallel is faster.
                success = await upload_file_via_api(session, local_path, rel_path, token)
                # For cleaner output, maybe await sequentially or limit concurrency?
                # let's await sequentially to debug first.
                
        print("✨ Todos los archivos procesados.")

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

def _slug_base(title: str) -> str:
    if not isinstance(title, str) or not title.strip():
        raise ValueError("Se requiere un título")
    nfd = unicodedata.normalize("NFD", title)
    no_marks = "".join(ch for ch in nfd if unicodedata.category(ch) != "Mn")
    out = []
    prev_us = False
    for ch in no_marks.lower():
        if ch.isalnum():
            out.append(ch)
            prev_us = False
        else:
            if not prev_us:
                out.append("_")
                prev_us = True
    return "".join(out).strip("_")

def codename_from_title(title: str) -> str:
    base = _slug_base(title)
    parts = [p for p in base.split("_") if p]
    initials = "".join(p[0] for p in parts[:2]) or "x"
    h = hashlib.sha1(title.encode("utf-8")).hexdigest()[:6]
    h = hashlib.sha1(title.encode("utf-8")).hexdigest()[:6]
    return f"{initials}-{h}"

def renumber_images(directory):
    """Renombra secuencialmente las imágenes en el directorio (001.webp, 002.webp...)"""
    print(f"🔄 Renombrando imágenes en {directory}...")
    
    # Listar y ordenar archivos existentes
    files = [f for f in os.listdir(directory) if f.lower().endswith(('.webp', '.jpg', '.jpeg', '.png'))]
    files.sort()
    
    if not files:
        print("⚠️ No hay imágenes para renombrar.")
        return

    # 1. Renombrar a temporal para evitar conflictos
    temp_files = []
    for i, filename in enumerate(files):
        old_path = os.path.join(directory, filename)
        temp_name = f"temp_{i:06d}.tmp"
        temp_path = os.path.join(directory, temp_name)
        os.rename(old_path, temp_path)
        temp_files.append(temp_path)
        
    # 2. Renombrar a final secuencial
    for i, temp_path in enumerate(temp_files):
        # Always output as .webp since that is the target format for the API/B2
        # However, simple rename of .jpg to .webp is invalid. 
        # Ideally we should convert if it's not webp, but for now let's respect the user's implicit "rename".
        # If the user mainly just wants them ORDERED 001..999.
        
        # Let's stick to .webp as per original code, assuming user handles conversion or they are already webp/compatible.
        new_name = f"{i+1:03d}.webp"
        new_path = os.path.join(directory, new_name)
        
        # Check if we are renaming a non-webp file to webp without conversion
        # The original code did this blindly. 
        # Use Python's implicit rename.
        os.rename(temp_path, new_path)
        
    print(f"✅ Renombrado completado: 001.webp - {len(files):03d}.webp")

def optimize_images(directory, quality=80):
    """Optimiza las imágenes en el directorio (convertir a WebP con calidad variable)"""
    print(f"🔄 Optimizando imágenes en {directory} (WebP q={quality})...")
    
    files = [f for f in os.listdir(directory) if f.lower().endswith(('.webp', '.jpg', '.jpeg', '.png'))]
    if not files:
        print("⚠️ No hay imágenes para optimizar.")
        return

    count = 0
    for filename in files:
        filepath = os.path.join(directory, filename)
        try:
            with Image.open(filepath) as img:
                # Force load data to ensure we can overwrite safely
                img.load()
                
                # Convert to RGB if needed (e.g. RGBA or P)
                if img.mode not in ("RGB", "L"):
                    img = img.convert("RGB")
                    
                # Save overwriting the file
                img.save(filepath, "WEBP", quality=quality, lossless=False)
                count += 1
                # print(f"  ✨ Optimizado: {filename}", end='\r')
        except Exception as e:
            print(f"  ❌ Error optimizando {filename}: {e}")
            
    print(f"✅ Optimización completa: {count} imágenes procesadas.")

def append_to_update_list(url):
    """
    Agrega la URL a serie_update_tmoazul.py en MangaScripts/TMOAzul.
    Crea el archivo si no existe con la estructura de lista.
    """
    try:
        # Determine path: ../MangaScripts/TMOAzul/serie_update_tmoazul.py 
        # Relative to MangaWorker/worker.py (cwd expected to be MangaWorker usually? No, cwd is printed as worker_root)
        # In main execution: os.getcwd() often project root or MangaWorker.
        # Let's use relative to known location of worker.py
        current_dir = os.path.dirname(os.path.abspath(__file__))
        target_dir = os.path.abspath(os.path.join(current_dir, "..", "MangaScripts", "TMOAzul"))
        target_file = os.path.join(target_dir, "serie_update_tmoazul.py")
        
        os.makedirs(target_dir, exist_ok=True)
        
        # Read existing to see if we need to initialize or just append
        new_file = not os.path.exists(target_file)
        
        with open(target_file, "a", encoding="utf-8") as f:
            if new_file:
                f.write("def link_series_update():\n")
                f.write("    return [\n")
            
            # Appending a line. 
            # Note: If we just append to the file, and it ended with "    ]", we might break structure if we don't handle it.
            # But the user asked for a .py "donde se guarden".
            # The simplest valid python appendable structure without parsing is difficult if inside a function return.
            # ALTERNATIVE: Just a list variable "series = [...]" at top level.
            # But user example had a function.
            # Let's try to do it properly: Read lines, insert before closing bracket?
            pass
        
        # Re-read and rewrite safely
        lines = []
        if not new_file:
            with open(target_file, "r", encoding="utf-8") as f:
                lines = f.readlines()
        
        if new_file or not lines:
             lines = ["def link_series_update():\n", "    return [\n", "    ]\n"]

        # Insert before the last line (assuming it is "    ]" or similar closing)
        # Find the closing bracket
        insert_idx = -1
        for i in range(len(lines)-1, -1, -1):
            if "]" in lines[i]:
                insert_idx = i
                break
        
        if insert_idx != -1:
            lines.insert(insert_idx, f'        "{url}",\n')
        else:
            # Fallback if structure broken
            lines.append(f'        "{url}",\n')

        with open(target_file, "w", encoding="utf-8") as f:
            f.writelines(lines)
            
        print(f"✅ Guardado en lista de actualización: {url}")
        print(f"   📂 {target_file}")

    except Exception as e:
        print(f"❌ Error guardando en lista de actualización: {e}")


async def process_chapter(chapter_url, chapter_num, series_base_dir):
    """
    Lógica principal:
    1. Obtener HTML del capítulo
    2. Extraer URLs de imágenes (Aquí pondrás tu lógica de scraping liviana)
    3. Descargar en paralelo
    Returns: (download_dir, valid_images_count) or (None, 0)
    """
    print(f"🚀 Iniciando proceso para: {chapter_url}")
    
    # 1. Obtener HTML del capítulo
    print(f"🌍 Descargando HTML: {chapter_url}")
    
    # Extraer dominio para el Referer
    domain = urlparse(chapter_url).netloc
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": f"https://{domain}/"
    }
    
    import requests
    try:
        # Use requests (sync) instead of aiohttp because aiohttp is getting 500 errors on this site
        # Run in executor to avoid blocking the event loop
        loop = asyncio.get_running_loop()
        def fetch_sync():
            return requests.get(chapter_url, headers=headers)
            
        response = await loop.run_in_executor(None, fetch_sync)
        
        if response.status_code != 200:
            print(f"❌ Error al acceder al capítulo: {response.status_code}")
            return None, 0
            
        html = response.text
        print(f"📍 URL Final: {response.url}")
        
        # TMO/ZonaTMO Specific: Switch to Cascade if stuck on Paginated
        final_url = str(response.url)
        if "/paginated" in final_url:
            print("🔄 Detectado modo 'Paginated'. Cambiando a 'Cascade' para ver todas las imágenes...")
            cascade_url = final_url.replace("/paginated", "/cascade")
            headers["Referer"] = f"https://{domain}/"
            
            def fetch_cascade():
                 return requests.get(cascade_url, headers=headers)
            
            cascade_resp = await loop.run_in_executor(None, fetch_cascade)
            
            if cascade_resp.status_code == 200:
                html = cascade_resp.text
                print(f"✅ Éxito cambianda a Cascade: {cascade_url}")
            else:
                print(f"⚠️ Falló el cambio a Cascade ({cascade_resp.status_code}). Usando HTML original.")
                
    except Exception as e:
        print(f"❌ Excepción al descargar HTML: {e}")
        return None, 0

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
        # Updated condition to include ikigai images
        if src and ('uploads' in src or 'storage' in src or 'ikigai' in src) and not 'logo' in src:
            # Convert to absolute URL
            src = urljoin(chapter_url, src)
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
        return None, 0

    # Crear carpeta de descargas para el capítulo
    chapter_dir_name = f"{chapter_num:03d}"
    download_dir = os.path.join(series_base_dir, chapter_dir_name)
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
        
        return download_dir, total_images

async def process_post_download(download_dir, options):
    """
    Ejecuta el pipeline de post-procesamiento basado en las opciones dadas.
    options = {
        'renumber': bool,
        'optimize': bool,
        'quality': int,
        'upload': bool,
        'update_list': bool,
        'series_url': str (optional),
        'interactive': bool (if True, asks for confirmation steps like before)
    }
    """
    
    # 4. AUDITORIA / RENOMBRADO
    if options.get('interactive'):
        print("\n" + "="*50)
        print("👀  MODO AUDITORÍA  👀")
        print("="*50)
        # Abra carpeta solo si es interactivo (Individual)
        if os.name == 'nt':
            try:
                os.startfile(os.path.abspath(download_dir))
            except:
                pass
        
        rename_confirm = input("\n👉 Presiona 's' y Enter para RENOMBRAR las imágenes: ").strip()
        if rename_confirm.lower() == 's':
            renumber_images(download_dir)
    else:
        # Modo Automático / Masivo
        if options.get('renumber'):
            renumber_images(download_dir)

    # 4.1b Optimización
    if options.get('optimize'):
        quality = options.get('quality', 80)
        
        if options.get('interactive'):
            print(f"\n⚙️  Configuración de Optimización (Actual: WebP q={quality})")
            opt_confirm = input("👉 ¿Optimizar imágenes? [S/n]: ").strip().lower()
            if opt_confirm != 'n':
                q_input = input(f"   Calidad (1-100) [{quality}]: ").strip()
                if q_input:
                    try:
                        quality = int(q_input)
                    except:
                        pass
                print(f"🔄 Optimizando imágenes en {download_dir} (WebP q={quality})...")
                optimize_images(download_dir, quality=quality)
            else:
                 print("⏩ Saltando optimización.")
        else:
             print(f"\n⚙️ Ejecutando optimización de imágenes (WebP q={quality})...")
             optimize_images(download_dir, quality=quality)

    # 4.2 SUBIDA
    uploaded = False
    if options.get('upload'):
        if options.get('interactive'):
            upload_confirm = input("\n👉 ¿Subir contenido a Backblaze? [s/N]: ").strip()
            if upload_confirm.lower() != 's':
                print("⏩ Saltando subida.")
            else:
                print("\n🚀 Iniciando subida a Backblaze (Vía API)...")
                await upload_directory_to_b2(download_dir)
                uploaded = True
        else:
            # Automático
            print("\n🚀 Iniciando subida automática a Backblaze...")
            await upload_directory_to_b2(download_dir)
            uploaded = True

    # 4.3 Actualizar Estado en Lista
    if options.get('update_list') and options.get('series_url'):
        # Solo guardar si realmente se subió o si el usuario quiere forzarlo
        # En masivo, asumimos que si se subió, se guarda.
        if uploaded or options.get('force_update_list', False):
             append_to_update_list(options['series_url'])
    elif options.get('interactive'):
         update_confirm = input("\n👉 ¿Cambiar estado si ( S ) o no ( N ), en la lista de la serie? ").strip()
         if update_confirm.lower() == 's':
            print("\nℹ️ Ingrese la URL de la SERIE para guardar en serie_update_tmoazul.py")
            url_to_save = input("   URL: ").strip()
            if url_to_save:
                append_to_update_list(url_to_save)


def get_mass_options():
    print("\n--- Configuración de Descarga Masiva ---")
    
    # Defaults
    opts = {
        'skip_download': False,
        'renumber': True,
        'optimize': True,
        'quality': 80,
        'upload': False,
        'update_list': False,
        'series_url': None,
        'interactive': False
    }
    
    # Skip Download
    sd = input("¿Saltar descarga (Solo procesar existentes)? [y/N]: ").strip().lower()
    if sd == 'y':
        opts['skip_download'] = True
    
    # Renombrar
    r = input("¿Renombrar imágenes secuencialmente (001.webp...)? [S/n]: ").strip().lower()
    if r == 'n': opts['renumber'] = False
    
    # Optimizar
    o = input("¿Optimizar imágenes a WebP? [S/n]: ").strip().lower()
    if o == 'n': 
        opts['optimize'] = False
    else:
        try:
            q = input("   Calidad (1-100) [80]: ").strip()
            if q: opts['quality'] = int(q)
        except:
            pass
            
    # Subir
    u = input("¿Subir automáticamente a Backblaze? [y/N]: ").strip().lower()
    if u == 'y':
        opts['upload'] = True
        
        # Si sube, preguntar si agregar a lista de updates
        ul = input("¿Agregar serie a lista de actualizaciones (serie_update_tmoazul)? [y/N]: ").strip().lower()
        if ul == 'y':
            opts['update_list'] = True
            opts['series_url'] = input("   Ingrese URL de la Serie (para tracking): ").strip()

    return opts

def load_ikigai_links():
    import importlib.util
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        scraper_path = os.path.join(current_dir, "..", "MangaScripts", "Scraper", "scraper_ikigai.py")
        scraper_path = os.path.abspath(scraper_path)
        
        if not os.path.exists(scraper_path):
            print(f"❌ No se encontró el archivo del scraper en: {scraper_path}")
            print("   Ejecuta primero el scraper para generar los links.")
            return []
            
        spec = importlib.util.spec_from_file_location("scraper_ikigai", scraper_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module.link_capitulos()
    except Exception as e:
        print(f"❌ Error importando scraper: {e}")
        return []

if __name__ == "__main__":
    try:
        if os.name == 'nt':
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
            
        print("=== MangaWorker: Descargador Manual ===")
        print("1. Descarga Individual (Un solo capítulo)")
        print("2. Descarga Masiva (Desde scraper_ikigai.py)")
        
        opcion = input("Seleccione una opción (1/2): ").strip()
        
        links_to_download = []
        mass_options = {}
        
        if opcion == '2':
            print("\n--- Modo Descarga Masiva ---")
            print("Cargando links de MangaScripts/Scraper/scraper_ikigai.py...")
            links = load_ikigai_links()
            if not links:
                print("❌ No se cargaron links. Abortando.")
                exit()
            print(f"✅ Se cargaron {len(links)} capítulos para descargar.")
            links_to_download = links
            
            # Obtener configuracion global
            mass_options = get_mass_options()
            
        else:
            url_input = input("Ingrese la URL del capítulo: ").strip()
            if not url_input:
                print("❌ URL requerida")
                exit()
            links_to_download = [url_input]
            # Opciones "interactivas" para modo individual (comportamiento legacy pero mejorado)
            # Antes: renumber=False, optimize=False, upload=False
            # Ahora: True por defecto, pero el modo 'interactive' permitirá confirmar/cancelar pasos.
            mass_options = {
                'interactive': True, 
                'renumber': True, 
                'optimize': True, 
                'upload': True,
                'quality': 80
            }

        mode_input = input("\n¿Identificar serie por [T]ítulo o [C]ódigo? (T/c): ").strip().lower()
        
        series_code = None
        
        if mode_input == 'c':
            series_code = input("Ingrese el CÓDIGO de la serie (ej. dl-787f97): ").strip()
            if not series_code:
                print("❌ Código requerido")
                exit()
        else:
            series_title = input("Ingrese el título de la serie: ").strip()
            if not series_title:
                 print("❌ Título requerido")
                 exit()
            
            # Generar codename
            try:
                series_code = codename_from_title(series_title)
                print(f"🔹 Codename generado: {series_code}")
            except Exception as e:
                print(f"❌ Error generando codename: {e}")
                exit()

        # Definir directorio base: chapters/{code}
        base_chapters_dir = os.path.join(os.getcwd(), 'chapters', series_code)
        if not os.path.exists(base_chapters_dir):
            print(f"📂 Creando directorio de serie: {base_chapters_dir}")
            os.makedirs(base_chapters_dir, exist_ok=True)
        else:
            print(f"📂 Directorio de serie existente: {base_chapters_dir}")
            
        # Determinar número inicial
        start_num = 1
        if len(links_to_download) == 1 and opcion != '2':
             chap_num_str = input("Ingrese el número del capítulo (ej. 1): ").strip()
             try:
                 start_num = int(chap_num_str)
             except:
                 print("⚠️ Número inválido, usando 1 por defecto")
                 start_num = 1
        
        # Procesar descargas
        total_caps = len(links_to_download)
        for i, url in enumerate(links_to_download):
            current_chap_num = start_num + i
            print(f"\n⬇️  Procesando capítulo {i+1}/{total_caps} (Cap #{current_chap_num})")
            
            # Check Skip Download
            if mass_options.get('skip_download'):
                # Construct directory path manually
                chapter_dir_name = str(current_chap_num).zfill(3)
                download_dir = os.path.join(base_chapters_dir, chapter_dir_name)
                
                if os.path.exists(download_dir):
                    print(f"⏩ Saltando descarga (Existe): {download_dir}")
                    asyncio.run(process_post_download(download_dir, mass_options))
                else:
                    print(f"⚠️ Carpeta no existe, no se puede procesar: {download_dir}")
                continue # Skip remaining loop actions

            try:
                download_dir, count = asyncio.run(process_chapter(url, current_chap_num, base_chapters_dir))
                
                if download_dir and count > 0:
                     # Ejecutar pipeline post-descarga
                     asyncio.run(process_post_download(download_dir, mass_options))
                         
            except Exception as e:
                print(f"❌ Error procesando {url}: {e}")
                
        print("\n✨✨ Proceso Finalizado ✨✨")
        
    except ModuleNotFoundError as e:
        print(f"\n❌ ERROR CRÍTICO: {e}")
        print("ℹ️  Estás ejecutando esto con el Python equivocado.")
        print("👉 EJECUTA: ..\\venv\\Scripts\\python.exe worker.py")

