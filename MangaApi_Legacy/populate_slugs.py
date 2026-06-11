import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'MangaApi.settings')
django.setup()

from ApiCore.Models.manga_models import manga

count = 0
for m in manga.objects.filter(slug__isnull=True):
    # The modified save() method handles generation
    m.save()
    print(f"Generated slug for: {m.titulo} -> {m.slug}")
    count += 1

print(f"Successfully updated {count} mangas.")
