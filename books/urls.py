from django.urls import path 
from . import views

urlpatterns = [
    path('index/', views.index),
    path('categories/',views.get_all_categories,name="get-all-categories"),
    path('',views.get_all_books, name= "get-all-books"),
    path('addcategory/',views.post_category,name="post-category"),
    path('deletecategory/<int:category_id>/',views.delete_category,name="delete-category"),
    path('updatecategory/<int:category_id>/',views.update_category,name="update-category"),
    # path('bookdetail/<int:id>/', views.get_book_by_id, name="book-detail"),
    path('addbook/',views.post_book,name="post-book"),
    path('deletebook/<int:book_id>/',views.delete_book,name="delete-book"),
    path('updatebook/<int:book_id>/',views.update_book,name="update-book"),
]
