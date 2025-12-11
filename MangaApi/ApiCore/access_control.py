from functools import wraps
from django.contrib.contenttypes.models import ContentType
from django.http import HttpResponseForbidden
from django.contrib.auth.models import Group
from .models import Permission, AccessGrant, Owner
try:
    from rest_framework.permissions import BasePermission, SAFE_METHODS
except Exception:
    BasePermission = None
    SAFE_METHODS = ('GET', 'HEAD', 'OPTIONS')


def get_permission(codename):
    perm, _ = Permission.objects.get_or_create(codename=codename, defaults={"name": codename})
    return perm


def has_permission(user, obj, codename):
    """Check if `user` has `codename` permission on `obj`.

    Rules (discretionary):
    - superusers always allowed
    - explicit Owner record grants all permissions
    - explicit AccessGrant for the user and permission grants/denies
    - default: deny
    """
    if user is None:
        return False
    if getattr(user, "is_superuser", False):
        return True

    # owner check
    try:
        ct = ContentType.objects.get_for_model(obj.__class__)
        owner_qs = Owner.objects.filter(content_type=ct, object_id=str(getattr(obj, 'pk', getattr(obj, 'id', None))), user=user)
        if owner_qs.exists():
            return True
    except Exception:
        pass

    # permission grants (user-specific)
    try:
        perm = Permission.objects.filter(codename=codename).first()
        if not perm:
            return False
        ct = ContentType.objects.get_for_model(obj.__class__)
        obj_id = str(getattr(obj, 'pk', getattr(obj, 'id', None)))
        grants = AccessGrant.objects.filter(user=user, content_type=ct, object_id__in=(obj_id, '*'), permission=perm)
        # if any explicit deny exists, deny; otherwise any allow grants access
        if grants.filter(allow=False).exists():
            return False
        if grants.filter(allow=True).exists():
            return True
        # group-based grants: check all groups the user belongs to
        try:
            groups = list(user.groups.all()) if getattr(user, 'is_authenticated', False) else []
            if groups:
                g_grants = AccessGrant.objects.filter(group__in=groups, content_type=ct, object_id__in=(obj_id, '*'), permission=perm)
                if g_grants.filter(allow=False).exists():
                    return False
                if g_grants.filter(allow=True).exists():
                    return True
        except Exception:
            pass
    except Exception:
        pass

    return False


def grant_permission(user, obj, codename, allow=True):
    perm = get_permission(codename)
    ct = ContentType.objects.get_for_model(obj.__class__)
    ag, created = AccessGrant.objects.get_or_create(
        user=user, group=None, content_type=ct, object_id=str(getattr(obj, 'pk', getattr(obj, 'id', None))), permission=perm,
        defaults={"allow": allow}
    )
    if not created and ag.allow != allow:
        ag.allow = allow
        ag.save()
    return ag


def grant_group_permission(group, obj, codename, allow=True):
    perm = get_permission(codename)
    ct = ContentType.objects.get_for_model(obj.__class__)
    ag, created = AccessGrant.objects.get_or_create(
        user=None, group=group, content_type=ct, object_id=str(getattr(obj, 'pk', getattr(obj, 'id', None))), permission=perm,
        defaults={"allow": allow}
    )
    if not created and ag.allow != allow:
        ag.allow = allow
        ag.save()
    return ag


def create_profile(name, permissions=None):
    """Create a Django Group named `name` and optionally attach global permissions.

    `permissions` is a list of tuples (codename, content_model_or_none).
    If content_model_or_none is None, grant is created with object_id='*' (global).
    """
    permissions = permissions or []
    group, _ = Group.objects.get_or_create(name=name)
    for codename, model in permissions:
        perm = get_permission(codename)
        if model is None:
            # global grant across model type None => make content_type=null and object_id='*'
            # we'll attach to wildcard content by setting content_type to ContentType of User model as placeholder
            # instead, use object_id='*' with content_type set when needed by checks
            # For simplicity, create grants with content_type pointing to ContentType of model if provided; otherwise leave content_type as None
            # Here we'll create per-app global grants with content_type set to a special value '*' convention stored in object_id
            from django.contrib.contenttypes.models import ContentType as CT
            # Use a sentinel content type (site-wide) by setting content_type to ContentType for User as generic holder
            sentinel_ct = CT.objects.get_for_model(Group)
            AccessGrant.objects.get_or_create(user=None, group=group, content_type=sentinel_ct, object_id='*', permission=perm, defaults={'allow': True})
        else:
            ct = ContentType.objects.get_for_model(model)
            AccessGrant.objects.get_or_create(user=None, group=group, content_type=ct, object_id='*', permission=perm, defaults={'allow': True})

    return group


def require_permission(codename, obj_arg='obj'):
    """Decorator for Django views: expects the view to receive the target object
    as a keyword argument named `obj_arg` (default 'obj'). If not found, it will
    try to resolve by 'pk' in kwargs only for Model-based views.
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped(request, *args, **kwargs):
            target = kwargs.get(obj_arg)
            if target is None:
                # try to resolve by pk using view kwargs and view's module - best-effort
                pk = kwargs.get('pk') or kwargs.get('id')
                if pk is None:
                    return HttpResponseForbidden('Missing target object for permission check')
                # user must resolve object themselves in view; we cannot import arbitrary models here
                return HttpResponseForbidden('Cannot resolve object for permission check')

            if has_permission(request.user, target, codename):
                return view_func(request, *args, **kwargs)
            return HttpResponseForbidden('Permission denied')

        return _wrapped
    return decorator


class DRFDACPermission(BasePermission):
    """DRF permission class that enforces DAC rules on object-level write operations.

    - Safe methods (GET, HEAD, OPTIONS) are allowed to anyone.
    - POST/create requires authenticated user.
    - PUT/PATCH/DELETE require `has_permission(user, obj, 'write')`.
    """

    def has_permission(self, request, view):
        # Allow safe methods to everyone
        if request.method in SAFE_METHODS:
            return True
        # POST: require authentication (creating objects)
        if request.method == 'POST':
            return bool(request.user and request.user.is_authenticated)
        # For other methods, defer to object-level permission
        return True

    def has_object_permission(self, request, view, obj):
        # Safe methods already allowed
        if request.method in SAFE_METHODS:
            return True
        # For modify/delete, require explicit 'write' permission
        return has_permission(request.user, obj, 'write')
