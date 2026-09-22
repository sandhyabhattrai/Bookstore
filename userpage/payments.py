"""Online payment adapters — eSewa ePay v2 (UAT) and Khalti ePayment v2 (sandbox).

Both gateways run in TEST mode by default so the college demo works without
any merchant onboarding:
  * eSewa UAT uses officially published test credentials (merchant code
    EPAYTEST) — no signup needed at all.
  * Khalti sandbox needs a self-serve test-merchant signup
    (test-admin.khalti.com, login OTP 987654) — no approval email required.

Going live later = swap keys + base URLs via env. COD stays the default.
All server-to-gateway calls are fail-closed (transport errors → False/None).
"""

import base64
import binascii
import hashlib
import hmac
import json
import logging
import uuid

import requests
from django.conf import settings

logger = logging.getLogger(__name__)


def new_payment_ref(prefix='pay'):
    """Unguessable reference tying our Order to a gateway transaction."""
    return f'{prefix}-{uuid.uuid4().hex[:16]}'


# ---------------------------------------------------------------------------
# eSewa ePay v2 (UAT)
# ---------------------------------------------------------------------------

def esewa_config():
    return {
        'merchant_code': settings.ESEWA_MERCHANT_CODE,
        'secret_key': settings.ESEWA_SECRET_KEY,
        'form_url': settings.ESEWA_FORM_URL,
        'status_url': settings.ESEWA_STATUS_URL,
    }


def esewa_signature(secret_key, total_amount, transaction_uuid, product_code):
    """HMAC-SHA256 (base64) over total_amount,transaction_uuid,product_code."""
    message = (
        f'total_amount={total_amount},'
        f'transaction_uuid={transaction_uuid},'
        f'product_code={product_code}'
    )
    digest = hmac.new(
        secret_key.encode('utf-8'), message.encode('utf-8'), hashlib.sha256
    ).digest()
    return base64.b64encode(digest).decode('utf-8')


def esewa_initiate_fields(order, transaction_uuid, success_url, failure_url):
    """Hidden form fields to POST at eSewa (amounts as plain strings)."""
    cfg = esewa_config()
    total_amount = str(order.total_price)
    return {
        'amount': str(order.total_price),
        'tax_amount': '0',
        'total_amount': total_amount,
        'transaction_uuid': transaction_uuid,
        'product_code': cfg['merchant_code'],
        'product_service_charge': '0',
        'product_delivery_charge': '0',
        'success_url': success_url,
        'failure_url': failure_url,
        'signed_field_names': 'total_amount,transaction_uuid,product_code',
        'signature': esewa_signature(
            cfg['secret_key'], total_amount, transaction_uuid, cfg['merchant_code']
        ),
    }


def esewa_decode_callback(data_param):
    """Decode eSewa's base64 success payload → dict (None if malformed)."""
    if not data_param:
        return None
    try:
        return json.loads(base64.b64decode(data_param).decode('utf-8'))
    except (ValueError, binascii.Error, UnicodeDecodeError) as exc:
        logger.warning('eSewa callback decode failed: %s', exc)
        return None


def esewa_verify_signature(payload):
    """Recompute the callback signature; reject tampered amounts."""
    try:
        expected = esewa_signature(
            esewa_config()['secret_key'],
            str(payload['total_amount']),
            payload['transaction_uuid'],
            payload['product_code'],
        )
    except KeyError:
        return False
    return hmac.compare_digest(expected, payload.get('signature', ''))


def esewa_status_check(product_code, total_amount, transaction_uuid):
    """Server-side status lookup. Returns status string, None on transport error."""
    try:
        resp = requests.get(
            esewa_config()['status_url'],
            params={
                'product_code': product_code,
                'total_amount': total_amount,
                'transaction_uuid': transaction_uuid,
            },
            timeout=10,
        )
        return resp.json().get('status')
    except Exception as exc:
        logger.warning('eSewa status check failed: %s', exc)
        return None


# ---------------------------------------------------------------------------
# Khalti ePayment v2 (sandbox)
# ---------------------------------------------------------------------------

def khalti_enabled():
    return bool(settings.KHALTI_SECRET_KEY)


def khalti_config():
    return {
        'secret_key': settings.KHALTI_SECRET_KEY,
        'base_url': settings.KHALTI_BASE_URL.rstrip('/') + '/',
    }


def _khalti_headers():
    return {
        'Authorization': f"Key {khalti_config()['secret_key']}",
        'Content-Type': 'application/json',
    }


def khalti_initiate(amount_paisa, purchase_order_id, purchase_order_name,
                    return_url, website_url, customer_name=''):
    """Initiate payment → (pidx, payment_url) or (None, error_message)."""
    if not khalti_enabled():
        return None, 'Khalti test key is not configured.'
    payload = {
        'return_url': return_url,
        'website_url': website_url,
        'amount': amount_paisa,
        'purchase_order_id': purchase_order_id,
        'purchase_order_name': purchase_order_name,
    }
    if customer_name:
        payload['customer_info'] = {'name': customer_name}
    try:
        resp = requests.post(
            khalti_config()['base_url'] + 'epayment/initiate/',
            json=payload, headers=_khalti_headers(), timeout=10,
        )
        data = resp.json()
    except Exception as exc:
        logger.warning('Khalti initiate transport failure: %s', exc)
        return None, 'Could not reach Khalti. Please try again.'
    if resp.status_code == 200 and data.get('pidx') and data.get('payment_url'):
        return data['pidx'], data['payment_url']
    logger.warning('Khalti initiate rejected: %r', data)
    return None, 'Khalti rejected the payment request.'


def khalti_lookup(pidx):
    """Look up a payment → status string ('Completed', ...) or None on error."""
    if not khalti_enabled():
        return None
    try:
        resp = requests.post(
            khalti_config()['base_url'] + 'epayment/lookup/',
            json={'pidx': pidx}, headers=_khalti_headers(), timeout=10,
        )
        return resp.json().get('status')
    except Exception as exc:
        logger.warning('Khalti lookup transport failure: %s', exc)
        return None
