from django.conf import settings
from django.db import models


class Board(models.Model):
    name = models.CharField(max_length=120, unique=True)
    code = models.CharField(max_length=40, unique=True)
    short_name = models.CharField(max_length=60, blank=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=60, blank=True)
    sort_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['sort_order', 'name']

    def __str__(self):
        return self.name


class BoardMembership(models.Model):
    board = models.ForeignKey(Board, on_delete=models.CASCADE, related_name='memberships')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='board_memberships')
    role = models.CharField(max_length=80, blank=True)
    is_active = models.BooleanField(default=True)
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['board', 'user'], name='unique_board_user')]
