from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.db.models import ProtectedError
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from accounts.auth import admin_only
from userpage.models import Order

from .forms import BookForm, CategoryForm
from .models import Book, Category


@login_required
@admin_only
def get_all_categories(request):
    categories = Category.objects.all().order_by('category_name')
    paginator = Paginator(categories, 20)
    return render(request, "books/category/allcategories.html", {
        'categories': paginator.get_page(request.GET.get('page')),
    })


@login_required
@admin_only
def post_category(request):
    if request.method == "POST":
        form = CategoryForm(request.POST)
        if form.is_valid():
            form.save()
            messages.add_message(request, messages.SUCCESS, "Category added successfully")
            return redirect(reverse("get-all-categories"))
        messages.add_message(request, messages.ERROR, "Failed to add category")
        return render(request, "books/category/postcategory.html", {'form': form})

    return render(request, "books/category/postcategory.html", {
        'form': CategoryForm(),
    })


@login_required
@admin_only
@require_POST
def delete_category(request, category_id):
    # Books are PROTECTed: deletion fails if books still use this category.
    category = get_object_or_404(Category, id=category_id)
    try:
        category.delete()
    except ProtectedError:
        count = Book.objects.filter(category=category).count()
        messages.add_message(
            request, messages.ERROR,
            f"Cannot delete category: {count} book(s) still use it. "
            "Reassign or delete those books first."
        )
        return redirect(reverse("get-all-categories"))
    messages.add_message(request, messages.SUCCESS, "Category deleted successfully")
    return redirect(reverse("get-all-categories"))


@login_required
@admin_only
def update_category(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    if request.method == "POST":
        form = CategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            messages.add_message(request, messages.SUCCESS, "Category updated successfully")
            return redirect(reverse("get-all-categories"))
        messages.add_message(request, messages.ERROR, "Failed to update category")
        return render(request, "books/category/updatecategory.html", {'form': form})
    return render(request, "books/category/updatecategory.html", {
        'form': CategoryForm(instance=category),
    })


@login_required
@admin_only
def get_all_books(request):
    books = Book.objects.select_related('category').all().order_by('-created_at')
    paginator = Paginator(books, 20)
    return render(request, "books/book/allbooks.html", {
        'books': paginator.get_page(request.GET.get('page')),
    })


@login_required
@admin_only
def post_book(request):
    if request.method == 'POST':
        form = BookForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.add_message(request, messages.SUCCESS, 'Book Added Successfully')
            return redirect(reverse('get-all-books'))
        messages.add_message(request, messages.ERROR, 'Failed to Add book')
        return render(request, 'books/book/postbook.html', {'form': form})

    return render(request, "books/book/postbook.html", {
        'form': BookForm(),
    })


@login_required
@admin_only
@require_POST
def delete_book(request, book_id):
    book = get_object_or_404(Book, pk=book_id)
    book.delete()
    messages.add_message(request, messages.SUCCESS, 'Book Deleted Successfully')
    return redirect(reverse('get-all-books'))


@login_required
@admin_only
def update_book(request, book_id):
    book = get_object_or_404(Book, pk=book_id)
    if request.method == 'POST':
        form = BookForm(request.POST, request.FILES, instance=book)
        if form.is_valid():
            form.save()
            messages.add_message(request, messages.SUCCESS, 'Book Updated Successfully')
            return redirect(reverse('get-all-books'))
        messages.add_message(request, messages.ERROR, 'Failed to Update book')
        return render(request, 'books/book/updatebook.html', {'form': form})
    return render(request, 'books/book/updatebook.html', {
        'form': BookForm(instance=book),
    })


@login_required
@admin_only
def admin_dashboard(request):
    return render(request, "books/dashboard/dashboard.html", {
        'total_delivered': Order.objects.filter(status=Order.STATUS_DELIVERED).count(),
        'total_users': User.objects.filter(is_staff=False).count(),
        'total_books': Book.objects.filter(instock=True).count(),
        'pending_books': Order.objects.filter(status=Order.STATUS_PENDING).count(),
        'total_categories': Category.objects.count(),
        'total_admins': User.objects.filter(is_staff=True).count(),
    })


@login_required
@admin_only
def all_orders(request):
    orders = Order.objects.select_related('book', 'user').all().order_by('-ordered_at')
    paginator = Paginator(orders, 20)
    return render(request, "books/dashboard/orders.html", {
        'orders': paginator.get_page(request.GET.get('page')),
    })


@login_required
@admin_only
def customers(request):
    users = User.objects.all().order_by('-date_joined')
    paginator = Paginator(users, 20)
    return render(request, "books/dashboard/customers.html", {
        'users': paginator.get_page(request.GET.get('page')),
    })
