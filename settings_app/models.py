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
    business_type_options = models.JSONField(default=list, blank=True)
    income_ranges = models.JSONField(default=list, blank=True)
    portfolio_options = models.JSONField(default=list, blank=True)
    family_type_options = models.JSONField(default=list, blank=True)
    language_options = models.JSONField(default=list, blank=True)
    marital_status_options = models.JSONField(default=list, blank=True)
    relationship_options = models.JSONField(default=list, blank=True)
    caste_tribe_options = models.JSONField(default=list, blank=True)
    nationality_options = models.JSONField(default=list, blank=True)
    country_options = models.JSONField(default=list, blank=True)
    physical_status_options = models.JSONField(default=list, blank=True)
    disability_options = models.JSONField(default=list, blank=True)
    known_disease_options = models.JSONField(default=list, blank=True)
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
        if not settings.business_type_options:
            settings.business_type_options = ['Salaried / Employment', 'Self-employed', 'Sole Proprietorship', 'Partnership', 'Private Limited Company', 'Family Business', 'Professional Practice', 'Freelance / Consultancy', 'Not applicable', 'Other']
        if not settings.income_ranges:
            settings.income_ranges = ['No income', 'Below 50,000', '50,000 - 100,000', '100,000 - 200,000', '200,000 - 500,000', 'Above 500,000', 'Other']
        if not settings.portfolio_options:
            settings.portfolio_options = ['Family Harmony', 'Seniors', 'Portfolio 3', 'Portfolio 4', 'Portfolio 5', 'Portfolio 6']
        if not settings.family_type_options:
            settings.family_type_options = ['Nuclear', 'Joint', 'Extended']
        if not settings.language_options:
            settings.language_options = ['English', 'Urdu', 'Gujarati', 'Sindhi', 'Punjabi', 'Pashto', 'Burushaski', 'Shina', 'Khowar', 'Other']
        if not settings.marital_status_options:
            settings.marital_status_options = ['Never married', 'Divorced', 'Widowed', 'Separated', 'Other']
        if not settings.relationship_options:
            settings.relationship_options = ['Father', 'Mother', 'Brother', 'Sister', 'Son', 'Daughter', 'Guardian', 'Other']
        if not settings.caste_tribe_options or settings.caste_tribe_options == ['Other']:
            settings.caste_tribe_options = ['Khoja', 'Momin', 'Gilgit', 'Hunza', 'Ghizar', 'Punal', 'Gojali', 'Other']
        if not settings.nationality_options:
            settings.nationality_options = ['Pakistani', 'Other']
        if not settings.country_options:
            settings.country_options = ['Pakistan', 'United States', 'United Kingdom', 'Canada', 'United Arab Emirates', 'Other']
        if not settings.physical_status_options:
            settings.physical_status_options = ['Healthy / Fit', 'Average', 'Underweight', 'Overweight', 'Other']
        if not settings.disability_options:
            settings.disability_options = ['None', 'Physical', 'Visual', 'Hearing', 'Speech', 'Intellectual / Developmental', 'Multiple', 'Other']
        if not settings.known_disease_options:
            settings.known_disease_options = ['Diabetes', 'High cholesterol', 'Thyroid disorder', 'High blood pressure', 'Heart condition', 'Asthma', 'Other']
        settings.save(update_fields=['title_options', 'education_levels', 'occupation_options', 'employer_options', 'business_type_options', 'income_ranges', 'portfolio_options', 'family_type_options', 'language_options', 'marital_status_options', 'relationship_options', 'caste_tribe_options', 'nationality_options', 'country_options', 'physical_status_options', 'disability_options', 'known_disease_options'])
        return settings
