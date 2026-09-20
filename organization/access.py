from datetime import date

from django.db.models import Q

from .models import UserJurisdictionAccess


def active_accesses(user, board=None):
    today = date.today()
    query = UserJurisdictionAccess.objects.filter(user=user, is_active=True).filter(
        Q(start_date__isnull=True) | Q(start_date__lte=today),
        Q(end_date__isnull=True) | Q(end_date__gte=today),
    )
    if board is not None:
        query = query.filter(Q(board__isnull=True) | Q(board=board))
    return query


def has_jurisdiction_access(user, *, region=None, local_council=None, jamatkhana=None, board=None):
    if user.is_superuser:
        return True
    accesses = active_accesses(user, board)
    if jamatkhana is not None:
        accesses = accesses.filter(Q(level='NATIONAL') | Q(level='REGIONAL', regional_council=jamatkhana.local_council.regional_council) | Q(level='LOCAL', local_council=jamatkhana.local_council) | Q(level='JK', jamatkhana=jamatkhana))
    elif local_council is not None:
        accesses = accesses.filter(Q(level='NATIONAL') | Q(level='REGIONAL', regional_council=local_council.regional_council) | Q(level='LOCAL', local_council=local_council))
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
