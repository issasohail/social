from django.contrib import admin

from .models import Case, CaseActivity, CaseDocument, CaseNote

admin.site.register([Case, CaseNote, CaseDocument, CaseActivity])
