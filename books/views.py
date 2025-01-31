from django.shortcuts import render
from django.http import HttpResponse
from .models import Book,Category

# Create your views here.
def index(request):
    return HttpResponse('This is the first page. ')

def homepage(request):
    context = {
        'name': "Sandhya Bhattarai",
        'course': "Python django"
    }
    return render(request,"books/index.html",context)

def contact(request):
    return render(request,"books/second.html",{
    'name': "sandhya bhattarai",
    'phone': "9812345678"
    })


def all_books(request):
    allbooks = Book.objects.all()
    return render(request,"books/collection.html",{
        'books': allbooks
    })

# def get_book_by_id(request,id):
#     data ={}
#     for book in list_all_books:
#         if book["id"] == int(id):
#             data["id"] = int(id)
#             data["name"] =  book["name"] 
#     return render(request,"books/book_detail.html",{
#         'book': data
#     })


def get_all_categories(request):
    all_categories = Category.object.all()
    return render(request,"books/allcategories.html",{
        'categories': all_categories
    })