import hashlib

from django.shortcuts import get_object_or_404
from django.utils import timezone

from audit.services import record_audit
from .models import ProfileShare


def find_share(raw_token):
    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
    return get_object_or_404(ProfileShare, token_hash=token_hash)


def open_share(request, raw_token):
    share = find_share(raw_token)
    if not share.is_available():
        return None
    share.views = share.views + 1
    share.save(update_fields=['views'])
    record_audit(request, 'share_opened', instance=share)
    return share
