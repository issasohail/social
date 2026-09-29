from django.db import migrations, models


def seed(apps, schema_editor):
    Settings = apps.get_model("settings_app", "FamilyHarmonySettings")
    obj, _ = Settings.objects.get_or_create(pk=1)
    obj.default_expiry_days = 7
    obj.family_type_options = ["Nuclear", "Joint", "Extended"]
    obj.language_options = ["English", "Urdu", "Gujarati", "Sindhi", "Punjabi", "Pashto", "Burushaski", "Shina", "Khowar", "Other"]
    obj.marital_status_options = ["Never married", "Divorced", "Widowed", "Separated", "Other"]
    obj.relationship_options = ["Father", "Mother", "Brother", "Sister", "Son", "Daughter", "Guardian", "Other"]
    obj.education_levels = ["Matric / SSC", "O Level", "Intermediate / HSSC", "A Level", "Diploma", "Bachelor", "Master", "MPhil", "PhD", "Professional qualification", "Other"]
    obj.occupation_options = ["Salaried", "Self Employed", "Business Owner", "Government Employee", "Private Employee", "Doctor", "Engineer", "Teacher / Education", "IT / Technology", "Finance / Banking", "Lawyer", "Student", "Homemaker", "Retired", "Unemployed", "Other"]
    obj.income_ranges = ["No income", "Below PKR 50,000", "PKR 50,000 - 100,000", "PKR 100,001 - 200,000", "PKR 200,001 - 300,000", "PKR 300,001 - 500,000", "PKR 500,001 - 1,000,000", "Above PKR 1,000,000", "Prefer not to say"]
    obj.save()

class Migration(migrations.Migration):
    dependencies=[("settings_app","0005_seed_ivs_settings")]
    operations=[
        migrations.AddField(model_name="familyharmonysettings", name="family_type_options", field=models.JSONField(blank=True, default=list)),
        migrations.AddField(model_name="familyharmonysettings", name="language_options", field=models.JSONField(blank=True, default=list)),
        migrations.AddField(model_name="familyharmonysettings", name="marital_status_options", field=models.JSONField(blank=True, default=list)),
        migrations.AddField(model_name="familyharmonysettings", name="relationship_options", field=models.JSONField(blank=True, default=list)),
        migrations.RunPython(seed, migrations.RunPython.noop),
    ]
