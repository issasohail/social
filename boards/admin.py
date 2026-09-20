from django.contrib import admin

from .models import Board, BoardMembership

admin.site.register([Board, BoardMembership])
