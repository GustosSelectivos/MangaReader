from rest_framework import serializers
from ApiCore.models.manga_models import manga, manga_alt_titulo, manga_cover, manga_autor, manga_tag
from ApiCore.models.mantenedor_models import autores, estados, demografia, tags
from ApiCore.utils.serializers import DynamicFieldsModelSerializer


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


class MangaSerializer(DynamicFieldsModelSerializer):
	estado_display = serializers.CharField(source='estado.descripcion', read_only=True)
	demografia_display = serializers.CharField(source='demografia.descripcion', read_only=True)
	dem_color = serializers.CharField(source='demografia.color', read_only=True)
	cover_url = serializers.SerializerMethodField()

	def get_cover_url(self, obj):
		# Priorizar cover principal vigente usando la lista ya cargada (prefetch)
		try:
			from ApiCore.services.b2_service import B2Service
			
			# obj.covers.all() ya está en memoria gracias al prefetch_related
			covers = list(obj.covers.all())
			# Filtramos en Python en lugar de SQL
			main = next((c for c in covers if c.vigente and c.tipo_cover == 'main'), None)
			# Si no hay main explicito, usamos el primero vigente (fallback)
			if not main:
				main = next((c for c in covers if c.vigente), None)

			if main:
				url = getattr(main, 'url_imagen', None)
				if isinstance(url, str):
					return B2Service.normalize_image_url(url)
		except Exception:
			pass
		return None
	autor_display = serializers.CharField(source='autor.nombre', read_only=True)
	tags = MangaTagSerializer(many=True, read_only=True)
	cover_image = serializers.ImageField(write_only=True, required=False)

	def create(self, validated_data):
		# El serializer NO hace I/O de red.
		# El archivo ya fue extraído por la view antes de llamar a save();
		# aquí simplemente lo descartamos del validated_data para que el ORM no lo procese.
		validated_data.pop('cover_image', None)
		return super().create(validated_data)

	def update(self, instance, validated_data):
		# Igual que create(): descartar el campo de archivo.
		# La subida real es responsabilidad de CoverUploadService (llamado desde la view).
		validated_data.pop('cover_image', None)
		return super().update(instance, validated_data)

	class Meta:
		model = manga
		fields = [
			'id', 'slug', 'titulo', 'sinopsis', 'estado', 'estado_display', 'demografia', 'demografia_display', 'dem_color', 'cover_url',
			'autor', 'autor_display', 'fecha_lanzamiento', 'creado_en', 'actualizado_en', 'vigente', 'vistas', 'codigo', 'tipo_serie',
			'erotico', 'tags', 'cover_image'
		]

class MangaCardSerializer(DynamicFieldsModelSerializer):
    """
    Serializer lighter for Lists/Grids (Home, Library).
    Excludes: tags, synopsis, authors, dates.
    Includes: id, slug, title, type, cover, demography.
    """
    demografia_display = serializers.CharField(source='demografia.descripcion', read_only=True)
    dem_color = serializers.CharField(source='demografia.color', read_only=True)
    estado_display = serializers.CharField(source='estado.descripcion', read_only=True)
    cover_url = serializers.SerializerMethodField()

    def get_cover_url(self, obj):
        try:
            # We assume prefetch is active, but if not, fail gracefully
            covers = list(obj.covers.all())
            main = next((c for c in covers if c.vigente and c.tipo_cover == 'main'), None)
            if not main:
                main = next((c for c in covers if c.vigente), None)

            if main:
                url = getattr(main, 'url_imagen', None)
                if isinstance(url, str) and (url.startswith('http://') or url.startswith('https://')):
                    return url
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

    class Meta:
        model = manga
        fields = [
            'id', 'slug', 'titulo', 'tipo_serie', 'cover_url', 
            'demografia', 'demografia_display', 'dem_color', 'estado_display', 'vistas', 'erotico'
        ]

