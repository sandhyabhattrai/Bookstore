from django import forms
from .models import Category,Book

class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['category_name']

class BookForm(forms.ModelForm):
    class Meta:
        model = Book
        exclude = ['created_at']

    def clean_price(self):
        price = self.cleaned_data['price']
        if price < 0:
            raise forms.ValidationError("Price can't be negative.") 
        return price

    def clean_name(self):
        name = self.cleaned_data.get('name')
        if not name:
            return name
        if not name[0].isupper():
            raise forms.ValidationError("Book name must start with capital letter.")
        return name

    def clean(self):
        cleaned_data = super().clean()
        name = (cleaned_data.get('name') or '').strip()
        description = (cleaned_data.get('description') or '').strip()
        author = (cleaned_data.get('author') or '').strip()
        if name and description and name.lower() == description.lower():
            raise forms.ValidationError("Book name and description can't be same.")
        if name and author and name.lower() == author.lower():
            raise forms.ValidationError("Book name and author name can't be same.")
        return cleaned_data
