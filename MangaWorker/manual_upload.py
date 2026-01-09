import os
import requests
import json
from dotenv import load_dotenv

# Reutilizar .env del worker
load_dotenv()

API_URL = os.getenv("BACKEND_API_URL", "http://127.0.0.1:8000/api")
# Adjust CDN/B2 host to match the requested format
B2_HOST = "https://f005.backblazeb2.com/file/MangaApi"

def get_token():
    """Autenticación para obtener token JWT"""
    username = os.getenv("API_USER")
    password = os.getenv("API_PASS")
    
    if not username or not password:
        # Fallback manual si no hay .env
        print("⚠️ No se encontraron API_USER/API_PASS en .env")
        username = input("Usuario API: ").strip()
        import getpass
        password = getpass.getpass("Contraseña API: ").strip()

    try:
        resp = requests.post(f"{API_URL}/token/", json={"username": username, "password": password})
        if resp.status_code == 200:
            return resp.json().get("access")
        else:
            print(f"❌ Error Login: {resp.status_code} - {resp.text}")
            return None
    except Exception as e:
        print(f"❌ Excepción Login: {e}")
        return None

def main():
    print("=== Subida Masiva de Capítulos (Registro API) ===")
    
    token = get_token()
    if not token:
        return

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    # 1. Inputs del usuario
    try:
        manga_id = int(input("ID del Manga (en la API): ").strip())
        series_code = input("Código de la serie (ej. dl-787f97): ").strip()
        base_path = input(f"Ruta base local de capítulos (Enter para 'chapters/{series_code}'): ").strip()
        
        if not base_path:
            base_path = os.path.join(os.getcwd(), "chapters", series_code)
            
        if not os.path.exists(base_path):
            print(f"❌ La ruta no existe: {base_path}")
            return

        start_chapter = float(input("Número de capítulo inicial (ej. 15): ").strip())
        volume_num = float(input("Número de volumen (ej. 1): ").strip())
        end_chapter = float(input("Número de capítulo final (inclusive) (ej. 60): ").strip())
        
        # Calcular cantidad basada en rango
        limit = int(end_chapter - start_chapter + 1)
        
        if limit <= 0:
             print("❌ El capítulo final debe ser mayor o igual al inicial.")
             return

    except ValueError:
        print("❌ Dato inválido. Asegúrate de ingresar números donde corresponde.")
        return

    print(f"\n🚀 Iniciando subida de {limit} capítulos (Del {start_chapter} al {end_chapter}) para Manga #{manga_id}...")
    print(f"📂 Leyendo desde: {base_path}")

    success_count = 0

    for i in range(limit):
        current_num = start_chapter + i
        # Formato de carpeta local: 015 (3 dígitos)
        folder_name = f"{int(current_num):03d}" 
        chapter_path = os.path.join(base_path, folder_name)

        if not os.path.exists(chapter_path):
            print(f"⚠️ Saltando Cap #{current_num}: No existe carpeta '{folder_name}'")
            continue

        valid_exts = ('.webp', '.jpg', '.jpeg', '.png')
        images = [f for f in os.listdir(chapter_path) if f.lower().endswith(valid_exts)]
        image_count = len(images)

        if image_count == 0:
            print(f"⚠️ Saltando Cap #{current_num}: Carpeta vacía")
            continue

        img_urls = []
        for img_idx in range(1, image_count + 1):
            filename = f"{img_idx:03d}.webp" 
            url = f"{B2_HOST}/chapters/{series_code}/{folder_name}/{filename}"
            img_urls.append(url)

        payload = {
            "manga": manga_id,
            "capitulo_numero": f"{current_num:.2f}",
            "titulo": f"Capítulo {int(current_num):03d}",
            "volumen_numero": f"{volume_num:.2f}",
            "pages": {
                "images": img_urls
            }
        }

        # POST Real
        try:
            print(f"📤 Subiendo Cap #{current_num} ({image_count} imgs)...", end=" ")
            resp = requests.post(f"{API_URL}/chapters/", json=payload, headers=headers)
            
            if resp.status_code in [200, 201]:
                print("✅ OK")
                success_count += 1
            else:
                print(f"❌ Error {resp.status_code}")
                # print(resp.text) # Uncomment for debug
        except Exception as e:
            print(f"❌ Error conexión: {e}")

    print(f"\n✨ Proceso finalizado. {success_count}/{limit} capítulos registrados.")

if __name__ == "__main__":
    main()
