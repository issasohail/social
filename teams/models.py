from django.core.exceptions import ValidationError
from django.db import models


class Term(models.Model):
    name = models.CharField(max_length=80, unique=True)
    start_date = models.DateField()
    end_date = models.DateField()
    is_current = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['-is_current', '-start_date', 'sort_order', 'name']

    def clean(self):
        if self.end_date < self.start_date:
            raise ValidationError({'end_date': 'End date cannot be before start date.'})

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.is_current:
            Term.objects.exclude(pk=self.pk).filter(is_current=True).update(is_current=False)

    def __str__(self):
        return self.name


class TeamCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)
    sort_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['sort_order', 'name']
        verbose_name_plural = 'Team categories'

    def __str__(self):
        return self.name


class TeamPosition(models.Model):
    name = models.CharField(max_length=100, unique=True)
    category = models.ForeignKey(TeamCategory, null=True, blank=True, on_delete=models.PROTECT, related_name='positions')
    sort_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['sort_order', 'name']

    def __str__(self):
        return self.name


class Portfolio(models.Model):
    board = models.ForeignKey('boards.Board', on_delete=models.PROTECT, related_name='team_portfolios')
    name = models.CharField(max_length=120)
    code = models.CharField(max_length=50)
    sort_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['board__sort_order', 'board__name', 'sort_order', 'name']
        constraints = [
            models.UniqueConstraint(fields=['board', 'name'], name='unique_board_portfolio_name'),
            models.UniqueConstraint(fields=['board', 'code'], name='unique_board_portfolio_code'),
        ]

    def __str__(self):
        board = self.board.short_name or self.board.name
        return f'{board} — {self.name}'


class TeamAppointment(models.Model):
    class Level(models.TextChoices):
        NATIONAL = 'NATIONAL', 'National'
        REGIONAL = 'REGIONAL', 'Regional'
        LOCAL = 'LOCAL', 'Local Council'
        JK = 'JK', 'Jamatkhana'

    term = models.ForeignKey(Term, on_delete=models.PROTECT, related_name='appointments')
    board = models.ForeignKey('boards.Board', on_delete=models.PROTECT, related_name='team_appointments')
    person = models.ForeignKey('people.Person', on_delete=models.PROTECT, related_name='team_appointments')
    position = models.ForeignKey(TeamPosition, on_delete=models.PROTECT, related_name='appointments')
    portfolio = models.ForeignKey(Portfolio, null=True, blank=True, on_delete=models.PROTECT, related_name='appointments')
    level = models.CharField(max_length=12, choices=Level.choices)
    national_council = models.ForeignKey('organization.NationalCouncil', null=True, blank=True, on_delete=models.PROTECT, related_name='team_appointments')
    regional_council = models.ForeignKey('organization.RegionalCouncil', null=True, blank=True, on_delete=models.PROTECT, related_name='team_appointments')
    local_council = models.ForeignKey('organization.LocalCouncil', null=True, blank=True, on_delete=models.PROTECT, related_name='team_appointments')
    jamatkhana = models.ForeignKey('organization.Jamatkhana', null=True, blank=True, on_delete=models.PROTECT, related_name='team_appointments')
    covered_jamatkhanas = models.ManyToManyField('organization.Jamatkhana', blank=True, related_name='covered_team_appointments')
    appointment_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey('auth.User', null=True, blank=True, on_delete=models.SET_NULL, related_name='team_appointments_created')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['position__sort_order', 'position__name', 'person__full_name']
        indexes = [
            models.Index(fields=['term', 'board', 'level', 'is_active']),
            models.Index(fields=['regional_council', 'local_council', 'jamatkhana']),
        ]

    def clean(self):
        errors = {}
        if self.end_date and self.appointment_date and self.end_date < self.appointment_date:
            errors['end_date'] = 'End date cannot be before appointment date.'
        if self.level == self.Level.NATIONAL and not self.national_council_id:
            errors['national_council'] = 'National council is required.'
        if self.level == self.Level.REGIONAL and not self.regional_council_id:
            errors['regional_council'] = 'Regional council is required.'
        if self.level == self.Level.LOCAL and not self.local_council_id:
            errors['local_council'] = 'Local council is required.'
        if self.level == self.Level.JK and not self.jamatkhana_id:
            errors['jamatkhana'] = 'Jamatkhana is required.'
        if self.portfolio_id and self.board_id and self.portfolio.board_id != self.board_id:
            errors['portfolio'] = 'Portfolio must belong to the selected board.'
        if errors:
            raise ValidationError(errors)

    @property
    def jurisdiction_name(self):
        return self.jamatkhana or self.local_council or self.regional_council or self.national_council

    def __str__(self):
        return f'{self.person} - {self.position} ({self.term})'
