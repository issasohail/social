from io import BytesIO
from urllib.parse import quote

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from openpyxl import Workbook
from PIL import Image, ImageDraw, ImageFont
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer

from boards.models import Board
from organization.access import active_accesses
from organization.models import Jamatkhana, LocalCouncil, NationalCouncil, RegionalCouncil
from .forms import TeamAppointmentForm
from .models import Portfolio, TeamAppointment, TeamPosition, Term


def _scoped(qs, user):
    if user.is_superuser:
        return qs
    allowed = Q()
    for access in active_accesses(user):
        board_q = Q() if not access.board_id else Q(board_id=access.board_id)
        if access.level == 'NATIONAL':
            if access.national_council_id:
                allowed |= board_q & Q(national_council_id=access.national_council_id)
            else:
                allowed |= board_q
        elif access.level == 'REGIONAL' and access.regional_council_id:
            allowed |= board_q & Q(regional_council_id=access.regional_council_id)
        elif access.level == 'LOCAL' and access.local_council_id:
            allowed |= board_q & Q(local_council_id=access.local_council_id)
        elif access.level == 'JK' and access.jamatkhana_id:
            allowed |= board_q & (Q(jamatkhana_id=access.jamatkhana_id) | Q(covered_jamatkhanas=access.jamatkhana_id))
    return qs.filter(allowed).distinct() if allowed else qs.none()


def _filtered(request):
    qs = TeamAppointment.objects.select_related('term','board','person','position','portfolio','national_council','regional_council','local_council','jamatkhana').prefetch_related('covered_jamatkhanas')
    qs = _scoped(qs, request.user)
    term = request.GET.get('term') or ''
    if not term:
        current = Term.objects.filter(is_current=True, is_active=True).first()
        if current:
            term = str(current.pk)
    filters = {
        'term': term,
        'board': request.GET.get('board',''),
        'level': request.GET.get('level',''),
        'regional': request.GET.get('regional',''),
        'local': request.GET.get('local',''),
        'jk': request.GET.get('jk',''),
        'portfolio': request.GET.get('portfolio',''),
        'position': request.GET.get('position',''),
        'status': request.GET.get('status','active'),
        'q': request.GET.get('q','').strip(),
    }
    if filters['term']: qs = qs.filter(term_id=filters['term'])
    if filters['board']: qs = qs.filter(board_id=filters['board'])
    if filters['level']: qs = qs.filter(level=filters['level'])
    if filters['regional']: qs = qs.filter(regional_council_id=filters['regional'])
    if filters['local']: qs = qs.filter(local_council_id=filters['local'])
    if filters['jk']: qs = qs.filter(Q(jamatkhana_id=filters['jk'])|Q(covered_jamatkhanas=filters['jk'])).distinct()
    if filters['portfolio']: qs = qs.filter(portfolio_id=filters['portfolio'])
    if filters['position']: qs = qs.filter(position_id=filters['position'])
    if filters['status'] == 'active': qs = qs.filter(is_active=True)
    elif filters['status'] == 'inactive': qs = qs.filter(is_active=False)
    if filters['q']:
        q = filters['q']
        qs = qs.filter(Q(person__full_name__icontains=q)|Q(person__mobile__icontains=q)|Q(person__email__icontains=q)|Q(position__name__icontains=q)|Q(portfolio__name__icontains=q))
    return qs, filters


@login_required
def team_list(request):
    qs, filters = _filtered(request)
    ctx = {
        'appointments': qs,
        'filters': filters,
        'terms': Term.objects.filter(is_active=True),
        'boards': Board.objects.filter(is_active=True).order_by('sort_order','name'),
        'positions': TeamPosition.objects.filter(is_active=True),
        'portfolios': Portfolio.objects.filter(is_active=True),
        'regions': RegionalCouncil.objects.filter(is_active=True),
        'locals': LocalCouncil.objects.filter(is_active=True),
        'jks': Jamatkhana.objects.filter(is_active=True),
        'levels': TeamAppointment.Level.choices,
    }
    return render(request, 'teams/list.html', ctx)


@login_required
def team_detail(request, pk):
    obj = get_object_or_404(_scoped(TeamAppointment.objects.select_related('term','board','person','position','portfolio','national_council','regional_council','local_council','jamatkhana').prefetch_related('covered_jamatkhanas'), request.user), pk=pk)
    history = TeamAppointment.objects.filter(person=obj.person).select_related('term','board','position','portfolio').order_by('-term__start_date')
    return render(request, 'teams/detail.html', {'appointment':obj,'history':history})


@login_required
def team_create(request):
    if not (request.user.is_superuser or request.user.has_perm('teams.add_teamappointment')):
        messages.error(request, 'You do not have permission to add team appointments.')
        return redirect('team_list')
    form = TeamAppointmentForm(request.POST or None)
    if form.is_valid():
        obj = form.save(commit=False); obj.created_by=request.user; obj.save(); form.save_m2m()
        messages.success(request, 'Team appointment added.')
        return redirect('team_detail', pk=obj.pk)
    return render(request,'teams/form.html',{'form':form,'title':'Add team appointment'})


@login_required
def team_edit(request, pk):
    obj = get_object_or_404(_scoped(TeamAppointment.objects.all(), request.user), pk=pk)
    if not (request.user.is_superuser or request.user.has_perm('teams.change_teamappointment')):
        messages.error(request, 'You do not have permission to edit team appointments.')
        return redirect('team_detail', pk=pk)
    form=TeamAppointmentForm(request.POST or None, instance=obj)
    if form.is_valid():
        form.save(); messages.success(request,'Team appointment updated.'); return redirect('team_detail',pk=pk)
    return render(request,'teams/form.html',{'form':form,'title':'Edit team appointment','appointment':obj})


def _export_rows(qs):
    for i,a in enumerate(qs,1):
        coverage=', '.join(str(x) for x in a.covered_jamatkhanas.all())
        yield [i,a.person.full_name,a.position.name,a.portfolio.name if a.portfolio else '',a.get_level_display(),str(a.jurisdiction_name or ''),coverage,a.person.mobile or a.person.whatsapp_number,a.person.email,a.term.name,'Active' if a.is_active else 'Inactive']


@login_required
def team_export(request, export_format):
    qs, filters = _filtered(request)
    rows=list(_export_rows(qs))
    stamp=timezone.localtime().strftime('%d %b %Y %H:%M')
    term=Term.objects.filter(pk=filters.get('term')).first()
    title=f'Teams & Contacts - {term.name if term else "All terms"}'
    headers=['S/N','Name','Position','Portfolio','Level','Jurisdiction','JK Coverage','Phone','Email','Term','Status']
    if export_format == 'xlsx':
        wb=Workbook(); ws=wb.active; ws.title='Teams & Contacts'; ws.append([title]); ws.append(['Generated',stamp]); ws.append([]); ws.append(headers)
        for row in rows: ws.append(row)
        for col in ws.columns:
            letter=col[0].column_letter; ws.column_dimensions[letter].width=min(max(12,max(len(str(c.value or '')) for c in col)+2),35)
        out=BytesIO(); wb.save(out)
        r=HttpResponse(out.getvalue(),content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'); r['Content-Disposition']='attachment; filename="teams_contacts.xlsx"'; return r
    if export_format == 'pdf':
        out=BytesIO()
        def footer(canvas,doc):
            canvas.saveState(); canvas.setFont('Helvetica',8); canvas.drawString(12*mm,8*mm,f'Generated: {stamp}'); canvas.drawRightString(285*mm,8*mm,f'Page {doc.page}'); canvas.restoreState()
        doc=SimpleDocTemplate(out,pagesize=landscape(A4),leftMargin=9*mm,rightMargin=9*mm,topMargin=10*mm,bottomMargin=14*mm)
        styles=getSampleStyleSheet(); data=[[Paragraph(f'<b>{h}</b>',styles['BodyText']) for h in headers]]+[[Paragraph(str(v or ''),styles['BodyText']) for v in row] for row in rows]
        table=Table(data,repeatRows=1,colWidths=[9*mm,33*mm,28*mm,29*mm,19*mm,31*mm,34*mm,26*mm,37*mm,22*mm,18*mm])
        table.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#eaf6f5')),('GRID',(0,0),(-1,-1),0.35,colors.HexColor('#cbd5e1')),('VALIGN',(0,0),(-1,-1),'TOP'),('FONTSIZE',(0,0),(-1,-1),7),('LEFTPADDING',(0,0),(-1,-1),3),('RIGHTPADDING',(0,0),(-1,-1),3)]))
        doc.build([Paragraph(title,styles['Title']),Spacer(1,4*mm),table],onFirstPage=footer,onLaterPages=footer)
        r=HttpResponse(out.getvalue(),content_type='application/pdf'); r['Content-Disposition']='attachment; filename="teams_contacts.pdf"'; return r
    if export_format == 'jpg':
        widths=[50,260,190,190,130,220,260,170,260,120,100]; width=sum(widths)+40; rowh=42; height=max(300,160+(len(rows)+1)*rowh+55)
        img=Image.new('RGB',(width,height),'white'); d=ImageDraw.Draw(img); font=ImageFont.load_default(); d.text((20,20),title,fill='black',font=font); d.text((20,42),f'Generated: {stamp}',fill='black',font=font)
        y=80; x=20
        for j,h in enumerate(headers): d.rectangle((x,y,x+widths[j],y+rowh),outline='gray'); d.text((x+4,y+14),h,fill='black',font=font); x+=widths[j]
        y+=rowh
        for row in rows:
            x=20
            for j,v in enumerate(row):
                d.rectangle((x,y,x+widths[j],y+rowh),outline='lightgray'); txt=str(v or ''); maxchars=max(5,widths[j]//7); d.text((x+4,y+14),txt[:maxchars],fill='black',font=font); x+=widths[j]
            y+=rowh
        d.text((20,height-25),f'Generated: {stamp}',fill='black',font=font); d.text((width-90,height-25),'Page 1',fill='black',font=font)
        out=BytesIO(); img.save(out,'JPEG',quality=90)
        r=HttpResponse(out.getvalue(),content_type='image/jpeg'); r['Content-Disposition']='attachment; filename="teams_contacts.jpg"'; return r
    return HttpResponse('Unsupported format',status=400)


@login_required
def term_list(request):
    if not request.user.is_superuser:
        return redirect('team_list')
    return render(request,'teams/terms.html',{'terms':Term.objects.all()})

@login_required
def team_settings(request):
    if not request.user.is_superuser:
        return redirect('team_list')
    from .forms import TermForm, TeamPositionForm, PortfolioForm
    kind=request.GET.get('kind','term')
    forms={'term':TermForm,'position':TeamPositionForm,'portfolio':PortfolioForm}
    models={'term':Term,'position':TeamPosition,'portfolio':Portfolio}
    Form=forms.get(kind,TermForm); Model=models.get(kind,Term)
    instance=None
    edit=request.GET.get('edit')
    if edit: instance=get_object_or_404(Model,pk=edit)
    form=Form(request.POST or None,instance=instance)
    if request.method=='POST' and form.is_valid():
        form.save(); messages.success(request,'Team setting saved.'); return redirect(f"{reverse('team_settings')}?kind={kind}")
    return render(request,'teams/settings.html',{'kind':kind,'form':form,'items':Model.objects.all()})
