from django.shortcuts import render,redirect
from django.http import HttpResponse
from django.contrib import messages
from . models import Book,Category
from . forms import CategoryForm, BookForm

# Create your views here.
def index(request):
    return HttpResponse('This is the first page. ')


# function to get all categories
def get_all_categories(request):
    all_categories = Category.object.all()
    return render(request,"books/category/allcategories.html",{
        'categories': all_categories
    })


# function to create a category
def post_category(request):
    if request.method == "POST":
        form = CategoryForm(request.POST)
        if form.is_valid():
            form.save()
            messages.add_message(request,messages.SUCCESS,"Category added successfully")
            return redirect("/books/categories/")
        else:
            messages.add_message(request,messages.ERROR,"Failed to add category")
            return render(request,"books/category/postcategory.html",{'form': form})
    return render(request,"books/category/postcategory.html",{
        'form': CategoryForm
    })

# function to delete a category
def delete_category(request,category_id):
    category = Category.objects.get(id=category_id)
    category.delete()
    messages.add_message(request,messages.SUCCESS,"Category deleted successfully")
    return redirect("/books/categories/")


# function to update a category
def update_category(request,category_id):
    category = Category.objects.get(id=category_id)
    if request.method == "POST":
        form = CategoryForm(request.POST,instance=category)
        if form.is_valid():
            form.save()
            messages.add_message(request,messages.SUCCESS,"Category updated successfully")
            return redirect("/books/categories/")
        else:
            messages.add_message(request,messages.ERROR,"Failed to update category")
            return render(request,"books/category/updatecategory.html",{'form': form})
    return render(request,"books/category/updatecategory.html",{

        'form': CategoryForm(instance=category)
    }
)

# get all books 
def get_all_books(request):
    all_books = Book.objects.all()
    return render(request,"books/book/allbooks.html",{
        'books': all_books
    })

# post book
def post_book(request):
    if request.method == 'POST':
        form = BookForm(request.POST)
        if form.is_valid():
            form.save()
            messages.add_message(request,messages.SUCCESS,'Book Added Successfully')
            return redirect('/books/') #http://localhost:8000/books
        else:
            messages.add_message(request,messages.ERROR,'Failed to Add book')
            return render(request,'books/book/postbook.html',{'form': form})
        
    return render(request,"books/postbook.html",{
        'form': BookForm
    }
    )


# delete book
def delete_book(request,book_id):
    book = Book.objects.get(pk=book_id)
    book.delete()
    messages.add_message(request,messages.SUCCESS,'Book Deleted Successfully')
    return redirect('/books/')


# update book
def update_book(request,book_id):
    book = Book.objects.get(pk=book_id)
    if request.method == 'POST':
        form = BookForm(request.POST,instance=book)
        if form.is_valid():
            form.save()
            messages.add_message(request,messages.SUCCESS,'Book Updated Successfully')
            return redirect('/books/')
        else:
            messages.add_message(request,messages.ERROR,'Failed to Update book')
            return render(request,'books/book/updatebook.html',{'form': form})
    return render(request,'books/book/updatebook.html',{
        'form': BookForm(instance=book)
    })
