from django.conf import settings
from rest_framework import serializers
from ApiCore.Models.chapter_models import chapter
from ApiCore.Models.manga_models import manga


class ChapterSerializer(serializers.ModelSerializer):
	# Mostrar el nombre (titulo) del manga en lugar del ID
	manga_titulo = serializers.CharField(source='manga.titulo', read_only=True)
	pages = serializers.SerializerMethodField()

	def get_pages(self, obj):
		if not obj.pages or 'images' not in obj.pages:
			return {'images': []}
		
		images = obj.pages['images']
		
		# Convertir URLs a CDN
		if hasattr(settings, 'USE_CDN') and settings.USE_CDN:
			cdn_images = []
			for url in images:
				if 'backblazeb2.com' in url:
					path = url.split('backblazeb2.com')[1]
					cdn_images.append(f"https://{settings.CDN_DOMAIN}{path}")
				else:
					cdn_images.append(url)
			images = cdn_images
		
		return {'images': images}

	class Meta:
		model = chapter
		fields = ['id', 'manga', 'manga_titulo', 'capitulo_numero', 'titulo', 'volumen_numero', 'pages']

