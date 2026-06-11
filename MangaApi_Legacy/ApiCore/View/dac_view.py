from rest_framework import viewsets, status
from rest_framework.decorators import action, permission_classes as drf_permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser, IsAuthenticatedOrReadOnly
from django.contrib.auth.models import Group, User
from ApiCore.Serializer.dac_serializer import GroupSerializer, AccessGrantSerializer
from ApiCore.access_control import grant_group_permission, create_profile
from ApiCore.models import AccessGrant, Permission
from ApiCore.models import manga_models, chapter_models
from django.contrib.contenttypes.models import ContentType


MODEL_MAP = {
    'manga': getattr(manga_models, 'manga', None),
    'chapter': getattr(chapter_models, 'chapter', None),
}


class ProfileViewSet(viewsets.ModelViewSet):
    """Manage profiles (Django Groups) and allow assigning users and group grants."""
    queryset = Group.objects.prefetch_related('user_set').all()
    serializer_class = GroupSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def create(self, request, *args, **kwargs):
        # only admins can create profiles
        if not request.user or not request.user.is_staff:
            return Response({'detail': 'Only administrators can create profiles'}, status=status.HTTP_403_FORBIDDEN)
        return super().create(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        if not request.user or not request.user.is_staff:
            return Response({'detail': 'Only administrators can modify profiles'}, status=status.HTTP_403_FORBIDDEN)
        return super().update(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        if not request.user or not request.user.is_staff:
            return Response({'detail': 'Only administrators can modify profiles'}, status=status.HTTP_403_FORBIDDEN)
        return super().partial_update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        if not request.user or not request.user.is_staff:
            return Response({'detail': 'Only administrators can delete profiles'}, status=status.HTTP_403_FORBIDDEN)
        return super().destroy(request, *args, **kwargs)

    @action(detail=True, methods=['post'], url_path='add-user')
    @drf_permission_classes([IsAdminUser])
    def add_user(self, request, pk=None):
        group = self.get_object()
        user_id = request.data.get('user_id')
        if not user_id:
            return Response({'detail': 'user_id required'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            user = User.objects.get(pk=user_id)
            user.groups.add(group)
            user.save()
            return Response({'detail': 'user added'})
        except User.DoesNotExist:
            return Response({'detail': 'user not found'}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=True, methods=['post'], url_path='remove-user')
    @drf_permission_classes([IsAdminUser])
    def remove_user(self, request, pk=None):
        group = self.get_object()
        user_id = request.data.get('user_id')
        if not user_id:
            return Response({'detail': 'user_id required'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            user = User.objects.get(pk=user_id)
            user.groups.remove(group)
            user.save()
            return Response({'detail': 'user removed'})
        except User.DoesNotExist:
            return Response({'detail': 'user not found'}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=True, methods=['post'], url_path='grant')
    @drf_permission_classes([IsAdminUser])
    def grant(self, request, pk=None):
        """Grant a permission to this group.

        Expected JSON: { "codename": "write", "model": "manga" , "object_id": optional }
        If `object_id` omitted, grant is global for that model (object_id='*').
        """
        group = self.get_object()
        codename = request.data.get('codename')
        model_key = request.data.get('model')
        object_id = request.data.get('object_id', '*')
        if not codename or not model_key:
            return Response({'detail': 'codename and model required'}, status=status.HTTP_400_BAD_REQUEST)

        model_cls = MODEL_MAP.get(model_key)
        if model_cls is None:
            return Response({'detail': f'unknown model {model_key}'}, status=status.HTTP_400_BAD_REQUEST)

        # Use ContentType for the model
        ct = ContentType.objects.get_for_model(model_cls)
        perm, _ = Permission.objects.get_or_create(codename=codename, defaults={'name': codename})
        ag = grant_group_permission(group, model_cls(), codename) if object_id == '*' else grant_group_permission(group, model_cls(), codename)
        # grant_group_permission helper will create wildcard by using object.pk; we need to ensure object_id stored
        # Simpler: directly create AccessGrant for group
        from ApiCore.models import AccessGrant as AG
        ag_obj, created = AG.objects.get_or_create(user=None, group=group, content_type=ct, object_id=str(object_id), permission=perm, defaults={'allow': True})
        serializer = AccessGrantSerializer(ag_obj)
        return Response(serializer.data)

    @action(detail=True, methods=['get'], url_path='grants')
    @drf_permission_classes([IsAdminUser])
    def grants(self, request, pk=None):
        group = self.get_object()
        qs = AccessGrant.objects.filter(group=group)
        serializer = AccessGrantSerializer(qs, many=True)
        return Response(serializer.data)


class AccessGrantViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = AccessGrant.objects.select_related('permission', 'user', 'group', 'content_type').all()
    serializer_class = AccessGrantSerializer
