# MangaAPI Project

Modern full-stack platform for managing and reading manga/chapters. It consists of:

- Django REST backend (`MangaApi/`) providing data models (mangas, chapters, demografías, tags, autores, estados), authentication, and admin endpoints.
- Vue 3 + Vite frontend (`MangaClient/`) for browsing, filtering (including erotic content segregation), admin uploads, and mantenedor management.
- Python utility framework (`MangaFramework/`) and standalone scripts under `Capitulos_Manga_Download/` for scraping, mass image downloading, renaming, conversion (e.g. WEBP), and JSON chapter payload generation.

## 1. Quick Start

### 1.1 Clone & Enter Project

```powershell
git clone <repo-url> MangaAPI
cd MangaAPI
```

### 1.2 Create & Activate Virtual Environment (Windows PowerShell)

```powershell
python -m venv venv
venv\Scripts\Activate.ps1
```

(If execution policy blocks activation: `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`)

### 1.3 Install Backend Dependencies

If `requirements.txt` is already present:

```powershell
pip install -r requirements.txt
```

If you need to generate it (after installing packages):

```powershell
pip freeze > requirements.txt
```

### 1.4 Environment Variables

Create a `.env` (or configure directly in `settings.py`) for any external services (e.g. Backblaze B2 bucket base URL, secret keys, debug flags). Typical variables:

```env
DJANGO_SECRET_KEY=your-secret
DJANGO_DEBUG=True
BACKBLAZE_BASE_URL=https://f005.backblazeb2.com/file/MangaApi
ALLOWED_HOSTS=*
```

Adjust to match your deployment/security needs.

### 1.5 Apply Migrations & Create Superuser

```powershell
python manage.py migrate
python manage.py createsuperuser
```

### 1.6 Run Backend Server

```powershell
python manage.py runserver
```

Backend will listen on `http://127.0.0.1:8000/`.

### 1.7 Run Frontend (Vue Client)

Open a new terminal:

```powershell
cd MangaClient
npm install
npm run dev
```

Vite dev server default: `http://127.0.0.1:5173/` (or the port it prints). The frontend expects the API at `http://127.0.0.1:8000/api/` (adjust service config if different).

## 2. Project Structure Overview

```text
MangaApi/            # Django project
  manage.py
  MangaApi/          # Core settings, URLs, ASGI/Wsgi
  ApiCore/           # Apps: models, views, filters, serializers, router
MangaClient/         # Vue 3 frontend with Pinia, Vue Router, components/views
MangaFramework/      # Reusable Python tools for scraping, conversion, metadata
Capitulos_Manga_Download/  # Operational scripts for chapter image handling
```

### 2.1 Backend Highlights

- Models cover: Manga, Chapter, Demografía, Tag, Autor, Estado.
- Boolean `erotico` for content segregation.
- Filter endpoints: allow querying by demografía, erotico flag, tags, etc.
- Authentication: Django/DRF token/JWT (ensure correct login endpoint in auth store).

### 2.2 Frontend Highlights

- Home & Library: lists separated by erotic vs non-erotic, +18 badge.
- Chapter Reader: two-page ("libreta") mode, orientation logic, image centering.
- Admin (Dev) Area: upload chapters, manage mantenedores (demografías, tags, autores, estados), edit mangas (toggle erotic flag).
- Upload Flow: generates Backblaze-style URLs and constructs payload `{ manga, capitulo_numero, titulo, volumen_numero, pages: { images: [...] } }`.

### 2.3 Utility Framework & Scripts

- `MangaFramework/`: reusable modules (scraper, downloader, renamer, converter).
- `Capitulos_Manga_Download/`: raw scripts to batch download, rename, convert images to `.webp`, build JSON manifests.

## 3. Typical Workflow

1. Add core mantenedores (Demografías, Tags, Autores, Estados) via admin interface or API.
2. Create Manga entries with associated metadata (including `erotico` flag if applicable).
3. Prepare chapter images (download → rename sequentially → convert to webp).
4. Generate chapter image URL list using Backblazeb2 pattern + zero-padded numbering.
5. Use Upload Chapter screen to submit chapter payload; later edit if needed.
6. Frontend displays updated chapters; users browse while filters hide erotic content by default.

## 4. Upload Chapter Payload Format

Example JSON body sent to backend:

```json
{
  "manga": 12,
  "capitulo_numero": "005",
  "titulo": "Comienzo del Arco",
  "volumen_numero": "02",
  "pages": {
    "images": [
      "https://f005.backblazeb2.com/file/MangaApi/chapters/ABC123/005/001.webp",
      "https://f005.backblazeb2.com/file/MangaApi/chapters/ABC123/005/002.webp"
    ]
  }
}
```

The series code / chapter padding should match your backend expectations.

## 5. Authentication

- Frontend login uses Django/DRF token issuance endpoint (e.g. `/api/token/` or `/api/auth/login/`).
- Successful login sets Authorization header for protected dev/admin routes.
- Token persisted in localStorage to restore session on reload.

## 6. Development Conventions

- Keep chapter image numbering zero-padded (001, 002, ...).
- Use `form-control-sm` for compact admin forms.
- Show edit button; enable inline fields only in edit mode; save via PATCH.
- Segregate erotic content: initial views show non-erotic; dedicated tab shows erotic + +18 badge.

## 7. Regenerating Requirements

After adding/removing Python packages:

```powershell
pip install <package>
pip freeze > requirements.txt
```

Commit updated `requirements.txt` so environments stay in sync.

## 8. Common Issues & Fixes

| Issue | Cause | Fix |
|-------|-------|-----|
| `python freeze` error | Wrong command | Use `pip freeze > requirements.txt` or `python -m pip freeze > requirements.txt` |
| 404 on chapters endpoint | Wrong URL path | Confirm router path `/api/chapters/chapters/` |
| Dev menu missing | Auth token not set | Ensure login succeeds; check Authorization header |
| Dark mode unreadable text | Missing overrides | Confirm CSS variables or `.text-muted` override |

## 9. Running Tests (if configured)

Backend tests (example):

```powershell
python manage.py test
```

Add more tests under `MangaFramework/tests/` or `ApiCore/tests.py` to validate new logic.

## 10. Next Enhancements (Suggested)

- Add dropdown of predefined author types.
- Add delete buttons for mantenedores.
- Implement image list reorder/remove in chapter edit screen.
- Token refresh mechanism (JWT) for long sessions.

---

Made with Django, Vue 3, and a custom manga tooling framework.
