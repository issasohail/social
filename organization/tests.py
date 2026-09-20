from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from organization.models import Jamatkhana, LocalCouncil, NationalCouncil, RegionalCouncil


User = get_user_model()


class OrganizationHierarchyViewsTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='admin', password='secret123')
        self.client.force_login(self.user)

        self.national = NationalCouncil.objects.create(name='National Council', code='NC-001', is_active=True)
        self.region = RegionalCouncil.objects.create(national_council=self.national, name='Central Region', code='RC-001', is_active=True)
        self.local = LocalCouncil.objects.create(regional_council=self.region, name='Karachi Local Council', code='LC-001', is_active=True)
        self.jk = Jamatkhana.objects.create(local_council=self.local, name='North Jamatkhana', short_name='JK-01', code='JK-001', is_active=True)

    def test_regional_councils_page_renders(self):
        response = self.client.get(reverse('regional_councils'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Regional Council')
        self.assertContains(response, 'RC-001')

    def test_local_councils_page_renders(self):
        response = self.client.get(reverse('local_councils'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Local Council')
        self.assertContains(response, 'LC-001')

    def test_jamatkhana_page_renders(self):
        response = self.client.get(reverse('jamatkhanas'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Jamatkhana')
        self.assertContains(response, 'JK-001')
