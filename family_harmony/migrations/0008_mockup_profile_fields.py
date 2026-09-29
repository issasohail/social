from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("family_harmony", "0007_profile_health_assets")]

    operations = [
        migrations.AddField(model_name="familyharmonyprofile", name="brothers_count", field=models.PositiveSmallIntegerField(blank=True, null=True)),
        migrations.AddField(model_name="familyharmonyprofile", name="sisters_count", field=models.PositiveSmallIntegerField(blank=True, null=True)),
        migrations.AddField(model_name="familyharmonypreference", name="preferred_family_type", field=models.CharField(blank=True, max_length=80)),
        migrations.AddField(model_name="familyharmonypreference", name="preferred_caste_tribe", field=models.CharField(blank=True, max_length=120)),
        migrations.AddField(model_name="familyharmonypreference", name="preferred_country", field=models.CharField(blank=True, max_length=120)),
    ]
