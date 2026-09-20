from django.db import migrations


NATIONAL_CODE = 'PK'

REGIONAL_COUNCILS = [
    ('RC01', 'North East'),
    ('north', 'Northern'),
    ('south', 'Southern'),
    ('CE', 'Central Council'),
]

LOCAL_COUNCILS = [
    ('05', 'Rawalpindi', 'CE'),
    ('peshawar', 'Peshawar', 'CE'),
    ('lahore', 'Lahore', 'CE'),
    ('002', 'Sargodha', 'CE'),
    ('lcnorth1', 'lc north 1', 'north'),
    ('lcnorth02', 'lcNorth02', 'north'),
]

JAMATKHANAS = [
    ('CE0509', 'Golden Jubilee (GJ)', 'CE0509', '05'),
    ('CE0505', 'Karimabad', 'CE0505', '05'),
    ('CE0507', 'Rawalpindi', 'CE0507', '05'),
    ('CE0501', 'Abbotabad', 'CE0501', '05'),
    ('CE0514', 'Ali Muhammad Society', 'CE0514', '05'),
    ('CE0506', 'Muzafferabad', 'CE0506', '05'),
    ('CE0502', 'Attock', 'CE0502', '05'),
    ('CE0515', 'Chitral Town', 'CE0515', '05'),
    ('CE0516', 'Golden Model Town', 'CE0516', '05'),
    ('CE0513', 'Gulshan E Fatima', 'CE0513', '05'),
    ('CE0504', 'Islamabad', 'CE0504', '05'),
    ('CE0510', 'Prince Villa Society', 'CE0510', '05'),
    ('CE0508', 'Taxila', 'CE0508', '05'),
    ('CE0503', 'Bhurban', 'CE0503', '05'),
]


def seed_ivs_hierarchy(apps, schema_editor):
    NationalCouncil = apps.get_model('organization', 'NationalCouncil')
    RegionalCouncil = apps.get_model('organization', 'RegionalCouncil')
    LocalCouncil = apps.get_model('organization', 'LocalCouncil')
    Jamatkhana = apps.get_model('organization', 'Jamatkhana')

    national, _ = NationalCouncil.objects.update_or_create(
        code=NATIONAL_CODE,
        defaults={'name': 'Pakistan', 'is_active': True},
    )
    regions = {}
    for code, name in REGIONAL_COUNCILS:
        region, _ = RegionalCouncil.objects.update_or_create(
            code=code,
            defaults={
                'name': name,
                'national_council': national,
                'is_active': True,
            },
        )
        regions[code] = region

    locals_by_code = {}
    for code, name, regional_code in LOCAL_COUNCILS:
        local, _ = LocalCouncil.objects.update_or_create(
            code=code,
            defaults={
                'name': name,
                'regional_council': regions[regional_code],
                'is_active': True,
            },
        )
        locals_by_code[code] = local

    for code, name, short_name, local_code in JAMATKHANAS:
        Jamatkhana.objects.update_or_create(
            code=code,
            defaults={
                'name': name,
                'short_name': short_name,
                'local_council': locals_by_code[local_code],
                'is_active': True,
            },
        )


def unseed_ivs_hierarchy(apps, schema_editor):
    NationalCouncil = apps.get_model('organization', 'NationalCouncil')
    RegionalCouncil = apps.get_model('organization', 'RegionalCouncil')
    LocalCouncil = apps.get_model('organization', 'LocalCouncil')
    Jamatkhana = apps.get_model('organization', 'Jamatkhana')

    Jamatkhana.objects.filter(code__in=[row[0] for row in JAMATKHANAS]).delete()
    LocalCouncil.objects.filter(code__in=[row[0] for row in LOCAL_COUNCILS]).delete()
    RegionalCouncil.objects.filter(code__in=[row[0] for row in REGIONAL_COUNCILS]).delete()
    NationalCouncil.objects.filter(code=NATIONAL_CODE).delete()


class Migration(migrations.Migration):
    dependencies = [
        ('organization', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(seed_ivs_hierarchy, unseed_ivs_hierarchy),
    ]
