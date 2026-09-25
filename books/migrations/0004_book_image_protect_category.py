# Generated for: PROTECT category deletes, S3-ready book image field

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('books', '0003_book_category'),
    ]

    operations = [
        migrations.AlterField(
            model_name='book',
            name='category',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='books.category'),
        ),
        migrations.AlterField(
            model_name='book',
            name='imageUrl',
            field=models.CharField(blank=True, default='', max_length=300),
        ),
        migrations.AddField(
            model_name='book',
            name='image',
            field=models.ImageField(blank=True, null=True, upload_to='books/'),
        ),
    ]
