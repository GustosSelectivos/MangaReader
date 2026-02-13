from django.core.management.base import BaseCommand
from ApiCore.permissions.definitions import setup_groups_and_permissions

class Command(BaseCommand):
    help = 'Configura grupos y permisos del sistema'

    def handle(self, *args, **options):
        self.stdout.write('Configurando sistema de permisos...')
        try:
            setup_groups_and_permissions()
            self.stdout.write(self.style.SUCCESS('✅ Sistema de permisos configurado'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error configurando permisos: {e}'))
