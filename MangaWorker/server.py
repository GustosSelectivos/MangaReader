from fastapi import FastAPI, HTTPException, BackgroundTasks, Security, Depends
from fastapi.security.api_key import APIKeyHeader
from pydantic import BaseModel
import os
import shutil
import asyncio
import worker  # Import the refactored worker module

app = FastAPI()

# Configuración de Seguridad
API_KEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

async def get_api_key(api_key_header: str = Security(api_key_header)):
    """Verifica que la petición tenga la API Key correcta"""
    expected_key = os.getenv("WORKER_API_KEY")
    
    if not expected_key:
        print("⚠️  ALERTA DE SEGURIDAD: WORKER_API_KEY no configurada en entorno.")
        # Check if we are in dev/test, otherwise raise error
        # raise HTTPException(status_code=500, detail="Server misconfiguration: Missing API Key")
        pass # Allow for dev for now
        
    if expected_key and api_key_header != expected_key:
        raise HTTPException(status_code=403, detail="Acceso Denegado: API Key inválida")
    return api_key_header

class ChapterRequest(BaseModel):
    url: str
    series_title: str
    chapter_number: int
    series_code: str = None # Optional

async def process_chapter_task(req: ChapterRequest):
    print(f"🚀 [Server] Iniciando tarea de fondo para: {req.url}")
    
    try:
        # 1. Generate Codename & Paths
        if req.series_code:
            series_code = req.series_code
            print(f"🔹 [Server] Usando código manual: {series_code}")
        else:
            series_code = worker.codename_from_title(req.series_title)
            print(f"🔹 [Server] Código generado: {series_code}")
            
        base_chapters_dir = os.path.join(os.getcwd(), 'chapters', series_code)
        os.makedirs(base_chapters_dir, exist_ok=True)
        
        # 2. Process (Scrape & Download)
        download_dir, count = await worker.process_chapter(req.url, req.chapter_number, base_chapters_dir)
        
        if not download_dir or count == 0:
            print("❌ [Server] Falló la descarga o no se encontraron imágenes.")
            # TODO: Notify Backend of Failure
            return

        print(f"✅ [Server] Descarga exitosa ({count} imágenes). Iniciando subida...")

        # 3. Upload to B2 (using Env Creds)
        # Note: server should have API_USER/API_PASS in env
        success = await worker.upload_directory_to_b2(download_dir)
        
        if success:
            print(f"✨ [Server] Subida completada para {req.series_title} - Cap {req.chapter_number}")
            await notify_backend_completion(req)
        else:
            print("❌ [Server] Falló la subida a B2.")
            # TODO: Notify Backend of Failure

        # 4. Cleanup (Optional: Remove local files if upload success)
        # shutil.rmtree(download_dir) 
        
    except Exception as e:
        print(f"🔥 Error Crítico en worker: {e}")

async def notify_backend_completion(req: ChapterRequest):
    url = f"{worker.API_BASE_URL}/chapters/completed/"
    payload = {
        "series_title": req.series_title,
        "chapter_number": req.chapter_number,
        "status": "success"
    }
    # Authenticate if needed (worker.py has login logic, but maybe we assume server is trusted IP or uses key?)
    # For now, simplistic post.
    try:
        async with aiohttp.ClientSession() as session:
             # We might need token. worker.login_and_get_token?
             # Let's try without first (if backend view has IsAuthenticated, it will fail).
             # ChapterViewSet has permission_classes = [DRFDACPermission]. 
             # DRFDACPermission usually requires Auth.
             
             # Quick Hack: Login first.
             # We should cache token in a real app.
             token = await worker.login_and_get_token(session, os.getenv("API_USER"), os.getenv("API_PASS"))
             headers = {"Authorization": f"Bearer {token}"} if token else {}
             
             async with session.post(url, json=payload, headers=headers) as resp:
                 if resp.status == 200:
                     print("✅ [Server] Notificación enviada al Backend")
                 else:
                     text = await resp.text()
                     print(f"⚠️ [Server] Falló notificación al Backend: {resp.status} - {text}")
    except Exception as e:
        print(f"❌ [Server] Error notificando al Backend: {e}")

@app.post("/download")
async def start_download(req: ChapterRequest, background_tasks: BackgroundTasks, api_key: str = Depends(get_api_key)):
    """Endpoint que recibe la URL y lanza el trabajo en background"""
    background_tasks.add_task(process_chapter_task, req)
    return {"status": "started", "message": f"Procesando Cap {req.chapter_number} de {req.series_title}"}

@app.get("/health")
def health_check():
    return {"status": "ok", "service": "MangaWorker"}

