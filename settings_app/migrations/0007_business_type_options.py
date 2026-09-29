from django.db import migrations, models

def seed(apps, schema_editor):
    Settings = apps.get_model("settings_app", "FamilyHarmonySettings")
    obj, _ = Settings.objects.get_or_create(pk=1)
    if not obj.business_type_options:
        obj.business_type_options = ["Salaried / Employment", "Self-employed", "Sole Proprietorship", "Partnership", "Private Limited Company", "Family Business", "Professional Practice", "Freelance / Consultancy", "Not applicable", "Other"]
        obj.save(update_fields=["business_type_options"])

class Migration(migrations.Migration):
    dependencies=[("settings_app","0006_family_profile_lists")]
    operations=[migrations.AddField(model_name="familyharmonysettings", name="business_type_options", field=models.JSONField(blank=True, default=list)), migrations.RunPython(seed, migrations.RunPython.noop)]
