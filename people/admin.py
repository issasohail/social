from django.contrib import admin

from .models import Family, FamilyMembership, Person, PersonRelationship

admin.site.register([Person, Family, FamilyMembership, PersonRelationship])
