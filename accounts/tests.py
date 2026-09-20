from django.contrib.auth.models import Group
from django.test import TestCase

from .forms import StaffUserForm


class StaffAccountTests(TestCase):
	def setUp(self):
		self.admin = self.client
		from django.contrib.auth import get_user_model
		self.user = get_user_model().objects.create_superuser('root', 'root@example.com', 'strong-pass-123')

	def test_superuser_can_create_staff_user_through_form(self):
		group = Group.objects.create(name='Local Admin')
		form = StaffUserForm(data={'username': 'staff', 'email': 'staff@example.com', 'password': 'staff-pass-123', 'groups': [group.pk], 'is_active': True})
		self.assertTrue(form.is_valid())
		user = form.save()
		self.assertTrue(user.check_password('staff-pass-123'))
		self.assertEqual(user.groups.get(), group)

	def test_staff_admin_page_requires_superuser(self):
		self.client.force_login(self.user)
		self.assertEqual(self.client.get('/staff-admin/users/').status_code, 200)
