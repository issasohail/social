from django.db import migrations


IVS_OCCUPATIONS = [
    'Salaried',
    'Self Employed',
    'Retired',
    'Homemaker',
    'Student',
    'Unemployed',
]


def seed_ivs_settings(apps, schema_editor):
    Settings = apps.get_model('settings_app', 'FamilyHarmonySettings')
    settings, _ = Settings.objects.get_or_create(pk=1)
    settings.title_options = ['Mr', 'Mrs', 'Miss', 'Ms', 'Dr', 'Prof', 'Other']
    settings.education_levels = ['Metric', 'O Level', 'Bachelor', 'Master', 'PhD', 'Other']
    settings.occupation_options = IVS_OCCUPATIONS
    settings.employer_options = ['Government', 'Private company', 'Own business', 'NGO', 'Self-employed', 'Not applicable', 'Other']
    settings.income_ranges = ['No income', 'Below 50,000', '50,000 - 100,000', '100,000 - 200,000', '200,000 - 500,000', 'Above 500,000', 'Other']
    settings.portfolio_options = ['Family Harmony', 'Seniors', 'Portfolio 3', 'Portfolio 4', 'Portfolio 5', 'Portfolio 6']
    settings.save(update_fields=[
        'title_options',
        'education_levels',
        'occupation_options',
        'employer_options',
        'income_ranges',
        'portfolio_options',
    ])


def unseed_ivs_settings(apps, schema_editor):
    Settings = apps.get_model('settings_app', 'FamilyHarmonySettings')
    Settings.objects.filter(pk=1).update(
        title_options=[],
        education_levels=[],
        occupation_options=[],
        employer_options=[],
        income_ranges=[],
        portfolio_options=[],
    )


class Migration(migrations.Migration):
    dependencies = [
        ('settings_app', '0004_familyharmonysettings_portfolio_options'),
    ]

    operations = [
        migrations.RunPython(seed_ivs_settings, unseed_ivs_settings),
    ]
