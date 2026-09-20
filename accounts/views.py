from functools import wraps

from django.contrib import messages
from django.contrib.auth.models import User
from django.db import transaction
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render

from audit.services import record_audit
from organization.models import UserJurisdictionAccess

from .forms import JurisdictionAccessForm, StaffUserForm


def staff_admin_required(view):
	@wraps(view)
	def wrapped(request, *args, **kwargs):
		if not request.user.is_authenticated:
			return redirect('login')
		if not request.user.is_superuser:
			return HttpResponseForbidden('Only a superuser can manage accounts and jurisdiction access.')
		return view(request, *args, **kwargs)
	return wrapped


@staff_admin_required
def staff_users(request):
	users = User.objects.prefetch_related('groups', 'jurisdiction_access').order_by('username')
	return render(request, 'accounts/users.html', {'users': users})


@staff_admin_required
@transaction.atomic
def staff_user_create(request):
	if request.method == 'POST':
		form = StaffUserForm(request.POST)
		if form.is_valid():
			user = form.save()
			record_audit(request, 'user_created', instance=user)
			messages.success(request, f'User {user.username} created.')
			return redirect('staff_users')
	else:
		form = StaffUserForm()
	return render(request, 'accounts/user_form.html', {'form': form})


@staff_admin_required
@transaction.atomic
def staff_access_create(request, user_id):
	user = get_object_or_404(User, pk=user_id)
	if request.method == 'POST':
		form = JurisdictionAccessForm(request.POST)
		if form.is_valid():
			access = form.save(commit=False)
			access.user = user
			access.granted_by = request.user
			access.save()
			record_audit(request, 'jurisdiction_changed', instance=access)
			messages.success(request, f'Access assigned to {user.username}.')
			return redirect('staff_users')
	else:
		form = JurisdictionAccessForm()
	return render(request, 'accounts/access_form.html', {'form': form, 'managed_user': user})


@staff_admin_required
@transaction.atomic
def staff_access_delete(request, access_id):
	access = get_object_or_404(UserJurisdictionAccess, pk=access_id)
	if request.method == 'POST':
		username = access.user.username
		access.is_active = False
		access.save(update_fields=['is_active', 'updated_at'])
		record_audit(request, 'jurisdiction_changed', instance=access, new_values={'is_active': False})
		messages.success(request, f'Access removed from {username}.')
	return redirect('staff_users')
