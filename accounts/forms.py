from django import forms
from django.contrib.auth.models import Group, Permission, User
from django.db.models import Q

from boards.models import Board
from people.models import Person
from organization.access import LEVEL_RANK, active_accesses
from organization.models import Jamatkhana, LocalCouncil, NationalCouncil, RegionalCouncil, UserJurisdictionAccess
from .models import UserProfile


class PersonChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, person):
        phone = person.whatsapp_number or person.mobile or 'No phone'
        jk = str(person.jamatkhana) if person.jamatkhana_id else 'No Jamatkhana'
        return f'{person.full_name} — {phone} — {jk}'


class StaffUserForm(forms.ModelForm):
    person = PersonChoiceField(queryset=Person.objects.none(), required=True, label='Person')
    password = forms.CharField(widget=forms.PasswordInput, min_length=8, label='Initial password')
    groups = forms.ModelMultipleChoiceField(
        queryset=Group.objects.all().order_by('name'), required=False,
        widget=forms.CheckboxSelectMultiple, label='Group permissions'
    )

    class Meta:
        model = User
        fields = ('username', 'password', 'groups', 'is_active')

    def __init__(self, *args, actor=None, **kwargs):
        super().__init__(*args, **kwargs)
        people = Person.objects.filter(is_active=True).select_related('jamatkhana__local_council__regional_council')
        linked_person_ids = UserProfile.objects.exclude(person_id=None).values_list('person_id', flat=True)
        if self.instance and self.instance.pk and hasattr(self.instance, 'profile') and self.instance.profile.person_id:
            linked_person_ids = linked_person_ids.exclude(user=self.instance)
        people = people.exclude(pk__in=linked_person_ids)
        if actor and not actor.is_superuser:
            q = Q()
            for access in active_accesses(actor):
                if access.level == UserJurisdictionAccess.Level.NATIONAL and access.national_council_id:
                    q |= Q(jamatkhana__local_council__regional_council__national_council_id=access.national_council_id)
                elif access.level == UserJurisdictionAccess.Level.REGIONAL and access.regional_council_id:
                    q |= Q(jamatkhana__local_council__regional_council_id=access.regional_council_id)
                elif access.level == UserJurisdictionAccess.Level.LOCAL and access.local_council_id:
                    q |= Q(jamatkhana__local_council_id=access.local_council_id)
                elif access.level == UserJurisdictionAccess.Level.JK and access.jamatkhana_id:
                    q |= Q(jamatkhana_id=access.jamatkhana_id)
            people = people.filter(q) if q else people.none()
        self.fields['person'].queryset = people.order_by('full_name')
        self.fields['person'].widget.attrs.update({'data-searchable': 'true', 'data-placeholder': 'Search name, phone, Jamatkhana or council'})
        self.fields['username'].widget.attrs['autocomplete'] = 'off'
        self.fields['password'].widget.attrs['autocomplete'] = 'new-password'

    def save(self, commit=True):
        user = super().save(commit=False)
        person = self.cleaned_data['person']
        user.first_name = person.first_name
        user.last_name = person.last_name
        user.email = person.email
        user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
            self.save_m2m()
            phone = person.whatsapp_number or person.mobile or ''
            UserProfile.objects.update_or_create(user=user, defaults={'phone_number': phone, 'person': person})
        return user


class PermissionChoiceField(forms.ModelMultipleChoiceField):
    def label_from_instance(self, permission):
        action = permission.codename.split('_', 1)[0].replace('_', ' ').title()
        model = permission.content_type.model.replace('_', ' ').title()
        app = permission.content_type.app_label.replace('_', ' ').title()
        return f'{app} — {model} — {action}'


class GroupPermissionForm(forms.ModelForm):
    permissions = PermissionChoiceField(
        queryset=Permission.objects.select_related('content_type').order_by(
            'content_type__app_label', 'content_type__model', 'codename'
        ),
        required=False,
        widget=forms.SelectMultiple(attrs={
            'data-searchable': 'true',
            'data-placeholder': 'Search permissions by app, model or action',
            'size': '14',
        }),
        label='Permissions',
    )

    class Meta:
        model = Group
        fields = ('name', 'permissions')


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ('phone_number', 'person')


class JurisdictionAccessForm(forms.ModelForm):
    capabilities = forms.MultipleChoiceField(
        choices=UserJurisdictionAccess.CAPABILITY_CHOICES,
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label='Capabilities',
    )

    class Meta:
        model = UserJurisdictionAccess
        fields = (
            'level', 'role', 'national_council', 'regional_council', 'local_council',
            'jamatkhana', 'board', 'capabilities', 'is_active', 'start_date', 'end_date'
        )
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, actor=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.actor = actor
        self.fields['national_council'].queryset = NationalCouncil.objects.filter(is_active=True).order_by('name')
        self.fields['regional_council'].queryset = RegionalCouncil.objects.filter(is_active=True).order_by('name')
        self.fields['local_council'].queryset = LocalCouncil.objects.filter(is_active=True).order_by('name')
        self.fields['jamatkhana'].queryset = Jamatkhana.objects.filter(is_active=True).select_related('local_council__regional_council').order_by('name')
        self.fields['board'].queryset = Board.objects.filter(is_active=True).order_by('sort_order', 'name')
        self.fields['board'].empty_label = 'All boards (Council authority)'
        self.fields['jamatkhana'].label_from_instance = lambda o: o.hierarchy_label
        for name in ('level', 'role', 'national_council', 'regional_council', 'local_council', 'jamatkhana', 'board'):
            self.fields[name].widget.attrs['data-searchable'] = 'true'

        # Role presets make the common workflow quick while capabilities remain explicit/editable.
        if not self.is_bound and not self.instance.pk:
            self.initial.setdefault('role', UserJurisdictionAccess.Role.MEMBER)
            self.initial.setdefault('capabilities', ['people_view', 'teams_view'])
            self.initial.setdefault('is_active', True)

        if actor and not actor.is_superuser:
            accesses = list(active_accesses(actor))
            managing_accesses = [
                access for access in accesses
                if access.role == UserJurisdictionAccess.Role.ADMIN and access.has_capability('manage_users')
            ]
            allowed_levels = {
                value for value, _label in UserJurisdictionAccess.Level.choices
                if any(LEVEL_RANK.get(value, 0) <= LEVEL_RANK.get(access.level, 0) for access in managing_accesses)
            }
            self.fields['level'].choices = [
                choice for choice in UserJurisdictionAccess.Level.choices if choice[0] in allowed_levels
            ]
            national_ids, regional_ids, local_ids, jk_ids, board_ids = set(), set(), set(), set(), set()
            council_wide = False
            for own in accesses:
                if own.role != UserJurisdictionAccess.Role.ADMIN or not own.has_capability('manage_users'):
                    continue
                if own.board_id:
                    board_ids.add(own.board_id)
                else:
                    council_wide = True
                if own.level == UserJurisdictionAccess.Level.NATIONAL and own.national_council_id:
                    national_ids.add(own.national_council_id)
                    regions = RegionalCouncil.objects.filter(national_council_id=own.national_council_id)
                    regional_ids.update(regions.values_list('id', flat=True))
                    locals_qs = LocalCouncil.objects.filter(regional_council_id__in=regional_ids)
                    local_ids.update(locals_qs.values_list('id', flat=True))
                    jk_ids.update(Jamatkhana.objects.filter(local_council_id__in=local_ids).values_list('id', flat=True))
                elif own.level == UserJurisdictionAccess.Level.REGIONAL and own.regional_council_id:
                    regional_ids.add(own.regional_council_id)
                    national_ids.add(own.regional_council.national_council_id)
                    locals_qs = LocalCouncil.objects.filter(regional_council_id=own.regional_council_id)
                    local_ids.update(locals_qs.values_list('id', flat=True))
                    jk_ids.update(Jamatkhana.objects.filter(local_council_id__in=local_ids).values_list('id', flat=True))
                elif own.level == UserJurisdictionAccess.Level.LOCAL and own.local_council_id:
                    local_ids.add(own.local_council_id)
                    regional_ids.add(own.local_council.regional_council_id)
                    national_ids.add(own.local_council.regional_council.national_council_id)
                    jk_ids.update(Jamatkhana.objects.filter(local_council_id=own.local_council_id).values_list('id', flat=True))
                elif own.level == UserJurisdictionAccess.Level.JK and own.jamatkhana_id:
                    jk_ids.add(own.jamatkhana_id)
                    local_ids.add(own.jamatkhana.local_council_id)
                    regional_ids.add(own.jamatkhana.local_council.regional_council_id)
                    national_ids.add(own.jamatkhana.local_council.regional_council.national_council_id)
            self.fields['national_council'].queryset = self.fields['national_council'].queryset.filter(id__in=national_ids)
            self.fields['regional_council'].queryset = self.fields['regional_council'].queryset.filter(id__in=regional_ids)
            self.fields['local_council'].queryset = self.fields['local_council'].queryset.filter(id__in=local_ids)
            self.fields['jamatkhana'].queryset = self.fields['jamatkhana'].queryset.filter(id__in=jk_ids)
            if not council_wide:
                self.fields['board'].queryset = self.fields['board'].queryset.filter(id__in=board_ids)
                self.fields['board'].empty_label = None

    def clean(self):
        cleaned = super().clean()
        level = cleaned.get('level')
        required = {
            UserJurisdictionAccess.Level.NATIONAL: 'national_council',
            UserJurisdictionAccess.Level.REGIONAL: 'regional_council',
            UserJurisdictionAccess.Level.LOCAL: 'local_council',
            UserJurisdictionAccess.Level.JK: 'jamatkhana',
        }
        field = required.get(level)
        if field and not cleaned.get(field):
            self.add_error(field, 'Select the jurisdiction for this access level.')

        # Canonicalize the hierarchy from the most-specific selected object.
        if level == UserJurisdictionAccess.Level.REGIONAL and cleaned.get('regional_council'):
            cleaned['national_council'] = cleaned['regional_council'].national_council
            cleaned['local_council'] = None
            cleaned['jamatkhana'] = None
        elif level == UserJurisdictionAccess.Level.LOCAL and cleaned.get('local_council'):
            cleaned['regional_council'] = cleaned['local_council'].regional_council
            cleaned['national_council'] = cleaned['regional_council'].national_council
            cleaned['jamatkhana'] = None
        elif level == UserJurisdictionAccess.Level.JK and cleaned.get('jamatkhana'):
            cleaned['local_council'] = cleaned['jamatkhana'].local_council
            cleaned['regional_council'] = cleaned['local_council'].regional_council
            cleaned['national_council'] = cleaned['regional_council'].national_council
        elif level == UserJurisdictionAccess.Level.NATIONAL:
            cleaned['regional_council'] = None
            cleaned['local_council'] = None
            cleaned['jamatkhana'] = None

        role = cleaned.get('role')
        caps = list(cleaned.get('capabilities') or [])
        if role != UserJurisdictionAccess.Role.ADMIN and 'manage_users' in caps:
            self.add_error('capabilities', 'Only an Admin access may manage subordinate users.')
        return cleaned
