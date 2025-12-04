from rest_framework import serializers
from ApiCore.Models.manga_models import manga, manga_alt_titulo, manga_cover, manga_autor, manga_tag
from ApiCore.Models.mantenedor_models import autores, estados, demografia, tags


class MangaAltTituloSerializer(serializers.ModelSerializer):
	manga_titulo = serializers.CharField(source='manga.titulo', read_only=True)
	class Meta:
		model = manga_alt_titulo
		fields = ['id', 'manga', 'manga_titulo', 'titulo_alternativo', 'codigo_lenguaje', 'vigente']


class MangaCoverSerializer(serializers.ModelSerializer):
	manga_titulo = serializers.CharField(source='manga.titulo', read_only=True)
	# URL absoluto si el campo es relativo
	url_absoluta = serializers.SerializerMethodField()
	def get_url_absoluta(self, obj):
		url = getattr(obj, 'url_imagen', None)
		if not url:
			return None
		# Si ya parece absoluta, devolver tal cual
		if isinstance(url, str) and (url.startswith('http://') or url.startswith('https://')):
			return url
		# Intentar construir absoluta usando request si existe
		request = self.context.get('request') if hasattr(self, 'context') else None
		if request and isinstance(url, str):
			try:
				return request.build_absolute_uri(url)
			except Exception:
				return url
		return url
	class Meta:
		model = manga_cover
		fields = ['id', 'manga', 'manga_titulo', 'url_imagen', 'url_absoluta', 'tipo_cover', 'vigente']


class MangaAutorSerializer(serializers.ModelSerializer):
	manga_titulo = serializers.CharField(source='manga.titulo', read_only=True)
	autor_nombre = serializers.CharField(source='autor.nombre', read_only=True)
	class Meta:
		model = manga_autor
		fields = ['id', 'manga', 'manga_titulo', 'autor', 'autor_nombre', 'rol', 'vigente']


class MangaTagSerializer(serializers.ModelSerializer):
	manga_titulo = serializers.CharField(source='manga.titulo', read_only=True)
	tag_descripcion = serializers.CharField(source='tag.descripcion', read_only=True)
	class Meta:
		model = manga_tag
		fields = ['id', 'manga', 'manga_titulo', 'tag', 'tag_descripcion', 'vigente']


class MangaSerializer(serializers.ModelSerializer):
	estado_display = serializers.CharField(source='estado.nombre', read_only=True)
	demografia_display = serializers.CharField(source='demografia.descripcion', read_only=True)
	dem_color = serializers.CharField(source='demografia.color', read_only=True)
	cover_url = serializers.SerializerMethodField()

	def get_cover_url(self, obj):
		# Priorizar cover principal vigente
		try:
			main = obj.covers.filter(vigente=True).order_by('id').first()
			if main:
				url = getattr(main, 'url_imagen', None)
				if isinstance(url, str) and (url.startswith('http://') or url.startswith('https://')):
					return url
				# Construir absoluta si es relativa
				request = self.context.get('request') if hasattr(self, 'context') else None
				if request and isinstance(url, str):
					try:
						return request.build_absolute_uri(url)
					except Exception:
						return url
				return url
		except Exception:
			pass
		return None
	autor_display = serializers.CharField(source='autor.nombre', read_only=True)

	class Meta:
		model = manga
		fields = [
			'id', 'titulo', 'sinopsis', 'estado', 'estado_display', 'demografia', 'demografia_display', 'dem_color', 'cover_url',
			'autor', 'autor_display', 'fecha_lanzamiento', 'creado_en', 'actualizado_en', 'vigente', 'vistas', 'codigo', 'tipo_serie',
			'erotico'
		]

