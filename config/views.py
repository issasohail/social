from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.shortcuts import render

from family_harmony.models import FamilyHarmonyProfile
from organization.models import Jamatkhana, LocalCouncil, NationalCouncil, RegionalCouncil
from people.models import Person


@login_required
def dashboard(request):
    context = {
        'people_count': Person.objects.filter(is_active=True).count(),
        'active_profiles': FamilyHarmonyProfile.objects.filter(status='ACTIVE').count(),
        'regions': RegionalCouncil.objects.filter(is_active=True).count(),
        'jamatkhanas': Jamatkhana.objects.filter(is_active=True).count(),
        'profile_statuses': FamilyHarmonyProfile.objects.values('status').annotate(total=Count('id')).order_by('status'),
    }
    return render(request, 'dashboard.html', context)


@login_required
def organization_overview(request):
    return render(request, 'organization/overview.html', {'nationals': NationalCouncil.objects.prefetch_related('regions__locals__jamatkhanas')})


@login_required
def people_list(request):
    query = request.GET.get('q', '').strip()
    people = Person.objects.filter(is_active=True).select_related('region', 'local_council', 'jamatkhana')
    if query:
        people = people.filter(full_name__icontains=query)
    return render(request, 'people/list.html', {'people': people[:100], 'query': query})


@login_required
def harmony_list(request):
    profiles = FamilyHarmonyProfile.objects.select_related('person', 'owning_region', 'owning_jamatkhana')
    status = request.GET.get('status', '').strip()
    if status:
        profiles = profiles.filter(status=status)
    return render(request, 'family_harmony/list.html', {'profiles': profiles[:100], 'status': status, 'statuses': FamilyHarmonyProfile.Status.choices})