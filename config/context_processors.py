def social_nav(request):
    count = 0
    can_manage_access = False
    if getattr(request, 'user', None) and request.user.is_authenticated:
        try:
            from family_harmony.models import PublicFormInvitation
            count = PublicFormInvitation.objects.filter(
                submitted_at__isnull=False,
                profile__isnull=False,
                profile__status__in=['DRAFT','AWAITING_CONSENT'],
            ).count()
        except Exception:
            count = 0
        try:
            from organization.access import user_has_capability
            can_manage_access = user_has_capability(request.user, 'manage_users')
        except Exception:
            can_manage_access = request.user.is_superuser
    return {
        'PENDING_APPROVAL_COUNT': count,
        'USER_CAN_MANAGE_ACCESS': can_manage_access,
    }
