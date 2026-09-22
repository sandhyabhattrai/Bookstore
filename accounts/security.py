"""hCaptcha verification for bot protection on checkout, plus login throttling."""

import logging

from django.conf import settings
from django.core.cache import cache

try:
    import requests
except ImportError:  # minimal installs: CAPTCHA verifies as failed (fail-closed)
    requests = None

logger = logging.getLogger(__name__)

# Login throttling: max failures per key within the window.
LOGIN_ATTEMPT_LIMIT = 5
LOGIN_ATTEMPT_WINDOW = 5 * 60  # seconds


def _attempts_key(key):
    return f'login-attempts:{key}'


def login_throttled(key):
    try:
        return cache.get(_attempts_key(key), 0) >= LOGIN_ATTEMPT_LIMIT
    except Exception:
        return False


def register_login_attempt(key):
    try:
        attempts = cache.get(_attempts_key(key), 0) + 1
        cache.set(_attempts_key(key), attempts, LOGIN_ATTEMPT_WINDOW)
    except Exception:
        pass


def clear_login_attempts(key):
    try:
        cache.delete(_attempts_key(key))
    except Exception:
        pass


def hcaptcha_enabled():
    return bool(settings.HCAPTCHA_ENABLED)


def verify_hcaptcha(token, remote_ip=None):
    """Verify an hCaptcha client token server-side. Fail-closed: any
    transport error, bad response or explicit failure returns False."""
    if not token or not hcaptcha_enabled() or requests is None:
        return False
    data = {'secret': settings.HCAPTCHA_SECRET, 'response': token}
    if remote_ip:
        data['remoteip'] = remote_ip
    try:
        resp = requests.post(
            settings.HCAPTCHA_VERIFY_URL, data=data, timeout=settings.HCAPTCHA_TIMEOUT
        )
        result = resp.json()
    except Exception as exc:
        logger.warning('hCaptcha verification transport failure: %s', exc)
        return False
    ok = bool(result.get('success'))
    if not ok:
        logger.warning('hCaptcha verification failed: %r', result.get('error-codes'))
    return ok
