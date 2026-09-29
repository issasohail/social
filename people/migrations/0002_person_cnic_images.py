from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [('people', '0001_initial')]
    operations = [
        migrations.AddField(model_name='person', name='cnic_front', field=models.ImageField(blank=True, upload_to='people/cnic/%Y/%m/')),
        migrations.AddField(model_name='person', name='cnic_back', field=models.ImageField(blank=True, upload_to='people/cnic/%Y/%m/')),
    ]
