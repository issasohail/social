from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [('family_harmony', '0006_marriage_profile_form_fields')]
    operations = [
        migrations.AddField(model_name='familyharmonyprofile', name='weight_kg', field=models.DecimalField(blank=True, decimal_places=1, max_digits=5, null=True)),
        migrations.AddField(model_name='familyharmonyprofile', name='physical_status', field=models.CharField(blank=True, max_length=100)),
        migrations.AddField(model_name='familyharmonyprofile', name='disability_status', field=models.CharField(blank=True, max_length=120)),
        migrations.AddField(model_name='familyharmonyprofile', name='known_diseases', field=models.JSONField(blank=True, default=list)),
        migrations.AddField(model_name='familyharmonyprofile', name='owns_house', field=models.BooleanField(blank=True, null=True)),
        migrations.AddField(model_name='familyharmonyprofile', name='owns_car', field=models.BooleanField(blank=True, null=True)),
    ]
