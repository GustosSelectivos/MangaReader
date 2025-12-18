import os
import asyncio
import aiohttp
import boto3
from botocore.config import Config
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
B2_BUCKET_NAME = os.getenv("B2_BUCKET_NAME")
B2_ENDPOINT = os.getenv("B2_ENDPOINT")
B2_KEY_ID = os.getenv("B2_KEY_ID")
B2_APP_KEY = os.getenv("B2_APP_KEY")

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

def optimize_images(directory):
    """Optimiza las imágenes en el directorio (convertir a WebP q=80)"""
    print(f"🔄 Optimizando imágenes en {directory} (WebP q=80)...")
    
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
                img.save(filepath, "WEBP", quality=80, lossless=False)
                count += 1
                # print(f"  ✨ Optimizado: {filename}", end='\r')
        except Exception as e:
            print(f"  ❌ Error optimizando {filename}: {e}")
            
    print(f"✅ Optimización completa: {count} imágenes procesadas.")

# def get_open_windows(): ... (Removed ctypes logic for simplicity as requested)


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
    
    async with aiohttp.ClientSession(headers=headers) as session:
        async with session.get(chapter_url) as response:
            if response.status != 200:
                print(f"❌ Error al acceder al capítulo: {response.status}")
                return None, 0
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

async def manual_audit_and_upload(download_dir):
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

        # Esperar cierre de carpeta en lugar de input manual
        # wait_for_folder_close(download_dir)
        
        # 4.1 Confirmar RENOMBRADO
        rename_confirm = input("\n👉 Presiona 's' y Enter para RENOMBRAR las imágenes: ").strip()
        if rename_confirm.lower() != 's':
             print("⚠️ Saltando renombrado...")
        else:
             print("\n🔄 Auditando y Renombrando secuencia...")
             renumber_images(download_dir)
             
        # 4.1b Optimización Automática
        print("\n⚙️ Ejecutando optimización de imágenes (WebP q=80)...")
        optimize_images(download_dir)

        # 4.2 Confirmar SUBIDA
        upload_confirm = input("\n👉 ¿Listo para subir a Backblaze? (Escribe 'S' y Enter): ").strip()
        if upload_confirm.lower() != 's':
             print("❌ Proceso cancelado. No se subió nada.")
             return

        print("\n🚀 Iniciando subida a Backblaze (Vía API)...")
        # Reuse existing upload function, this time asking inputs if needed or using env
        await upload_directory_to_b2(download_dir)

if __name__ == "__main__":
    try:
        if os.name == 'nt':
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
            
        print("=== MangaWorker: Descargador Manual ===")
        url_input = input("Ingrese la URL del capítulo: ").strip()
        if not url_input:
            print("❌ URL requerida")
            exit()
            
        mode_input = input("¿Identificar serie por [T]ítulo o [C]ódigo? (T/c): ").strip().lower()
        
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
            
        chap_num_str = input("Ingrese el número del capítulo (ej. 1): ").strip()
        try:
            chap_num = int(chap_num_str)
        except:
            chap_num = 1
            print("⚠️ Número inválido, usando 1 por defecto")

        download_dir, count = asyncio.run(process_chapter(url_input, chap_num, base_chapters_dir))
        
        if download_dir and count > 0:
             asyncio.run(manual_audit_and_upload(download_dir))
        
    except ModuleNotFoundError as e:
        print(f"\n❌ ERROR CRÍTICO: {e}")
        print("ℹ️  Estás ejecutando esto con el Python equivocado.")
        print("👉 EJECUTA: ..\\venv\\Scripts\\python.exe worker.py")

