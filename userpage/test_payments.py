"""Sandbox payment tests — eSewa UAT + Khalti sandbox. All gateway HTTP mocked."""

import base64
import datetime
import json
from decimal import Decimal
from unittest import mock

from books.models import Book, Category
from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django.urls import reverse

from userpage import payments

from .models import Cart, Order

GATEWAY_SETTINGS = {
    'HCAPTCHA_ENABLED': False,
    'HCAPTCHA_SITEKEY': '',
    'HCAPTCHA_SECRET': '',
    'ESEWA_MERCHANT_CODE': 'EPAYTEST',
    'ESEWA_SECRET_KEY': 'test-secret',
    'KHALTI_SECRET_KEY': 'test-khalti-secret',
    'KHALTI_BASE_URL': 'https://dev.khalti.com/api/v2/',
}


def make_buyer(username='buyer'):
    return User.objects.create_user(username, password='pw123456')


def make_book(name='Dune'):
    category, _ = Category.objects.get_or_create(category_name='Fiction')
    return Book.objects.create(
        name=name, author='Herbert', price=Decimal('19.99'),
        image_url='http://x/y.jpg', description='Epic sci-fi novel',
        published_date=datetime.date(2020, 1, 1), category=category,
    )


class FakeResp:
    def __init__(self, data, status_code=200):
        self._data = data
        self.status_code = status_code

    def json(self):
        return self._data


@override_settings(**GATEWAY_SETTINGS)
class EsewaHelperTests(TestCase):
    def test_signature_round_trip_and_tamper_rejected(self):
        sig = payments.esewa_signature('test-secret', '39.98', 'order-abc', 'EPAYTEST')
        payload = {
            'total_amount': '39.98', 'transaction_uuid': 'order-abc',
            'product_code': 'EPAYTEST', 'signature': sig,
        }
        self.assertTrue(payments.esewa_verify_signature(payload))
        tampered = dict(payload, total_amount='1.00')
        self.assertFalse(payments.esewa_verify_signature(tampered))

    def test_decode_rejects_garbage(self):
        self.assertIsNone(payments.esewa_decode_callback(''))
        self.assertIsNone(payments.esewa_decode_callback('!!!not-base64!!!'))


@override_settings(**GATEWAY_SETTINGS)
class EsewaFlowTests(TestCase):
    def setUp(self):
        self.buyer = make_buyer()
        self.book = make_book()
        self.client.force_login(self.buyer)
        self.cart = Cart.objects.create(user=self.buyer, book=self.book)

    def _order_data(self):
        return {'quantity': 2, 'address': 'Kathmandu',
                'contact_no': '+9779800000000', 'payment_method': 'eSewa'}

    def test_esewa_choice_renders_signed_redirect_form(self):
        resp = self.client.post(
            reverse('user-order', args=[self.cart.id, self.book.id]), self._order_data()
        )
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'rc-epay.esewa.com.np')
        self.assertContains(resp, 'EPAYTEST')
        order = Order.objects.get(user=self.buyer)
        self.assertEqual(order.payment_method, Order.PAYMENT_ESEWA)
        self.assertFalse(order.payment_status)
        # Cart stays until the gateway confirms payment.
        self.assertTrue(Cart.objects.filter(pk=self.cart.pk).exists())

    def _signed_callback(self, order):
        payload = {
            'transaction_uuid': order.payment_ref,
            'total_amount': str(order.total_price),
            'product_code': 'EPAYTEST',
        }
        payload['signature'] = payments.esewa_signature(
            'test-secret', payload['total_amount'],
            payload['transaction_uuid'], payload['product_code'],
        )
        return base64.b64encode(json.dumps(payload).encode()).decode()

    def _unpaid_esewa_order(self):
        return Order.objects.create(
            book=self.book, user=self.buyer, quantity=2,
            total_price=Decimal('39.98'), payment_method=Order.PAYMENT_ESEWA,
            payment_ref='order-abc123', contact_no='+9779800000000',
            address='Kathmandu', status=Order.STATUS_PENDING, payment_status=False,
        )

    def test_esewa_success_marks_paid_and_clears_cart(self):
        order = self._unpaid_esewa_order()
        with mock.patch.object(payments, 'esewa_status_check', return_value='COMPLETE'):
            resp = self.client.get(
                reverse('esewa-success'), {'data': self._signed_callback(order)}
            )
        self.assertRedirects(resp, reverse('myorders'))
        order.refresh_from_db()
        self.assertTrue(order.payment_status)
        self.assertFalse(Cart.objects.filter(pk=self.cart.pk).exists())

    def test_esewa_success_rejects_tampered_signature(self):
        order = self._unpaid_esewa_order()
        payload = {
            'transaction_uuid': order.payment_ref, 'total_amount': '1.00',
            'product_code': 'EPAYTEST', 'signature': 'bogus',
        }
        data = base64.b64encode(json.dumps(payload).encode()).decode()
        with mock.patch.object(payments, 'esewa_status_check', return_value='COMPLETE'):
            resp = self.client.get(reverse('esewa-success'), {'data': data})
        self.assertRedirects(resp, reverse('myorders'))
        order.refresh_from_db()
        self.assertFalse(order.payment_status)

    def test_esewa_success_rejects_canceled_status(self):
        order = self._unpaid_esewa_order()
        with mock.patch.object(payments, 'esewa_status_check', return_value='CANCELED'):
            resp = self.client.get(
                reverse('esewa-success'), {'data': self._signed_callback(order)}
            )
        self.assertRedirects(resp, reverse('myorders'))
        order.refresh_from_db()
        self.assertFalse(order.payment_status)

    def test_esewa_failure_keeps_order_pending(self):
        order = self._unpaid_esewa_order()
        resp = self.client.get(reverse('esewa-failure'))
        self.assertRedirects(resp, reverse('myorders'))
        order.refresh_from_db()
        self.assertFalse(order.payment_status)


@override_settings(**GATEWAY_SETTINGS)
class KhaltiFlowTests(TestCase):
    def setUp(self):
        self.buyer = make_buyer()
        self.book = make_book()
        self.client.force_login(self.buyer)
        self.cart = Cart.objects.create(user=self.buyer, book=self.book)

    def _order_data(self):
        return {'quantity': 2, 'address': 'Kathmandu',
                'contact_no': '+9779800000000', 'payment_method': 'Khalti'}

    def test_khalti_choice_redirects_to_payment_url(self):
        fake = FakeResp({'pidx': 'test-pidx-1', 'payment_url': 'https://pay.khalti.com/pidx'})
        with mock.patch.object(payments.requests, 'post', return_value=fake):
            resp = self.client.post(
                reverse('user-order', args=[self.cart.id, self.book.id]), self._order_data()
            )
        self.assertRedirects(resp, 'https://pay.khalti.com/pidx', fetch_redirect_response=False)
        order = Order.objects.get(user=self.buyer)
        self.assertEqual(order.payment_ref, 'test-pidx-1')
        self.assertFalse(order.payment_status)

    def test_khalti_initiate_failure_creates_no_order(self):
        fake = FakeResp({'error': 'nope'}, status_code=400)
        with mock.patch.object(payments.requests, 'post', return_value=fake):
            resp = self.client.post(
                reverse('user-order', args=[self.cart.id, self.book.id]), self._order_data()
            )
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(Order.objects.exists())

    def _unpaid_khalti_order(self):
        return Order.objects.create(
            book=self.book, user=self.buyer, quantity=2,
            total_price=Decimal('39.98'), payment_method=Order.PAYMENT_KHALTI,
            payment_ref='test-pidx-9', contact_no='+9779800000000',
            address='Kathmandu', status=Order.STATUS_PENDING, payment_status=False,
        )

    def test_khalti_return_completed_marks_paid(self):
        order = self._unpaid_khalti_order()
        fake = FakeResp({'status': 'Completed', 'pidx': 'test-pidx-9'})
        with mock.patch.object(payments.requests, 'post', return_value=fake):
            resp = self.client.get(reverse('khalti-return'), {'pidx': 'test-pidx-9'})
        self.assertRedirects(resp, reverse('myorders'))
        order.refresh_from_db()
        self.assertTrue(order.payment_status)
        self.assertFalse(Cart.objects.filter(pk=self.cart.pk).exists())

    def test_khalti_return_pending_keeps_unpaid(self):
        order = self._unpaid_khalti_order()
        fake = FakeResp({'status': 'Pending', 'pidx': 'test-pidx-9'})
        with mock.patch.object(payments.requests, 'post', return_value=fake):
            resp = self.client.get(reverse('khalti-return'), {'pidx': 'test-pidx-9'})
        self.assertRedirects(resp, reverse('myorders'))
        order.refresh_from_db()
        self.assertFalse(order.payment_status)
