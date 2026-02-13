from django.contrib.auth.models import User, Group
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver

class UserProfile(models.Model):
    """
    Perfil de usuario extendido - SAFE para producción
    Se vincula al User existente sin romper nada
    """
    
    PROFILE_CHOICES = [
        ('home_only', 'Home Only'),
        ('premium', 'Premium'),
        ('moderator', 'Moderator'),
        ('admin', 'Admin'),
    ]
    
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='userprofile'
    )
    
    profile = models.CharField(
        max_length=20,
        choices=PROFILE_CHOICES,
        default='home_only',
        db_index=True
    )
    
    # Metadata adicional
    profile_updated_at = models.DateTimeField(auto_now=True)
    banned = models.BooleanField(default=False)
    ban_reason = models.TextField(blank=True)
    
    class Meta:
        db_table = 'user_profiles'
        permissions = [
            # Permisos de contenido
            ('view_nsfw_content', 'Can view NSFW content'),
            ('view_premium_content', 'Can view premium content'),
            
            # Permisos de admin
            ('access_admin_panel', 'Can access admin panel'),
            ('manage_users', 'Can manage users'),
            ('manage_manga', 'Can manage manga'),
            ('manage_chapters', 'Can manage chapters'),
            ('view_analytics', 'Can view analytics'),
            
            # Permisos de moderación
            ('moderate_comments', 'Can moderate comments'),
            ('moderate_reports', 'Can moderate reports'),
        ]
    
    def save(self, *args, **kwargs):
        """Sincronizar perfil con grupo Django automáticamente"""
        super().save(*args, **kwargs)
        self.sync_groups()
    
    def sync_groups(self):
        """Asignar el usuario al grupo correcto según su perfil"""
        from ApiCore.permissions.definitions import PROFILE_GROUPS
        
        # Remover de todos los grupos de perfil
        self.user.groups.clear()
        
        # Agregar al grupo correspondiente
        group_name = PROFILE_GROUPS.get(self.profile)
        if group_name:
            group, _ = Group.objects.get_or_create(name=group_name)
            self.user.groups.add(group)
    
    def has_profile_permission(self, perm_codename):
        """Atajo para verificar permisos del perfil"""
        # Chequea si el usuario tiene el permiso (ya sea por grupo o directo)
        # Nota: 'ApiCore' es la app label.
        return self.user.has_perm(f'ApiCore.{perm_codename}')
    
    @property
    def can_view_nsfw(self):
        return self.has_profile_permission('view_nsfw_content')
    
    @property
    def can_access_admin(self):
        return self.has_profile_permission('access_admin_panel')
    
    @property
    def is_moderator_or_higher(self):
        return self.profile in ['moderator', 'admin']
    
    def __str__(self):
        return f"{self.user.username} ({self.get_profile_display()})"


# Signal para crear UserProfile automáticamente cuando se crea un User
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Crear UserProfile automáticamente para cada nuevo User"""
    if created:
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """Guardar UserProfile cuando se guarda User"""
    if hasattr(instance, 'userprofile'):
        instance.userprofile.save()
