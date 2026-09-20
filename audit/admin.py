from django.contrib import admin

from .models import AuditLog

@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('created_at', 'actor', 'action', 'model_name', 'object_id')
    readonly_fields = [field.name for field in AuditLog._meta.fields]
