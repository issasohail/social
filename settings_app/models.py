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
    occupation_options = models.JSONField(default=list, blank=True)
    employer_options = models.JSONField(default=list, blank=True)
    income_ranges = models.JSONField(default=list, blank=True)
    portfolio_options = models.JSONField(default=list, blank=True)
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
        if not settings.occupation_options:
            settings.occupation_options = ['Government employee', 'Private employee', 'Business owner', 'Self-employed', 'Teacher', 'Doctor', 'Engineer', 'Student', 'Homemaker', 'Retired', 'Unemployed', 'Other']
        if not settings.employer_options:
            settings.employer_options = ['Government', 'Private company', 'Own business', 'NGO', 'Self-employed', 'Not applicable', 'Other']
        if not settings.income_ranges:
            settings.income_ranges = ['No income', 'Below 50,000', '50,000 - 100,000', '100,000 - 200,000', '200,000 - 500,000', 'Above 500,000', 'Other']
        if not settings.portfolio_options:
            settings.portfolio_options = ['Family Harmony', 'Seniors', 'Portfolio 3', 'Portfolio 4', 'Portfolio 5', 'Portfolio 6']
        settings.save(update_fields=['title_options', 'education_levels', 'occupation_options', 'employer_options', 'income_ranges', 'portfolio_options'])
        return settings
