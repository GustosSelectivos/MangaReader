from rest_framework import serializers
from django.contrib.auth.models import Group, User
from ApiCore.models import AccessGrant, Permission


class UserLiteSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email')


class GroupSerializer(serializers.ModelSerializer):
    users = UserLiteSerializer(many=True, read_only=True, source='user_set')

    class Meta:
        model = Group
        fields = ('id', 'name', 'users')


class PermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Permission
        fields = ('id', 'codename', 'name')


class AccessGrantSerializer(serializers.ModelSerializer):
    permission = PermissionSerializer(read_only=True)

    class Meta:
        model = AccessGrant
        fields = ('id', 'user', 'group', 'content_type', 'object_id', 'permission', 'allow', 'created')
        read_only_fields = ('created',)
