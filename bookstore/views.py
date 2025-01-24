from django.http import HttpResponse

def homepage(request):
    return HttpResponse("<h1> This is the Home page, </h1>")

def aboutus(request):
    return HttpResponse("<h1> This is the About section. </h1>")

def contactpage(request):
    return HttpResponse("<h1> This is the Contact Us page. </h1>")