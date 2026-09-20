import hashlib
import secrets
from datetime import timedelta

from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.cache import never_cache

from family_harmony.models import FamilyHarmonyProfile
from family_harmony.models import PublicFormInvitation
from organization.models import Jamatkhana, LocalCouncil, NationalCouncil, RegionalCouncil
from people.models import Person
from sharing.services import open_share


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


@never_cache
def public_form(request, token):
    invitation = get_object_or_404(PublicFormInvitation, token_hash=hashlib.sha256(token.encode()).hexdigest())
    if not invitation.is_available():
        raise Http404('This form link has expired or has already been submitted.')
    if request.method == 'POST':
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        if not first_name:
            return render(request, 'family_harmony/public_form.html', {'invitation': invitation, 'error': 'First name is required.'})
        person = Person.objects.create(
            first_name=first_name, last_name=last_name, mobile=request.POST.get('mobile', '').strip(),
            email=request.POST.get('email', '').strip(), city=request.POST.get('city', '').strip(),
            gender=request.POST.get('gender', '').strip(), date_of_birth=request.POST.get('date_of_birth') or None,
            region=invitation.preselected_region, local_council=invitation.preselected_local_council,
            jamatkhana=invitation.preselected_jamatkhana,
        )
        profile = FamilyHarmonyProfile.objects.create(person=person, status=FamilyHarmonyProfile.Status.AWAITING_CONSENT, owning_region=invitation.preselected_region, owning_local_council=invitation.preselected_local_council, owning_jamatkhana=invitation.preselected_jamatkhana)
        invitation.profile = profile
        invitation.submitted_at = timezone.now()
        invitation.save(update_fields=['profile', 'submitted_at'])
        return render(request, 'family_harmony/public_submitted.html')
    return render(request, 'family_harmony/public_form.html', {'invitation': invitation})


@never_cache
def shared_profile(request, token):
    share = open_share(request, token)
    if share is None:
        raise Http404('This profile link is no longer available.')
    profile = share.profile
    return render(request, 'family_harmony/shared_profile.html', {'profile': profile, 'share': share})


@login_required
def create_form_invitation(request):
    if not request.user.has_perm('family_harmony.add_familyharmonyprofile'):
        raise Http404()
    raw_token = secrets.token_urlsafe(32)
    invitation = PublicFormInvitation.objects.create(token_hash=hashlib.sha256(raw_token.encode()).hexdigest(), created_by=request.user, expires_at=timezone.now() + timedelta(days=4))
    return render(request, 'family_harmony/invitation_created.html', {'token': raw_token, 'invitation': invitation})