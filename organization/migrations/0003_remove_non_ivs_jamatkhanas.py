from django.db import migrations


IVS_JK_CODES = {
    'CE0501',
    'CE0502',
    'CE0503',
    'CE0504',
    'CE0505',
    'CE0506',
    'CE0507',
    'CE0508',
    'CE0509',
    'CE0510',
    'CE0513',
    'CE0514',
    'CE0515',
    'CE0516',
}


def remove_non_ivs_jamatkhanas(apps, schema_editor):
    Jamatkhana = apps.get_model('organization', 'Jamatkhana')
    Person = apps.get_model('people', 'Person')
    FamilyHarmonyProfile = apps.get_model('family_harmony', 'FamilyHarmonyProfile')
    PublicFormInvitation = apps.get_model('family_harmony', 'PublicFormInvitation')
    CrossJurisdictionRequest = apps.get_model('family_harmony', 'CrossJurisdictionRequest')
    Case = apps.get_model('cases', 'Case')
    UserJurisdictionAccess = apps.get_model('organization', 'UserJurisdictionAccess')

    obsolete_ids = list(
        Jamatkhana.objects.exclude(code__in=IVS_JK_CODES).values_list('id', flat=True)
    )
    if not obsolete_ids:
        return

    Person.objects.filter(jamatkhana_id__in=obsolete_ids).update(jamatkhana_id=None)
    FamilyHarmonyProfile.objects.filter(owning_jamatkhana_id__in=obsolete_ids).update(owning_jamatkhana_id=None)
    PublicFormInvitation.objects.filter(preselected_jamatkhana_id__in=obsolete_ids).update(preselected_jamatkhana_id=None)
    CrossJurisdictionRequest.objects.filter(requester_jk_id__in=obsolete_ids).update(requester_jk_id=None)
    CrossJurisdictionRequest.objects.filter(target_jk_id__in=obsolete_ids).update(target_jk_id=None)
    Case.objects.filter(jamatkhana_id__in=obsolete_ids).update(jamatkhana_id=None)
    UserJurisdictionAccess.objects.filter(jamatkhana_id__in=obsolete_ids).update(jamatkhana_id=None)
    Jamatkhana.objects.filter(id__in=obsolete_ids).delete()


def restore_is_not_supported(apps, schema_editor):
    # The removed records are demo data or records outside the IVS source set.
    # They cannot be reconstructed safely from this migration.
    pass


class Migration(migrations.Migration):
    dependencies = [
        ('organization', '0002_seed_ivs_hierarchy'),
        ('people', '0001_initial'),
        ('family_harmony', '0005_familyharmonyprofile_portfolio'),
        ('cases', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(remove_non_ivs_jamatkhanas, restore_is_not_supported),
    ]
