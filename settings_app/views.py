from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from .models import FamilyHarmonySettings


@login_required
def settings_page(request):
    settings = FamilyHarmonySettings.current()
    if request.method == 'POST':
        title_lines = request.POST.get('title_options', '').strip()
        education_lines = request.POST.get('education_levels', '').strip()
        settings.title_options = [item.strip() for item in title_lines.splitlines() if item.strip()] or settings.title_options
        settings.education_levels = [item.strip() for item in education_lines.splitlines() if item.strip()] or settings.education_levels
        settings.default_expiry_days = int(request.POST.get('default_expiry_days', settings.default_expiry_days))
        settings.minimum_expiry_days = int(request.POST.get('minimum_expiry_days', settings.minimum_expiry_days))
        settings.maximum_expiry_days = int(request.POST.get('maximum_expiry_days', settings.maximum_expiry_days))
        settings.default_max_views = int(request.POST.get('default_max_views', settings.default_max_views))
        settings.require_last_four_cnic = request.POST.get('require_last_four_cnic') == 'on'
        settings.photo_visibility = request.POST.get('photo_visibility', settings.photo_visibility)
        settings.name_visibility = request.POST.get('name_visibility', settings.name_visibility)
        settings.save()
    return render(request, 'settings_app/settings.html', {'settings': settings})
