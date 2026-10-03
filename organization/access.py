from datetime import date

from django.db.models import Q

from .models import UserJurisdictionAccess


LEVEL_RANK = {
    UserJurisdictionAccess.Level.NATIONAL: 4,
    UserJurisdictionAccess.Level.REGIONAL: 3,
    UserJurisdictionAccess.Level.LOCAL: 2,
    UserJurisdictionAccess.Level.JK: 1,
}

ROLE_RANK = {
    UserJurisdictionAccess.Role.ADMIN: 4,
    UserJurisdictionAccess.Role.MANAGER: 3,
    UserJurisdictionAccess.Role.MEMBER: 2,
    UserJurisdictionAccess.Role.VIEWER: 1,
}


def active_accesses(user, board=None):
    today = date.today()
    query = UserJurisdictionAccess.objects.filter(user=user, is_active=True).filter(
        Q(start_date__isnull=True) | Q(start_date__lte=today),
        Q(end_date__isnull=True) | Q(end_date__gte=today),
    )
    if board is not None:
        query = query.filter(Q(board__isnull=True) | Q(board=board))
    return query.select_related(
        'board', 'national_council', 'regional_council', 'local_council',
        'jamatkhana__local_council__regional_council__national_council',
    )


def user_has_capability(user, code, *, board=None):
    if user.is_superuser:
        return True
    return any(access.has_capability(code) for access in active_accesses(user, board))


def _same_or_descendant(own, target):
    """Return True when target sits inside own's jurisdiction, including same level."""
    if LEVEL_RANK.get(target.level, 0) > LEVEL_RANK.get(own.level, 0):
        return False
    if own.level == UserJurisdictionAccess.Level.NATIONAL:
        return bool(own.national_council_id and target.national_council_id == own.national_council_id)
    if own.level == UserJurisdictionAccess.Level.REGIONAL:
        if not own.regional_council_id:
            return False
        return bool(target.regional_council_id == own.regional_council_id)
    if own.level == UserJurisdictionAccess.Level.LOCAL:
        if not own.local_council_id:
            return False
        return bool(target.local_council_id == own.local_council_id)
    if own.level == UserJurisdictionAccess.Level.JK:
        return bool(own.jamatkhana_id and target.jamatkhana_id == own.jamatkhana_id)
    return False


def can_delegate_access(actor, target):
    """
    Council admins delegate to any board in their jurisdiction and below.
    Board admins delegate downward only inside the same board.
    Nobody can grant a stronger role than their own role.
    """
    if actor.is_superuser:
        return True
    for own in active_accesses(actor):
        if own.role != UserJurisdictionAccess.Role.ADMIN:
            continue
        if not own.has_capability('manage_users'):
            continue
        if ROLE_RANK.get(target.role, 0) > ROLE_RANK.get(own.role, 0):
            continue
        target_caps = set(target.capabilities or [])
        own_caps = set(own.capabilities or [])
        if not target_caps.issubset(own_caps):
            continue
        if not _same_or_descendant(own, target):
            continue
        if own.board_id:
            if target.board_id != own.board_id:
                continue
        # Council-wide own access (board NULL) may grant council-wide or any board.
        return True
    return False


def visible_access_q(user, prefix='jurisdiction_access'):
    """Q expression for user records whose access is inside the actor's delegable scope."""
    if user.is_superuser:
        return None
    q = Q()
    for own in active_accesses(user):
        if own.role != UserJurisdictionAccess.Role.ADMIN or not own.has_capability('manage_users'):
            continue
        base = Q(**{f'{prefix}__is_active': True})
        if own.level == UserJurisdictionAccess.Level.NATIONAL and own.national_council_id:
            base &= Q(**{f'{prefix}__national_council_id': own.national_council_id})
        elif own.level == UserJurisdictionAccess.Level.REGIONAL and own.regional_council_id:
            base &= Q(**{f'{prefix}__regional_council_id': own.regional_council_id})
        elif own.level == UserJurisdictionAccess.Level.LOCAL and own.local_council_id:
            base &= Q(**{f'{prefix}__local_council_id': own.local_council_id})
        elif own.level == UserJurisdictionAccess.Level.JK and own.jamatkhana_id:
            base &= Q(**{f'{prefix}__jamatkhana_id': own.jamatkhana_id})
        else:
            continue
        if own.board_id:
            base &= Q(**{f'{prefix}__board_id': own.board_id})
        q |= base
    return q


def has_jurisdiction_access(user, *, region=None, local_council=None, jamatkhana=None, board=None):
    if user.is_superuser:
        return True
    accesses = active_accesses(user, board)
    if jamatkhana is not None:
        accesses = accesses.filter(
            Q(level='NATIONAL') |
            Q(level='REGIONAL', regional_council=jamatkhana.local_council.regional_council) |
            Q(level='LOCAL', local_council=jamatkhana.local_council) |
            Q(level='JK', jamatkhana=jamatkhana)
        )
    elif local_council is not None:
        accesses = accesses.filter(
            Q(level='NATIONAL') |
            Q(level='REGIONAL', regional_council=local_council.regional_council) |
            Q(level='LOCAL', local_council=local_council)
        )
    elif region is not None:
        accesses = accesses.filter(Q(level='NATIONAL') | Q(level='REGIONAL', regional_council=region))
    return accesses.exists()


def scoped_jurisdiction_filter(queryset, user, *, region_field='owning_region', local_field='owning_local_council', jk_field='owning_jamatkhana', board=None):
    if user.is_superuser:
        return queryset
    filters = Q()
    for access in active_accesses(user, board):
        if access.level == 'NATIONAL':
            return queryset
        if access.level == 'REGIONAL' and access.regional_council_id:
            filters |= Q(**{f'{region_field}_id': access.regional_council_id})
        elif access.level == 'LOCAL' and access.local_council_id:
            filters |= Q(**{f'{local_field}_id': access.local_council_id})
        elif access.level == 'JK' and access.jamatkhana_id:
            filters |= Q(**{f'{jk_field}_id': access.jamatkhana_id})
    return queryset.filter(filters) if filters else queryset.none()
