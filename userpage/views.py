from django.contrib import messages
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db import IntegrityError
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from accounts.auth import admin_only, user_only
from accounts.security import hcaptcha_enabled, verify_hcaptcha
from books.models import Book

from .forms import OrderForm
from .models import Cart, Order


def homepage(request):
    books = Book.objects.select_related('category').all().order_by('-id')[:8]
    return render(request, 'client/homepage.html', {
        'books': books,
    })


def bookpage(request):
    query = request.GET.get('q', '').strip()
    books = Book.objects.select_related('category').all().order_by('-created_at')
    if query:
        books = books.filter(Q(name__icontains=query) | Q(author__icontains=query))
    paginator = Paginator(books, 12)
    return render(request, 'client/bookpage.html', {
        'books': paginator.get_page(request.GET.get('page')),
        'query': query,
    })


def book_details(request, book_id):
    book = get_object_or_404(Book, id=book_id)
    return render(request, 'client/bookdetail.html', {'book': book})


@login_required
@user_only
@require_POST
def add_to_cart(request, book_id):
    user = request.user
    book = get_object_or_404(Book, id=book_id)

    if Cart.objects.filter(user=user, book=book).exists():
        messages.add_message(request, messages.ERROR, 'This book is already in your cart')
        return redirect(reverse('bookpage'))
    try:
        Cart.objects.create(user=user, book=book)
    except IntegrityError:
        messages.add_message(request, messages.ERROR, 'This book is already in your cart')
        return redirect(reverse('bookpage'))
    messages.add_message(request, messages.SUCCESS, 'Book added to cart successfully')
    return redirect(reverse('cart'))


@login_required
@user_only
def cart_page(request):
    carts = Cart.objects.select_related('book').filter(user=request.user)
    cart_items = list(carts)
    cart_total = sum((item.book.price for item in cart_items), 0)
    return render(request, 'client/cart.html', {
        'carts': cart_items,
        'cart_total': cart_total,
        'cart_count': len(cart_items),
    })


@login_required
@user_only
@require_POST
def delete_from_cart(request, cart_id):
    Cart.objects.filter(user=request.user, id=cart_id).delete()
    messages.add_message(request, messages.SUCCESS, 'Book removed from cart successfully')
    return redirect(reverse('cart'))


def _order_context(form, book=None, cart=None):
    return {
        'form': form,
        'book': book,
        'cart': cart,
        'hcaptcha_enabled': hcaptcha_enabled(),
        'hcaptcha_sitekey': settings.HCAPTCHA_SITEKEY,
    }


@login_required
@user_only
def user_order(request, cart_id, book_id):
    user = request.user
    book = get_object_or_404(Book, id=book_id)
    cart = get_object_or_404(Cart, id=cart_id, user=user)
    if cart.book_id != book.id:
        messages.add_message(request, messages.ERROR, 'Cart item does not match this book.')
        return redirect(reverse('cart'))
    if request.method == 'POST':
        form = OrderForm(request.POST)
        if hcaptcha_enabled() and not verify_hcaptcha(
            request.POST.get('h-captcha-response', ''), request.META.get('REMOTE_ADDR')
        ):
            messages.add_message(request, messages.ERROR, 'Please complete the CAPTCHA.')
            return render(request, 'client/orderform.html', _order_context(form, book=book, cart=cart))
        if form.is_valid():
            data = form.cleaned_data
            quantity = data['quantity']
            total_price = quantity * book.price
            Order.objects.create(
                book=book,
                user=user,
                quantity=quantity,
                total_price=total_price,
                payment_method=Order.PAYMENT_COD,
                contact_no=data['contact_no'],
                address=data['address'],
                status=Order.STATUS_PENDING,
                payment_status=False,
            )
            cart.delete()
            messages.add_message(request, messages.SUCCESS, 'Order placed successfully')
            return redirect(reverse('myorders'))
        messages.add_message(request, messages.ERROR, 'Order Failed')
        return render(request, 'client/orderform.html', _order_context(form, book=book, cart=cart))
    return render(request, 'client/orderform.html', _order_context(OrderForm(), book=book, cart=cart))


@login_required
@user_only
def show_myorder(request):
    orders = Order.objects.select_related('book').filter(user=request.user).order_by('-ordered_at')
    paginator = Paginator(orders, 12)
    return render(request, 'client/myorder.html', {
        'orders': paginator.get_page(request.GET.get('page')),
    })


@login_required
@admin_only
@require_POST
def mark_as_deliver(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    order.status = Order.STATUS_DELIVERED
    order.save(update_fields=['status'])
    messages.add_message(request, messages.SUCCESS, 'Order marked as delivered')
    return redirect(reverse('all-orders'))
