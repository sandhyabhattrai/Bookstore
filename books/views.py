from django.shortcuts import render
from django.http import HttpResponse
from .data import list_all_books

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
    contents = {
        'collection': list_all_books
    } 
    return render(request,"books/collection.html",contents)

def get_book_by_id(request,id):
    book = [book for book in list_all_books if book["id"]== id]
    return render(request,"book/book_detail.html",{
        'book': book
    })

