from django.conf import settings
from django.db import models


class AuditLog(models.Model):
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    action = models.CharField(max_length=80)
    model_name = models.CharField(max_length=120, blank=True)
    object_id = models.CharField(max_length=80, blank=True)
    board = models.ForeignKey('boards.Board', null=True, blank=True, on_delete=models.SET_NULL)
    jurisdiction = models.CharField(max_length=160, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    old_values = models.JSONField(default=dict, blank=True)
    new_values = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        permissions = [('view_audit', 'Can view audit log')]
        ordering = ['-created_at']
        indexes = [models.Index(fields=['created_at']), models.Index(fields=['actor', 'action']), models.Index(fields=['model_name', 'object_id'])]
