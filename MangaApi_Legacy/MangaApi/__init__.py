"""Package initializer for MangaApi project.

If you prefer using PyMySQL (no compilation) instead of mysqlclient,
install `PyMySQL` in the virtualenv and this shim will make it available
as `MySQLdb` for Django's MySQL backend.
"""

try:
	import pymysql
	pymysql.install_as_MySQLdb()
except Exception:
	# PyMySQL not installed or failed to import; fallback to configured DB driver
	pass
