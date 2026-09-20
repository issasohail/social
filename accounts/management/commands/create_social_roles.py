from django.contrib.auth.models import Group, Permission
from django.core.management.base import BaseCommand


ROLE_PERMISSIONS = {
    'Super Admin': [],
    'National Admin': ['view_person', 'add_person', 'change_person'],
    'National Board Member': ['view_person', 'view_case'],
    'Regional Admin': ['view_person', 'add_person', 'change_person', 'view_case'],
    'Regional Board Member': ['view_person', 'view_case'],
    'Local Admin': ['view_person', 'add_person', 'change_person', 'view_case'],
    'Local Board Member': ['view_person', 'view_case'],
    'JK Admin': ['view_person', 'add_person', 'change_person', 'view_case'],
    'JK Team Member': ['view_person', 'view_case'],
    'Family Harmony Officer': ['view_person', 'add_person', 'change_person', 'view_familyharmonyprofile', 'add_familyharmonyprofile', 'change_familyharmonyprofile'],
    'Auditor / Read Only': ['view_person', 'view_case', 'view_auditlog'],
}


class Command(BaseCommand):
    help = 'Create or update the standard Social Welfare role groups.'

    def handle(self, *args, **options):
        for role, codenames in ROLE_PERMISSIONS.items():
            group, _ = Group.objects.get_or_create(name=role)
            group.permissions.add(*Permission.objects.filter(codename__in=codenames))
        self.stdout.write(self.style.SUCCESS('Social Welfare role groups are ready.'))