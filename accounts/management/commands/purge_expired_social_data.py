from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from family_harmony.models import PublicFormInvitation
from sharing.models import ProfileShare


class Command(BaseCommand):
    help = 'Remove expired invitations and shares. Never deletes people, cases, profiles, or audit history.'

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true')
        parser.add_argument('--confirm', action='store_true')

    def handle(self, *args, **options):
        if not options['dry_run'] and not options['confirm']:
            raise CommandError('Pass --dry-run or --confirm.')
        now = timezone.now()
        shares = ProfileShare.objects.filter(expires_at__lt=now)
        invitations = PublicFormInvitation.objects.filter(expires_at__lt=now, submitted_at__isnull=True)
        self.stdout.write(f'Expired shares: {shares.count()}; expired unused invitations: {invitations.count()}')
        if options['confirm']:
            shares.delete()
            invitations.delete()
            self.stdout.write(self.style.SUCCESS('Expired technical records purged.'))
