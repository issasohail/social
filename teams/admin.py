from django.contrib import admin
from .models import Portfolio, TeamAppointment, TeamPosition, Term

admin.site.register([Term, TeamPosition, Portfolio, TeamAppointment])
