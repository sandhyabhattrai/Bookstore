import datetime
import shutil
import tempfile
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django.urls import reverse

from userpage.models import Cart, Order

from .models import Book, Category


def make_book(name='Dune', author='Herbert', price=Decimal('19.99'), category=None):
    category = category or Category.objects.create(category_name='Fiction')
    return Book.objects.create(
        name=name, author=author, price=price, image_url='http://x/y.jpg',
        description='Epic sci-fi novel', published_date=datetime.date(2020, 1, 1),
        category=category,
    )


class StaffRequiredTests(TestCase):
    def setUp(self):
        self.buyer = User.objects.create_user('buyer', password='pw123456')
        staff = User.objects.create_user('staff', password='pw123456')
        staff.is_staff = True
        staff.save()
        self.staff = staff

    def test_anonymous_redirected_to_login(self):
        resp = self.client.get(reverse('get-all-books'))
        self.assertEqual(resp.status_code, 302)
        self.assertIn(reverse('login'), resp['Location'])

    def test_non_staff_bounced_to_homepage(self):
        self.client.force_login(self.buyer)
        resp = self.client.get(reverse('get-all-books'))
        self.assertRedirects(resp, reverse('homepage'))


class CategoryTests(TestCase):
    def setUp(self):
        staff = User.objects.create_user('staff', password='pw123456')
        staff.is_staff = True
        staff.save()
        self.client.force_login(staff)

    def test_post_category_creates(self):
        resp = self.client.post(reverse('post-category'), {'category_name': 'Sci-Fi'})
        self.assertRedirects(resp, reverse('get-all-categories'))
        self.assertTrue(Category.objects.filter(category_name='Sci-Fi').exists())

    def test_delete_empty_category(self):
        cat = Category.objects.create(category_name='Empty')
        resp = self.client.post(reverse('delete-category', args=[cat.id]))
        self.assertRedirects(resp, reverse('get-all-categories'))
        self.assertFalse(Category.objects.filter(pk=cat.pk).exists())

    def test_delete_category_with_books_blocked(self):
        cat = Category.objects.create(category_name='Used')
        make_book(category=cat)
        resp = self.client.post(reverse('delete-category', args=[cat.id]), follow=True)
        self.assertContains(resp, 'still use it', status_code=200)
        self.assertTrue(Category.objects.filter(pk=cat.pk).exists())
        self.assertEqual(Book.objects.filter(category=cat).count(), 1)

    def test_delete_category_requires_post(self):
        cat = Category.objects.create(category_name='Empty')
        self.assertEqual(
            self.client.get(reverse('delete-category', args=[cat.id])).status_code, 405
        )
        self.assertTrue(Category.objects.filter(pk=cat.pk).exists())

    def test_update_category(self):
        cat = Category.objects.create(category_name='Old')
        resp = self.client.post(
            reverse('update-category', args=[cat.id]), {'category_name': 'New'}
        )
        self.assertRedirects(resp, reverse('get-all-categories'))
        self.assertEqual(Category.objects.get(pk=cat.pk).category_name, 'New')

    def test_category_404(self):
        self.assertEqual(
            self.client.post(reverse('delete-category', args=[999])).status_code, 404
        )


class BookTests(TestCase):
    @classmethod
    def setUpClass(cls):
        cls._media = tempfile.mkdtemp()
        cls._media_override = override_settings(MEDIA_ROOT=cls._media)
        cls._media_override.enable()
        super().setUpClass()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        cls._media_override.disable()
        shutil.rmtree(cls._media, ignore_errors=True)

    def setUp(self):
        staff = User.objects.create_user('staff', password='pw123456')
        staff.is_staff = True
        staff.save()
        self.client.force_login(staff)
        self.cat = Category.objects.create(category_name='Fiction')

    def _book_data(self, **overrides):
        data = {
            'name': 'Dune', 'author': 'Herbert', 'price': '19.99',
            'description': 'Epic sci-fi novel', 'published_date': '2020-01-01',
            'category': self.cat.pk,
        }
        data.update(overrides)
        return data

    def test_post_book_creates(self):
        resp = self.client.post(reverse('post-book'), self._book_data())
        self.assertRedirects(resp, reverse('get-all-books'))
        self.assertTrue(Book.objects.filter(name='Dune').exists())

    def test_post_book_rejects_negative_price(self):
        resp = self.client.post(reverse('post-book'), self._book_data(price='-5'))
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(Book.objects.exists())

    def test_delete_book_requires_post(self):
        book = make_book(category=self.cat)
        self.assertEqual(
            self.client.get(reverse('delete-book', args=[book.id])).status_code, 405
        )
        self.assertTrue(Book.objects.filter(pk=book.pk).exists())

    def test_delete_book(self):
        book = make_book(category=self.cat)
        resp = self.client.post(reverse('delete-book', args=[book.id]))
        self.assertRedirects(resp, reverse('get-all-books'))
        self.assertFalse(Book.objects.filter(pk=book.pk).exists())

    def test_update_book_saves_files(self):
        from django.core.files.uploadedfile import SimpleUploadedFile
        book = make_book(category=self.cat)
        gif = (
            b'GIF89a\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xff\xff\xff!\xf9\x04\x00\x00\x00\x00\x00,\x00\x00\x00\x00'
            b'\x01\x00\x01\x00\x00\x02\x02D\x01\x00;'
        )
        resp = self.client.post(
            reverse('update-book', args=[book.id]),
            {**self._book_data(name='Dune Messiah'),
             'image': SimpleUploadedFile('cover.gif', gif, 'image/gif')},
        )
        self.assertRedirects(resp, reverse('get-all-books'))
        book.refresh_from_db()
        self.assertEqual(book.name, 'Dune Messiah')
        self.assertTrue(bool(book.image))

    def test_dashboard_counts(self):
        buyer = User.objects.create_user('buyer', password='pw123456')
        book = make_book(category=self.cat)
        Order.objects.create(
            book=book, user=buyer, quantity=1, total_price=Decimal('19.99'),
            status=Order.STATUS_DELIVERED, payment_method='Cash on Delivery',
            contact_no='+9779800000000', address='Kathmandu',
        )
        resp = self.client.get(reverse('admin-dashboard'))
        self.assertEqual(resp.status_code, 200)
        content = resp.content.decode()
        for needle in ['Delivered: 1', 'Active: 1', 'In Stock: 1', 'Categories: 1', 'Admins: 1']:
            self.assertIn(needle, content)

    def test_book_list_paginates(self):
        for i in range(21):
            make_book(name=f'Book {i:02d}', category=self.cat)
        resp = self.client.get(reverse('get-all-books') + '?page=2')
        self.assertEqual(resp.status_code, 200)
        self.assertIn('Page 2 of 2', resp.content.decode())
