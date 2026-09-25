# Generated rename: Book.imageUrl -> Book.image_url (no data change).

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('books', '0004_book_image_protect_category'),
    ]

    operations = [
        migrations.RenameField(
            model_name='book',
            old_name='imageUrl',
            new_name='image_url',
        ),
    ]
