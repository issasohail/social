from django.contrib import admin

from .models import Jamatkhana, LocalCouncil, NationalCouncil, RegionalCouncil, UserJurisdictionAccess

admin.site.register([NationalCouncil, RegionalCouncil, LocalCouncil, Jamatkhana, UserJurisdictionAccess])
