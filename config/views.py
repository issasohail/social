import hashlib
import secrets
from io import BytesIO
from datetime import timedelta
from urllib.parse import quote

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Count, Q
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.cache import never_cache
from django.core.paginator import Paginator

from family_harmony.models import FamilyHarmonyProfile
from family_harmony.models import PublicFormInvitation
from family_harmony.forms import FamilyHarmonyPreferenceForm, FamilyHarmonyProfileForm
from organization.models import Jamatkhana, LocalCouncil, NationalCouncil, RegionalCouncil
from people.forms import PersonForm
from people.models import Person, normalize_phone_number
from sharing.services import open_share
from sharing.models import PersonShare, ProfileShare
from settings_app.models import FamilyHarmonySettings


def health(request):
    return HttpResponse('ok', content_type='text/plain')


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
def regional_councils(request):
    query = (request.GET.get('q') or '').strip()
    regional_councils_qs = RegionalCouncil.objects.filter(is_active=True).select_related('national_council')
    if query:
        regional_councils_qs = regional_councils_qs.filter(Q(name__icontains=query) | Q(code__icontains=query))
    page = Paginator(regional_councils_qs.order_by('name'), 25).get_page(request.GET.get('page'))
    context = {
        'page_obj': page,
        'items': page,
        'query': query,
        'title': 'Regional Council',
        'subtitle': 'Manage RCs and their local coverage.',
        'stats': {
            'total': RegionalCouncil.objects.filter(is_active=True).count(),
            'active': RegionalCouncil.objects.filter(is_active=True).count(),
            'linked': LocalCouncil.objects.filter(is_active=True).count(),
        },
    }
    return render(request, 'organization/regional_councils.html', context)


@login_required
def local_councils(request):
    query = (request.GET.get('q') or '').strip()
    region_filter = request.GET.get('region', '')
    local_councils_qs = LocalCouncil.objects.filter(is_active=True).select_related('regional_council', 'regional_council__national_council')
    if query:
        local_councils_qs = local_councils_qs.filter(Q(name__icontains=query) | Q(code__icontains=query))
    if region_filter:
        local_councils_qs = local_councils_qs.filter(regional_council_id=region_filter)
    page = Paginator(local_councils_qs.order_by('name'), 25).get_page(request.GET.get('page'))
    context = {
        'page_obj': page,
        'items': page,
        'query': query,
        'region': region_filter,
        'regions': RegionalCouncil.objects.filter(is_active=True).order_by('name'),
        'title': 'Local Council',
        'subtitle': 'Manage LC structures and their JK memberships.',
        'stats': {
            'total': LocalCouncil.objects.filter(is_active=True).count(),
            'active': LocalCouncil.objects.filter(is_active=True).count(),
            'linked': Jamatkhana.objects.filter(is_active=True).count(),
        },
    }
    return render(request, 'organization/local_councils.html', context)


@login_required
def jamatkhanas(request):
    query = (request.GET.get('q') or '').strip()
    local_filter = request.GET.get('local_council', '')
    jamatkhanas_qs = Jamatkhana.objects.filter(is_active=True).select_related('local_council', 'local_council__regional_council', 'local_council__regional_council__national_council')
    if query:
        jamatkhanas_qs = jamatkhanas_qs.filter(Q(name__icontains=query) | Q(code__icontains=query) | Q(short_name__icontains=query))
    if local_filter:
        jamatkhanas_qs = jamatkhanas_qs.filter(local_council_id=local_filter)
    page = Paginator(jamatkhanas_qs.order_by('name'), 25).get_page(request.GET.get('page'))
    context = {
        'page_obj': page,
        'items': page,
        'query': query,
        'local_council': local_filter,
        'local_councils': LocalCouncil.objects.filter(is_active=True).select_related('regional_council').order_by('name'),
        'title': 'Jamatkhana',
        'subtitle': 'Manage JK assignments, coverage, and membership details.',
        'stats': {
            'total': Jamatkhana.objects.filter(is_active=True).count(),
            'active': Jamatkhana.objects.filter(is_active=True).count(),
            'linked': Person.objects.filter(is_active=True).count(),
        },
    }
    return render(request, 'organization/jamatkhanas.html', context)


@login_required
def people_list(request):
    query = request.GET.get('q', '').strip()
    people = Person.objects.filter(is_active=True).select_related('region', 'local_council', 'jamatkhana', 'harmony_profile')
    if query:
        people = people.filter(full_name__icontains=query) | people.filter(mobile__icontains=query) | people.filter(city__icontains=query)
    if request.GET.get('gender'):
        people = people.filter(gender=request.GET['gender'])
    if request.GET.get('city'):
        people = people.filter(city__icontains=request.GET['city'])
    if request.GET.get('local_council'):
        people = people.filter(local_council_id=request.GET['local_council'])
    if request.GET.get('jamatkhana'):
        people = people.filter(jamatkhana_id=request.GET['jamatkhana'])
    context = {
        'local_councils': LocalCouncil.objects.filter(is_active=True).order_by('name'),
        'jamatkhanas': Jamatkhana.objects.filter(is_active=True).select_related('local_council').order_by('name'),
        'local_council': request.GET.get('local_council', ''),
        'jamatkhana': request.GET.get('jamatkhana', ''),
    }
    return _people_response(request, people.distinct().order_by('full_name'), query, context)


@login_required
def harmony_list(request):
    profiles = FamilyHarmonyProfile.objects.select_related('person', 'owning_region', 'owning_local_council', 'owning_jamatkhana')
    status = request.GET.get('status', '').strip()
    if status:
        profiles = profiles.filter(status=status)
    if request.GET.get('gender'):
        profiles = profiles.filter(person__gender=request.GET['gender'])
    if request.GET.get('city'):
        profiles = profiles.filter(person__city__icontains=request.GET['city'])
    if request.GET.get('profession'):
        profiles = profiles.filter(profession__icontains=request.GET['profession'])
    if request.GET.get('portfolio'):
        profiles = profiles.filter(portfolio=request.GET['portfolio'])
    if request.GET.get('local_council'):
        profiles = profiles.filter(owning_local_council_id=request.GET['local_council'])
    if request.GET.get('jamatkhana'):
        profiles = profiles.filter(owning_jamatkhana_id=request.GET['jamatkhana'])
    return _harmony_response(request, profiles.order_by('person__full_name'), status, {
        'local_councils': LocalCouncil.objects.filter(is_active=True).order_by('name'),
        'jamatkhanas': Jamatkhana.objects.filter(is_active=True).select_related('local_council').order_by('name'),
        'portfolio_options': FamilyHarmonySettings.current().portfolio_options,
        'portfolio': request.GET.get('portfolio', ''),
        'local_council': request.GET.get('local_council', ''),
        'jamatkhana': request.GET.get('jamatkhana', ''),
    })


def _filter_subtitle(request):
    labels = {'q': 'Search', 'gender': 'Gender', 'city': 'City', 'local_council': 'LC', 'jamatkhana': 'JK', 'portfolio': 'Portfolio', 'status': 'Status', 'profession': 'Profession'}
    values = [f'{labels[key]}: {request.GET[key]}' for key in labels if request.GET.get(key)]
    return ' | '.join(values) or 'All records'


def _export_response(request, rows, headers, title, subtitle=''):
    export_format = request.GET.get('format')
    subtitle = subtitle or _filter_subtitle(request)
    stamp = timezone.localtime().strftime('%d %b %Y %H:%M')
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
        from reportlab.lib.pagesizes import A4, landscape
        from reportlab.lib import colors
        from reportlab.lib.styles import ParagraphStyle
        from reportlab.lib.units import mm
        from reportlab.pdfgen import canvas
        from reportlab.platypus import Paragraph, Table, TableStyle
        from xml.sax.saxutils import escape
        output = BytesIO()
        page_width, page_height = landscape(A4)
        rows_per_page = 27
        page_count = max(1, (len(rows) + rows_per_page - 1) // rows_per_page)
        pdf = canvas.Canvas(output, pagesize=(page_width, page_height))
        content_width = page_width - (28 * mm)
        header_style = ParagraphStyle('export_header', fontName='Helvetica-Bold', fontSize=7, leading=8, textColor=colors.white)
        cell_style = ParagraphStyle('export_cell', fontName='Helvetica', fontSize=6.7, leading=8, textColor=colors.HexColor('#18313b'))
        for page_number in range(page_count):
            pdf.setFillColorRGB(0.07, 0.42, 0.41)
            pdf.rect(0, page_height - 72, page_width, 72, fill=1, stroke=0)
            pdf.setFillColorRGB(1, 1, 1)
            pdf.setFont('Helvetica-Bold', 16)
            pdf.drawString(36, page_height - 32, title)
            pdf.setFont('Helvetica', 9)
            pdf.drawString(36, page_height - 51, subtitle)

            table_rows = [[Paragraph(escape(str(header)), header_style) for header in headers]]
            for row in rows[page_number * rows_per_page:(page_number + 1) * rows_per_page]:
                table_rows.append([Paragraph(escape(str(value or '—')), cell_style) for value in row])
            column_width = content_width / len(headers)
            table = Table(table_rows, colWidths=[column_width] * len(headers), repeatRows=1)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#126b68')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#eef5f1')]),
                ('GRID', (0, 0), (-1, -1), 0.35, colors.HexColor('#dce5df')),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('LEFTPADDING', (0, 0), (-1, -1), 4),
                ('RIGHTPADDING', (0, 0), (-1, -1), 4),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ]))
            table_width, table_height = table.wrapOn(pdf, content_width, page_height)
            table.drawOn(pdf, 14 * mm, page_height - 92 - table_height)
            pdf.setFillColorRGB(0.40, 0.45, 0.46)
            pdf.setFont('Helvetica', 8)
            pdf.drawString(36, 22, stamp)
            pdf.drawRightString(page_width - 36, 22, f'Page {page_number + 1} of {page_count}')
            pdf.showPage()
        pdf.save()
        response = HttpResponse(output.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{title.lower().replace(" ", "-")}.pdf"'
        return response
    if export_format == 'jpg':
        from PIL import Image, ImageDraw
        image = Image.new('RGB', (1600, max(280, 48 * (len(rows) + 5))), '#f5f7f2')
        draw = ImageDraw.Draw(image)
        draw.rectangle((0, 0, 1600, 108), fill='#126b68')
        draw.text((36, 24), title, fill='white')
        draw.text((36, 66), subtitle, fill='#dff2ea')
        y = 140
        draw.text((36, y), ' | '.join(headers), fill='#126b68')
        for row in rows:
            y += 34
            draw.text((24, y), ' | '.join(str(value or '')[:45] for value in row), fill='#18313b')
        draw.text((36, image.height - 34), stamp, fill='#6b7d82')
        draw.text((1450, image.height - 34), 'Page 1 of 1', fill='#6b7d82')
        output = BytesIO()
        image.save(output, format='JPEG', quality=90)
        response = HttpResponse(output.getvalue(), content_type='image/jpeg')
        response['Content-Disposition'] = f'attachment; filename="{title.lower().replace(" ", "-")}.jpg"'
        return response
    return None


def _people_response(request, people, query, extra_context=None):
    rows = [(person.serial_number, person.full_name, person.age or '', person.gender, person.city, person.occupation, person.masked_identity_number()) for person in people]
    export = _export_response(request, rows, ['Serial', 'Name', 'Age', 'Gender', 'City', 'Occupation', 'CNIC'], 'People', _filter_subtitle(request))
    if export:
        return export
    page = Paginator(people, 50).get_page(request.GET.get('page'))
    context = {'people': page, 'page_obj': page, 'query': query, 'gender': request.GET.get('gender', ''), 'city': request.GET.get('city', '')}
    context.update(extra_context or {})
    return render(request, 'people/list.html', context)


def _harmony_response(request, profiles, status, extra_context=None):
    rows = [(profile.serial_number, profile.person.full_name, profile.person.age or '', profile.person.gender, profile.person.city, profile.owning_local_council.name if profile.owning_local_council else '—', profile.owning_jamatkhana.name if profile.owning_jamatkhana else '—', profile.profession, profile.get_status_display()) for profile in profiles]
    export = _export_response(request, rows, ['Serial', 'Name', 'Age', 'Gender', 'City', 'Current LC', 'Current JK', 'Profession', 'Status'], 'Family Harmony', _filter_subtitle(request))
    if export:
        return export
    page = Paginator(profiles, 50).get_page(request.GET.get('page'))
    context = {'profiles': page, 'page_obj': page, 'status': status, 'statuses': FamilyHarmonyProfile.Status.choices, 'gender': request.GET.get('gender', ''), 'city': request.GET.get('city', ''), 'profession': request.GET.get('profession', '')}
    context.update(extra_context or {})
    return render(request, 'family_harmony/list.html', context)


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
def person_export(request, person_id, export_format):
    person = get_object_or_404(Person, pk=person_id)
    rows = [(person.serial_number, person.full_name, person.age or '', person.gender or '—', person.city or '—', person.occupation or '—', person.masked_identity_number() or '—')]
    headers = ['Serial', 'Name', 'Age', 'Gender', 'City', 'Occupation', 'CNIC']
    export = _export_response(request, rows, headers, f'Person: {person.full_name}', 'Person detail')
    if export is not None:
        return export
    raise Http404()


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
def inline_update_person(request):
    if request.method != 'POST':
        return HttpResponse('Method not allowed', status=405)

    person_id = request.POST.get('person_id') or request.POST.get('id')
    field_name = request.POST.get('field')
    value = request.POST.get('value', '')
    person = get_object_or_404(Person, pk=person_id)

    allowed_fields = {
        'first_name', 'middle_name', 'last_name', 'title', 'gender', 'city', 'occupation',
        'mobile', 'alternate_mobile', 'whatsapp_number', 'email', 'marital_status',
        'identity_number', 'current_address', 'permanent_address'
    }
    if field_name not in allowed_fields:
        return HttpResponse('Unsupported field', status=400)

    setattr(person, field_name, value)
    person.save()
    return HttpResponse('OK')


@login_required
def harmony_create(request):
    person_id = request.POST.get('person_id') or request.GET.get('person_id')
    if not person_id:
        people = Person.objects.filter(is_active=True, harmony_profile__isnull=True).order_by('full_name')
        return render(request, 'family_harmony/select_person.html', {'people': people})

    person = get_object_or_404(Person, pk=person_id, is_active=True)
    if hasattr(person, 'harmony_profile'):
        return redirect('harmony_edit', profile_id=person.harmony_profile.pk)
    person_form = PersonForm(request.POST or None, request.FILES or None, instance=person)
    profile_form = FamilyHarmonyProfileForm(request.POST or None)
    if person_form.is_valid() and profile_form.is_valid():
        person = person_form.save(commit=False)
        person.updated_by = request.user
        person.save()
        profile = profile_form.save(commit=False)
        profile.person = person
        profile.save()
        return redirect('harmony_detail', profile_id=profile.pk)
    return render(request, 'family_harmony/form.html', {'person_form': person_form, 'profile_form': profile_form, 'person_id': person.pk, 'title': 'Add Family Harmony profile'})


@login_required
def harmony_detail(request, profile_id):
    profile = get_object_or_404(FamilyHarmonyProfile.objects.select_related('person'), pk=profile_id)
    return render(request, 'family_harmony/detail.html', {'profile': profile})


@login_required
def harmony_export(request, profile_id, export_format):
    profile = get_object_or_404(FamilyHarmonyProfile.objects.select_related('person', 'owning_region', 'owning_local_council', 'owning_jamatkhana'), pk=profile_id)
    person = profile.person
    serial = f'FH-{profile.pk:05d}'
    stamp = timezone.localtime().strftime('%d %b %Y %H:%M')
    location = f'Region: {profile.owning_region or "—"} | Local: {profile.owning_local_council or "—"} | JK: {profile.owning_jamatkhana or "—"}'
    sections = [
        ('Profile', [f'Serial number: {serial}', f'Name: {person.full_name}', f'Age: {person.age or "—"}', f'Gender: {person.gender or "—"}', f'Status: {profile.get_status_display()}', location]),
        ('Education and work', [f'Education: {profile.qualification or profile.education_level or "—"}', f'Institution: {profile.institution or "—"}', f'Profession: {profile.profession or "—"}', f'Employer: {profile.employer_or_business or "—"}', f'Experience: {profile.years_experience or "—"}', f'Financial status: {profile.financial_status or "—"}']),
        ('Family and personality', [f'Family background: {profile.family_background or "—"}', f'Family values: {profile.family_values or "—"}', f'Personality: {profile.personality or "—"}', f'Interests: {profile.interests or "—"}', f'Languages: {profile.languages or "—"}']),
        ('Seeking', [f'Age range: {profile.preferences.minimum_age if hasattr(profile, "preferences") else "—"} - {profile.preferences.maximum_age if hasattr(profile, "preferences") else "—"}', f'Locations: {", ".join(profile.preferences.preferred_locations) if hasattr(profile, "preferences") else "—"}', f'Education: {profile.preferences.preferred_education if hasattr(profile, "preferences") else "—"}', f'Expectations: {profile.preferences.free_text_seeking_description if hasattr(profile, "preferences") else "—"}']),
        ('About', [f'Personal statement: {profile.personal_statement or "—"}', f'Expectations: {profile.expectations or "—"}', f'Contact release: withheld from external profile']),
    ]
    if export_format == 'pdf':
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.utils import ImageReader
        from reportlab.pdfgen import canvas
        output = BytesIO()
        page_width, page_height = A4
        lines = [(heading, line) for heading, values in sections for line in values]
        per_page = 23
        page_count = max(1, (len(lines) + per_page - 1) // per_page)
        pdf = canvas.Canvas(output, pagesize=A4)
        for page_number in range(page_count):
            pdf.setFillColorRGB(0.07, 0.42, 0.41)
            pdf.rect(0, page_height - 92, page_width, 92, fill=1, stroke=0)
            pdf.setFillColorRGB(1, 1, 1)
            pdf.setFont('Helvetica-Bold', 20)
            pdf.drawString(42, page_height - 45, 'Family Harmony Profile')
            pdf.setFont('Helvetica', 9)
            pdf.drawString(42, page_height - 64, location)
            if page_number == 0 and person.photo:
                try:
                    pdf.drawImage(ImageReader(person.photo.path), page_width - 125, page_height - 82, 70, 70, preserveAspectRatio=True, mask='auto')
                except (OSError, ValueError):
                    pass
            y = page_height - 125
            previous_heading = None
            for heading, line in lines[page_number * per_page:(page_number + 1) * per_page]:
                if heading != previous_heading:
                    pdf.setFillColorRGB(0.85, 0.93, 0.90)
                    pdf.rect(36, y - 4, page_width - 72, 18, fill=1, stroke=0)
                    pdf.setFillColorRGB(0.07, 0.42, 0.41)
                    pdf.setFont('Helvetica-Bold', 10)
                    pdf.drawString(44, y, heading)
                    y -= 22
                    previous_heading = heading
                pdf.setFillColorRGB(0.10, 0.15, 0.18)
                pdf.setFont('Helvetica', 9)
                text = pdf.beginText(46, y)
                text.textLine(line[:145])
                pdf.drawText(text)
                y -= 17
            pdf.setFillColorRGB(0.40, 0.45, 0.46)
            pdf.setFont('Helvetica', 8)
            pdf.drawString(36, 22, stamp)
            pdf.drawRightString(page_width - 36, 22, f'Profile {serial} | Page {page_number + 1} of {page_count}')
            pdf.showPage()
        pdf.save()
        response = HttpResponse(output.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{serial.lower()}-family-harmony.pdf"'
        return response
    if export_format == 'jpg':
        from PIL import Image, ImageDraw, ImageFont
        image = Image.new('RGB', (1400, 1900), '#f5f7f2')
        draw = ImageDraw.Draw(image)
        draw.rectangle((0, 0, 1400, 190), fill='#126b68')
        draw.text((60, 55), 'Family Harmony Profile', fill='white')
        draw.text((60, 112), f'{serial}  |  {location}', fill='#dff2ea')
        if person.photo:
            try:
                photo = Image.open(person.photo.path).convert('RGB').resize((210, 210))
                image.paste(photo, (1120, 30))
            except (OSError, ValueError):
                pass
        y = 240
        for heading, values in sections:
            draw.rectangle((50, y, 1350, y + 38), fill='#d9ebe4')
            draw.text((70, y + 10), heading, fill='#126b68')
            y += 60
            for value in values:
                draw.text((75, y), value[:115], fill='#18313b')
                y += 34
            y += 18
        draw.text((60, 1850), stamp, fill='#6b7d82')
        draw.text((1080, 1850), 'Page 1 of 1', fill='#6b7d82')
        output = BytesIO()
        image.save(output, format='JPEG', quality=92)
        response = HttpResponse(output.getvalue(), content_type='image/jpeg')
        response['Content-Disposition'] = f'attachment; filename="{serial.lower()}-family-harmony.jpg"'
        return response
    raise Http404()


@login_required
def create_profile_share(request, profile_id):
    profile = get_object_or_404(FamilyHarmonyProfile, pk=profile_id)
    settings = FamilyHarmonySettings.current()
    raw_token = secrets.token_urlsafe(32)
    expiry_days = max(settings.minimum_expiry_days, min(settings.default_expiry_days, settings.maximum_expiry_days))
    share = ProfileShare.objects.create(profile=profile, created_by=request.user, token_hash=hashlib.sha256(raw_token.encode()).hexdigest(), expires_at=timezone.now() + timedelta(days=expiry_days), max_views=settings.default_max_views, require_last_four=settings.require_last_four_cnic)
    share_url = request.build_absolute_uri(f'/family-harmony/share/{raw_token}/')
    whatsapp_text = quote(f'Family Harmony profile: {profile.person.full_name}\nPlease review this confidential profile: {share_url}\nLink expires in {expiry_days} days.')
    if request.GET.get('redirect') == 'whatsapp':
        return redirect(f'https://wa.me/?text={whatsapp_text}')
    return render(request, 'family_harmony/share_created.html', {'profile': profile, 'share': share, 'share_url': share_url, 'whatsapp_url': f'https://wa.me/?text={whatsapp_text}'})


@login_required
def create_person_share(request, person_id):
    person = get_object_or_404(Person, pk=person_id)
    settings = FamilyHarmonySettings.current()
    raw_token = secrets.token_urlsafe(32)
    expiry_days = max(settings.minimum_expiry_days, min(settings.default_expiry_days, settings.maximum_expiry_days))
    share = PersonShare.objects.create(
        person=person,
        created_by=request.user,
        token_hash=hashlib.sha256(raw_token.encode()).hexdigest(),
        expires_at=timezone.now() + timedelta(days=expiry_days),
        max_views=settings.default_max_views,
    )
    share_url = request.build_absolute_uri(f'/people/share/{raw_token}/')
    phone = normalize_phone_number(getattr(getattr(request.user, 'profile', None), 'phone_number', ''))
    recipient = ''.join(character for character in phone if character.isdigit())
    whatsapp_text = quote(f'Person detail: {person.full_name}\nPlease review this confidential detail: {share_url}\nLink expires in {expiry_days} days.')
    whatsapp_url = f'https://wa.me/{recipient}?text={whatsapp_text}' if recipient else f'https://wa.me/?text={whatsapp_text}'
    return redirect(whatsapp_url)


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


@login_required
def harmony_inline_update(request):
    if request.method != 'POST':
        return HttpResponse('Method not allowed', status=405)

    profile_id = request.POST.get('profile_id') or request.POST.get('id')
    field_name = request.POST.get('field')
    value = request.POST.get('value', '')
    profile = get_object_or_404(FamilyHarmonyProfile, pk=profile_id)

    allowed_fields = {'status', 'profession', 'education_level', 'institution', 'employer_or_business', 'financial_status', 'city'}
    if field_name not in allowed_fields:
        return HttpResponse('Unsupported field', status=400)

    if field_name == 'city':
        profile.person.city = value
        profile.person.save(update_fields=['city'])
    elif field_name == 'status':
        if value in {choice[0] for choice in FamilyHarmonyProfile.Status.choices}:
            profile.status = value
            profile.save(update_fields=['status'])
        else:
            return HttpResponse('Invalid status', status=400)
    else:
        setattr(profile, field_name, value)
        profile.save(update_fields=[field_name])

    return HttpResponse('OK')


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


@never_cache
def shared_person(request, token):
    share = get_object_or_404(PersonShare, token_hash=hashlib.sha256(token.encode()).hexdigest())
    if not share.is_available():
        raise Http404('This person link is no longer available.')
    share.views += 1
    share.save(update_fields=['views'])
    return render(request, 'people/shared_detail.html', {'person': share.person, 'share': share})


@login_required
def create_form_invitation(request):
    if not request.user.has_perm('family_harmony.add_familyharmonyprofile'):
        raise Http404()
    raw_token = secrets.token_urlsafe(32)
    invitation = PublicFormInvitation.objects.create(token_hash=hashlib.sha256(raw_token.encode()).hexdigest(), created_by=request.user, expires_at=timezone.now() + timedelta(days=4))
    return render(request, 'family_harmony/invitation_created.html', {'token': raw_token, 'invitation': invitation})