from django.db import models

class autores(models.Model):
    id = models.BigAutoField(primary_key=True, db_column='AUT_ID')
    nombre = models.CharField(max_length=100, null=False, db_column='AUT_NOMBRE')
    autor_tipo = [
        ("mangaka", "mangaka"),
        ("ilustrador", "ilustrador"),
        ("guionista", "guionista")
    ]
    tipo_autor = models.CharField(max_length=20, choices=autor_tipo, default='mangaka', null=False, db_column='AUT_TIPO_AUTOR')
    foto = models.CharField(max_length=255, null=True, db_column='AUT_FOTO')
    creado_en = models.DateTimeField(auto_now_add=True, db_column='AUT_CREACION')
    vigente = models.BooleanField(default=True, null=False, db_column='AUT_VIGENTE')
    
    class Meta:
        db_table = 'apicore_autores'

class estados(models.Model):
    id = models.BigAutoField(primary_key=True, db_column='EST_ID')
    descripcion = models.CharField(max_length=255, null=True, db_column='EST_DESCRIPCION')
    vigente = models.BooleanField(default=True, null=False, db_column='EST_VIGENTE')
    
    class Meta:
        db_table = 'apicore_estados'

class demografia(models.Model):
    id = models.BigAutoField(primary_key=True, db_column='DEM_ID')
    descripcion = models.CharField(max_length=255, null=True, db_column='DEM_DESCRIPCION')
    color = models.CharField(max_length=7, null=True, db_column='DEM_COLOR')
    vigente = models.BooleanField(default=True, null=False, db_column='DEM_VIGENTE')
    
    class Meta:
        db_table = 'apicore_demografia'

class tags(models.Model):
    id = models.BigAutoField(primary_key=True, db_column='TAG_ID')
    descripcion = models.CharField(max_length=255, null=True, db_column='TAG_DESCRIPCION')
    vigente = models.BooleanField(default=True, null=False, db_column='TAG_VIGENTE')
    
    class Meta:
        db_table = 'apicore_tags'