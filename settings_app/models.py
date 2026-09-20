from django.db import models


class FamilyHarmonySettings(models.Model):
    default_expiry_days = models.PositiveSmallIntegerField(default=4)
    minimum_expiry_days = models.PositiveSmallIntegerField(default=1)
    maximum_expiry_days = models.PositiveSmallIntegerField(default=30)
    default_max_views = models.PositiveIntegerField(default=5)
    require_last_four_cnic = models.BooleanField(default=False)
    photo_visibility = models.CharField(max_length=30, default='after_interest')
    name_visibility = models.CharField(max_length=30, default='full_name')
    title_options = models.JSONField(default=list, blank=True)
    education_levels = models.JSONField(default=list, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Family Harmony settings'

    def __str__(self):
        return 'Family Harmony settings'

    @classmethod
    def current(cls):
        settings, _ = cls.objects.get_or_create(pk=1)
        if not settings.title_options:
            settings.title_options = ['Mr', 'Mrs', 'Miss', 'Ms', 'Dr', 'Prof', 'Other']
        if not settings.education_levels:
            settings.education_levels = ['Metric', 'O Level', 'Bachelor', 'Master', 'PhD', 'Other']
        settings.save(update_fields=['title_options', 'education_levels'])
        return settings
