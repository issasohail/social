from django.contrib import admin

from .models import Consent, FamilyHarmonyPreference, FamilyHarmonyProfile

admin.site.register([FamilyHarmonyProfile, FamilyHarmonyPreference, Consent])
