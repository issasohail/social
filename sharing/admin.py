from django.contrib import admin

from .models import ProfileShare

@admin.register(ProfileShare)
class ProfileShareAdmin(admin.ModelAdmin):
    list_display = ('profile', 'created_at', 'expires_at', 'views', 'revoked_at')
    readonly_fields = ('token_hash', 'created_at')
