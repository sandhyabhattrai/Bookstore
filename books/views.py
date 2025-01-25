from django.shortcuts import render
from django.http import HttpResponse

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
    list_all_books = [
    {
        "name": "Palpasa Cafe",
        "author" : "Narayan Wagle",
        "price" : "NRP 395",
        "instock" : "yes",
        "description" : "A thought-provoking novel about love, art, and the impact of Nepal's Maoist insurgency, told through the eyes of an artist.",
        "published_date" : "2005"
    },

    {
        "name": "Karnali Blues",
        "author" : "Buddhi Sagar",
        "price" : "NRP 480",
        "instock" : "no",
        "description" : "A beautifully written coming-of-age story about a boy and his relationship with his ailing father, set in the Karnali region.",
        "published_date" : "2010"
    },

    {
        "name": "Shirishko Phool",
        "author" : "Parijat",
        "price" : "NPR 200",
        "instock" : "yes",
        "description" : " A classic Nepali novel that delves into existentialism, unfulfilled love, and the human condition.",
        "published_date" : "1964"
    },

    {
        "name": "Atomic Habits",
        "author" : "James Charles",
        "price" : "NRP 750",
        "instock" : "no",
        "description" : "A guide to building good habits and breaking bad ones using small, incremental changes.",
        "published_date" : "2018"
    },

    {
        "name": "The Fault in Our Stars",
        "author" : "John Green",
        "price" : "NRP 600",
        "instock" : "yes",
        "description" : "A heartwarming and heartbreaking love story about two teenagers, Hazel and Augustus, who meet at a cancer support group and navigate love, loss, and life's big questions together.",
        "published_date" : "2012"
    }
    ]
    contents = {
        'collection': list_all_books
    } 
    return render(request,"books/books.html",contents)
