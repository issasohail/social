from django.db import migrations, models


DEFAULT_VIEW_CAPABILITIES = ['people_view', 'harmony_view', 'teams_view']


def seed_existing_access(apps, schema_editor):
    Access = apps.get_model('organization', 'UserJurisdictionAccess')
    # Existing rows represented jurisdictional visibility, not delegated administration.
    # Preserve that safely as Viewer access; superusers keep unrestricted administration.
    Access.objects.filter(capabilities=[]).update(capabilities=DEFAULT_VIEW_CAPABILITIES)


class Migration(migrations.Migration):
    dependencies = [
        ('organization', '0004_seed_central_region_local_councils'),
    ]

    operations = [
        migrations.AddField(
            model_name='userjurisdictionaccess',
            name='role',
            field=models.CharField(choices=[('ADMIN', 'Admin'), ('MANAGER', 'Manager'), ('MEMBER', 'Member'), ('VIEWER', 'Viewer')], default='VIEWER', max_length=12),
        ),
        migrations.AddField(
            model_name='userjurisdictionaccess',
            name='capabilities',
            field=models.JSONField(blank=True, default=list),
        ),
        migrations.AlterField(
            model_name='userjurisdictionaccess',
            name='level',
            field=models.CharField(choices=[('NATIONAL', 'National'), ('REGIONAL', 'Regional'), ('LOCAL', 'Local Council'), ('JK', 'Jamatkhana')], max_length=12),
        ),
        migrations.RunPython(seed_existing_access, migrations.RunPython.noop),
    ]
