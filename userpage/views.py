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

from . import payments
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
        'khalti_enabled': payments.khalti_enabled(),
        'payments_test_mode': settings.PAYMENTS_TEST_MODE,
        'payment_choices': [c[0] for c in Order.PAYMENT],
    }


def _complete_online_order(order):
    """Mark a verified online order paid and clear its cart row."""
    order.payment_status = True
    order.status = Order.STATUS_PENDING
    order.save(update_fields=['payment_status', 'status'])
    Cart.objects.filter(user=order.user, book=order.book).delete()


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
            method = request.POST.get('payment_method', Order.PAYMENT_COD)
            if method not in dict(Order.PAYMENT):
                method = Order.PAYMENT_COD
            if method == Order.PAYMENT_COD:
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
            # Online (test-mode) flow: create the unpaid order first so the
            # gateway reference is stable, then hand off to the provider.
            ref = payments.new_payment_ref('order')
            order = Order.objects.create(
                book=book,
                user=user,
                quantity=quantity,
                total_price=total_price,
                payment_method=method,
                payment_ref=ref,
                contact_no=data['contact_no'],
                address=data['address'],
                status=Order.STATUS_PENDING,
                payment_status=False,
            )
            if method == Order.PAYMENT_ESEWA:
                success_url = request.build_absolute_uri(reverse('esewa-success'))
                failure_url = request.build_absolute_uri(reverse('esewa-failure'))
                return render(request, 'client/payments/esewa_redirect.html', {
                    'order': order,
                    'form_url': payments.esewa_config()['form_url'],
                    'fields': payments.esewa_initiate_fields(
                        order, ref, success_url, failure_url
                    ),
                    'payments_test_mode': settings.PAYMENTS_TEST_MODE,
                })
            # Khalti: initiate server-side, then redirect the buyer.
            amount_paisa = int(total_price * 100)
            site_url = f'{request.scheme}://{request.get_host()}'
            pidx, payment_url = payments.khalti_initiate(
                amount_paisa=amount_paisa,
                purchase_order_id=ref,
                purchase_order_name=f'Bookstore order: {book.name}'[:60],
                return_url=request.build_absolute_uri(reverse('khalti-return')),
                website_url=site_url,
                customer_name=user.username,
            )
            if pidx is None:
                order.delete()
                messages.add_message(request, messages.ERROR, payment_url)
                return render(request, 'client/orderform.html', _order_context(form, book=book, cart=cart))
            order.payment_ref = pidx
            order.save(update_fields=['payment_ref'])
            return redirect(payment_url)
        messages.add_message(request, messages.ERROR, 'Order Failed')
        return render(request, 'client/orderform.html', _order_context(form, book=book, cart=cart))
    return render(request, 'client/orderform.html', _order_context(OrderForm(), book=book, cart=cart))


@login_required
@user_only
def esewa_success(request):
    """eSewa redirect target: verify signature + status, then confirm."""
    payload = payments.esewa_decode_callback(request.GET.get('data', ''))
    if payload is None:
        messages.add_message(request, messages.ERROR, 'Invalid payment response from eSewa.')
        return redirect(reverse('myorders'))
    order = Order.objects.filter(
        payment_ref=payload.get('transaction_uuid', ''),
        payment_method=Order.PAYMENT_ESEWA,
    ).first()
    if order is None or order.user_id != request.user.id:
        messages.add_message(request, messages.ERROR, 'Order not found for this payment.')
        return redirect(reverse('myorders'))
    if not payments.esewa_verify_signature(payload):
        messages.add_message(request, messages.ERROR, 'Payment verification failed (bad signature).')
        return redirect(reverse('myorders'))
    status = payments.esewa_status_check(
        payload['product_code'], str(payload['total_amount']), payload['transaction_uuid']
    )
    if status is not None and status != 'COMPLETE':
        messages.add_message(request, messages.ERROR, f'eSewa reports status: {status}.')
        return redirect(reverse('myorders'))
    _complete_online_order(order)
    messages.add_message(request, messages.SUCCESS, 'eSewa payment verified. Order placed successfully.')
    return redirect(reverse('myorders'))


@login_required
@user_only
def esewa_failure(request):
    messages.add_message(request, messages.ERROR, 'eSewa payment failed or was cancelled. Your order is still pending.')
    return redirect(reverse('myorders'))


@login_required
@user_only
def khalti_return(request):
    """Khalti redirect target: look up pidx, confirm only on Completed."""
    pidx = request.GET.get('pidx', '')
    if not pidx:
        messages.add_message(request, messages.ERROR, 'Khalti payment was cancelled.')
        return redirect(reverse('myorders'))
    order = Order.objects.filter(
        payment_ref=pidx, payment_method=Order.PAYMENT_KHALTI
    ).first()
    if order is None or order.user_id != request.user.id:
        messages.add_message(request, messages.ERROR, 'Order not found for this payment.')
        return redirect(reverse('myorders'))
    if payments.khalti_lookup(pidx) == 'Completed':
        _complete_online_order(order)
        messages.add_message(request, messages.SUCCESS, 'Khalti payment verified. Order placed successfully.')
    else:
        messages.add_message(request, messages.ERROR, 'Khalti payment not completed. Your order is still pending.')
    return redirect(reverse('myorders'))


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
