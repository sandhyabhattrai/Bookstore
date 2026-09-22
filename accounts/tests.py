from unittest import mock

from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django.urls import reverse


class LocalAuthTests(TestCase):
    def setUp(self):
        User.objects.create_user('buyer', password='pw123456')
        staff = User.objects.create_user('staff', password='pw123456')
        staff.is_staff = True
        staff.save()

    def test_buyer_redirected_home(self):
        resp = self.client.post(reverse('login'), {'username': 'buyer', 'password': 'pw123456'})
        self.assertRedirects(resp, reverse('homepage'))

    def test_staff_redirected_to_dashboard(self):
        resp = self.client.post(reverse('login'), {'username': 'staff', 'password': 'pw123456'})
        self.assertRedirects(resp, reverse('admin-dashboard'))

    def test_invalid_credentials_rejected(self):
        resp = self.client.post(reverse('login'), {'username': 'buyer', 'password': 'wrong'})
        self.assertContains(resp, 'Invalid username or password', status_code=200)
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_login_throttled_after_repeated_failures(self):
        for _ in range(5):
            self.client.post(reverse('login'), {'username': 'buyer', 'password': 'wrong'})
        resp = self.client.post(reverse('login'), {'username': 'buyer', 'password': 'wrong'})
        self.assertContains(resp, 'Too many failed attempts', status_code=200)

    def test_register_creates_user(self):
        resp = self.client.post(reverse('register'), {
            'username': 'newbuyer', 'password1': 'StrongPass123!', 'password2': 'StrongPass123!',
        })
        self.assertRedirects(resp, reverse('login'))
        self.assertTrue(User.objects.filter(username='newbuyer').exists())


class LogoutTests(TestCase):
    def test_logout_requires_post(self):
        User.objects.create_user('buyer', password='pw123456')
        self.client.login(username='buyer', password='pw123456')
        self.assertEqual(self.client.get(reverse('logout')).status_code, 405)
        resp = self.client.post(reverse('logout'))
        self.assertRedirects(resp, reverse('homepage'))


class CheckoutHCaptchaTests(TestCase):
    """hCaptcha now guards order placement (payments/checkout area)."""

    def setUp(self):
        import datetime
        from decimal import Decimal

        from books.models import Book, Category
        from userpage.models import Cart

        self.buyer = User.objects.create_user('buyer', password='pw123456')
        category = Category.objects.create(category_name='Fiction')
        book = Book.objects.create(
            name='Dune', author='Herbert', price=Decimal('19.99'),
            image_url='http://x/y.jpg', description='Epic sci-fi novel',
            published_date=datetime.date(2020, 1, 1), category=category,
        )
        self.book = book
        self.cart = Cart.objects.create(user=self.buyer, book=book)
        self.client.force_login(self.buyer)

    def _order_url(self):
        return reverse('user-order', args=[self.cart.id, self.book.id])

    def _order_data(self, **overrides):
        data = {
            'quantity': 1, 'address': 'Kathmandu',
            'contact_no': '+9779800000000',
        }
        data.update(overrides)
        return data

    def _order_count(self):
        from userpage.models import Order
        return Order.objects.filter(user=self.buyer).count()

    @override_settings(HCAPTCHA_ENABLED=True, HCAPTCHA_SITEKEY='s', HCAPTCHA_SECRET='x')
    def test_order_blocked_without_captcha_token(self):
        resp = self.client.post(self._order_url(), self._order_data())
        self.assertContains(resp, 'Please complete the CAPTCHA', status_code=200)
        self.assertEqual(self._order_count(), 0)

    @override_settings(HCAPTCHA_ENABLED=True, HCAPTCHA_SITEKEY='s', HCAPTCHA_SECRET='x')
    def test_order_passes_with_valid_captcha(self):
        with mock.patch('accounts.security.requests.post') as fake_post:
            fake_post.return_value.json.return_value = {'success': True}
            resp = self.client.post(
                self._order_url(),
                self._order_data(**{'h-captcha-response': 'token123'}),
            )
        self.assertRedirects(resp, reverse('myorders'))
        self.assertEqual(self._order_count(), 1)

    @override_settings(HCAPTCHA_ENABLED=True, HCAPTCHA_SITEKEY='s', HCAPTCHA_SECRET='x')
    def test_order_blocked_when_captcha_rejected(self):
        with mock.patch('accounts.security.requests.post') as fake_post:
            fake_post.return_value.json.return_value = {'success': False}
            resp = self.client.post(
                self._order_url(),
                self._order_data(**{'h-captcha-response': 'token123'}),
            )
        self.assertContains(resp, 'Please complete the CAPTCHA', status_code=200)
        self.assertEqual(self._order_count(), 0)

    def test_captcha_not_required_when_disabled(self):
        resp = self.client.post(self._order_url(), self._order_data())
        self.assertRedirects(resp, reverse('myorders'))
        self.assertEqual(self._order_count(), 1)
