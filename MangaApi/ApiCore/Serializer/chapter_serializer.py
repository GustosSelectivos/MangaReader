from rest_framework import serializers
from ApiCore.Models.chapter_models import chapter
from ApiCore.Models.manga_models import manga


class ChapterSerializer(serializers.ModelSerializer):
	# Mostrar el nombre (titulo) del manga en lugar del ID
	manga_titulo = serializers.CharField(source='manga.titulo', read_only=True)

	class Meta:
		model = chapter
		fields = ['id', 'manga', 'manga_titulo', 'capitulo_numero', 'titulo', 'volumen_numero', 'pages']

