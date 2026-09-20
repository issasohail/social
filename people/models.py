from datetime import date

from django.conf import settings
from django.db import models

from organization.models import Jamatkhana, LocalCouncil, RegionalCouncil


class Person(models.Model):
    class IdentityType(models.TextChoices):
        CNIC = 'CNIC', 'CNIC'
        NICOP = 'NICOP', 'NICOP'
        BFORM_CRC = 'BFORM_CRC', 'B-Form / CRC'
        PASSPORT = 'PASSPORT', 'Passport'
        BIRTH_CERTIFICATE = 'BIRTH_CERTIFICATE', 'Birth certificate'
        OTHER = 'OTHER', 'Other'

    title = models.CharField(max_length=30, blank=True)
    first_name = models.CharField(max_length=100)
    middle_name = models.CharField(max_length=100, blank=True)
    last_name = models.CharField(max_length=100, blank=True)
    full_name = models.CharField(max_length=305)
    gender = models.CharField(max_length=40, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    nationality = models.CharField(max_length=80, default='Pakistani', blank=True)
    identity_type = models.CharField(max_length=30, choices=IdentityType.choices, blank=True)
    identity_number = models.CharField(max_length=80, blank=True)
    normalized_identity_number = models.CharField(max_length=80, unique=True, null=True, blank=True)
    mobile = models.CharField(max_length=30, blank=True)
    alternate_mobile = models.CharField(max_length=30, blank=True)
    whatsapp_number = models.CharField(max_length=30, blank=True)
    email = models.EmailField(blank=True)
    current_address = models.TextField(blank=True)
    permanent_address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    province = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, default='Pakistan', blank=True)
    region = models.ForeignKey(RegionalCouncil, null=True, blank=True, on_delete=models.PROTECT, related_name='people')
    local_council = models.ForeignKey(LocalCouncil, null=True, blank=True, on_delete=models.PROTECT, related_name='people')
    jamatkhana = models.ForeignKey(Jamatkhana, null=True, blank=True, on_delete=models.PROTECT, related_name='people')
    marital_status = models.CharField(max_length=50, blank=True)
    education = models.CharField(max_length=160, blank=True)
    education_details = models.TextField(blank=True)
    occupation = models.CharField(max_length=160, blank=True)
    employer_or_business = models.CharField(max_length=160, blank=True)
    income_range = models.CharField(max_length=80, blank=True)
    languages = models.CharField(max_length=255, blank=True)
    interests = models.TextField(blank=True)
    photo = models.ImageField(upload_to='people/%Y/%m/', blank=True)
    facebook_url = models.URLField(blank=True)
    linkedin_url = models.URLField(blank=True)
    instagram_url = models.URLField(blank=True)
    other_social_url = models.URLField(blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='people_created')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='people_updated')
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    archived_at = models.DateTimeField(null=True, blank=True)
    is_demo = models.BooleanField(default=False)

    class Meta:
        permissions = [('view_full_cnic', 'Can view full CNIC'), ('export_person', 'Can export person data')]
        indexes = [models.Index(fields=['full_name']), models.Index(fields=['mobile']), models.Index(fields=['date_of_birth']), models.Index(fields=['region', 'local_council', 'jamatkhana'])]

    def save(self, *args, **kwargs):
        self.full_name = ' '.join(part for part in [self.first_name, self.middle_name, self.last_name] if part).strip()
        self.normalized_identity_number = ''.join(self.identity_number.split()).upper() or None
        super().save(*args, **kwargs)

    @property
    def age(self):
        if not self.date_of_birth:
            return None
        today = date.today()
        return today.year - self.date_of_birth.year - ((today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day))

    def masked_identity_number(self):
        value = self.identity_number or ''
        if len(value) <= 5:
            return '*' * len(value)
        return f'{value[:5]}-*****-{value[-1:]}' if self.identity_type == self.IdentityType.CNIC else f'{value[:2]}***{value[-2:]}'

    def __str__(self):
        return self.full_name


class Family(models.Model):
    name = models.CharField(max_length=160)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)


class FamilyMembership(models.Model):
    family = models.ForeignKey(Family, on_delete=models.CASCADE, related_name='memberships')
    person = models.ForeignKey(Person, on_delete=models.CASCADE, related_name='family_memberships')
    role = models.CharField(max_length=60, blank=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['family', 'person'], name='unique_family_member')]


class PersonRelationship(models.Model):
    class Type(models.TextChoices):
        SPOUSE = 'spouse', 'Spouse'
        FATHER = 'father', 'Father'
        MOTHER = 'mother', 'Mother'
        SON = 'son', 'Son'
        DAUGHTER = 'daughter', 'Daughter'
        BROTHER = 'brother', 'Brother'
        SISTER = 'sister', 'Sister'
        GUARDIAN = 'guardian', 'Guardian'
        DEPENDENT = 'dependent', 'Dependent'
        OTHER = 'other', 'Other'

    person = models.ForeignKey(Person, on_delete=models.CASCADE, related_name='relationships')
    related_person = models.ForeignKey(Person, on_delete=models.CASCADE, related_name='related_to')
    relationship_type = models.CharField(max_length=20, choices=Type.choices)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['person', 'related_person', 'relationship_type'], name='unique_person_relationship')]
