from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework.permissions import IsAdminUser
from django.contrib.auth import get_user_model
from django.db.models import Q

User = get_user_model()


class CurrentUserView(APIView):
    """Return basic data about the current user (or anonymous)."""
    permission_classes = [AllowAny]

    def get(self, request):
        user = request.user
        if not user or not user.is_authenticated:
            return Response({'authenticated': False, 'user': None})

        groups = list(user.groups.values_list('name', flat=True))
        return Response({
            'authenticated': True,
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'is_staff': user.is_staff,
            'is_superuser': user.is_superuser,
            'groups': groups,
        })


class UsersListView(APIView):
    """List users (admin only) with optional search query param `q`."""
    permission_classes = [IsAdminUser]

    def get(self, request):
        q = request.query_params.get('q', '').strip()
        qs = User.objects.all().order_by('username')
        if q:
            qs = qs.filter(username__icontains=q)
        data = list(qs.values('id', 'username', 'email')[:200])
        return Response({'count': len(data), 'results': data})


class CurrentUserPermissionsView(APIView):
    """Return a simple list of global permissions for the current user.

    The response contains `authenticated`, `permissions` (list of codenames)
    and `groups` (group names). Superusers receive a wildcard permission `*`.
    """
    permission_classes = [AllowAny]

    def get(self, request):
        user = request.user
        if not user or not user.is_authenticated:
            return Response({'authenticated': False, 'permissions': [], 'groups': []})

        # superuser -> full access
        if getattr(user, 'is_superuser', False):
            groups = list(user.groups.values_list('name', flat=True))
            return Response({'authenticated': True, 'permissions': ['*'], 'groups': groups})

        # Lazy import to avoid import cycles
        try:
            from ApiCore.models import AccessGrant
        except Exception:
            return Response({'authenticated': True, 'permissions': [], 'groups': list(user.groups.values_list('name', flat=True))})

        groups = list(user.groups.all())

        # Global grants use object_id='*' (convention used in create_profile)
        try:
            grants_qs = AccessGrant.objects.filter(
                (Q(user=user) | Q(group__in=groups)),
                object_id='*',
                allow=True
            ).select_related('permission')

            perms = sorted({g.permission.codename for g in grants_qs if getattr(g, 'permission', None)})
        except Exception:
            # If DB tables are missing or another DB error occurs, return empty perms
            perms = []

        return Response({'authenticated': True, 'permissions': perms, 'groups': [g.name for g in groups]})
