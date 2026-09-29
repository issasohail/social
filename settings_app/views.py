from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from .models import FamilyHarmonySettings


@login_required
def settings_page(request):
    settings = FamilyHarmonySettings.current()
    if request.method == 'POST':
        title_lines = request.POST.get('title_options', '').strip()
        education_lines = request.POST.get('education_levels', '').strip()
        occupation_lines = request.POST.get('occupation_options', '').strip()
        employer_lines = request.POST.get('employer_options', '').strip()
        business_type_lines = request.POST.get('business_type_options', '').strip()
        income_lines = request.POST.get('income_ranges', '').strip()
        portfolio_lines = request.POST.get('portfolio_options', '').strip()
        family_type_lines = request.POST.get('family_type_options', '').strip()
        language_lines = request.POST.get('language_options', '').strip()
        marital_lines = request.POST.get('marital_status_options', '').strip()
        relationship_lines = request.POST.get('relationship_options', '').strip()
        caste_lines = request.POST.get('caste_tribe_options', '').strip()
        nationality_lines = request.POST.get('nationality_options', '').strip()
        country_lines = request.POST.get('country_options', '').strip()
        physical_lines = request.POST.get('physical_status_options', '').strip()
        disability_lines = request.POST.get('disability_options', '').strip()
        disease_lines = request.POST.get('known_disease_options', '').strip()
        settings.title_options = [item.strip() for item in title_lines.splitlines() if item.strip()] or settings.title_options
        settings.education_levels = [item.strip() for item in education_lines.splitlines() if item.strip()] or settings.education_levels
        settings.occupation_options = [item.strip() for item in occupation_lines.splitlines() if item.strip()] or settings.occupation_options
        settings.employer_options = [item.strip() for item in employer_lines.splitlines() if item.strip()] or settings.employer_options
        settings.business_type_options = [item.strip() for item in business_type_lines.splitlines() if item.strip()] or settings.business_type_options
        settings.income_ranges = [item.strip() for item in income_lines.splitlines() if item.strip()] or settings.income_ranges
        settings.portfolio_options = [item.strip() for item in portfolio_lines.splitlines() if item.strip()] or settings.portfolio_options
        settings.family_type_options = [item.strip() for item in family_type_lines.splitlines() if item.strip()] or settings.family_type_options
        settings.language_options = [item.strip() for item in language_lines.splitlines() if item.strip()] or settings.language_options
        settings.marital_status_options = [item.strip() for item in marital_lines.splitlines() if item.strip()] or settings.marital_status_options
        settings.relationship_options = [item.strip() for item in relationship_lines.splitlines() if item.strip()] or settings.relationship_options
        settings.caste_tribe_options = [item.strip() for item in caste_lines.splitlines() if item.strip()] or settings.caste_tribe_options
        settings.nationality_options = [item.strip() for item in nationality_lines.splitlines() if item.strip()] or settings.nationality_options
        settings.country_options = [item.strip() for item in country_lines.splitlines() if item.strip()] or settings.country_options
        settings.physical_status_options = [item.strip() for item in physical_lines.splitlines() if item.strip()] or settings.physical_status_options
        settings.disability_options = [item.strip() for item in disability_lines.splitlines() if item.strip()] or settings.disability_options
        settings.known_disease_options = [item.strip() for item in disease_lines.splitlines() if item.strip()] or settings.known_disease_options
        settings.default_expiry_days = int(request.POST.get('default_expiry_days', settings.default_expiry_days))
        settings.minimum_expiry_days = int(request.POST.get('minimum_expiry_days', settings.minimum_expiry_days))
        settings.maximum_expiry_days = int(request.POST.get('maximum_expiry_days', settings.maximum_expiry_days))
        settings.default_max_views = int(request.POST.get('default_max_views', settings.default_max_views))
        settings.require_last_four_cnic = request.POST.get('require_last_four_cnic') == 'on'
        settings.photo_visibility = request.POST.get('photo_visibility', settings.photo_visibility)
        settings.name_visibility = request.POST.get('name_visibility', settings.name_visibility)
        settings.save()
    return render(request, 'settings_app/settings.html', {'settings': settings})


SETTING_LIST_FIELDS = {
    'education': 'education_levels', 'title': 'title_options', 'occupation': 'occupation_options',
    'business_type': 'business_type_options', 'income': 'income_ranges', 'family_type': 'family_type_options',
    'language': 'language_options', 'marital_status': 'marital_status_options', 'relationship': 'relationship_options',
    'caste_tribe': 'caste_tribe_options', 'nationality': 'nationality_options', 'country': 'country_options',
    'physical_status': 'physical_status_options', 'disability': 'disability_options', 'known_disease': 'known_disease_options',
}

@login_required
@require_POST
def setting_list_crud(request, category):
    if not request.user.is_superuser:
        return JsonResponse({'ok': False, 'error': 'Superuser access required.'}, status=403)
    field = SETTING_LIST_FIELDS.get(category)
    if not field:
        return JsonResponse({'ok': False, 'error': 'Unknown setting list.'}, status=404)
    obj = FamilyHarmonySettings.current()
    values = list(getattr(obj, field) or [])
    action = request.POST.get('action', '').strip()
    value = request.POST.get('value', '').strip()
    try:
        if action == 'add':
            if not value: raise ValueError('Value is required.')
            if value.casefold() in {x.casefold() for x in values}: raise ValueError('That value already exists.')
            values.append(value)
        elif action == 'update':
            index = int(request.POST.get('index'))
            if not value: raise ValueError('Value is required.')
            if not 0 <= index < len(values): raise ValueError('Invalid row.')
            if value.casefold() in {x.casefold() for i,x in enumerate(values) if i != index}: raise ValueError('That value already exists.')
            values[index] = value
        elif action == 'delete':
            index = int(request.POST.get('index'))
            if not 0 <= index < len(values): raise ValueError('Invalid row.')
            values.pop(index)
        else:
            raise ValueError('Unknown action.')
        setattr(obj, field, values); obj.save(update_fields=[field, 'updated_at'])
        return JsonResponse({'ok': True, 'values': values})
    except (ValueError, TypeError) as exc:
        return JsonResponse({'ok': False, 'error': str(exc)}, status=400)
