from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies=[("family_harmony","0005_familyharmonyprofile_portfolio")]
    operations=[
        migrations.AddField(model_name="familyharmonyprofile", name="father_name", field=models.CharField(blank=True,max_length=180)),
        migrations.AddField(model_name="familyharmonyprofile", name="father_occupation", field=models.CharField(blank=True,max_length=180)),
        migrations.AddField(model_name="familyharmonyprofile", name="mother_name", field=models.CharField(blank=True,max_length=180)),
        migrations.AddField(model_name="familyharmonyprofile", name="mother_occupation", field=models.CharField(blank=True,max_length=180)),
        migrations.AddField(model_name="familyharmonyprofile", name="siblings_summary", field=models.CharField(blank=True,max_length=255)),
        migrations.AddField(model_name="familyharmonyprofile", name="family_residence", field=models.CharField(blank=True,max_length=180)),
        migrations.AddField(model_name="familyharmonyprofile", name="family_type", field=models.CharField(blank=True,max_length=80)),
        migrations.AddField(model_name="familyharmonyprofile", name="caste_tribe", field=models.CharField(blank=True,max_length=120)),
        migrations.AddField(model_name="familyharmonyprofile", name="guardian_contact", field=models.CharField(blank=True,max_length=180)),
        migrations.AddField(model_name="familyharmonypreference", name="preferred_education_options", field=models.JSONField(blank=True,default=list)),
        migrations.AddField(model_name="familyharmonypreference", name="preferred_income_options", field=models.JSONField(blank=True,default=list)),
        migrations.AddField(model_name="familyharmonypreference", name="preferred_marital_status_options", field=models.JSONField(blank=True,default=list)),
    ]
