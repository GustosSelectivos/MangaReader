from .settings import *

# Use in-memory SQLite for CI tests to avoid external DB dependencies
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

# Speed up password hashing in tests
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]

# Disable migrations for faster test setup (optional)
class DisableMigrations(dict):
    def __contains__(self, item):
        return True
    def __getitem__(self, item):
        return 'notmigrations'

MIGRATION_MODULES = DisableMigrations()