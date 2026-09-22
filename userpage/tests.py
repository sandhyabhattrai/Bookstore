import datetime
from decimal import Decimal

from books.models import Book, Category
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import Cart, Order


def make_book(name='Dune', category=None):
    category = category or Category.objects.create(category_name='Fiction')
    return Book.objects.create(
        name=name, author='Herbert', price=Decimal('19.99'),
        image_url='http://x/y.jpg', description='Epic sci-fi novel',
        published_date=datetime.date(2020, 1, 1), category=category,
    )


def make_users():
    buyer = User.objects.create_user('buyer', password='pw123456')
    staff = User.objects.create_user('staff', password='pw123456')
    staff.is_staff = True
    staff.save()
    return buyer, staff


class CartTests(TestCase):
    def setUp(self):
        self.buyer, _ = make_users()
        self.book = make_book()
        self.client.force_login(self.buyer)

    def test_add_to_cart_requires_post(self):
        self.assertEqual(
            self.client.get(reverse('add-to-cart', args=[self.book.id])).status_code, 405
        )
        self.assertFalse(Cart.objects.exists())

    def test_add_to_cart_creates(self):
        resp = self.client.post(reverse('add-to-cart', args=[self.book.id]))
        self.assertRedirects(resp, reverse('cart'))
        self.assertTrue(Cart.objects.filter(user=self.buyer, book=self.book).exists())

    def test_add_duplicate_book_rejected(self):
        Cart.objects.create(user=self.buyer, book=self.book)
        resp = self.client.post(reverse('add-to-cart', args=[self.book.id]), follow=True)
        self.assertContains(resp, 'already in your cart', status_code=200)
        self.assertEqual(Cart.objects.filter(user=self.buyer).count(), 1)

    def test_delete_from_cart_requires_post(self):
        cart = Cart.objects.create(user=self.buyer, book=self.book)
        self.assertEqual(
            self.client.get(reverse('delete-from-cart', args=[cart.id])).status_code, 405
        )
        self.assertTrue(Cart.objects.filter(pk=cart.pk).exists())

    def test_delete_from_cart(self):
        cart = Cart.objects.create(user=self.buyer, book=self.book)
        resp = self.client.post(reverse('delete-from-cart', args=[cart.id]))
        self.assertRedirects(resp, reverse('cart'))
        self.assertFalse(Cart.objects.filter(pk=cart.pk).exists())

    def test_cannot_delete_other_users_cart(self):
        other = User.objects.create_user('other', password='pw123456')
        cart = Cart.objects.create(user=other, book=self.book)
        self.client.post(reverse('delete-from-cart', args=[cart.id]))
        self.assertTrue(Cart.objects.filter(pk=cart.pk).exists())


class OrderTests(TestCase):
    def setUp(self):
        self.buyer, self.staff = make_users()
        self.book = make_book()
        self.client.force_login(self.buyer)
        self.cart = Cart.objects.create(user=self.buyer, book=self.book)

    def _order_data(self, **overrides):
        data = {
            'quantity': 2, 'address': 'Kathmandu',
            'contact_no': '+9779800000000',
        }
        data.update(overrides)
        return data

    def test_cash_order_clears_cart_and_totals_exact(self):
        resp = self.client.post(
            reverse('user-order', args=[self.cart.id, self.book.id]), self._order_data()
        )
        self.assertRedirects(resp, reverse('myorders'))
        order = Order.objects.get(user=self.buyer)
        self.assertEqual(str(order.total_price), '39.98')
        self.assertEqual(order.payment_method, Order.PAYMENT_COD)
        self.assertEqual(order.status, Order.STATUS_PENDING)
        self.assertFalse(order.payment_status)
        self.assertFalse(Cart.objects.filter(pk=self.cart.pk).exists())

    def test_order_rejects_bad_contact(self):
        resp = self.client.post(
            reverse('user-order', args=[self.cart.id, self.book.id]),
            self._order_data(contact_no='abc'),
        )
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(Order.objects.exists())

    def test_cart_book_mismatch_rejected(self):
        other_book = make_book(name='Other')
        resp = self.client.post(
            reverse('user-order', args=[self.cart.id, other_book.id]), self._order_data()
        )
        self.assertRedirects(resp, reverse('cart'))
        self.assertFalse(Order.objects.exists())

    def test_cannot_order_other_users_cart(self):
        other = User.objects.create_user('other', password='pw123456')
        other_cart = Cart.objects.create(user=other, book=self.book)
        resp = self.client.post(
            reverse('user-order', args=[other_cart.id, self.book.id]), self._order_data()
        )
        self.assertEqual(resp.status_code, 404)
        self.assertFalse(Order.objects.exists())


class DeliverTests(TestCase):
    def setUp(self):
        self.buyer, self.staff = make_users()
        book = make_book()
        self.order = Order.objects.create(
            book=book, user=self.buyer, quantity=1, total_price=Decimal('19.99'),
            status=Order.STATUS_PENDING, payment_method='Cash on Delivery',
            contact_no='+9779800000000', address='Kathmandu',
        )

    def test_user_cannot_deliver(self):
        self.client.force_login(self.buyer)
        resp = self.client.post(reverse('mark-as-deliver', args=[self.order.id]))
        self.assertRedirects(resp, reverse('homepage'))
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, Order.STATUS_PENDING)

    def test_deliver_requires_post(self):
        self.client.force_login(self.staff)
        self.assertEqual(
            self.client.get(reverse('mark-as-deliver', args=[self.order.id])).status_code,
            405,
        )

    def test_staff_can_deliver(self):
        self.client.force_login(self.staff)
        resp = self.client.post(reverse('mark-as-deliver', args=[self.order.id]))
        self.assertRedirects(resp, reverse('all-orders'))
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, Order.STATUS_DELIVERED)


class PageTests(TestCase):
    def test_book_details_404(self):
        self.assertEqual(
            self.client.get(reverse('book-details', args=[999])).status_code, 404
        )

    def test_bookpage_paginates(self):
        for i in range(13):
            make_book(name=f'Book {i:02d}')
        resp = self.client.get(reverse('bookpage') + '?page=2')
        self.assertEqual(resp.status_code, 200)
        self.assertIn('Page 2 of 2', resp.content.decode())

    def test_search_filters_by_name_and_author(self):
        make_book(name='Palpasa Cafe', category=None)
        resp = self.client.get(reverse('bookpage') + '?q=palpasa')
        self.assertEqual(resp.status_code, 200)
        content = resp.content.decode()
        self.assertIn('Palpasa Cafe', content)
        self.assertIn('result', content)

    def test_search_empty_state(self):
        resp = self.client.get(reverse('bookpage') + '?q=zzz-no-such-book')
        self.assertEqual(resp.status_code, 200)
        self.assertIn('No books found', resp.content.decode())
