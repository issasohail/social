from urllib.parse import quote
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import logout
from django.http import FileResponse, Http404, JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST
from .forms_tools import BackupSettingsForm, BackupUploadForm, BackupRestoreForm, SuggestionTicketForm, SuggestionReplyForm
from .backup_utils import *
from .suggestion_store import create_ticket, get_ticket, list_tickets, delete_ticket, update_status, add_reply, STATUS_CHOICES, TYPE_CHOICES

superuser_required=user_passes_test(lambda u:u.is_superuser)

@login_required
@superuser_required
def backup_center(request):
    config=load_backup_settings()
    backups=list_backups(config)
    for i,b in enumerate(backups,1): b.serial_number=i
    protected=protected_backup_ids(backups,retention_count(config))
    for b in backups: b.is_protected=b.id in protected
    restore_choices=[('', '----------')]+[(b.id,f'S.N {b.serial_number} · {b.get_backup_type_display()} · {b.name} ({b.created_at:%Y-%m-%d %H:%M})') for b in backups if b.file_exists and b.backup_type in {'db','media','full'}]
    selected=request.GET.get('selected_backup')
    def context(settings_form=None):
        return {'backup_settings_form':settings_form or BackupSettingsForm(initial=config),'backup_upload_form':BackupUploadForm(),'restore_form':BackupRestoreForm(backup_choices=restore_choices,initial={'backup_id':selected}),'backups':backups,'backup_storage':backup_storage_summary(config),'backup_help_modals':[]}
    if request.method=='GET': return render(request,'settings_app/backup_center.html',context())
    action=request.POST.get('action')
    try:
        if action=='save_backup_settings':
            form=BackupSettingsForm(request.POST)
            if form.is_valid(): save_backup_settings(form.cleaned_data); messages.success(request,'Backup settings saved.'); return redirect('backup_center')
            return render(request,'settings_app/backup_center.html',context(form))
        if action=='upload_backup':
            form=BackupUploadForm(request.POST,request.FILES)
            if form.is_valid():
                typ=detect_uploaded_backup_type(form.cleaned_data['backup_file']); uploaded=save_uploaded_backup(config,typ,form.cleaned_data['backup_file']); messages.success(request,f'{typ.title()} backup detected and uploaded: {uploaded.name}'); return redirect(f"{reverse('backup_center')}?selected_backup={quote(uploaded.name,safe='')}#restore-backup")
            messages.error(request,'Upload failed. Choose a valid backup file.'); return redirect('backup_center')
        if action=='backup_db': created=create_db_backup(config); prune_old_backups(config); messages.success(request,f'Database backup created: {created.name}')
        elif action=='backup_media': created=create_media_backup(config); prune_old_backups(config); messages.success(request,f'Media backup created: {created.name}')
        elif action=='backup_code': created=create_code_backup(config); prune_old_backups(config); messages.success(request,f'Code backup created: {created.name}')
        elif action=='backup_full': created=create_full_backup(config); prune_old_backups(config); messages.success(request,f'Full backup created: {created.name}')
        elif action=='purge_old_backups':
            if request.POST.get('confirm_text')!='PURGE': messages.error(request,'Backup purge was not confirmed.')
            else:
                result=purge_old_backups(config); messages.success(request,f"Purged {len(result['deleted'])} old backup file(s). Reclaimed {result['reclaimed_bytes']/(1024*1024):.2f} MB.")
        elif action=='restore_smart':
            form=BackupRestoreForm(request.POST,backup_choices=restore_choices)
            if not form.is_valid() or form.cleaned_data.get('confirm_text')!='RESTORE': messages.error(request,'Restore confirmation failed.')
            else:
                backup=next((b for b in backups if b.id==form.cleaned_data['backup_id']),None)
                if not backup: raise RuntimeError('Selected backup was not found.')
                if backup.backup_type=='db': safety=create_db_backup({**config,'enable_db_backup':True}); restore_database(config,backup.id)
                elif backup.backup_type=='media': safety=create_media_backup({**config,'enable_media_backup':True}); restore_media(config,backup.id)
                elif backup.backup_type=='full': safety=create_full_backup({**config,'enable_full_backup':True}); restore_full(config,backup.id)
                else: raise RuntimeError('Code-only backups cannot be restored from Smart Restore.')
                logout(request); messages.success(request,f'{backup.get_backup_type_display()} restore completed. Safety backup: {safety.name}. Please log in again.'); return redirect('login')
        elif action=='fresh_reset': messages.error(request,'Fresh reset is intentionally disabled for Social Welfare.')
        else: messages.error(request,'Unknown backup action.')
    except Exception as exc: messages.error(request,f'Backup operation failed: {exc}')
    return redirect('backup_center')

@login_required
@superuser_required
def backup_download(request,backup_id):
    config=load_backup_settings(); item=next((x for x in list_backups(config) if x.id==backup_id and x.file_exists),None)
    if not item: raise Http404
    return FileResponse(open(item.display_path,'rb'),as_attachment=True,filename=backup_id)

@login_required
@superuser_required
@require_POST
def backup_delete(request,backup_id):
    try:
        delete_backup(load_backup_settings(),backup_id)
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest': return JsonResponse({'success': True})
        messages.success(request,'Backup deleted.'); return redirect('backup_center')
    except Exception as exc:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest': return JsonResponse({'success': False, 'error': str(exc)}, status=400)
        messages.error(request,str(exc)); return redirect('backup_center')

@login_required
def suggestion_list(request):
    status=request.GET.get('status','PENDING'); typ=request.GET.get('type','')
    return render(request,'settings_app/suggestions/list.html',{'tickets':list_tickets(status=status or None,ticket_type=typ or None),'status_choices':STATUS_CHOICES,'type_choices':TYPE_CHOICES,'selected_status':status,'selected_type':typ})

@login_required
def suggestion_create(request):
    form=SuggestionTicketForm(request.POST or None)
    if request.method=='POST' and form.is_valid():
        ticket=create_ticket(form.cleaned_data,request.user,request.FILES.getlist('photos')); messages.success(request,'Suggestion saved.'); return redirect('suggestion_detail',pk=ticket.id)
    return render(request,'settings_app/suggestions/form.html',{'form':form})

@login_required
def suggestion_detail(request,pk):
    ticket=get_ticket(pk)
    if not ticket: raise Http404
    if request.method == 'POST':
        form=SuggestionReplyForm(request.POST)
        selected_status=request.POST.get('status') if (request.user.is_staff or request.user.is_superuser) else None
        if form.is_valid():
            message=(form.cleaned_data.get('message') or '').strip(); photos=request.FILES.getlist('photos')
            if message or photos or selected_status:
                add_reply(ticket.id,message,request.user,status=selected_status,files=photos); messages.success(request,'Reply saved.'); return redirect('suggestion_detail',pk=ticket.id)
            messages.error(request,'Reply, image, or status change is required.')
    else: form=SuggestionReplyForm()
    ticket=get_ticket(pk)
    return render(request,'settings_app/suggestions/detail.html',{'ticket':ticket,'form':form,'status_choices':STATUS_CHOICES})

@login_required
@require_POST
def suggestion_status_update(request,pk):
    if not (request.user.is_staff or request.user.is_superuser):
        return JsonResponse({'ok':False,'error':'Not allowed'},status=403)
    new_status=request.POST.get('status')
    if new_status not in dict(STATUS_CHOICES): return JsonResponse({'ok':False,'error':'Invalid status'},status=400)
    ticket=update_status(pk,new_status)
    return JsonResponse({'ok':bool(ticket),'status':new_status},status=200 if ticket else 404)

@login_required
@require_POST
def suggestion_delete(request,pk):
    ticket=get_ticket(pk)
    if not ticket: return JsonResponse({'success':False,'error':'Suggestion not found.'},status=404)
    if not (request.user.is_staff or request.user.is_superuser or ticket.user_name_snapshot==request.user.get_username()): return JsonResponse({'success':False,'error':'Permission denied.'},status=403)
    if not delete_ticket(pk): return JsonResponse({'success':False,'error':'Suggestion not found.'},status=404)
    return JsonResponse({'success':True})
