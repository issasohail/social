def social_nav(request):
    count = 0
    if getattr(request, 'user', None) and request.user.is_authenticated:
        try:
            from family_harmony.models import PublicFormInvitation
            count = PublicFormInvitation.objects.filter(submitted_at__isnull=False, profile__isnull=False, profile__status__in=['DRAFT','AWAITING_CONSENT']).count()
        except Exception:
            count = 0
    return {'PENDING_APPROVAL_COUNT': count}
