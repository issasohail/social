from datetime import date

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from boards.models import Board
from family_harmony.models import FamilyHarmonyPreference, FamilyHarmonyProfile
from organization.models import Jamatkhana, LocalCouncil, NationalCouncil, RegionalCouncil
from people.models import Person


class Command(BaseCommand):
    help = 'Create fictional Social Welfare demo data.'

    def add_arguments(self, parser):
        parser.add_argument('--confirm', action='store_true')
        parser.add_argument('--jks-per-local', type=int, default=2)
        parser.add_argument('--profiles-per-jk', type=int, default=5)

    @transaction.atomic
    def handle(self, *args, **options):
        if not options['confirm']:
            raise CommandError('Pass --confirm to create demo data.')
        for name, code in [('Family Harmony', 'FAMILY_HARMONY'), ('Seniors', 'SENIORS'), ('Economic Support', 'ECONOMIC_SUPPORT'), ('Children', 'CHILDREN')]:
            Board.objects.get_or_create(code=code, defaults={'name': name})
        national = NationalCouncil.objects.create(name='Demo National Council', code='DEMO-NATIONAL')
        for region_no in range(1, 5):
            region = RegionalCouncil.objects.create(national_council=national, name=f'Demo Region {region_no}', code=f'DEMO-R{region_no}')
            for local_no in range(1, 4):
                local = LocalCouncil.objects.create(regional_council=region, name=f'Demo Local {region_no}-{local_no}', code=f'DEMO-R{region_no}-L{local_no}')
                for jk_no in range(1, options['jks_per_local'] + 1):
                    jk = Jamatkhana.objects.create(local_council=local, name=f'Demo JK {region_no}-{local_no}-{jk_no}', short_name=f'JK {region_no}-{local_no}-{jk_no}', code=f'DEMO-R{region_no}-L{local_no}-J{jk_no}')
                    for profile_no in range(1, options['profiles_per_jk'] + 1):
                        person = Person.objects.create(first_name=f'Demo', last_name=f'Candidate {region_no}{local_no}{jk_no}{profile_no}', gender='Female' if profile_no % 2 else 'Male', date_of_birth=date(1985 + profile_no, 1, 1), city=f'Demo City {region_no}', jamatkhana=jk, local_council=local, region=region, is_demo=True)
                        profile = FamilyHarmonyProfile.objects.create(person=person, status='ACTIVE', owning_jamatkhana=jk, owning_local_council=local, owning_region=region, profession='Demo professional', is_demo=True)
                        FamilyHarmonyPreference.objects.create(profile=profile, minimum_age=25, maximum_age=45)
        self.stdout.write(self.style.SUCCESS('Fictional demo data created.'))