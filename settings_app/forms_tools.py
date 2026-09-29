from django import forms

class BackupSettingsForm(forms.Form):
    backup_root=forms.CharField(label='Backup Root Folder')
    retention_count=forms.IntegerField(min_value=1,max_value=200)
    mysqldump_path=forms.CharField(required=False)
    mysql_path=forms.CharField(required=False)
    include_db_in_full=forms.BooleanField(required=False)
    include_media_in_full=forms.BooleanField(required=False)
    include_code_in_full=forms.BooleanField(required=False)
    compress_backups=forms.BooleanField(required=False)
    auto_delete_old_backups=forms.BooleanField(required=False)
    enable_db_backup=forms.BooleanField(required=False)
    enable_media_backup=forms.BooleanField(required=False)
    enable_code_backup=forms.BooleanField(required=False)
    enable_full_backup=forms.BooleanField(required=False)
    fresh_reset_enabled=forms.BooleanField(required=False)

class BackupUploadForm(forms.Form):
    backup_file=forms.FileField()
    def clean_backup_file(self):
        f=self.cleaned_data['backup_file']
        if not f.name.lower().endswith(('.sql','.sql.gz','.sqlite3','.zip')):
            raise forms.ValidationError('Use .sql, .sql.gz, .sqlite3 or .zip.')
        return f

class SuggestionTicketForm(forms.Form):
    ticket_type=forms.ChoiceField(choices=(('SUGGESTION','Suggestion'),('ERROR','Report Error')))
    screen_name=forms.CharField(required=False)
    title=forms.CharField(max_length=160)
    description=forms.CharField(required=False,widget=forms.Textarea(attrs={'rows':5}))
    priority=forms.ChoiceField(choices=(('LOW','Low'),('NORMAL','Normal'),('HIGH','High'),('URGENT','Urgent')),initial='NORMAL')

class SuggestionReplyForm(forms.Form):
    message=forms.CharField(required=False, widget=forms.Textarea(attrs={'rows':3, 'placeholder':'Add a reply or update'}))

class BackupRestoreForm(forms.Form):
    backup_id=forms.ChoiceField(choices=())
    confirm_text=forms.CharField(required=False)
    def __init__(self,*args,backup_choices=None,**kwargs):
        super().__init__(*args,**kwargs); self.fields['backup_id'].choices=backup_choices or [('', '----------')]
