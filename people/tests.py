from datetime import date

from django.contrib.auth import get_user_model
from django.test import TestCase

from people.models import Person


class PersonTests(TestCase):
    def test_identity_is_normalized_and_age_is_calculated(self):
        person = Person.objects.create(first_name='Test', last_name='Person', identity_type='CNIC', identity_number='35202-1234567-1', date_of_birth=date(2000, 1, 1))
        self.assertEqual(person.normalized_identity_number, '35202-1234567-1')
        self.assertIsNotNone(person.age)
        self.assertEqual(person.masked_identity_number(), '35202-*****-1')

    def test_people_list_requires_login(self):
        response = self.client.get('/people/')
        self.assertEqual(response.status_code, 302)

    def test_full_identity_requires_permission_in_application_layer(self):
        user = get_user_model().objects.create_user(username='staff', password='test-pass-123')
        person = Person.objects.create(first_name='Test', last_name='Person', identity_type='CNIC', identity_number='35202-1234567-1')
        self.assertFalse(user.has_perm('people.view_full_cnic'))
        self.assertEqual(person.masked_identity_number(), '35202-*****-1')
