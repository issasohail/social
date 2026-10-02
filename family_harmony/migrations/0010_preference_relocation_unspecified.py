from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('family_harmony', '0009_seed_complete_demo_profiles')]

    operations = [
        migrations.AlterField(
            model_name='familyharmonypreference',
            name='willingness_to_relocate',
            field=models.BooleanField(blank=True, default=None, null=True),
        ),
    ]
