from django.db import models

# Create your models here

class Category(models.Model):
    category_name = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.category_name}"

class Book(models.Model):
    name = models.CharField(max_length=100)
    author = models.CharField(max_length=200)
    price = models.DecimalField(max_digits=6, decimal_places=2)
    instock = models.BooleanField(default=True)
    # Legacy external URL. Kept for existing rows; prefer `image` for new uploads.
    image_url = models.CharField(max_length=300, blank=True, default='')
    # S3-backed (or local MEDIA_ROOT) upload. See settings USE_S3 / STORAGES.
    image = models.ImageField(upload_to='books/', blank=True, null=True)
    description = models.TextField()
    published_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    # PROTECT: deleting a category with books must fail instead of wiping books.
    category = models.ForeignKey(Category, on_delete=models.PROTECT)

    def __str__(self):
        return f"{self.name} ({self.author})"

    @property
    def cover_url(self):
        if self.image:
            try:
                return self.image.url
            except ValueError:
                pass
        return self.image_url or ''

