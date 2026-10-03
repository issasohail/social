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


class DelegatedAccessRulesTest(TestCase):
    def setUp(self):
        from boards.models import Board
        from organization.models import UserJurisdictionAccess

        self.Access = UserJurisdictionAccess
        self.board_a = Board.objects.create(name='Social Welfare Board', code='SWB')
        self.board_b = Board.objects.create(name='Health Board', code='HB')
        self.national = NationalCouncil.objects.create(name='National', code='NAT')
        self.region_a = RegionalCouncil.objects.create(national_council=self.national, name='Central', code='CENTRAL')
        self.region_b = RegionalCouncil.objects.create(national_council=self.national, name='South', code='SOUTH')
        self.local_a = LocalCouncil.objects.create(regional_council=self.region_a, name='Rawalpindi', code='RWP')
        self.local_b = LocalCouncil.objects.create(regional_council=self.region_b, name='Karachi', code='KHI')
        self.jk_a = Jamatkhana.objects.create(local_council=self.local_a, name='Karimabad', code='KAR')
        self.jk_b = Jamatkhana.objects.create(local_council=self.local_b, name='Garden', code='GAR')
        self.actor = User.objects.create_user('delegator')

    def _access(self, *, level, board=None, role='ADMIN', caps=None, region=None, local=None, jk=None):
        kwargs = dict(
            user=self.actor,
            level=level,
            role=role,
            board=board,
            capabilities=caps if caps is not None else ['manage_users', 'people_view'],
            national_council=self.national,
            regional_council=region,
            local_council=local,
            jamatkhana=jk,
        )
        return self.Access.objects.create(**kwargs)

    def _candidate(self, *, level, board=None, role='MEMBER', caps=None, region=None, local=None, jk=None):
        target = self.Access(
            level=level,
            role=role,
            board=board,
            capabilities=caps if caps is not None else ['people_view'],
            national_council=self.national,
            regional_council=region,
            local_council=local,
            jamatkhana=jk,
        )
        return target

    def test_council_admin_can_delegate_any_board_downward_in_scope(self):
        from organization.access import can_delegate_access
        self._access(level='REGIONAL', region=self.region_a, board=None)
        target = self._candidate(level='JK', region=self.region_a, local=self.local_a, jk=self.jk_a, board=self.board_b)
        self.assertTrue(can_delegate_access(self.actor, target))

    def test_board_admin_cannot_cross_board(self):
        from organization.access import can_delegate_access
        self._access(level='REGIONAL', region=self.region_a, board=self.board_a)
        target = self._candidate(level='LOCAL', region=self.region_a, local=self.local_a, board=self.board_b)
        self.assertFalse(can_delegate_access(self.actor, target))

    def test_board_admin_can_delegate_same_board_downward(self):
        from organization.access import can_delegate_access
        self._access(level='REGIONAL', region=self.region_a, board=self.board_a)
        target = self._candidate(level='LOCAL', region=self.region_a, local=self.local_a, board=self.board_a)
        self.assertTrue(can_delegate_access(self.actor, target))

    def test_local_admin_cannot_delegate_outside_local(self):
        from organization.access import can_delegate_access
        self._access(level='LOCAL', region=self.region_a, local=self.local_a)
        target = self._candidate(level='JK', region=self.region_b, local=self.local_b, jk=self.jk_b)
        self.assertFalse(can_delegate_access(self.actor, target))

    def test_admin_cannot_grant_capability_they_do_not_have(self):
        from organization.access import can_delegate_access
        self._access(level='LOCAL', region=self.region_a, local=self.local_a, caps=['manage_users', 'people_view'])
        target = self._candidate(
            level='JK', region=self.region_a, local=self.local_a, jk=self.jk_a,
            caps=['people_view', 'people_export'],
        )
        self.assertFalse(can_delegate_access(self.actor, target))
