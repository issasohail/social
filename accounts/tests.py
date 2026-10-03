from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management import call_command
from django.test import TestCase

from people.models import Person

from .forms import StaffUserForm


User = get_user_model()


class StaffAccountTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_superuser('root', 'root@example.com', 'strong-pass-123')

    def test_superuser_can_create_staff_user_from_person(self):
        group = Group.objects.create(name='Local Admin')
        person = Person.objects.create(
            first_name='Amina', last_name='Test', email='amina@example.com',
            mobile='03001234567', whatsapp_number='03001234567',
        )
        form = StaffUserForm(
            data={
                'person': person.pk,
                'username': 'staff',
                'password': 'staff-pass-123',
                'groups': [group.pk],
                'is_active': True,
            },
            actor=self.user,
        )
        self.assertTrue(form.is_valid(), form.errors)
        user = form.save()
        self.assertTrue(user.check_password('staff-pass-123'))
        self.assertEqual(user.groups.get(), group)
        self.assertEqual(user.profile.person, person)
        self.assertEqual(user.email, person.email)
        self.assertEqual(user.first_name, person.first_name)

    def test_staff_admin_page_requires_management_access_or_superuser(self):
        self.client.force_login(self.user)
        self.assertEqual(self.client.get('/staff-admin/users/').status_code, 200)

    def test_demo_seed_is_idempotent_by_default(self):
        call_command('seed_social_demo', confirm=True, jks_per_local=1, profiles_per_jk=1)
        first_count = Person.objects.filter(is_demo=True).count()
        call_command('seed_social_demo', confirm=True, jks_per_local=1, profiles_per_jk=1)
        self.assertEqual(Person.objects.filter(is_demo=True).count(), first_count)
