import django.db.models.deletion
from django.db import migrations, models


def link_profiles_to_people(apps, schema_editor):
    UserProfile = apps.get_model('accounts', 'UserProfile')
    Person = apps.get_model('people', 'Person')

    for profile in UserProfile.objects.select_related('user').filter(person__isnull=True):
        email = (profile.user.email or '').strip()
        if not email:
            continue
        matches = Person.objects.filter(email__iexact=email, is_active=True)
        if matches.count() == 1:
            person = matches.first()
            if not UserProfile.objects.filter(person_id=person.pk).exclude(pk=profile.pk).exists():
                profile.person_id = person.pk
                if not profile.phone_number:
                    profile.phone_number = person.whatsapp_number or person.mobile or ''
                profile.save(update_fields=['person', 'phone_number'])


class Migration(migrations.Migration):
    dependencies = [
        ('accounts', '0001_initial'),
        ('people', '0004_person_willing_to_relocate_unspecified'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='person',
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='staff_profile', to='people.person'),
        ),
        migrations.RunPython(link_profiles_to_people, migrations.RunPython.noop),
    ]
