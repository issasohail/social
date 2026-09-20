from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from family_harmony.models import FamilyHarmonyProfile
from organization.models import Jamatkhana, LocalCouncil, NationalCouncil, RegionalCouncil
from people.models import Person
from sharing.models import ProfileShare
from .models import FamilyHarmonySettings


class SettingsAndExportTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username='admin', password='admin123')
        self.client.force_login(self.user)
        national = NationalCouncil.objects.create(name='National Council', code='NC-001')
        region = RegionalCouncil.objects.create(national_council=national, name='Regional Council', code='RC-001')
        local = LocalCouncil.objects.create(regional_council=region, name='Local Council', code='LC-001')
        jk = Jamatkhana.objects.create(local_council=local, name='Jamatkhana One', short_name='JK-1', code='JK-001')
        self.person = Person.objects.create(first_name='Ali', last_name='Khan', mobile='03001234567', city='Karachi', gender='Male', title='Mr', local_council=local, jamatkhana=jk)
        self.profile = FamilyHarmonyProfile.objects.create(person=self.person, owning_region=region, owning_local_council=local, owning_jamatkhana=jk)

    def test_settings_page_is_available(self):
        response = self.client.get(reverse('settings'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Education levels')

    def test_person_detail_has_export_buttons(self):
        response = self.client.get(reverse('person_detail', args=[self.person.pk]))
        self.assertContains(response, 'Export PDF')
        self.assertContains(response, 'Export JPG')

    def test_harmony_detail_has_export_buttons(self):
        response = self.client.get(reverse('harmony_detail', args=[self.profile.pk]))
        self.assertContains(response, 'Export PDF')
        self.assertContains(response, 'Export JPG')

    def test_list_views_show_serials_and_cnic_label(self):
        people_response = self.client.get(reverse('people'))
        self.assertContains(people_response, 'Serial')
        self.assertContains(people_response, 'CNIC')

        harmony_response = self.client.get(reverse('family_harmony'))
        self.assertContains(harmony_response, 'Serial')
        self.assertContains(harmony_response, 'Current LC')
        self.assertContains(harmony_response, 'Current JK')
        self.assertContains(harmony_response, 'WhatsApp')

    def test_inline_updates_persist_and_share_uses_configured_expiry(self):
        person_response = self.client.post(reverse('inline_update_person'), {'id': self.person.pk, 'field': 'city', 'value': 'Lahore'})
        self.assertEqual(person_response.status_code, 200)
        self.person.refresh_from_db()
        self.assertEqual(self.person.city, 'Lahore')

        harmony_response = self.client.post(reverse('harmony_inline_update'), {'id': self.profile.pk, 'field': 'profession', 'value': 'Teacher'})
        self.assertEqual(harmony_response.status_code, 200)
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.profession, 'Teacher')

        configured = FamilyHarmonySettings.current()
        configured.default_expiry_days = 9
        configured.minimum_expiry_days = 2
        configured.maximum_expiry_days = 30
        configured.save()
        share_response = self.client.get(reverse('create_profile_share', args=[self.profile.pk]) + '?redirect=whatsapp')
        self.assertEqual(share_response.status_code, 302)
        self.assertIn('wa.me', share_response['Location'])
        share = ProfileShare.objects.get(profile=self.profile)
        self.assertAlmostEqual((share.expires_at - share.created_at).total_seconds(), 9 * 86400, delta=10)
