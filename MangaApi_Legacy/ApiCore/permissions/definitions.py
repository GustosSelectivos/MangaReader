from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType

# Mapeo de perfiles a nombres de grupos
PROFILE_GROUPS = {
    'home_only': 'HomeOnly',
    'premium': 'Premium',
    'moderator': 'Moderator',
    'admin': 'Admin',
}

# Definición de permisos por perfil
PROFILE_PERMISSIONS = {
    'HomeOnly': [
        # Solo lectura básica (sin NSFW)
    ],
    
    'Premium': [
        'view_nsfw_content',
        'view_premium_content',
    ],
    
    'Moderator': [
        # Todos los de Premium +
        'view_nsfw_content',
        'view_premium_content',
        # Moderación
        'moderate_comments',
        'moderate_reports',
        'access_admin_panel',
        'view_analytics',
    ],
    
    'Admin': [
        # Control total
        'view_nsfw_content',
        'view_premium_content',
        'access_admin_panel',
        'manage_users',
        'manage_manga',
        'manage_chapters',
        'moderate_comments',
        'moderate_reports',
        'view_analytics',
    ],
}


def setup_groups_and_permissions():
    """
    Crea grupos y asigna permisos
    Llamar en management command o post_migrate signal
    """
    # Importar UserProfile para obtener el ContentType correcto donde se definen los permisos
    from ApiCore.models import UserProfile
    
    # Obtener content type de UserProfile (donde definimos los permisos en Meta)
    # OJO: Los permisos se crean asociados al modelo donde se definen en Meta.
    user_profile_ct = ContentType.objects.get_for_model(UserProfile)
    
    for profile_key, group_name in PROFILE_GROUPS.items():
        # Crear grupo si no existe
        group, created = Group.objects.get_or_create(name=group_name)
        
        # Siempre actualizar permisos
        # Limpiar permisos existentes
        group.permissions.clear()
        
        # Agregar permisos definidos
        perm_codenames = PROFILE_PERMISSIONS.get(group_name, [])
        
        for codename in perm_codenames:
            try:
                # Los permisos personalizados están en UserProfile
                perm = Permission.objects.get(
                    codename=codename,
                    content_type=user_profile_ct
                )
                group.permissions.add(perm)
            except Permission.DoesNotExist:
                print(f"⚠️ Permiso no encontrado: {codename} (Asegúrate de haber corrido makemigrations/migrate)")
        
        print(f"✅ Grupo '{group_name}' configurado con {len(perm_codenames)} permisos")
