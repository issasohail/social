from django.db import models
from django.contrib.auth.models import User


class UserProfile(models.Model):
	user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
	phone_number = models.CharField(max_length=30, blank=True)
	person = models.OneToOneField('people.Person', null=True, blank=True, on_delete=models.SET_NULL, related_name='staff_profile')

	def __str__(self):
		return self.user.get_username()
