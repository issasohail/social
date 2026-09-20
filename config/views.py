import hashlib
import secrets
from io import BytesIO
from datetime import timedelta

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Count
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.cache import never_cache

from family_harmony.models import FamilyHarmonyProfile
from family_harmony.models import PublicFormInvitation
from family_harmony.forms import FamilyHarmonyPreferenceForm, FamilyHarmonyProfileForm
from organization.models import Jamatkhana, LocalCouncil, NationalCouncil, RegionalCouncil
from people.forms import PersonForm
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
        people = people.filter(full_name__icontains=query) | people.filter(mobile__icontains=query) | people.filter(city__icontains=query)
    if request.GET.get('gender'):
        people = people.filter(gender=request.GET['gender'])
    if request.GET.get('city'):
        people = people.filter(city__icontains=request.GET['city'])
    return _people_response(request, people.distinct().order_by('full_name'), query)


@login_required
def harmony_list(request):
    profiles = FamilyHarmonyProfile.objects.select_related('person', 'owning_region', 'owning_jamatkhana')
    status = request.GET.get('status', '').strip()
    if status:
        profiles = profiles.filter(status=status)
    if request.GET.get('gender'):
        profiles = profiles.filter(person__gender=request.GET['gender'])
    if request.GET.get('city'):
        profiles = profiles.filter(person__city__icontains=request.GET['city'])
    if request.GET.get('profession'):
        profiles = profiles.filter(profession__icontains=request.GET['profession'])
    return _harmony_response(request, profiles.order_by('person__full_name'), status)


def _export_response(request, rows, headers, title):
    export_format = request.GET.get('format')
    if export_format == 'xlsx':
        from openpyxl import Workbook
        workbook = Workbook()
        sheet = workbook.active
        sheet.title = title[:31]
        sheet.append(headers)
        for row in rows:
            sheet.append(row)
        output = BytesIO()
        workbook.save(output)
        response = HttpResponse(output.getvalue(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = f'attachment; filename="{title.lower().replace(" ", "-")}.xlsx"'
        return response
    if export_format == 'pdf':
        from reportlab.lib.pagesizes import landscape, letter
        from reportlab.pdfgen import canvas
        output = BytesIO()
        pdf = canvas.Canvas(output, pagesize=landscape(letter))
        pdf.setFont('Helvetica-Bold', 12)
        pdf.drawString(36, 560, title)
        pdf.setFont('Helvetica', 8)
        y = 540
        pdf.drawString(36, y, ' | '.join(headers))
        y -= 16
        for row in rows:
            pdf.drawString(36, y, ' | '.join(str(value or '')[:35] for value in row))
            y -= 13
            if y < 30:
                pdf.showPage()
                y = 560
        pdf.save()
        response = HttpResponse(output.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{title.lower().replace(" ", "-")}.pdf"'
        return response
    if export_format == 'jpg':
        from PIL import Image, ImageDraw
        image = Image.new('RGB', (1400, max(120, 45 * (len(rows) + 2))), 'white')
        draw = ImageDraw.Draw(image)
        draw.text((24, 18), title, fill='#18313b')
        y = 55
        draw.text((24, y), ' | '.join(headers), fill='#126b68')
        for row in rows:
            y += 28
            draw.text((24, y), ' | '.join(str(value or '')[:45] for value in row), fill='#18313b')
        output = BytesIO()
        image.save(output, format='JPEG', quality=90)
        response = HttpResponse(output.getvalue(), content_type='image/jpeg')
        response['Content-Disposition'] = f'attachment; filename="{title.lower().replace(" ", "-")}.jpg"'
        return response
    return None


def _people_response(request, people, query):
    rows = [(person.full_name, person.age or '', person.gender, person.city, person.occupation, person.masked_identity_number()) for person in people]
    export = _export_response(request, rows, ['Name', 'Age', 'Gender', 'City', 'Occupation', 'Identity'], 'People export')
    if export:
        return export
    return render(request, 'people/list.html', {'people': people[:250], 'query': query, 'gender': request.GET.get('gender', ''), 'city': request.GET.get('city', '')})


def _harmony_response(request, profiles, status):
    rows = [(profile.person.full_name, profile.person.age or '', profile.person.gender, profile.person.city, profile.profession, profile.get_status_display()) for profile in profiles]
    export = _export_response(request, rows, ['Name', 'Age', 'Gender', 'City', 'Profession', 'Status'], 'Family Harmony export')
    if export:
        return export
    return render(request, 'family_harmony/list.html', {'profiles': profiles[:250], 'status': status, 'statuses': FamilyHarmonyProfile.Status.choices, 'gender': request.GET.get('gender', ''), 'city': request.GET.get('city', ''), 'profession': request.GET.get('profession', '')})


@login_required
def person_create(request):
    form = PersonForm(request.POST or None, request.FILES or None)
    if form.is_valid():
        person = form.save(commit=False)
        person.created_by = request.user
        person.updated_by = request.user
        person.save()
        return redirect('person_detail', person_id=person.pk)
    return render(request, 'people/form.html', {'form': form, 'title': 'Add person'})


@login_required
def person_detail(request, person_id):
    return render(request, 'people/detail.html', {'person': get_object_or_404(Person, pk=person_id)})


@login_required
def person_edit(request, person_id):
    person = get_object_or_404(Person, pk=person_id)
    form = PersonForm(request.POST or None, request.FILES or None, instance=person)
    if form.is_valid():
        person = form.save(commit=False)
        person.updated_by = request.user
        person.save()
        return redirect('person_detail', person_id=person.pk)
    return render(request, 'people/form.html', {'form': form, 'title': 'Edit person', 'person': person})


@login_required
def person_delete(request, person_id):
    person = get_object_or_404(Person, pk=person_id)
    if request.method == 'POST':
        person.is_active = False
        person.archived_at = timezone.now()
        person.save(update_fields=['is_active', 'archived_at', 'updated_at'])
        return redirect('people')
    return render(request, 'confirm_delete.html', {'object': person, 'cancel_url': 'people'})


@login_required
def harmony_create(request):
    if request.method == 'POST':
        person_form = PersonForm(request.POST, request.FILES or None)
        profile_form = FamilyHarmonyProfileForm(request.POST)
        if person_form.is_valid() and profile_form.is_valid():
            person = person_form.save(commit=False)
            person.created_by = request.user
            person.updated_by = request.user
            person.save()
            profile = profile_form.save(commit=False)
            profile.person = person
            profile.save()
            return redirect('harmony_detail', profile_id=profile.pk)
    else:
        person_form = PersonForm()
        profile_form = FamilyHarmonyProfileForm()
    return render(request, 'family_harmony/form.html', {'person_form': person_form, 'profile_form': profile_form, 'title': 'Add Family Harmony profile'})


@login_required
def harmony_detail(request, profile_id):
    profile = get_object_or_404(FamilyHarmonyProfile.objects.select_related('person'), pk=profile_id)
    return render(request, 'family_harmony/detail.html', {'profile': profile})


@login_required
def harmony_edit(request, profile_id):
    profile = get_object_or_404(FamilyHarmonyProfile.objects.select_related('person'), pk=profile_id)
    person_form = PersonForm(request.POST or None, request.FILES or None, instance=profile.person)
    profile_form = FamilyHarmonyProfileForm(request.POST or None, instance=profile)
    if person_form.is_valid() and profile_form.is_valid():
        person_form.save()
        profile_form.save()
        return redirect('harmony_detail', profile_id=profile.pk)
    return render(request, 'family_harmony/form.html', {'person_form': person_form, 'profile_form': profile_form, 'title': 'Edit Family Harmony profile'})


@login_required
def harmony_delete(request, profile_id):
    profile = get_object_or_404(FamilyHarmonyProfile, pk=profile_id)
    if request.method == 'POST':
        profile.status = FamilyHarmonyProfile.Status.ARCHIVED
        profile.save(update_fields=['status', 'updated_at'])
        return redirect('family_harmony')
    return render(request, 'confirm_delete.html', {'object': profile, 'cancel_url': 'family_harmony'})


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