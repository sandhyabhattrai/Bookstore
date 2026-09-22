from django.db import models
from django.contrib.auth.models import User
from books.models import Book

# Create your models here.

class Cart(models.Model):
    user = models.ForeignKey(User,on_delete = models.CASCADE)
    book = models.ForeignKey(Book,on_delete = models.CASCADE)
    created_at = models.DateTimeField(auto_now_add = True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['user', 'book'], name='unique_cart_book_per_user'),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.book.name}"
    

class Order(models.Model):
    PAYMENT_COD = 'Cash on Delivery'
    # Online gateways (Esewa/Khalti) shelved for now — COD is the only
    # method. Re-add choices here when gateway integration returns.
    PAYMENT = (
        (PAYMENT_COD, PAYMENT_COD),
    )
    STATUS_PENDING = 'Pending...'
    STATUS_DELIVERED = 'Delivered...'
    STATUS = (
        (STATUS_PENDING, 'Pending'),
        (STATUS_DELIVERED, 'Delivered'),
    )
    book = models.ForeignKey(Book,on_delete=models.CASCADE)
    user = models.ForeignKey(User,on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1)
    total_price = models.DecimalField(max_digits=8, decimal_places=2, null=True)
    status = models.CharField(max_length=100,choices=STATUS,default=STATUS_PENDING)
    payment_method = models.CharField(max_length=100,choices=PAYMENT,default='Cash on Delivery')
    payment_status = models.BooleanField(default=False)
    contact_no = models.CharField(max_length=15)
    address = models.CharField(max_length=100)
    ordered_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.book.name}"
    