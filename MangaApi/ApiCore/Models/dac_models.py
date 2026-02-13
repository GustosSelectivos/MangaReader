from django.db import models
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey


User = get_user_model()


# Discretionary Access Control (DAC) models
class Permission(models.Model):
	"""Permission type, e.g. 'read', 'write', 'delete', or custom codenames."""
	codename = models.CharField(max_length=100, unique=True)
	name = models.CharField(max_length=200, blank=True)

	def __str__(self):
		return self.codename


class AccessGrant(models.Model):
	"""Grant a specific permission to a user or group over an object (generic)."""
	# who: user OR group
	user = models.ForeignKey(User, null=True, blank=True, on_delete=models.CASCADE)
	group = models.ForeignKey(Group, null=True, blank=True, on_delete=models.CASCADE)

	# what: generic object
	content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
	object_id = models.CharField(max_length=255)
	content_object = GenericForeignKey('content_type', 'object_id')

	permission = models.ForeignKey('Permission', on_delete=models.CASCADE)
	allow = models.BooleanField(default=True)
	created = models.DateTimeField(auto_now_add=True)

	class Meta:
		unique_together = (('user', 'group', 'content_type', 'object_id', 'permission'),)

	def __str__(self):
		who = self.user or (self.group.name if self.group else "<group>")
		return f"{who} {'ALLOW' if self.allow else 'DENY'} {self.permission} on {self.content_type}#{self.object_id}"


class Owner(models.Model):
	"""Optional explicit owner record for an object (convenience)."""
	user = models.ForeignKey(User, on_delete=models.CASCADE)
	content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
	object_id = models.CharField(max_length=255)
	content_object = GenericForeignKey('content_type', 'object_id')

	class Meta:
		unique_together = (('user', 'content_type', 'object_id'),)

	def __str__(self):
		return f"Owner: {self.user} -> {self.content_type}#{self.object_id}"


class AuditLog(models.Model):
	"""Audit log for DAC access attempts and denials."""
	user = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
	path = models.CharField(max_length=1024)
	method = models.CharField(max_length=10)
	view_name = models.CharField(max_length=255, blank=True)
	content_type = models.ForeignKey(ContentType, null=True, blank=True, on_delete=models.SET_NULL)
	object_id = models.CharField(max_length=255, null=True, blank=True)
	allowed = models.BooleanField(default=False)
	status_code = models.IntegerField(null=True, blank=True)
	detail = models.TextField(blank=True)
	created = models.DateTimeField(auto_now_add=True, db_index=True)

	class Meta:
		ordering = ["-created"]

	def __str__(self):
		who = self.user or "anon"
		return f"[{self.created.isoformat()}] {who} {self.method} {self.path} -> {'ALLOWED' if self.allowed else 'DENIED'}"
