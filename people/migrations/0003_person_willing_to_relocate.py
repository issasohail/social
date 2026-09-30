from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('people', '0002_person_cnic_images')]

    operations = [
        migrations.AddField(
            model_name='person',
            name='willing_to_relocate',
            field=models.BooleanField(default=False),
        ),
    ]
