from django.urls import path 
from . import views

urlpatterns = [
    path('index/', views.index),
    path('home/', views.homepage),
    path('contact/',views.contact),
    path('books/',views.all_books)
]