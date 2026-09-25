# Generated for: pending online orders (Decimal total, status choices)

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('userpage', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='total_price',
            field=models.DecimalField(decimal_places=2, max_digits=8, null=True),
        ),
        migrations.AlterField(
            model_name='order',
            name='status',
            field=models.CharField(
                choices=[('Pending...', 'Pending'), ('Delivered...', 'Delivered')],
                default='Pending...',
                max_length=100,
            ),
        ),
    ]
