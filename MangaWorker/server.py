from fastapi import FastAPI, HTTPException, BackgroundTasks, Security, Depends
from fastapi.security.api_key import APIKeyHeader
from pydantic import BaseModel
import os
import shutil
import asyncio
import aiohttp
import re
from urllib.parse import urlparse

app = FastAPI()

# Configuración de Seguridad
API_KEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

async def get_api_key(api_key_header: str = Security(api_key_header)):
    """Verifica que la petición tenga la API Key correcta"""
    expected_key = os.getenv("WORKER_API_KEY")
    
    # Si no hay variable configurada en el servidor, advertimos pero permitimos (o bloqueamos)
    # Para producción, bloqueamos por seguridad.
    if not expected_key:
        print("⚠️  ALERTA DE SEGURIDAD: WORKER_API_KEY no configurada en entorno.")
        raise HTTPException(status_code=500, detail="Server misconfiguration: Missing API Key")
        
    if api_key_header != expected_key:
        raise HTTPException(status_code=403, detail="Acceso Denegado: API Key inválida")
    return api_key_header

class ChapterRequest(BaseModel):
    url: str

async def download_image(session, url, current_index, total, save_dir):
    """Descarga asíncrona (Copiada y adaptada de worker.py)"""
    try:
        filename = f"{current_index:03d}.webp"
        filepath = os.path.join(save_dir, filename)
        
        async with session.get(url) as response:
            if response.status == 200:
                data = await response.read()
                with open(filepath, "wb") as f:
                    f.write(data)
                print(f"✅ [Server] Guardada {filename}")
                return filepath
            return None
    except Exception as e:
        print(f"❌ Exception en {url}: {e}")
        return None

async def process_chapter_task(chapter_url: str):
    print(f"🚀 [Server] Iniciando tarea de fondo para: {chapter_url}")
    
    # === Lógica de Scraping (Mirror de worker.py) ===
    try:
        domain = urlparse(chapter_url).netloc
        headers = {
            "User-Agent": "Mozilla/5.0",
            "Referer": f"https://{domain}/"
        }
        
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.get(chapter_url) as response:
                if response.status != 200:
                    print(f"❌ Error HTTP: {response.status}")
                    return
                
                # Auto-Cascade para TMO
                final_url = str(response.url)
                html = ""
                if "/paginated" in final_url:
                     cascade_url = final_url.replace("/paginated", "/cascade")
                     print("[Server] Switching to Cascade...")
                     async with session.get(cascade_url) as r2:
                         if r2.status == 200: html = await r2.text()
                else:
                    html = await response.text()
        
        # Extracción de imágenes (BeautifulSoup + Regex)
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, 'html.parser')
        images = soup.find_all('img')
        image_urls = []
        for img in images:
            src = img.get('src')
            if src and ('uploads' in src or 'storage' in src) and not 'logo' in src:
                image_urls.append(src)
        
        # Fallback Regex
        if not image_urls:
            urls = re.findall(r'(https?://[^"\s]+\.(?:jpg|jpeg|png|webp))', html)
            image_urls = [u for u in urls if 'uploads' in u and 'logo' not in u]
            
        image_urls = list(dict.fromkeys(image_urls))
        print(f"🔍 [Server] Encontradas {len(image_urls)} imágenes")
        
        if not image_urls: return

        # Descarga
        # Usamos carpeta temporal basada en ID o hash (aquí simple por demo)
        download_dir = "downloads_staging"
        os.makedirs(download_dir, exist_ok=True)
        
        async with aiohttp.ClientSession(headers=headers) as session:
            tasks = []
            for i, url in enumerate(image_urls):
                tasks.append(download_image(session, url, i+1, len(image_urls), download_dir))
            await asyncio.gather(*tasks)
            
        print("✨ [Server] Descarga completa. Iniciando subida a B2...")
        # upload_to_b2(download_dir)...
        # shutil.rmtree(download_dir) # Limpieza
        
    except Exception as e:
        print(f"🔥 Error Crítico en worker: {e}")


@app.post("/download")
async def start_download(req: ChapterRequest, background_tasks: BackgroundTasks, api_key: str = Depends(get_api_key)):
    """Endpoint que recibe la URL y lanza el trabajo en background"""
    background_tasks.add_task(process_chapter_task, req.url)
    return {"status": "started", "message": f"Procesando {req.url} en segundo plano"}

@app.get("/health")
def health_check():
    return {"status": "ok", "service": "MangaWorker"}
