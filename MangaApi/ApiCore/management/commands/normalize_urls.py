from django.core.management.base import BaseCommand
from ApiCore.models import manga, manga_cover
from ApiCore.services.b2_service import B2Service

class Command(BaseCommand):
    help = 'Normalizes all old Backblaze URLs in Manga and Manga Cover objects to the Cloudflare Worker URL'

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE('Starting URL normalization...'))
        
        # We need to search both manga and manga_cover as per schema
        # but let's just make sure both models are handled.
        
        # 1. Update Manga covers (url_imagen if present directly on model?, generally it uses manga_cover)
        # Checking schema logic, manga covers are stored in manga_cover.url_imagen
        updated_covers = 0
        covers = manga_cover.objects.all()
        for cover in covers:
            if cover.url_imagen and ('backblazeb2.com' in cover.url_imagen or 'f005' in cover.url_imagen):
                new_url = B2Service.normalize_image_url(cover.url_imagen)
                if new_url and new_url != cover.url_imagen:
                    cover.url_imagen = new_url
                    cover.save(update_fields=['url_imagen'])
                    updated_covers += 1
                    self.stdout.write(self.style.SUCCESS(f"Updated cover ID {cover.id} for Manga {cover.manga_id}"))
        
        self.stdout.write(self.style.SUCCESS(f'Successfully updated {updated_covers} Manga Covers.'))
        
        # Add Chapter pages normalization if Chapter contains direct B2 URLs
        from ApiCore.models import chapter
        updated_chapters = 0
        chapters = chapter.objects.all()
        for chap in chapters:
            if chap.pages and isinstance(chap.pages, dict) and 'images' in chap.pages:
                images = chap.pages['images']
                changed = False
                new_images = []
                for img_url in images:
                    if img_url and ('backblazeb2.com' in img_url or 'f005' in img_url):
                        new_url = B2Service.normalize_image_url(img_url, worker_domain='img.miswebtoons.uk')
                        new_images.append(new_url)
                        changed = True
                    else:
                        new_images.append(img_url)
                
                if changed:
                    chap.pages['images'] = new_images
                    chap.save(update_fields=['pages'])
                    updated_chapters += 1
                    self.stdout.write(self.style.SUCCESS(f"Updated images for Chapter ID {chap.id}"))
                    
        self.stdout.write(self.style.SUCCESS(f'Successfully updated {updated_chapters} Chapters.'))
        
        self.stdout.write(self.style.SUCCESS('Done!'))
