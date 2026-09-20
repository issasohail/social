import json
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from organization.models import Jamatkhana, LocalCouncil, NationalCouncil, RegionalCouncil


class Command(BaseCommand):
    help = 'Import organization hierarchy only from a JSON export. No people, users, passwords, or operational records are accepted.'

    def add_arguments(self, parser):
        parser.add_argument('source', type=str)
        parser.add_argument('--dry-run', action='store_true')
        parser.add_argument('--confirm', action='store_true')

    @transaction.atomic
    def handle(self, *args, **options):
        if not options['dry_run'] and not options['confirm']:
            raise CommandError('Pass --dry-run or --confirm.')
        source = Path(options['source'])
        if not source.exists():
            raise CommandError(f'File not found: {source}')
        payload = json.loads(source.read_text(encoding='utf-8'))
        if not isinstance(payload, dict) or 'national_councils' not in payload:
            raise CommandError('Expected JSON with a national_councils list.')
        counts = {'national': 0, 'regional': 0, 'local': 0, 'jamatkhana': 0}
        if options['dry_run']:
            for national in payload['national_councils']:
                counts['national'] += 1
                for region in national.get('regions', []):
                    counts['regional'] += 1
                    for local in region.get('locals', []):
                        counts['local'] += 1
                        counts['jamatkhana'] += len(local.get('jamatkhanas', []))
            self.stdout.write(f'Dry run: {counts}')
            return
        for national_data in payload['national_councils']:
            national, _ = NationalCouncil.objects.update_or_create(code=national_data['code'], defaults={'name': national_data['name'], 'is_active': national_data.get('is_active', True)})
            for region_data in national_data.get('regions', []):
                region, _ = RegionalCouncil.objects.update_or_create(code=region_data['code'], defaults={'national_council': national, 'name': region_data['name'], 'is_active': region_data.get('is_active', True)})
                for local_data in region_data.get('locals', []):
                    local, _ = LocalCouncil.objects.update_or_create(code=local_data['code'], defaults={'regional_council': region, 'name': local_data['name'], 'is_active': local_data.get('is_active', True)})
                    for jk_data in local_data.get('jamatkhanas', []):
                        Jamatkhana.objects.update_or_create(code=jk_data['code'], defaults={'local_council': local, 'name': jk_data['name'], 'short_name': jk_data.get('short_name', ''), 'is_active': jk_data.get('is_active', True), 'latitude': jk_data.get('latitude'), 'longitude': jk_data.get('longitude')})
        self.stdout.write(self.style.SUCCESS('Organization hierarchy imported.'))
