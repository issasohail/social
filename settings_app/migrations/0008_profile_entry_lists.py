from django.db import migrations, models


def seed(apps, schema_editor):
    S=apps.get_model("settings_app","FamilyHarmonySettings")
    obj,_=S.objects.get_or_create(pk=1)
    obj.caste_tribe_options=obj.caste_tribe_options or ["Other"]
    obj.nationality_options=obj.nationality_options or ["Pakistani","Other"]
    obj.country_options=obj.country_options or ["Pakistan","United States","United Kingdom","Canada","United Arab Emirates","Other"]
    obj.save(update_fields=["caste_tribe_options","nationality_options","country_options"])

class Migration(migrations.Migration):
    dependencies=[("settings_app","0007_business_type_options")]
    operations=[
      migrations.AddField(model_name="familyharmonysettings",name="caste_tribe_options",field=models.JSONField(blank=True,default=list)),
      migrations.AddField(model_name="familyharmonysettings",name="nationality_options",field=models.JSONField(blank=True,default=list)),
      migrations.AddField(model_name="familyharmonysettings",name="country_options",field=models.JSONField(blank=True,default=list)),
      migrations.RunPython(seed,migrations.RunPython.noop),
    ]
