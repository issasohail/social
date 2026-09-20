from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from organization.models import Jamatkhana, LocalCouncil, RegionalCouncil
from people.models import Person


class FamilyHarmonyProfile(models.Model):
    class Status(models.TextChoices):
        DRAFT = 'DRAFT', 'Draft'
        AWAITING_CONSENT = 'AWAITING_CONSENT', 'Awaiting consent'
        ACTIVE = 'ACTIVE', 'Active'
        PAUSED = 'PAUSED', 'Paused'
        INTRODUCTION_PENDING = 'INTRODUCTION_PENDING', 'Introduction pending'
        IN_DISCUSSION = 'IN_DISCUSSION', 'In discussion'
        FAMILY_MEETING = 'FAMILY_MEETING', 'Family meeting'
        ENGAGED = 'ENGAGED', 'Engaged'
        MARRIED = 'MARRIED', 'Married'
        CLOSED = 'CLOSED', 'Closed'
        ARCHIVED = 'ARCHIVED', 'Archived'

    person = models.OneToOneField(Person, on_delete=models.PROTECT, related_name='harmony_profile')
    status = models.CharField(max_length=30, choices=Status.choices, default=Status.DRAFT)
    assigned_officer = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    owning_jamatkhana = models.ForeignKey(Jamatkhana, null=True, blank=True, on_delete=models.PROTECT)
    owning_local_council = models.ForeignKey(LocalCouncil, null=True, blank=True, on_delete=models.PROTECT)
    owning_region = models.ForeignKey(RegionalCouncil, null=True, blank=True, on_delete=models.PROTECT)
    height_cm = models.PositiveSmallIntegerField(null=True, blank=True)
    education_level = models.CharField(max_length=100, blank=True)
    qualification = models.CharField(max_length=180, blank=True)
    institution = models.CharField(max_length=180, blank=True)
    profession = models.CharField(max_length=180, blank=True)
    years_experience = models.CharField(max_length=80, blank=True)
    financial_status = models.CharField(max_length=120, blank=True)
    family_background = models.TextField(blank=True)
    place_of_origin = models.CharField(max_length=160, blank=True)
    family_values = models.TextField(blank=True)
    personality = models.TextField(blank=True)
    smoking = models.CharField(max_length=60, blank=True)
    other_lifestyle_details = models.TextField(blank=True)
    children_count = models.PositiveSmallIntegerField(null=True, blank=True)
    child_details = models.TextField(blank=True)
    previous_marriage_notes = models.TextField(blank=True)
    disabilities = models.TextField(blank=True)
    health_information = models.TextField(blank=True)
    personal_statement = models.TextField(blank=True)
    expectations = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    consent_reviewed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_demo = models.BooleanField(default=False)

    class Meta:
        permissions = [('share_profile', 'Can share profile'), ('release_contact', 'Can release contact'), ('approve_cross_region', 'Can approve cross-jurisdiction introductions')]
        indexes = [models.Index(fields=['status']), models.Index(fields=['owning_region', 'owning_local_council', 'owning_jamatkhana']), models.Index(fields=['assigned_officer', 'status'])]

    def clean(self):
        if self.status == self.Status.ACTIVE:
            if not self.person.date_of_birth or (self.person.age or 0) < 18:
                raise ValidationError('Family Harmony profiles must have a date of birth and the candidate must be at least 18.')


class FamilyHarmonyPreference(models.Model):
    profile = models.OneToOneField(FamilyHarmonyProfile, on_delete=models.CASCADE, related_name='preferences')
    minimum_age = models.PositiveSmallIntegerField(null=True, blank=True)
    maximum_age = models.PositiveSmallIntegerField(null=True, blank=True)
    preferred_locations = models.JSONField(default=list, blank=True)
    preferred_regions = models.JSONField(default=list, blank=True)
    preferred_cities = models.JSONField(default=list, blank=True)
    preferred_education = models.CharField(max_length=180, blank=True)
    preferred_professions = models.JSONField(default=list, blank=True)
    preferred_income = models.CharField(max_length=120, blank=True)
    preferred_marital_status = models.CharField(max_length=120, blank=True)
    preferred_family_values = models.TextField(blank=True)
    preferred_personality = models.TextField(blank=True)
    willingness_to_relocate = models.BooleanField(default=False)
    preferred_languages = models.JSONField(default=list, blank=True)
    other_expectations = models.TextField(blank=True)
    free_text_seeking_description = models.TextField(blank=True)


class Consent(models.Model):
    person = models.ForeignKey(Person, on_delete=models.PROTECT, related_name='consents')
    profile = models.ForeignKey(FamilyHarmonyProfile, null=True, blank=True, on_delete=models.PROTECT, related_name='consents')
    consent_type = models.CharField(max_length=80)
    consent_given = models.BooleanField(default=False)
    consent_datetime = models.DateTimeField(default=timezone.now)
    method = models.CharField(max_length=80, blank=True)
    obtained_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL)
    profile_sharing_allowed = models.BooleanField(default=False)
    photo_sharing_allowed = models.BooleanField(default=False)
    contact_release_allowed = models.BooleanField(default=False)
    health_data_sharing_allowed = models.BooleanField(default=False)
    disability_data_sharing_allowed = models.BooleanField(default=False)
    notes = models.TextField(blank=True)
    revoked_at = models.DateTimeField(null=True, blank=True)
    revoked_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='consents_revoked')
    revocation_reason = models.TextField(blank=True)
