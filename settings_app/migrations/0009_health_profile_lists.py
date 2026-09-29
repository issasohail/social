from django.db import migrations, models

def seed(apps, schema_editor):
    Settings = apps.get_model('settings_app', 'FamilyHarmonySettings')
    obj, _ = Settings.objects.get_or_create(pk=1)
    if not obj.physical_status_options:
        obj.physical_status_options = ['Healthy / Fit', 'Average', 'Underweight', 'Overweight', 'Other']
    if not obj.disability_options:
        obj.disability_options = ['None', 'Physical', 'Visual', 'Hearing', 'Speech', 'Intellectual / Developmental', 'Multiple', 'Other']
    if not obj.known_disease_options:
        obj.known_disease_options = ['Diabetes', 'High cholesterol', 'Thyroid disorder', 'High blood pressure', 'Heart condition', 'Asthma', 'Other']
    obj.save(update_fields=['physical_status_options','disability_options','known_disease_options'])

class Migration(migrations.Migration):
    dependencies = [('settings_app', '0008_profile_entry_lists')]
    operations = [
        migrations.AddField(model_name='familyharmonysettings', name='physical_status_options', field=models.JSONField(blank=True, default=list)),
        migrations.AddField(model_name='familyharmonysettings', name='disability_options', field=models.JSONField(blank=True, default=list)),
        migrations.AddField(model_name='familyharmonysettings', name='known_disease_options', field=models.JSONField(blank=True, default=list)),
        migrations.RunPython(seed, migrations.RunPython.noop),
    ]
