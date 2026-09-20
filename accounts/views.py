from functools import wraps

from django.contrib import messages
from django.contrib.auth.models import User
from django.db import transaction
from django.db.models import Q
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render

from audit.services import record_audit
from organization.models import Jamatkhana, LocalCouncil, NationalCouncil, RegionalCouncil, UserJurisdictionAccess
from organization.access import active_accesses

from .forms import JurisdictionAccessForm, StaffUserForm


def staff_admin_required(view):
	@wraps(view)
	def wrapped(request, *args, **kwargs):
		if not request.user.is_authenticated:
			return redirect('login')
		if not request.user.is_superuser and not active_accesses(request.user).exists():
			return HttpResponseForbidden('You do not have user-management access.')
		return view(request, *args, **kwargs)
	return wrapped


def _visible_user_ids(user):
	if user.is_superuser:
		return None
	accesses = active_accesses(user)
	filters = Q()
	for access in accesses:
		if access.level == UserJurisdictionAccess.Level.NATIONAL:
			return None
		if access.level == UserJurisdictionAccess.Level.REGIONAL and access.regional_council_id:
			filters |= Q(jurisdiction_access__regional_council_id=access.regional_council_id)
		elif access.level == UserJurisdictionAccess.Level.LOCAL and access.local_council_id:
			filters |= Q(jurisdiction_access__local_council_id=access.local_council_id)
		elif access.level == UserJurisdictionAccess.Level.JK and access.jamatkhana_id:
			filters |= Q(jurisdiction_access__jamatkhana_id=access.jamatkhana_id)
	return filters


def _can_assign_access(actor, access):
	if actor.is_superuser:
		return True
	if access.level == UserJurisdictionAccess.Level.NATIONAL:
		return False
	for own in active_accesses(actor):
		if own.level == UserJurisdictionAccess.Level.NATIONAL:
			return True
		if own.level == UserJurisdictionAccess.Level.REGIONAL and own.regional_council_id:
			if access.level in (UserJurisdictionAccess.Level.LOCAL, UserJurisdictionAccess.Level.JK):
				if access.level == UserJurisdictionAccess.Level.LOCAL and access.local_council and access.local_council.regional_council_id == own.regional_council_id:
					return True
				if access.level == UserJurisdictionAccess.Level.JK and access.jamatkhana and access.jamatkhana.local_council.regional_council_id == own.regional_council_id:
					return True
		if own.level == UserJurisdictionAccess.Level.LOCAL and own.local_council_id:
			if access.level == UserJurisdictionAccess.Level.LOCAL and access.local_council_id == own.local_council_id:
				return True
			if access.level == UserJurisdictionAccess.Level.JK and access.jamatkhana and access.jamatkhana.local_council_id == own.local_council_id:
				return True
		if own.level == UserJurisdictionAccess.Level.JK and own.jamatkhana_id:
			if access.level == UserJurisdictionAccess.Level.JK and access.jamatkhana_id == own.jamatkhana_id:
				return True
	return False


@staff_admin_required
def staff_users(request):
	users = User.objects.prefetch_related(
		'groups',
		'jurisdiction_access__national_council',
		'jurisdiction_access__regional_council',
		'jurisdiction_access__local_council',
		'jurisdiction_access__jamatkhana',
	).order_by('username')
	visible_ids = _visible_user_ids(request.user)
	if visible_ids is not None:
		users = users.filter(visible_ids).distinct()
	query = request.GET.get('q', '').strip()
	level = request.GET.get('level', '').strip()
	national_id = request.GET.get('national_council', '').strip()
	regional_id = request.GET.get('regional_council', '').strip()
	local_id = request.GET.get('local_council', '').strip()
	jk_id = request.GET.get('jamatkhana', '').strip()
	if query:
		users = users.filter(Q(username__icontains=query) | Q(first_name__icontains=query) | Q(last_name__icontains=query) | Q(email__icontains=query))
	if level:
		users = users.filter(jurisdiction_access__level=level)
	if national_id:
		users = users.filter(jurisdiction_access__national_council_id=national_id)
	if regional_id:
		users = users.filter(jurisdiction_access__regional_council_id=regional_id)
	if local_id:
		users = users.filter(jurisdiction_access__local_council_id=local_id)
	if jk_id:
		users = users.filter(jurisdiction_access__jamatkhana_id=jk_id)
	users = users.distinct()
	for user in users:
		user.phone_number = getattr(getattr(user, 'profile', None), 'phone_number', '')
	return render(request, 'accounts/users.html', {
		'users': users,
		'levels': UserJurisdictionAccess.Level.choices,
		'filters': {'q': query, 'level': level, 'national_council': national_id, 'regional_council': regional_id, 'local_council': local_id, 'jamatkhana': jk_id},
		'national_councils': NationalCouncil.objects.filter(is_active=True).order_by('name'),
		'regional_councils': RegionalCouncil.objects.filter(is_active=True).order_by('name'),
		'local_councils': LocalCouncil.objects.filter(is_active=True).order_by('name'),
		'jamatkhanas': Jamatkhana.objects.filter(is_active=True).order_by('name'),
	})


@staff_admin_required
@transaction.atomic
def staff_user_create(request):
	if request.method == 'POST':
		form = StaffUserForm(request.POST)
		access_form = JurisdictionAccessForm(request.POST)
		if form.is_valid() and access_form.is_valid() and _can_assign_access(request.user, access_form.instance):
			user = form.save()
			access = access_form.save(commit=False)
			access.user = user
			access.granted_by = request.user
			access.save()
			record_audit(request, 'user_created', instance=user)
			messages.success(request, f'User {user.username} created.')
			return redirect('staff_users')
	else:
		form = StaffUserForm()
		access_form = JurisdictionAccessForm()
	if request.method == 'POST' and access_form.is_valid() and not _can_assign_access(request.user, access_form.instance):
		access_form.add_error(None, 'This access level or council is outside your management scope.')
	return render(request, 'accounts/user_form.html', {'form': form, 'access_form': access_form})


@staff_admin_required
@transaction.atomic
def staff_access_create(request, user_id):
	user = get_object_or_404(User, pk=user_id)
	if request.method == 'POST':
		form = JurisdictionAccessForm(request.POST)
		if form.is_valid() and _can_assign_access(request.user, form.instance):
			access = form.save(commit=False)
			access.user = user
			access.granted_by = request.user
			access.save()
			record_audit(request, 'jurisdiction_changed', instance=access)
			messages.success(request, f'Access assigned to {user.username}.')
			return redirect('staff_users')
	else:
		form = JurisdictionAccessForm()
	if request.method == 'POST' and form.is_valid() and not _can_assign_access(request.user, form.instance):
		form.add_error(None, 'This access level or council is outside your management scope.')
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
