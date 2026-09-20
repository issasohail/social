from datetime import date

from django.core.exceptions import ValidationError
from django.test import TestCase

from family_harmony.models import FamilyHarmonyProfile
from people.models import Person


class FamilyHarmonyTests(TestCase):
    def test_activation_requires_adult_with_birth_date(self):
        minor = Person.objects.create(first_name='Young', last_name='Candidate', date_of_birth=date.today())
        profile = FamilyHarmonyProfile(person=minor, status=FamilyHarmonyProfile.Status.ACTIVE)
        with self.assertRaises(ValidationError):
            profile.full_clean()

    def test_draft_can_exist_without_birth_date(self):
        person = Person.objects.create(first_name='Draft', last_name='Candidate')
        profile = FamilyHarmonyProfile(person=person)
        profile.full_clean()
