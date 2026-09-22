# Online gateways shelved: payment_method back to Cash on Delivery only.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('userpage', '0003_cart_unique_book_per_user'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='payment_method',
            field=models.CharField(
                choices=[('Cash on Delivery', 'Cash on Delivery')],
                default='Cash on Delivery',
                max_length=100,
            ),
        ),
    ]
