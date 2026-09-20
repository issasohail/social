from django.conf import settings
from django.db import models

from boards.models import Board
from organization.models import Jamatkhana, LocalCouncil, RegionalCouncil
from people.models import Person


class Case(models.Model):
    class Status(models.TextChoices):
        OPEN = 'OPEN', 'Open'
        ON_HOLD = 'ON_HOLD', 'On hold'
        CLOSED = 'CLOSED', 'Closed'

    class Priority(models.TextChoices):
        LOW = 'LOW', 'Low'
        NORMAL = 'NORMAL', 'Normal'
        HIGH = 'HIGH', 'High'
        URGENT = 'URGENT', 'Urgent'

    board = models.ForeignKey(Board, on_delete=models.PROTECT, related_name='cases')
    person = models.ForeignKey(Person, on_delete=models.PROTECT, related_name='cases')
    region = models.ForeignKey(RegionalCouncil, null=True, blank=True, on_delete=models.PROTECT)
    local_council = models.ForeignKey(LocalCouncil, null=True, blank=True, on_delete=models.PROTECT)
    jamatkhana = models.ForeignKey(Jamatkhana, null=True, blank=True, on_delete=models.PROTECT)
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='assigned_cases')
    case_type = models.CharField(max_length=100)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.OPEN)
    priority = models.CharField(max_length=20, choices=Priority.choices, default=Priority.NORMAL)
    opened_at = models.DateTimeField(auto_now_add=True)
    closed_at = models.DateTimeField(null=True, blank=True)
    summary = models.TextField(blank=True)
    outcome = models.TextField(blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL, related_name='cases_created')
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL, related_name='cases_updated')

    class Meta:
        indexes = [models.Index(fields=['board', 'status']), models.Index(fields=['region', 'local_council', 'jamatkhana'])]


class CaseNote(models.Model):
    case = models.ForeignKey(Case, on_delete=models.CASCADE, related_name='notes')
    confidential = models.BooleanField(default=True)
    note = models.TextField()
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)


class CaseDocument(models.Model):
    case = models.ForeignKey(Case, on_delete=models.CASCADE, related_name='documents')
    category = models.CharField(max_length=60, default='other')
    file = models.FileField(upload_to='case-documents/%Y/%m/')
    confidential = models.BooleanField(default=True)
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    uploaded_at = models.DateTimeField(auto_now_add=True)


class CaseActivity(models.Model):
    case = models.ForeignKey(Case, on_delete=models.CASCADE, related_name='activities')
    type = models.CharField(max_length=60)
    description = models.TextField()
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    timestamp = models.DateTimeField(auto_now_add=True)
