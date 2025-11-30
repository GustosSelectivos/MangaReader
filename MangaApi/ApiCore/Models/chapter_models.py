from django.db import models
from .manga_models import manga

class chapter(models.Model):
    id = models.BigAutoField(primary_key=True, db_column='CHR_ID')
    manga = models.ForeignKey(manga, on_delete=models.PROTECT, db_column='CHR_MANGA_ID')
    capitulo_numero = models.DecimalField(max_digits=6, decimal_places=2, null=False, db_column='CHR_CAPITULO_NUMERO')
    titulo = models.CharField(max_length=200, null=True, db_column='CHR_TITULO')
    volumen_numero = models.DecimalField(max_digits=6, decimal_places=2, null=True, db_column='CHR_VOLUMEN_NUMERO')
    pages = models.JSONField(default=dict, null=True, db_column='CHR_PAGES')
    