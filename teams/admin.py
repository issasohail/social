from django.contrib import admin
from .models import Portfolio, TeamAppointment, TeamCategory, TeamPosition, Term

admin.site.register([Term, TeamCategory, TeamPosition, Portfolio, TeamAppointment])
