# apps/ — Capa de organización por dominio
#
# Cada sub-package representa un dominio de negocio:
#   catalog/   → autores, estados, demografia, tags
#   mangas/    → manga, manga_cover, manga_autor, manga_tag, manga_alt_titulo
#   chapters/  → chapter
#   users/     → UserProfile
#   dac/       → Permission, AccessGrant, Owner, AuditLog
#
# Los modelos siguen viviendo en ApiCore (migrations intactas).
# Estos módulos re-exportan para ofrecer rutas de importación limpias
# y hospedar la capa de servicios de cada dominio.
