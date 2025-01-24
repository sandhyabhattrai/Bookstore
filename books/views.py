from django.shortcuts import render
from django.http import HttpResponse

# Create your views here.
def index(request):
    return HttpResponse('This is the first page. ')

def homepage(request):
    return render(request,"books/index.html")


