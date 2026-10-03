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

    @property
    def hierarchy_label(self):
        local = self.local_council
        region = local.regional_council if local else None
        # Avoid extra assumptions: Jamatkhana always has an LC in the current schema.
        if local and region:
            return f'{self.name} — {local.name} — {region.name}'
        if local:
            return f'{self.name} — {local.name}'
        return self.name

    @property
    def display_name(self):
        return self.hierarchy_label

    def __str__(self):
        return self.hierarchy_label


class UserJurisdictionAccess(TimeStampedModel):
    class Level(models.TextChoices):
        NATIONAL = 'NATIONAL', 'National'
        REGIONAL = 'REGIONAL', 'Regional'
        LOCAL = 'LOCAL', 'Local Council'
        JK = 'JK', 'Jamatkhana'

    class Role(models.TextChoices):
        ADMIN = 'ADMIN', 'Admin'
        MANAGER = 'MANAGER', 'Manager'
        MEMBER = 'MEMBER', 'Member'
        VIEWER = 'VIEWER', 'Viewer'

    CAPABILITY_CHOICES = (
        ('people_view', 'People: view'), ('people_edit', 'People: add/edit'),
        ('people_export', 'People: export'), ('people_share', 'People: share'),
        ('harmony_view', 'Family Harmony: view'), ('harmony_edit', 'Family Harmony: add/edit'),
        ('harmony_export', 'Family Harmony: export'), ('harmony_share', 'Family Harmony: share'),
        ('teams_view', 'Teams: view'), ('teams_edit', 'Teams: add/edit'),
        ('teams_export', 'Teams: export'), ('manage_users', 'User Access: manage subordinate users'),
    )

    user = models.ForeignKey('auth.User', on_delete=models.CASCADE, related_name='jurisdiction_access')
    level = models.CharField(max_length=12, choices=Level.choices)
    role = models.CharField(max_length=12, choices=Role.choices, default=Role.VIEWER)
    capabilities = models.JSONField(default=list, blank=True)
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

    @property
    def is_board_scoped(self):
        return bool(self.board_id)

    @property
    def authority_label(self):
        return f'{self.board.short_name or self.board.name} {self.get_role_display()}' if self.board_id else f'Council {self.get_role_display()}'

    @property
    def jurisdiction_label(self):
        if self.level == self.Level.JK and self.jamatkhana_id:
            return str(self.jamatkhana)
        if self.level == self.Level.LOCAL and self.local_council_id:
            return self.local_council.name
        if self.level == self.Level.REGIONAL and self.regional_council_id:
            return self.regional_council.name
        if self.level == self.Level.NATIONAL and self.national_council_id:
            return self.national_council.name
        return self.get_level_display()

    def has_capability(self, code):
        if self.role == self.Role.ADMIN and code == 'manage_users':
            return 'manage_users' in (self.capabilities or [])
        return code in (self.capabilities or [])
