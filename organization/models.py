from django.db import models


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class NationalCouncil(TimeStampedModel):
    name = models.CharField(max_length=160)
    code = models.CharField(max_length=40, unique=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class RegionalCouncil(TimeStampedModel):
    national_council = models.ForeignKey(NationalCouncil, on_delete=models.PROTECT, related_name='regions')
    name = models.CharField(max_length=160)
    code = models.CharField(max_length=40, unique=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        indexes = [models.Index(fields=['national_council', 'is_active'])]

    def __str__(self):
        return self.name


class LocalCouncil(TimeStampedModel):
    regional_council = models.ForeignKey(RegionalCouncil, on_delete=models.PROTECT, related_name='locals')
    name = models.CharField(max_length=160)
    code = models.CharField(max_length=40, unique=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        indexes = [models.Index(fields=['regional_council', 'is_active'])]

    def __str__(self):
        return self.name


class Jamatkhana(TimeStampedModel):
    local_council = models.ForeignKey(LocalCouncil, on_delete=models.PROTECT, related_name='jamatkhanas')
    name = models.CharField(max_length=160)
    short_name = models.CharField(max_length=80, blank=True)
    code = models.CharField(max_length=40, unique=True)
    is_active = models.BooleanField(default=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)

    class Meta:
        indexes = [models.Index(fields=['local_council', 'is_active'])]

    def __str__(self):
        return self.short_name or self.name


class UserJurisdictionAccess(TimeStampedModel):
    class Level(models.TextChoices):
        NATIONAL = 'NATIONAL', 'National'
        REGIONAL = 'REGIONAL', 'Regional'
        LOCAL = 'LOCAL', 'Local'
        JK = 'JK', 'Jamatkhana'

    user = models.ForeignKey('auth.User', on_delete=models.CASCADE, related_name='jurisdiction_access')
    level = models.CharField(max_length=12, choices=Level.choices)
    national_council = models.ForeignKey(NationalCouncil, null=True, blank=True, on_delete=models.CASCADE)
    regional_council = models.ForeignKey(RegionalCouncil, null=True, blank=True, on_delete=models.CASCADE)
    local_council = models.ForeignKey(LocalCouncil, null=True, blank=True, on_delete=models.CASCADE)
    jamatkhana = models.ForeignKey(Jamatkhana, null=True, blank=True, on_delete=models.CASCADE)
    board = models.ForeignKey('boards.Board', null=True, blank=True, on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    granted_by = models.ForeignKey('auth.User', null=True, blank=True, on_delete=models.SET_NULL, related_name='granted_jurisdictions')
    granted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [models.Index(fields=['user', 'level', 'is_active'])]
