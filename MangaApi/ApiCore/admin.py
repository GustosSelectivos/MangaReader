from django.contrib import admin
from .models import Permission, AccessGrant, Owner


@admin.register(Permission)
class PermissionAdmin(admin.ModelAdmin):
	list_display = ("codename", "name")
	search_fields = ("codename", "name")


@admin.register(AccessGrant)
class AccessGrantAdmin(admin.ModelAdmin):
	list_display = ("user", "group", "permission", "content_type", "object_id", "allow", "created")
	search_fields = ("user__username", "group__name", "object_id")
	list_filter = ("allow", "permission", "content_type")


@admin.register(Owner)
class OwnerAdmin(admin.ModelAdmin):
	list_display = ("user", "content_type", "object_id")
	search_fields = ("user__username", "object_id")


from .models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
	list_display = ("created", "user", "method", "path", "allowed", "status_code")
	list_filter = ("allowed", "method", "status_code")
	search_fields = ("user__username", "path", "detail")
	readonly_fields = ("created",)
