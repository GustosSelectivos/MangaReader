from django.db import models
from .mantenedor_models import *

class manga(models.Model):
    id = models.BigAutoField(primary_key=True, db_column='MNG_ID')
    codigo = models.CharField(max_length=50, unique=True, null=True, db_column='MNG_CODIGO')
    titulo = models.CharField(max_length=200, null=False, db_column='MNG_TITULO')
    sinopsis = models.TextField(null=True, db_column='MNG_SINOPSIS')
    estado = models.ForeignKey(estados, on_delete=models.PROTECT, db_column='MNG_ESTADO_ID')
    demografia = models.ForeignKey(demografia, on_delete=models.PROTECT, db_column='MNG_DEMOGRAFIA_ID')
    tipo_serie = [
        ("manga", "manga"),
        ("manhwa", "manhwa"),
        ("manhua", "manhua"),
        ("one shot", "one shot"),
        ("novel", "novel",),
        ("doujinshi", "doujinshi"),
        ("comic", "comic")
    ]
    tipo_serie = models.CharField(max_length=20, choices=tipo_serie, default='manga', null=False, db_column='MNG_TIPO_SERIE')
    autor = models.ForeignKey(autores, on_delete=models.PROTECT, db_column='MNG_AUTOR_ID')
    fecha_lanzamiento = models.DateField(null=True, db_column='MNG_FECHA_LANZAMIENTO')
    creado_en = models.DateTimeField(auto_now_add=True, db_column='MNG_CREACION')
    actualizado_en = models.DateTimeField(auto_now=True, db_column='MNG_ACTUALIZACION')
    vigente = models.BooleanField(default=True, null=False, db_column='MNG_VIGENTE')
    vistas = models.PositiveIntegerField(default=0, null=False, db_column='MNG_VISTA')
    erotico = models.BooleanField(default=False, null=False, db_column='MNG_EROTICO')
    
    class Meta:
        db_table = 'apicore_manga'

class manga_alt_titulo(models.Model):
    id = models.BigAutoField(primary_key=True, db_column='MAT_ID')
    manga = models.ForeignKey(manga, on_delete=models.PROTECT, db_column='MAT_MANGA_ID')
    titulo_alternativo = models.CharField(max_length=200, null=False, db_column='MAT_TITULO_ALTERNATIVO')
    codigo_lenguaje = models.CharField(max_length=10, null=False, db_column='MAT_CODIGO_LENGUAJE')
    vigente = models.BooleanField(default=True, null=False, db_column='MAT_VIGENTE')
    
    class Meta:
        db_table = 'apicore_manga_alt_titulo'

class manga_cover(models.Model):
    id = models.BigAutoField(primary_key=True, db_column='MCV_ID')
    manga = models.ForeignKey(manga, on_delete=models.PROTECT, db_column='MCV_MANGA_ID')
    url_imagen = models.CharField(max_length=255, null=False, db_column='MCV_URL_IMAGEN')
    cover_tipo = [
        ("main", "main"),
        ("thumbnail", "thumbnail"),
        ("banner", "banner"),
        ("extra", "extra")
    ]
    tipo_cover = models.CharField(max_length=20, choices=cover_tipo, default='main', null=False, db_column='MCV_COVER_TIPO')
    vigente = models.BooleanField(default=True, null=False, db_column='MCV_VIGENTE')
    
    class Meta:
        db_table = 'apicore_manga_cover'

class manga_autor(models.Model):
    id = models.BigAutoField(primary_key=True, db_column='MAU_ID')
    manga = models.ForeignKey(manga, on_delete=models.PROTECT, db_column='MAU_MANGA_ID')
    autor = models.ForeignKey(autores, on_delete=models.PROTECT, db_column='MAU_AUTOR_ID')
    rol_tipo = [
        ("author", "author"),
        ("illustrator", "illustrator"),
        ("writer", "writer"),
        ("editor", "editor")
    ]
    rol = models.CharField(max_length=20, choices=rol_tipo, default='author', null=False, db_column='MAU_ROL')
    vigente = models.BooleanField(default=True, null=False, db_column='MAU_VIGENTE')
    
    class Meta:
        db_table = 'apicore_manga_autor'

class manga_tag(models.Model):
    id = models.BigAutoField(primary_key=True, db_column='MTG_ID')
    manga = models.ForeignKey(manga, on_delete=models.PROTECT, db_column='MTG_MANGA_ID')
    tag = models.ForeignKey(tags, on_delete=models.PROTECT, db_column='MTG_TAG_ID')
    vigente = models.BooleanField(default=True, null=False, db_column='MTG_VIGENTE')
    
    class Meta:
        db_table = 'apicore_manga_tag'