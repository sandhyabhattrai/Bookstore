# Sandbox gateways: eSewa (UAT) + Khalti (sandbox) join Cash on Delivery.
# payment_ref stores the eSewa transaction_uuid or Khalti pidx.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('userpage', '0004_payment_cod_only'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='payment_method',
            field=models.CharField(
                choices=[
                    ('Cash on Delivery', 'Cash on Delivery'),
                    ('eSewa', 'eSewa'),
                    ('Khalti', 'Khalti'),
                ],
                default='Cash on Delivery',
                max_length=100,
            ),
        ),
        migrations.AddField(
            model_name='order',
            name='payment_ref',
            field=models.CharField(blank=True, default='', max_length=100),
        ),
    ]
