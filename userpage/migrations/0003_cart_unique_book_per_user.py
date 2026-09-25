# Generated for Cart per-user book uniqueness.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('userpage', '0002_order_total_price_status'),
    ]

    operations = [
        migrations.AddConstraint(
            model_name='cart',
            constraint=models.UniqueConstraint(fields=('user', 'book'), name='unique_cart_book_per_user'),
        ),
    ]
