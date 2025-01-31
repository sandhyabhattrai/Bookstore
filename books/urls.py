from django.urls import path 
from . import views

urlpatterns = [
    path('index/', views.index),
    path('home/', views.homepage),
    path('contact/',views.contact),
    path('categories/',views.get_all_categories,name="get-all-categories"),
    path('collection/',views.all_books, name= "get-all-books"),
    # path('bookdetail/<int:id>/', views.get_book_by_id, name="book-detail")
]
