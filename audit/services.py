from .models import AuditLog


def record_audit(request, action, *, instance=None, board=None, jurisdiction='', old_values=None, new_values=None):
    forwarded = request.META.get('HTTP_X_FORWARDED_FOR', '')
    ip_address = forwarded.split(',')[0].strip() if forwarded else request.META.get('REMOTE_ADDR')
    return AuditLog.objects.create(
        actor=request.user if request.user.is_authenticated else None,
        action=action,
        model_name=instance._meta.label if instance is not None else '',
        object_id=str(instance.pk) if instance is not None else '',
        board=board,
        jurisdiction=jurisdiction,
        ip_address=ip_address,
        user_agent=request.META.get('HTTP_USER_AGENT', '')[:1000],
        old_values=old_values or {},
        new_values=new_values or {},
    )
