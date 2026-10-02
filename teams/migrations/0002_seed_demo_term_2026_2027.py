from datetime import date

from django.db import migrations


TERM_NAME = '2026-2027'
DEMO_NOTE = 'Seeded demo team appointment for term 2026-2027.'


def seed_demo_team(apps, schema_editor):
    Term = apps.get_model('teams', 'Term')
    TeamPosition = apps.get_model('teams', 'TeamPosition')
    Portfolio = apps.get_model('teams', 'Portfolio')
    TeamAppointment = apps.get_model('teams', 'TeamAppointment')
    Board = apps.get_model('boards', 'Board')
    Person = apps.get_model('people', 'Person')
    NationalCouncil = apps.get_model('organization', 'NationalCouncil')
    RegionalCouncil = apps.get_model('organization', 'RegionalCouncil')
    LocalCouncil = apps.get_model('organization', 'LocalCouncil')
    Jamatkhana = apps.get_model('organization', 'Jamatkhana')

    # Make 2026-2027 the active/current demo term requested for testing.
    Term.objects.filter(is_current=True).exclude(name=TERM_NAME).update(is_current=False)
    term, _ = Term.objects.update_or_create(
        name=TERM_NAME,
        defaults={
            'start_date': date(2026, 7, 1),
            'end_date': date(2027, 6, 30),
            'is_current': True,
            'is_active': True,
            'notes': 'Demo/current term seeded for Teams & Contacts testing.',
            'sort_order': 10,
        },
    )

    board, _ = Board.objects.update_or_create(
        code='SWB',
        defaults={
            'name': 'National Social Welfare Board',
            'short_name': 'Social Welfare Board',
            'description': 'Social Welfare Board used for term-based team appointments.',
            'icon': 'people',
            'sort_order': 10,
            'is_active': True,
        },
    )

    # Prefer the canonical hierarchy seeded by organization.0004, while retaining
    # sensible fallbacks if the names/codes were edited before this migration runs.
    national = NationalCouncil.objects.filter(code='PK').first() or NationalCouncil.objects.filter(is_active=True).first()
    regional = RegionalCouncil.objects.filter(code='CENTRAL').first() or RegionalCouncil.objects.filter(is_active=True).first()
    local = LocalCouncil.objects.filter(code='CRC-RWP').first()
    if not local and regional:
        local = LocalCouncil.objects.filter(regional_council=regional, is_active=True).first()
    if not local:
        local = LocalCouncil.objects.filter(is_active=True).first()
    jk = Jamatkhana.objects.filter(code='CRC-RWP-JK01').first()
    if not jk and local:
        jk = Jamatkhana.objects.filter(local_council=local, is_active=True).first()
    if not jk:
        jk = Jamatkhana.objects.filter(is_active=True).first()

    # If hierarchy data has somehow been removed, avoid failing the whole migration.
    if not all([national, regional, local, jk]):
        return

    chairman = TeamPosition.objects.get(name='Chairman')
    secretary = TeamPosition.objects.get(name='Honorary Secretary')
    member = TeamPosition.objects.get(name='Member')
    lead = TeamPosition.objects.get(name='Portfolio Lead')
    helper = TeamPosition.objects.get(name='Helper')
    family_harmony = Portfolio.objects.get(name='Family Harmony')
    seniors = Portfolio.objects.get(name='Seniors')
    health = Portfolio.objects.get(name='Health')

    # One Person record is the single source of truth. These are clearly marked
    # demo records and can later be edited/replaced from the People module.
    people_seed = [
        ('Aamir', 'Khan', 'Male', '03001110001', 'aamir.team.demo@example.com'),
        ('Farah', 'Ali', 'Female', '03001110002', 'farah.team.demo@example.com'),
        ('Salim', 'Jaffer', 'Male', '03001110003', 'salim.team.demo@example.com'),
        ('Nadia', 'Karim', 'Female', '03001110004', 'nadia.team.demo@example.com'),
        ('Imran', 'Merchant', 'Male', '03001110005', 'imran.team.demo@example.com'),
        ('Shazia', 'Lakhani', 'Female', '03001110006', 'shazia.team.demo@example.com'),
        ('Yasir', 'Momin', 'Male', '03001110007', 'yasir.team.demo@example.com'),
        ('Rubina', 'Rupani', 'Female', '03001110008', 'rubina.team.demo@example.com'),
        ('Adil', 'Pirani', 'Male', '03001110009', 'adil.team.demo@example.com'),
        ('Saira', 'Virani', 'Female', '03001110010', 'saira.team.demo@example.com'),
        ('Noman', 'Khimani', 'Male', '03001110011', 'noman.team.demo@example.com'),
        ('Mariam', 'Nathani', 'Female', '03001110012', 'mariam.team.demo@example.com'),
    ]

    people = []
    for first_name, last_name, gender, mobile, email in people_seed:
        person, _ = Person.objects.update_or_create(
            email=email,
            defaults={
                'first_name': first_name,
                'middle_name': '',
                'last_name': last_name,
                'full_name': f'{first_name} {last_name}',
                'gender': gender,
                'nationality': 'Pakistani',
                'mobile': mobile,
                'whatsapp_number': mobile,
                'city': 'Rawalpindi',
                'province': 'Punjab',
                'country': 'Pakistan',
                'region': regional,
                'local_council': local,
                'jamatkhana': jk,
                'is_active': True,
                'is_demo': True,
            },
        )
        people.append(person)

    # Appointment matrix gives visible test data at every jurisdiction level.
    # portfolio=None means a board leadership post; portfolio posts demonstrate
    # the portfolio/lead/helper relationship as well.
    appointments = [
        # National Social Welfare Board
        (people[0], chairman, None, 'NATIONAL'),
        (people[1], secretary, None, 'NATIONAL'),
        (people[2], lead, family_harmony, 'NATIONAL'),
        # Regional Social Welfare Board
        (people[3], chairman, None, 'REGIONAL'),
        (people[4], lead, seniors, 'REGIONAL'),
        (people[5], member, family_harmony, 'REGIONAL'),
        # Local Council Social Welfare Board
        (people[6], chairman, None, 'LOCAL'),
        (people[7], lead, family_harmony, 'LOCAL'),
        (people[8], member, health, 'LOCAL'),
        # Jamatkhana Social Welfare team
        (people[9], lead, family_harmony, 'JK'),
        (people[10], member, family_harmony, 'JK'),
        (people[11], helper, family_harmony, 'JK'),
    ]

    for person, position, portfolio, level in appointments:
        defaults = {
            'portfolio': portfolio,
            'appointment_date': term.start_date,
            'end_date': term.end_date,
            'is_active': True,
            'notes': DEMO_NOTE,
            'national_council': national,
            'regional_council': regional if level in ('REGIONAL', 'LOCAL', 'JK') else None,
            'local_council': local if level in ('LOCAL', 'JK') else None,
            'jamatkhana': jk if level == 'JK' else None,
        }
        appointment, _ = TeamAppointment.objects.update_or_create(
            term=term,
            board=board,
            person=person,
            position=position,
            level=level,
            defaults=defaults,
        )
        # Demonstrate multi-JK coverage for lead/helper roles at local/JK level.
        if level in ('LOCAL', 'JK') and position.name in ('Portfolio Lead', 'Helper'):
            covered = list(Jamatkhana.objects.filter(local_council=local, is_active=True).order_by('id')[:3])
            if covered:
                appointment.covered_jamatkhanas.set(covered)


def unseed_demo_team(apps, schema_editor):
    TeamAppointment = apps.get_model('teams', 'TeamAppointment')
    Person = apps.get_model('people', 'Person')

    # Remove only records explicitly created for this demo data migration.
    TeamAppointment.objects.filter(notes=DEMO_NOTE).delete()
    Person.objects.filter(is_demo=True, email__endswith='.team.demo@example.com').delete()


class Migration(migrations.Migration):
    dependencies = [
        ('teams', '0001_initial'),
        ('people', '0004_person_willing_to_relocate_unspecified'),
    ]

    operations = [
        migrations.RunPython(seed_demo_team, unseed_demo_team),
    ]
