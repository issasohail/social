from collections import OrderedDict
from functools import wraps

from django.contrib import messages
from django.contrib.auth.models import Group, User
from django.db import transaction
from django.db.models import Q
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render

from audit.services import record_audit
from boards.models import Board
from organization.models import Jamatkhana, LocalCouncil, NationalCouncil, RegionalCouncil, UserJurisdictionAccess
from organization.access import active_accesses, can_delegate_access, user_has_capability, visible_access_q

from .forms import GroupPermissionForm, JurisdictionAccessForm, StaffUserForm




GROUP_PERMISSION_SECTION_TITLES = OrderedDict([
    ('people', 'People'),
    ('family_harmony', 'Family Harmony'),
    ('teams', 'Teams & Contacts'),
    ('accounts', 'User Access'),
    ('organization', 'Jamatkhana'),
    ('settings_app', 'Settings'),
    ('reports', 'Reports / Exports'),
    ('audit', 'Audit / Logs'),
    ('misc', 'System / Django'),
])


def _permission_label(permission):
    label = permission.name or permission.codename.replace('_', ' ')
    if label.lower().startswith('can '):
        label = label[4:]
    return label[:1].upper() + label[1:]


def _permission_section_key(permission):
    app_label = permission.content_type.app_label
    return app_label if app_label in GROUP_PERMISSION_SECTION_TITLES else 'misc'


def _permission_sections(form):
    raw_selected = form['permissions'].value() or []
    selected_ids = {int(value) for value in raw_selected if str(value).isdigit()}
    buckets = OrderedDict((key, {'key': key, 'title': title, 'items': []}) for key, title in GROUP_PERMISSION_SECTION_TITLES.items())
    for permission in form.fields['permissions'].queryset:
        section_key = _permission_section_key(permission)
        buckets[section_key]['items'].append({
            'id': permission.pk,
            'label': _permission_label(permission),
            'checked': permission.pk in selected_ids,
            'meta': f"{permission.content_type.model.replace('_', ' ').title()} · {permission.content_type.app_label.replace('_', ' ').title()}",
        })
    return [section for section in buckets.values() if section['items']]

def staff_admin_required(view):
    @wraps(view)
    def wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if not request.user.is_superuser and not user_has_capability(request.user, 'manage_users'):
            return HttpResponseForbidden('You do not have user-management access.')
        return view(request, *args, **kwargs)
    return wrapped


def _visible_users(user, queryset):
    if user.is_superuser:
        return queryset
    scope = visible_access_q(user)
    return queryset.filter(scope).distinct() if scope else queryset.none()


def _can_manage_existing_access(actor, access):
    if actor.is_superuser:
        return True
    return can_delegate_access(actor, access)


@staff_admin_required
def staff_users(request):
    users = User.objects.select_related('profile__person__jamatkhana__local_council__regional_council').prefetch_related(
        'groups',
        'jurisdiction_access__board',
        'jurisdiction_access__national_council',
        'jurisdiction_access__regional_council',
        'jurisdiction_access__local_council',
        'jurisdiction_access__jamatkhana__local_council__regional_council',
    ).order_by('username')
    users = _visible_users(request.user, users)

    query = request.GET.get('q', '').strip()
    level = request.GET.get('level', '').strip()
    role = request.GET.get('role', '').strip()
    board_id = request.GET.get('board', '').strip()
    national_id = request.GET.get('national_council', '').strip()
    regional_id = request.GET.get('regional_council', '').strip()
    local_id = request.GET.get('local_council', '').strip()
    jk_id = request.GET.get('jamatkhana', '').strip()
    if query:
        users = users.filter(
            Q(username__icontains=query) | Q(first_name__icontains=query) | Q(last_name__icontains=query) |
            Q(email__icontains=query) | Q(profile__person__full_name__icontains=query) |
            Q(profile__person__mobile__icontains=query) | Q(profile__person__whatsapp_number__icontains=query)
        )
    if level:
        users = users.filter(jurisdiction_access__level=level)
    if role:
        users = users.filter(jurisdiction_access__role=role)
    if board_id:
        users = users.filter(jurisdiction_access__board_id=board_id)
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
        profile = getattr(user, 'profile', None)
        person = getattr(profile, 'person', None) if profile else None
        user.person_record = person
        user.phone_number = (person.whatsapp_number or person.mobile) if person else (profile.phone_number if profile else '')

    return render(request, 'accounts/users.html', {
        'users': users,
        'levels': UserJurisdictionAccess.Level.choices,
        'roles': UserJurisdictionAccess.Role.choices,
        'filters': {
            'q': query, 'level': level, 'role': role, 'board': board_id,
            'national_council': national_id, 'regional_council': regional_id,
            'local_council': local_id, 'jamatkhana': jk_id,
        },
        'boards': Board.objects.filter(is_active=True).order_by('sort_order', 'name'),
        'national_councils': NationalCouncil.objects.filter(is_active=True).order_by('name'),
        'regional_councils': RegionalCouncil.objects.filter(is_active=True).order_by('name'),
        'local_councils': LocalCouncil.objects.filter(is_active=True).order_by('name'),
        'jamatkhanas': Jamatkhana.objects.filter(is_active=True).select_related('local_council__regional_council').order_by('name'),
    })


@staff_admin_required
@transaction.atomic
def staff_user_create(request):
    if request.method == 'POST':
        form = StaffUserForm(request.POST, actor=request.user)
        access_form = JurisdictionAccessForm(request.POST, actor=request.user)
        forms_valid = form.is_valid() and access_form.is_valid()
        if forms_valid and can_delegate_access(request.user, access_form.instance):
            user = form.save()
            access = access_form.save(commit=False)
            access.user = user
            access.granted_by = request.user
            access.save()
            record_audit(request, 'user_created', instance=user, new_values={
                'person_id': getattr(user.profile, 'person_id', None),
                'access': access.authority_label,
                'jurisdiction': access.jurisdiction_label,
            })
            messages.success(request, f'User {user.username} created for {user.get_full_name() or user.username}.')
            return redirect('staff_users')
        if forms_valid and not can_delegate_access(request.user, access_form.instance):
            access_form.add_error(None, 'You cannot grant access above your level, outside your jurisdiction, or outside your board scope.')
    else:
        form = StaffUserForm(actor=request.user)
        access_form = JurisdictionAccessForm(actor=request.user)
    return render(request, 'accounts/user_form.html', {'form': form, 'access_form': access_form})


@staff_admin_required
@transaction.atomic
def staff_access_create(request, user_id):
    managed_user = get_object_or_404(User.objects.select_related('profile__person'), pk=user_id)
    if not request.user.is_superuser:
        visible = _visible_users(request.user, User.objects.filter(pk=managed_user.pk)).exists()
        # Allow adding the first access to a newly-created user only through the create-user flow.
        if not visible:
            return HttpResponseForbidden('This user is outside your management scope.')
    if request.method == 'POST':
        form = JurisdictionAccessForm(request.POST, actor=request.user)
        if form.is_valid():
            candidate = form.instance
            if can_delegate_access(request.user, candidate):
                access = form.save(commit=False)
                access.user = managed_user
                access.granted_by = request.user
                access.save()
                record_audit(request, 'jurisdiction_changed', instance=access, new_values={
                    'role': access.role, 'board_id': access.board_id, 'capabilities': access.capabilities
                })
                messages.success(request, f'Access assigned to {managed_user.username}.')
                return redirect('staff_users')
            form.add_error(None, 'You cannot grant access above your level, outside your jurisdiction, or outside your board scope.')
    else:
        form = JurisdictionAccessForm(actor=request.user)
    return render(request, 'accounts/access_form.html', {'form': form, 'managed_user': managed_user})


@staff_admin_required
@transaction.atomic
def staff_access_delete(request, access_id):
    access = get_object_or_404(UserJurisdictionAccess.objects.select_related(
        'board', 'national_council', 'regional_council', 'local_council', 'jamatkhana__local_council__regional_council'
    ), pk=access_id)
    if not _can_manage_existing_access(request.user, access):
        return HttpResponseForbidden('This access assignment is outside your management scope.')
    if request.method == 'POST':
        username = access.user.username
        access.is_active = False
        access.save(update_fields=['is_active', 'updated_at'])
        record_audit(request, 'jurisdiction_changed', instance=access, new_values={'is_active': False})
        messages.success(request, f'Access removed from {username}.')
    return redirect('staff_users')


from django.contrib.auth.decorators import login_required

@login_required
def my_profile(request):
    user = request.user
    person = getattr(getattr(user, 'profile', None), 'person', None)
    if request.method == 'POST':
        # Staff identity comes from People when linked. Only unlinked legacy accounts edit names here.
        if not person:
            user.first_name = (request.POST.get('first_name') or '').strip()
            user.last_name = (request.POST.get('last_name') or '').strip()
            user.email = (request.POST.get('email') or '').strip()
            user.save(update_fields=['first_name','last_name','email'])
        messages.success(request, 'Profile updated.')
        return redirect('my_profile')
    return render(request, 'accounts/profile.html', {'profile_user': user, 'person': person})


@staff_admin_required
def group_permissions(request):
    # Django Groups are global permission bundles, so only the Super Admin may redefine them.
    if not request.user.is_superuser:
        return HttpResponseForbidden('Only a Super Admin can change global group permissions.')

    groups = Group.objects.prefetch_related('permissions__content_type').order_by('name')
    edit_id = request.GET.get('edit', '').strip()
    selected = Group.objects.filter(pk=edit_id).first() if edit_id.isdigit() else None
    if selected is None and groups.exists():
        selected = groups.first()

    if request.method == 'POST':
        group_id = request.POST.get('group_id', '').strip()
        selected = get_object_or_404(Group, pk=group_id) if group_id.isdigit() else None
        form = GroupPermissionForm(request.POST, instance=selected)
        if form.is_valid():
            group = form.save()
            messages.success(request, f'Group permission "{group.name}" updated.')
            return redirect(f'{request.path}?edit={group.pk}')
    else:
        form = GroupPermissionForm(instance=selected) if selected else GroupPermissionForm()

    return render(request, 'accounts/group_permissions.html', {
        'groups': groups,
        'selected_group': selected,
        'form': form,
        'permission_sections': _permission_sections(form),
    })
