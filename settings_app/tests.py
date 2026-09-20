from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from family_harmony.models import FamilyHarmonyProfile
from organization.models import Jamatkhana, LocalCouncil, NationalCouncil, RegionalCouncil
from people.models import Person
from people.forms import PersonForm
from accounts.models import UserProfile
from sharing.models import PersonShare, ProfileShare
from .models import FamilyHarmonySettings


class SettingsAndExportTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username='admin', password='admin123')
        UserProfile.objects.create(user=self.user, phone_number='03122550183')
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
        self.assertContains(people_response, 'Current LC')
        self.assertContains(people_response, 'Current JK')
        self.assertContains(people_response, 'select2-filter')
        self.assertContains(people_response, 'WhatsApp')

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

    def test_person_create_form_and_whatsapp_share(self):
        form_response = self.client.get(reverse('person_create'))
        self.assertContains(form_response, 'class="form-row"')
        self.assertContains(form_response, 'Person details')

        list_response = self.client.get(reverse('people'))
        self.assertContains(list_response, 'WhatsApp')
        share_response = self.client.get(reverse('create_person_share', args=[self.person.pk]))
        self.assertEqual(share_response.status_code, 302)
        self.assertIn('wa.me/923122550183', share_response['Location'])
        self.assertEqual(PersonShare.objects.filter(person=self.person).count(), 1)

    def test_person_dropdown_fields_use_settings_options(self):
        settings = FamilyHarmonySettings.current()
        settings.education_levels = ['Metric', 'PhD']
        settings.occupation_options = ['Teacher', 'Doctor']
        settings.employer_options = ['Government', 'Own business']
        settings.income_ranges = ['Below 50,000', 'Above 500,000']
        settings.save()
        form = PersonForm()
        self.assertEqual(form.fields['education'].choices[1][0], 'Metric')
        self.assertEqual(form.fields['occupation'].choices[1][0], 'Teacher')
        self.assertEqual(form.fields['employer_or_business'].choices[1][0], 'Government')
        self.assertEqual(form.fields['income_range'].choices[1][0], 'Below 50,000')

    def test_people_and_harmony_use_pagination_and_shared_person_source(self):
        for index in range(51):
            Person.objects.create(first_name=f'Page{index}', last_name='Person')
        people_response = self.client.get(reverse('people'))
        self.assertContains(people_response, 'Page 1 of 2')
        self.assertNotContains(people_response, 'Page 2 of 2')

        harmony_response = self.client.get(reverse('family_harmony') + f'?local_council={self.profile.owning_local_council_id}&jamatkhana={self.profile.owning_jamatkhana_id}')
        self.assertContains(harmony_response, 'All local councils')
        self.assertContains(harmony_response, 'All Jamatkhanas')
        self.assertEqual(self.profile.person.harmony_profile.pk, self.profile.pk)
