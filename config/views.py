import hashlib
import secrets
from io import BytesIO
from datetime import timedelta
from urllib.parse import quote

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.contrib import messages
from django.db import IntegrityError
from django.db.models.deletion import ProtectedError
from django.db.models import Count, Q
from django.http import Http404, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.cache import never_cache
from django.core.paginator import Paginator

from family_harmony.models import FamilyHarmonyProfile, FamilyHarmonyPreference
from family_harmony.models import PublicFormInvitation
from family_harmony.forms import FamilyHarmonyPreferenceForm, FamilyHarmonyProfileForm
from organization.models import Jamatkhana, LocalCouncil, NationalCouncil, RegionalCouncil
from people.forms import PersonForm
from people.models import Person, normalize_phone_number, normalize_cnic
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
    if request.method == 'POST':
        action = request.POST.get('action')
        try:
            if action == 'create':
                RegionalCouncil.objects.create(
                    national_council_id=request.POST.get('national_council'),
                    name=request.POST.get('name', '').strip(), code=request.POST.get('code', '').strip(),
                    is_active=request.POST.get('is_active') == 'on')
                messages.success(request, 'Regional Council created.')
            elif action == 'update':
                item = get_object_or_404(RegionalCouncil, pk=request.POST.get('id'))
                item.national_council_id=request.POST.get('national_council'); item.name=request.POST.get('name','').strip(); item.code=request.POST.get('code','').strip(); item.is_active=request.POST.get('is_active') == 'on'; item.save()
                messages.success(request, 'Regional Council updated.')
            elif action == 'delete':
                item = get_object_or_404(RegionalCouncil, pk=request.POST.get('id'))
                try: item.delete(); messages.success(request, 'Regional Council deleted.')
                except ProtectedError: item.is_active=False; item.save(update_fields=['is_active']); messages.warning(request, 'Regional Council is in use, so it was made inactive instead of being deleted.')
        except (IntegrityError, ValueError) as exc:
            messages.error(request, f'Could not save Regional Council. Check that the code is unique and required fields are filled. ({exc})')
        return redirect('regional_councils')
    query=(request.GET.get('q') or '').strip(); national_filter=request.GET.get('national',''); status_filter=request.GET.get('status','')
    qs=RegionalCouncil.objects.select_related('national_council').all()
    if query: qs=qs.filter(Q(name__icontains=query)|Q(code__icontains=query))
    if national_filter: qs=qs.filter(national_council_id=national_filter)
    if status_filter in ('active','inactive'): qs=qs.filter(is_active=status_filter=='active')
    page=Paginator(qs.order_by('name'),25).get_page(request.GET.get('page'))
    return render(request,'organization/regional_councils.html',{'page_obj':page,'items':page,'query':query,'national':national_filter,'status':status_filter,'nationals':NationalCouncil.objects.all().order_by('name'),'title':'Regional Council','subtitle':'Create, filter and edit Regional Councils inline.','stats':{'total':RegionalCouncil.objects.count(),'active':RegionalCouncil.objects.filter(is_active=True).count(),'linked':LocalCouncil.objects.filter(is_active=True).count()}})


@login_required
def local_councils(request):
    if request.method == 'POST':
        action=request.POST.get('action')
        try:
            if action == 'create':
                LocalCouncil.objects.create(regional_council_id=request.POST.get('regional_council'),name=request.POST.get('name','').strip(),code=request.POST.get('code','').strip(),is_active=request.POST.get('is_active')=='on'); messages.success(request,'Local Council created.')
            elif action == 'update':
                item=get_object_or_404(LocalCouncil,pk=request.POST.get('id')); item.regional_council_id=request.POST.get('regional_council'); item.name=request.POST.get('name','').strip(); item.code=request.POST.get('code','').strip(); item.is_active=request.POST.get('is_active')=='on'; item.save(); messages.success(request,'Local Council updated.')
            elif action == 'delete':
                item=get_object_or_404(LocalCouncil,pk=request.POST.get('id'))
                try: item.delete(); messages.success(request,'Local Council deleted.')
                except ProtectedError: item.is_active=False; item.save(update_fields=['is_active']); messages.warning(request,'Local Council is in use, so it was made inactive instead of being deleted.')
        except (IntegrityError,ValueError) as exc: messages.error(request,f'Could not save Local Council. Check that the code is unique and required fields are filled. ({exc})')
        return redirect('local_councils')
    query=(request.GET.get('q') or '').strip(); region_filter=request.GET.get('region',''); status_filter=request.GET.get('status','')
    qs=LocalCouncil.objects.select_related('regional_council','regional_council__national_council').all()
    if query: qs=qs.filter(Q(name__icontains=query)|Q(code__icontains=query))
    if region_filter: qs=qs.filter(regional_council_id=region_filter)
    if status_filter in ('active','inactive'): qs=qs.filter(is_active=status_filter=='active')
    page=Paginator(qs.order_by('regional_council__name','name'),25).get_page(request.GET.get('page'))
    return render(request,'organization/local_councils.html',{'page_obj':page,'items':page,'query':query,'region':region_filter,'status':status_filter,'regions':RegionalCouncil.objects.all().order_by('name'),'title':'Local Council','subtitle':'Create, filter and edit Local Councils inline.','stats':{'total':LocalCouncil.objects.count(),'active':LocalCouncil.objects.filter(is_active=True).count(),'linked':Jamatkhana.objects.filter(is_active=True).count()}})


@login_required
def jamatkhanas(request):
    if request.method == 'POST':
        action=request.POST.get('action')
        try:
            if action == 'create':
                Jamatkhana.objects.create(local_council_id=request.POST.get('local_council'),name=request.POST.get('name','').strip(),short_name=request.POST.get('short_name','').strip(),code=request.POST.get('code','').strip(),is_active=request.POST.get('is_active')=='on'); messages.success(request,'Jamatkhana created.')
            elif action == 'update':
                item=get_object_or_404(Jamatkhana,pk=request.POST.get('id')); item.local_council_id=request.POST.get('local_council'); item.name=request.POST.get('name','').strip(); item.short_name=request.POST.get('short_name','').strip(); item.code=request.POST.get('code','').strip(); item.is_active=request.POST.get('is_active')=='on'; item.save(); messages.success(request,'Jamatkhana updated.')
            elif action == 'delete':
                item=get_object_or_404(Jamatkhana,pk=request.POST.get('id'))
                try: item.delete(); messages.success(request,'Jamatkhana deleted.')
                except ProtectedError: item.is_active=False; item.save(update_fields=['is_active']); messages.warning(request,'Jamatkhana is in use, so it was made inactive instead of being deleted.')
        except (IntegrityError,ValueError) as exc: messages.error(request,f'Could not save Jamatkhana. Check that the code is unique and required fields are filled. ({exc})')
        return redirect('jamatkhanas')
    query=(request.GET.get('q') or '').strip(); region_filter=request.GET.get('region',''); local_filter=request.GET.get('local_council',''); status_filter=request.GET.get('status','')
    qs=Jamatkhana.objects.select_related('local_council','local_council__regional_council','local_council__regional_council__national_council').all()
    if query: qs=qs.filter(Q(name__icontains=query)|Q(code__icontains=query)|Q(short_name__icontains=query))
    if region_filter: qs=qs.filter(local_council__regional_council_id=region_filter)
    if local_filter: qs=qs.filter(local_council_id=local_filter)
    if status_filter in ('active','inactive'): qs=qs.filter(is_active=status_filter=='active')
    page=Paginator(qs.order_by('local_council__name','name'),25).get_page(request.GET.get('page'))
    return render(request,'organization/jamatkhanas.html',{'page_obj':page,'items':page,'query':query,'region':region_filter,'local_council':local_filter,'status':status_filter,'regions':RegionalCouncil.objects.all().order_by('name'),'local_councils':LocalCouncil.objects.select_related('regional_council').all().order_by('regional_council__name','name'),'title':'Jamatkhana','subtitle':'Create, filter and edit Jamatkhanas inline.','stats':{'total':Jamatkhana.objects.count(),'active':Jamatkhana.objects.filter(is_active=True).count(),'linked':Person.objects.filter(is_active=True).count()}})


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
    query = request.GET.get('q', '').strip()
    if query:
        profiles = profiles.filter(Q(person__full_name__icontains=query) | Q(person__mobile__icontains=query) | Q(person__city__icontains=query))
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
        'query': query,
        'portfolio': request.GET.get('portfolio', ''),
        'local_council': request.GET.get('local_council', ''),
        'jamatkhana': request.GET.get('jamatkhana', ''),
    })


def _filter_subtitle(request):
    labels = {'q': 'Search', 'gender': 'Gender', 'city': 'City', 'local_council': 'LC', 'jamatkhana': 'JK', 'portfolio': 'Portfolio', 'status': 'Status', 'profession': 'Profession'}
    values = []
    for key, label in labels.items():
        value = request.GET.get(key)
        if not value:
            continue
        if key == 'local_council':
            value = LocalCouncil.objects.filter(pk=value).values_list('name', flat=True).first() if value.isdigit() else value
        elif key == 'jamatkhana':
            value = Jamatkhana.objects.filter(pk=value).values_list('name', flat=True).first() if value.isdigit() else value
        values.append(f'{label}: {value}')
    return ' | '.join(values) or 'All records'


def _export_response(request, rows, headers, title, subtitle='', export_format=None):
    export_format = export_format or request.GET.get('format')
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
        pdf.setTitle(title)
        pdf.setAuthor('Social Welfare Center')
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
    rows = [(person.serial_number, person.full_name, person.age or '', person.gender, person.city, person.mobile, person.occupation, person.masked_identity_number()) for person in people]
    export = _export_response(request, rows, ['Serial', 'Name', 'Age', 'Gender', 'City', 'Phone', 'Occupation', 'CNIC'], 'People', _filter_subtitle(request))
    if export:
        return export
    page = Paginator(people, 50).get_page(request.GET.get('page'))
    context = {'people': page, 'page_obj': page, 'query': query, 'gender': request.GET.get('gender', ''), 'city': request.GET.get('city', '')}
    context.update(extra_context or {})
    return render(request, 'people/list.html', context)


def _harmony_response(request, profiles, status, extra_context=None):
    rows = [(profile.serial_number, profile.person.full_name, profile.person.age or '', profile.person.gender, profile.person.city, profile.person.mobile, profile.owning_local_council.name if profile.owning_local_council else '—', profile.owning_jamatkhana.name if profile.owning_jamatkhana else '—', profile.profession, profile.get_status_display()) for profile in profiles]
    export = _export_response(request, rows, ['Serial', 'Name', 'Age', 'Gender', 'City', 'Phone', 'Current LC', 'Current JK', 'Profession', 'Status'], 'Family Harmony', _filter_subtitle(request))
    if export:
        return export
    page = Paginator(profiles, 50).get_page(request.GET.get('page'))
    context = {'profiles': page, 'page_obj': page, 'query': request.GET.get('q', ''), 'status': status, 'statuses': FamilyHarmonyProfile.Status.choices, 'gender': request.GET.get('gender', ''), 'city': request.GET.get('city', ''), 'profession': request.GET.get('profession', '')}
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
    person=get_object_or_404(Person,pk=person_id)
    if export_format == 'pdf' and hasattr(person, 'harmony_profile'):
        return harmony_export(request, person.harmony_profile.pk, 'pdf')
    if export_format=='pdf':
        from reportlab.lib.pagesizes import letter
        from reportlab.pdfgen import canvas
        from reportlab.lib.utils import ImageReader
        output=BytesIO(); W,H=letter; c=canvas.Canvas(output,pagesize=letter); c.setTitle(f'Person - {person.full_name}')
        green=(.07,.42,.41); c.setFillColorRGB(*green); c.rect(0,H-78,W,78,fill=1,stroke=0); c.setFillColorRGB(1,1,1); c.setFont('Helvetica-Bold',18); c.drawString(34,H-36,'Social Welfare Center'); c.setFont('Helvetica',10); c.drawString(34,H-56,f'Person Detail · {person.serial_number}')
        y=H-112
        if person.photo:
            try: c.drawImage(ImageReader(person.photo.path),W-128,H-188,88,88,preserveAspectRatio=True,mask='auto')
            except Exception: pass
        c.setFillColorRGB(.1,.18,.2); c.setFont('Helvetica-Bold',17); c.drawString(34,y,person.full_name); y-=28
        sections=[('Personal Information',[('Title',person.title),('Gender',person.gender),('Date of Birth',person.date_of_birth),('Age',person.age),('Marital Status',person.marital_status),('Nationality',person.nationality)]),('Contact & Residence',[('Mobile',person.mobile),('WhatsApp',person.whatsapp_number),('Email',person.email),('City / Province',f'{person.city} / {person.province}'),('Country',person.country),('Current Address',person.current_address)]),('Organization',[('Regional Council',person.region),('Local Council',person.local_council),('Jamatkhana',person.jamatkhana)]),('Education & Career',[('Education',person.education),('Education Details',person.education_details),('Occupation',person.occupation),('Employer / Business',person.employer_or_business),('Income Range',person.income_range),('Languages',person.languages)])]
        for heading,items in sections:
            c.setFillColorRGB(.88,.94,.91); c.rect(30,y-4,W-60,18,fill=1,stroke=0); c.setFillColorRGB(*green); c.setFont('Helvetica-Bold',9); c.drawString(35,y+1,heading); y-=20
            for label,value in items:
                text=str(value or '—').replace('\n',' ')[:115]; c.setFillColorRGB(.2,.25,.25); c.setFont('Helvetica-Bold',7.5); c.drawString(35,y,label+':'); c.setFont('Helvetica',7.5); c.drawString(135,y,text); y-=13
            y-=5
        c.setStrokeColorRGB(.75,.8,.78); c.line(30,34,W-30,34); c.setFont('Helvetica',6.5); c.setFillColorRGB(.35,.4,.4); c.drawString(32,22,'Confidential Social Welfare record'); c.drawRightString(W-32,22,'US Letter · Page 1 of 1'); c.save()
        r=HttpResponse(output.getvalue(),content_type='application/pdf'); r['Content-Disposition']=f'attachment; filename="{person.serial_number.lower()}-person.pdf"'; return r
    rows=[(person.serial_number,person.full_name,person.age or '',person.gender or '—',person.city or '—',person.mobile or '—',person.occupation or '—',person.masked_identity_number() or '—')]
    export=_export_response(request,rows,['Serial','Name','Age','Gender','City','Phone','Occupation','CNIC'],f'Person: {person.full_name}','Person detail',export_format=export_format)
    if export is not None:return export
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
    preference_form = FamilyHarmonyPreferenceForm(request.POST or None)
    if person_form.is_valid() and profile_form.is_valid() and preference_form.is_valid():
        person = person_form.save(commit=False)
        person.updated_by = request.user
        person.save()
        profile = profile_form.save(commit=False)
        profile.person = person
        profile.owning_jamatkhana = person.jamatkhana
        profile.owning_local_council = person.local_council
        profile.owning_region = person.region
        profile.save()
        pref = preference_form.save(commit=False); pref.profile = profile; pref.save()
        return redirect('harmony_detail', profile_id=profile.pk)
    return render(request, 'family_harmony/form.html', {'person_form': person_form, 'profile_form': profile_form, 'preference_form': preference_form, 'person_id': person.pk, 'title': 'Add Family Harmony profile'})


@login_required
def harmony_detail(request, profile_id):
    profile = get_object_or_404(FamilyHarmonyProfile.objects.select_related('person'), pk=profile_id)
    return render(request, 'family_harmony/detail.html', {'profile': profile})



def _marriage_profile_pdf_response(profile):
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.utils import ImageReader
    from reportlab.pdfbase.pdfmetrics import stringWidth
    from reportlab.pdfgen import canvas

    person = profile.person
    pref = getattr(profile, 'preferences', None)
    output = BytesIO()
    width, height = letter
    pdf = canvas.Canvas(output, pagesize=letter)
    pdf.setTitle(f'Marriage Profile - {person.full_name}')
    navy = (0.09, 0.20, 0.29)
    pale = (0.91, 0.94, 0.96)
    ink = (0.12, 0.20, 0.25)
    muted = (0.38, 0.46, 0.50)

    def clean(value):
        if value in (None, '', []):
            return '—'
        if isinstance(value, (list, tuple)):
            return ', '.join(str(v) for v in value) or '—'
        return str(value)

    def wrap(text, font='Helvetica', size=6.8, max_width=175, max_lines=2):
        words = clean(text).replace('\n', ' ').split()
        lines, line = [], ''
        for word in words:
            test = (line + ' ' + word).strip()
            if stringWidth(test, font, size) <= max_width:
                line = test
            else:
                if line:
                    lines.append(line)
                line = word
                if len(lines) >= max_lines:
                    break
        if line and len(lines) < max_lines:
            lines.append(line)
        if not lines:
            lines = ['—']
        if len(lines) == max_lines and len(words) > sum(len(x.split()) for x in lines):
            lines[-1] = lines[-1][:-1] + '…' if len(lines[-1]) > 2 else lines[-1]
        return lines

    # Header mirrors the desktop biodata card.
    pdf.setFillColorRGB(*navy)
    pdf.rect(0, height - 138, width, 138, fill=1, stroke=0)
    photo_x, photo_y, photo_w, photo_h = 28, height - 128, 88, 106
    if person.photo:
        try:
            pdf.drawImage(ImageReader(person.photo.path), photo_x, photo_y, photo_w, photo_h,
                          preserveAspectRatio=True, anchor='c', mask='auto')
        except (OSError, ValueError):
            pass
    pdf.setStrokeColorRGB(0.75, 0.83, 0.87)
    pdf.rect(photo_x, photo_y, photo_w, photo_h, fill=0, stroke=1)
    pdf.setFillColorRGB(1, 1, 1)
    pdf.setFont('Helvetica-Bold', 20)
    pdf.drawString(134, height - 48, person.full_name[:38])
    pdf.setFont('Helvetica', 8)
    pdf.drawString(134, height - 68, f'{profile.serial_number}   |   Marriage Profile')
    pdf.drawString(134, height - 84, 'Aga Khan Social Welfare Board - Central Region')
    badges = [f'{person.age or "—"} yrs', person.gender or '—', profile.marital_status or person.marital_status or '—']
    bx = 134
    for badge in badges:
        bw = stringWidth(str(badge), 'Helvetica-Bold', 7) + 14
        pdf.setFillColorRGB(1, 1, 1)
        pdf.roundRect(bx, height - 112, bw, 18, 9, fill=1, stroke=0)
        pdf.setFillColorRGB(*navy)
        pdf.setFont('Helvetica-Bold', 7)
        pdf.drawCentredString(bx + bw / 2, height - 106, str(badge))
        bx += bw + 6

    y = height - 156

    def section(title, items):
        nonlocal y
        pdf.setFillColorRGB(*pale)
        pdf.roundRect(26, y - 2, width - 52, 17, 3, fill=1, stroke=0)
        pdf.setFillColorRGB(*navy)
        pdf.setFont('Helvetica-Bold', 8.5)
        pdf.drawString(32, y + 3, title)
        y -= 16
        col_w = (width - 64) / 2
        row_height = 22
        for index in range(0, len(items), 2):
            pair = items[index:index + 2]
            max_lines = 1
            rendered = []
            for label, value in pair:
                lines = wrap(value, max_width=col_w - 82, max_lines=2)
                max_lines = max(max_lines, len(lines))
                rendered.append((label, lines))
            row_height = 10 + (max_lines * 7)
            for col, (label, lines) in enumerate(rendered):
                x = 32 + col * col_w
                pdf.setFillColorRGB(*muted)
                pdf.setFont('Helvetica-Bold', 6.3)
                pdf.drawString(x, y, label.upper())
                pdf.setFillColorRGB(*ink)
                pdf.setFont('Helvetica', 6.8)
                for line_no, line in enumerate(lines):
                    pdf.drawString(x + 76, y - (line_no * 7), line)
            y -= row_height
        y -= 4

    height_text = '—'
    if profile.height_cm:
        total_inches = round(profile.height_cm / 2.54)
        height_text = f'{total_inches // 12} ft {total_inches % 12} in'
    section('Personal Information', [
        ('Age / DOB', f'{person.age or "—"} / {person.date_of_birth or "—"}'),
        ('Gender', person.gender), ('Marital Status', profile.marital_status or person.marital_status),
        ('Height / Weight', f'{height_text} / {profile.weight_kg or "—"} kg'),
        ('Physical Status', profile.physical_status), ('City / Country', f'{person.city or "—"}, {person.country or "—"}'),
        ('Jamatkhana', person.jamatkhana), ('Local Council', person.local_council),
    ])
    section('Family', [
        ('Father', f'{profile.father_name or "—"} / {profile.father_occupation or "—"}'),
        ('Mother', f'{profile.mother_name or "—"} / {profile.mother_occupation or "—"}'),
        ('Siblings', profile.siblings_summary), ('Family Residence', profile.family_residence),
        ('Family Type', profile.family_type), ('Caste / Tribe', profile.caste_tribe),
    ])
    section('Education & Career', [
        ('Education', profile.qualification or profile.education_level or person.education),
        ('Institution', profile.institution), ('Profession', profile.profession or person.occupation),
        ('Employer / Business', profile.employer_or_business or person.employer_or_business),
        ('Income', profile.income_range or person.income_range), ('Experience', profile.years_experience),
        ('House', 'Yes' if profile.owns_house is True else 'No' if profile.owns_house is False else '—'),
        ('Car', 'Yes' if profile.owns_car is True else 'No' if profile.owns_car is False else '—'),
    ])
    section('Health & Lifestyle', [
        ('Disability', profile.disability_status), ('Known Diseases', profile.known_diseases),
        ('Smoking', profile.smoking), ('Languages', profile.languages or person.languages),
        ('Interests', profile.interests or person.interests), ('Health Notes', profile.health_information),
    ])
    if pref:
        section('Preferences for Prospective Match', [
            ('Age Range', f'{pref.minimum_age or "Any"} - {pref.maximum_age or "Any"}'),
            ('Education', pref.preferred_education_options), ('Profession', pref.preferred_professions),
            ('Location', pref.preferred_cities or pref.preferred_locations), ('Income', pref.preferred_income_options),
            ('Marital Status', pref.preferred_marital_status_options), ('Languages', pref.preferred_languages),
            ('Relocation', 'Yes' if pref.willingness_to_relocate else 'No'),
        ])
    if y > 62:
        section('About', [('Personal Statement', profile.personal_statement), ('Other Expectations', pref.other_expectations if pref else profile.expectations)])

    pdf.setStrokeColorRGB(0.78, 0.82, 0.84)
    pdf.line(26, 34, width - 26, 34)
    pdf.setFillColorRGB(*muted)
    pdf.setFont('Helvetica', 6.3)
    pdf.drawString(28, 22, 'Confidential Family Harmony profile. CNIC images and internal documents are not included.')
    pdf.drawRightString(width - 28, 22, 'US Letter · Page 1 of 1')
    pdf.save()
    response = HttpResponse(output.getvalue(), content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{profile.serial_number.lower()}-marriage-profile.pdf"'
    return response

@login_required
def harmony_export(request, profile_id, export_format):
    profile = get_object_or_404(FamilyHarmonyProfile.objects.select_related('person','owning_region','owning_local_council','owning_jamatkhana'), pk=profile_id)
    person=profile.person; pref=getattr(profile,'preferences',None); serial=profile.serial_number
    if export_format == 'pdf':
        return _marriage_profile_pdf_response(profile)
    if export_format == 'jpg':
        from PIL import Image, ImageDraw
        image=Image.new('RGB',(1275,1650),'white'); draw=ImageDraw.Draw(image); draw.text((50,40),f'Marriage Profile - {person.full_name}',fill='black'); draw.text((50,90),'Use the PDF export for the designed one-page Letter profile.',fill='black'); output=BytesIO(); image.save(output,format='JPEG',quality=92); response=HttpResponse(output.getvalue(),content_type='image/jpeg'); response['Content-Disposition']=f'attachment; filename="{serial.lower()}-marriage-profile.jpg"'; return response
    raise Http404()


@login_required
def create_profile_share(request, profile_id):
    profile = get_object_or_404(FamilyHarmonyProfile, pk=profile_id)
    settings = FamilyHarmonySettings.current()
    raw_token = secrets.token_urlsafe(32)
    expiry_days = max(settings.minimum_expiry_days, min(settings.default_expiry_days, settings.maximum_expiry_days))
    share = ProfileShare.objects.create(profile=profile, created_by=request.user, token_hash=hashlib.sha256(raw_token.encode()).hexdigest(), expires_at=timezone.now() + timedelta(days=expiry_days), max_views=settings.default_max_views, require_last_four=settings.require_last_four_cnic)
    share_url = request.build_absolute_uri(reverse('shared_profile', kwargs={'token': raw_token}))
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
    share_url = request.build_absolute_uri(reverse('shared_person', kwargs={'token': raw_token}))
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
    preference, _ = FamilyHarmonyPreference.objects.get_or_create(profile=profile)
    preference_form = FamilyHarmonyPreferenceForm(request.POST or None, instance=preference)
    if person_form.is_valid() and profile_form.is_valid() and preference_form.is_valid():
        person = person_form.save()
        profile = profile_form.save(commit=False)
        profile.owning_jamatkhana = person.jamatkhana
        profile.owning_local_council = person.local_council
        profile.owning_region = person.region
        profile.save()
        preference_form.save()
        return redirect('harmony_detail', profile_id=profile.pk)
    return render(request, 'family_harmony/form.html', {'person_form': person_form, 'profile_form': profile_form, 'preference_form': preference_form, 'title': 'Edit Family Harmony profile'})


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
    if not invitation.is_available(): raise Http404('This form link has expired or has already been submitted.')
    settings = FamilyHarmonySettings.current()
    if request.method == 'POST':
        identity = (request.POST.get('identity_number') or '').strip()
        normalized = ''.join(normalize_cnic(identity).split()).upper() or None
        if normalized and Person.objects.filter(normalized_identity_number=normalized).exists():
            person_form = PersonForm(request.POST, request.FILES)
            profile_form = FamilyHarmonyProfileForm(request.POST)
            preference_form = FamilyHarmonyPreferenceForm(request.POST)
            return render(request, 'family_harmony/public_form.html', {
                'invitation': invitation, 'settings': settings, 'person_form': person_form,
                'profile_form': profile_form, 'preference_form': preference_form,
                'error': 'A record with this ID number already exists. Please contact the Family Harmony team instead of submitting again.', 'public_mode': True
            })
        person_form = PersonForm(request.POST, request.FILES)
        profile_form = FamilyHarmonyProfileForm(request.POST)
        preference_form = FamilyHarmonyPreferenceForm(request.POST)
        if person_form.is_valid() and profile_form.is_valid() and preference_form.is_valid():
            person = person_form.save(commit=False)
            # Jamatkhana is authoritative; RC/LC remain internal derived assignments.
            if not person.jamatkhana and invitation.preselected_jamatkhana:
                person.jamatkhana = invitation.preselected_jamatkhana
            if person.jamatkhana:
                person.local_council = person.jamatkhana.local_council
                person.region = person.local_council.regional_council
            else:
                person.local_council = invitation.preselected_local_council
                person.region = invitation.preselected_region
            person.save()
            profile=profile_form.save(commit=False); profile.person=person; profile.status=FamilyHarmonyProfile.Status.AWAITING_CONSENT
            profile.owning_region=person.region; profile.owning_local_council=person.local_council; profile.owning_jamatkhana=person.jamatkhana; profile.save()
            pref=preference_form.save(commit=False); pref.profile=profile; pref.save()
            invitation.profile=profile; invitation.submitted_at=timezone.now(); invitation.save(update_fields=['profile','submitted_at'])
            return render(request, 'family_harmony/public_submitted.html')
    else:
        person_form=PersonForm(); profile_form=FamilyHarmonyProfileForm(); preference_form=FamilyHarmonyPreferenceForm()
    return render(request, 'family_harmony/public_form.html', {'invitation': invitation, 'settings': settings, 'person_form': person_form, 'profile_form': profile_form, 'preference_form': preference_form, 'public_mode': True})

@never_cache
def identity_duplicate_check(request):
    value=(request.GET.get('identity_number') or '').strip()
    normalized=''.join(normalize_cnic(value).split()).upper()
    exists=bool(normalized and Person.objects.filter(normalized_identity_number=normalized).exists())
    return JsonResponse({'exists': exists, 'message': 'Record already exists.' if exists else ''})


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
    if not request.user.has_perm('family_harmony.add_familyharmonyprofile') and not request.user.is_superuser: raise Http404()
    raw_token=secrets.token_urlsafe(32); cfg=FamilyHarmonySettings.current(); days=max(cfg.minimum_expiry_days,min(cfg.default_expiry_days,cfg.maximum_expiry_days))
    invitation=PublicFormInvitation.objects.create(token_hash=hashlib.sha256(raw_token.encode()).hexdigest(),created_by=request.user,expires_at=timezone.now()+timedelta(days=days))
    public_url=request.build_absolute_uri(reverse('public_form',kwargs={'token':raw_token}))
    whatsapp_url='https://wa.me/?text='+quote(f'Marriage Profile Submission Form\nPlease complete this secure form: {public_url}\nNo username or password is required. Link expires in {days} days.')
    if request.GET.get('redirect')=='whatsapp': return redirect(whatsapp_url)
    return render(request,'family_harmony/invitation_created.html',{'token':raw_token,'invitation':invitation,'public_url':public_url,'whatsapp_url':whatsapp_url,'expiry_days':days})
@login_required
def organization_inline_update(request):
    if request.method != 'POST':
        return JsonResponse({'ok': False, 'error': 'POST required.'}, status=405)
    model_name = (request.POST.get('model') or '').lower()
    field = request.POST.get('field') or ''
    record_id = request.POST.get('id')
    value = (request.POST.get('value') or '').strip()
    model_map = {'regional': RegionalCouncil, 'local': LocalCouncil, 'jamatkhana': Jamatkhana}
    allowed = {
        'regional': {'name','code','national_council_id','is_active'},
        'local': {'name','code','regional_council_id','is_active'},
        'jamatkhana': {'name','short_name','code','local_council_id','is_active'},
    }
    Model = model_map.get(model_name)
    if not Model or field not in allowed.get(model_name, set()):
        return JsonResponse({'ok': False, 'error': 'Field is not editable.'}, status=400)
    item = get_object_or_404(Model, pk=record_id)
    try:
        if field == 'is_active': value = value.lower() in {'1','true','yes','on'}
        elif field.endswith('_id'): value = int(value)
        elif not value and field in {'name','code'}: raise ValueError('This field cannot be blank.')
        setattr(item, field, value); item.save()
        display = str(getattr(item, field[:-3])) if field.endswith('_id') else ('Yes' if value is True else 'No' if value is False else value)
        return JsonResponse({'ok': True, 'value': value, 'display': display})
    except (IntegrityError, ValueError) as exc:
        return JsonResponse({'ok': False, 'error': f'Could not save: {exc}'}, status=400)

@login_required
def pending_approvals(request):
    invitations = PublicFormInvitation.objects.filter(submitted_at__isnull=False, profile__isnull=False, profile__status__in=['DRAFT','AWAITING_CONSENT']).select_related('profile__person','created_by').order_by('-submitted_at')
    return render(request, 'pending_approvals.html', {'invitations': invitations})

@login_required
def pending_approval_action(request, invitation_id):
    if request.method != 'POST': raise Http404()
    invitation = get_object_or_404(PublicFormInvitation.objects.select_related('profile'), pk=invitation_id, profile__isnull=False)
    action = request.POST.get('action')
    if action == 'approve':
        invitation.profile.status = FamilyHarmonyProfile.Status.ACTIVE
        invitation.profile.save(update_fields=['status','updated_at'])
        messages.success(request, 'Marriage profile approved and activated.')
    elif action == 'reject':
        invitation.profile.status = FamilyHarmonyProfile.Status.ARCHIVED
        invitation.profile.save(update_fields=['status','updated_at'])
        messages.success(request, 'Marriage profile rejected and archived.')
    return redirect('pending_approvals')
