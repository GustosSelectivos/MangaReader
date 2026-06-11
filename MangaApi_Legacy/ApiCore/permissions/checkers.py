from rest_framework import permissions

class HasProfilePermission(permissions.BasePermission):
    """
    Verifica si el usuario tiene un permiso específico de perfil
    
    Uso:
    permission_classes = [HasProfilePermission]
    required_permission = 'view_nsfw_content' (definido en el ViewSet)
    """
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        # Verificar que el usuario tenga un perfil asociado
        if not hasattr(request.user, 'userprofile'):
            return False
            
        # Obtener permiso requerido del view
        required_perm = getattr(view, 'required_permission', None)
        
        if not required_perm:
            # Sin permiso específico, solo autenticación
            return True
        
        # Usar .userprofile
        return request.user.userprofile.has_profile_permission(required_perm)


class CanViewNSFW(permissions.BasePermission):
    """Permite acceso a contenido NSFW solo si el usuario tiene permiso"""
    
    def has_object_permission(self, request, view, obj):
        # Si el objeto no es NSFW, permitir siempre
        # Asumimos que el modelo tiene campo 'erotico' o 'is_nsfw'. 
        # Tus modelos usan 'erotico'.
        is_nsfw = getattr(obj, 'erotico', False)
        
        if not is_nsfw:
            return True
        
        # Si es NSFW, verificar permiso
        return (
            request.user.is_authenticated and 
            hasattr(request.user, 'userprofile') and
            request.user.userprofile.can_view_nsfw
        )


class IsModeratorOrAdmin(permissions.BasePermission):
    """Solo moderadores o admins"""
    
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and 
            hasattr(request.user, 'userprofile') and
            request.user.userprofile.is_moderator_or_higher
        )


class CanAccessAdminPanel(permissions.BasePermission):
    """Requiere permiso de acceso al panel de admin"""
    
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and 
            hasattr(request.user, 'userprofile') and
            request.user.userprofile.can_access_admin
        )
