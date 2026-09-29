from django.db import migrations


CASTE_TRIBE_OPTIONS = ['Khoja', 'Momin', 'Gilgit', 'Hunza', 'Ghizar', 'Punal', 'Gojali', 'Other']


def seed_caste_tribes(apps, schema_editor):
    Settings = apps.get_model('settings_app', 'FamilyHarmonySettings')
    settings, _ = Settings.objects.get_or_create(pk=1)
    if not settings.caste_tribe_options or settings.caste_tribe_options == ['Other']:
        settings.caste_tribe_options = CASTE_TRIBE_OPTIONS
        settings.save(update_fields=['caste_tribe_options'])


class Migration(migrations.Migration):
    dependencies = [('settings_app', '0009_health_profile_lists')]
    operations = [migrations.RunPython(seed_caste_tribes, migrations.RunPython.noop)]
