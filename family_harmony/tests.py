from datetime import date
from datetime import timedelta
import hashlib
import secrets

from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from family_harmony.models import FamilyHarmonyProfile, PublicFormInvitation
from people.models import Person
from sharing.models import ProfileShare


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

    def test_public_form_submission_stays_pending(self):
        user = get_user_model().objects.create_user(username='officer', password='pass-12345')
        raw_token = secrets.token_urlsafe(24)
        invitation = PublicFormInvitation.objects.create(token_hash=hashlib.sha256(raw_token.encode()).hexdigest(), created_by=user, expires_at=timezone.now() + timedelta(days=1))
        response = self.client.post(f'/family-harmony/form/{raw_token}/', {'first_name': 'Public', 'last_name': 'Candidate'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(FamilyHarmonyProfile.objects.get().status, FamilyHarmonyProfile.Status.AWAITING_CONSENT)
        invitation.refresh_from_db()
        self.assertIsNotNone(invitation.submitted_at)

    def test_expired_share_is_not_available(self):
        user = get_user_model().objects.create_user(username='share-owner', password='pass-12345')
        person = Person.objects.create(first_name='Shared', last_name='Candidate', date_of_birth=date(1990, 1, 1))
        profile = FamilyHarmonyProfile.objects.create(person=person, status=FamilyHarmonyProfile.Status.ACTIVE)
        share = ProfileShare.objects.create(profile=profile, created_by=user, token_hash='a' * 64, expires_at=timezone.now() - timedelta(minutes=1))
        self.assertFalse(share.is_available())
