import hashlib
import secrets

from django.conf import settings
from django.db import models
from django.utils import timezone

from family_harmony.models import FamilyHarmonyProfile


class ProfileShare(models.Model):
    profile = models.ForeignKey(FamilyHarmonyProfile, on_delete=models.PROTECT, related_name='shares')
    token_hash = models.CharField(max_length=64, unique=True)
    expires_at = models.DateTimeField()
    max_views = models.PositiveIntegerField(default=1)
    views = models.PositiveIntegerField(default=0)
    require_last_four = models.BooleanField(default=False)
    revoked_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [models.Index(fields=['token_hash']), models.Index(fields=['expires_at'])]

    @classmethod
    def issue(cls, profile, created_by, expires_at, **kwargs):
        raw_token = secrets.token_urlsafe(32)
        share = cls.objects.create(profile=profile, created_by=created_by, token_hash=hashlib.sha256(raw_token.encode()).hexdigest(), expires_at=expires_at, **kwargs)
        return share, raw_token

    def is_available(self):
        return not self.revoked_at and self.expires_at > timezone.now() and self.views < self.max_views
