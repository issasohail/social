from django.db import migrations

LOCALS = [
 ("CRC-RWP", "Ismaili Local Council for Rawalpindi"),
 ("CRC-ISB", "Ismaili Local Council for Islamabad"),
 ("CRC-LHE", "Ismaili Local Council for Lahore"),
 ("CRC-HFD", "Ismaili Local Council for Hafizabad"),
 ("CRC-PEW", "Ismaili Local Council for Peshawar"),
 ("CRC-MDN", "Ismaili Local Council for Mardan Areas"),
]

def seed(apps, schema_editor):
    National=apps.get_model("organization","NationalCouncil"); Regional=apps.get_model("organization","RegionalCouncil")
    Local=apps.get_model("organization","LocalCouncil"); JK=apps.get_model("organization","Jamatkhana")
    national,_=National.objects.update_or_create(code="PK", defaults={"name":"National Council of Pakistan","is_active":True})
    central,_=Regional.objects.update_or_create(code="CENTRAL", defaults={"name":"Central Regional Council","national_council":national,"is_active":True})
    for lc_code, lc_name in LOCALS:
        lc,_=Local.objects.update_or_create(code=lc_code, defaults={"name":lc_name,"regional_council":central,"is_active":True})
        short=lc_code.split("-")[-1]
        for n in range(1,5):
            code=f"{lc_code}-JK{n:02d}"
            city = lc_name.replace("Ismaili Local Council for ", "")
            name=f"{city} Jamatkhana {n:02d}"
            JK.objects.update_or_create(code=code, defaults={"name":name,"short_name":f"{city} JK {n:02d}","local_council":lc,"is_active":True})

class Migration(migrations.Migration):
    dependencies=[("organization","0003_remove_non_ivs_jamatkhanas")]
    operations=[migrations.RunPython(seed, migrations.RunPython.noop)]
