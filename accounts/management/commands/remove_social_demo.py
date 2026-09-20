from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from family_harmony.models import FamilyHarmonyProfile
from organization.models import Jamatkhana, LocalCouncil, NationalCouncil, RegionalCouncil
from people.models import Person


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true')
        parser.add_argument('--confirm', action='store_true')

    @transaction.atomic
    def handle(self, *args, **options):
        count = Person.objects.filter(is_demo=True).count()
        if options['dry_run']:
            self.stdout.write(f'{count} demo people would be removed.')
            return
        if not options['confirm']:
            raise CommandError('Pass --confirm to remove demo data.')
        FamilyHarmonyProfile.objects.filter(is_demo=True).delete()
        Person.objects.filter(is_demo=True).delete()
        Jamatkhana.objects.filter(code__startswith='DEMO-').delete()
        LocalCouncil.objects.filter(code__startswith='DEMO-').delete()
        RegionalCouncil.objects.filter(code__startswith='DEMO-').delete()
        NationalCouncil.objects.filter(code__startswith='DEMO-').delete()
        self.stdout.write(self.style.SUCCESS('Demo data removed.'))