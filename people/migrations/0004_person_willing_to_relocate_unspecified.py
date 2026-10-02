from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('people', '0003_person_willing_to_relocate')]

    operations = [
        migrations.AlterField(
            model_name='person',
            name='willing_to_relocate',
            field=models.BooleanField(blank=True, default=None, null=True),
        ),
    ]
